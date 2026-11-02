"""Carga local de cuponera y publicación de agregados mediante el Git ya configurado."""
import sys,json,secrets,threading,tempfile,os,re,time,subprocess,zipfile,webbrowser
from pathlib import Path
from datetime import datetime,timezone
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from urllib.parse import urlsplit,unquote
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.build-deps'))
from p0_ahorra import read_programs
MAX_UPLOAD=50*1024*1024

def atomic_json(path,value):
    temporary=path.with_suffix('.carga.tmp.json');temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8');temporary.replace(path)

def import_and_publish(root,filename,payload,progress,publisher=None):
    import msvcrt
    root=Path(root);logs=root/'registros';logs.mkdir(exist_ok=True)
    with (logs/'proceso.lock').open('a+b') as lock:
        lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0)
        try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        except OSError:raise ValueError('Hay otra actualización en curso. Espera a que termine y vuelve a cargar la cuponera.') from None
        staged=None
        try:
            if not filename.lower().endswith('.xlsx'):raise ValueError('Selecciona una cuponera Excel .xlsx')
            name=re.sub(r'[^\w. -]','_',Path(filename).name)
            if not name or name.startswith('.'):raise ValueError('El nombre del archivo no es válido')
            folder=root/'datos'/'fuentes'/'p0_ahorra';folder.mkdir(parents=True,exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=folder,suffix='.xlsx',prefix='.carga-',delete=False) as handle:handle.write(payload);staged=Path(handle.name)
            with zipfile.ZipFile(staged) as archive:
                if sum(i.file_size for i in archive.infolist())>200*1024*1024:raise ValueError('El Excel descomprimido supera el tamaño permitido')
            progress('Validando hojas, fechas y tiendas…')
            path=root/'sitio'/'data.js';text=path.read_text(encoding='utf-8');data=json.loads(text.split('=',1)[1].strip().rstrip(';'))
            programs=read_programs(staged,data['stores'])
            if not programs['stores']:raise ValueError('No hay tiendas de la cuponera que coincidan con la base del tablero')
            programs.update(sourceName=filename,importedAt=datetime.now(timezone.utc).isoformat())
            progress('Guardando la cuponera y actualizando P0/Ahorra+…')
            target=folder/name;staged.replace(target);staged=None
            config_path=root/'configuracion'/'config.local.json';config=json.loads(config_path.read_text(encoding='utf-8-sig'));config['p0_ahorra_source']=str(target.resolve());atomic_json(config_path,config)
            data.setdefault('productiveHours',{})['programs']=programs
            temporary=path.with_suffix('.carga.tmp.js');temporary.write_text('window.INVEX_DATA = '+json.dumps(data,ensure_ascii=False,allow_nan=False)+';\n',encoding='utf-8');temporary.replace(path)
            progress('Publicando el tablero y el HTML en GitHub…')
            if publisher:publisher(root)
            else:
                result=subprocess.run([sys.executable,'-X','utf8',str(root/'python'/'publicar_github.py')],cwd=root,text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=600)
                with (logs/'carga-cuponera.log').open('a',encoding='utf-8') as output:output.write('\n'+datetime.now(timezone.utc).isoformat()+'\n'+result.stdout+'\n'+result.stderr)
                if result.returncode:raise RuntimeError('La cuponera quedó guardada localmente, pero no se completó la publicación. Revisa registros/carga-cuponera.log y vuelve a intentarlo.')
            return programs
        finally:
            if staged and staged.exists():staged.unlink()
            lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)

class UploadApp:
    def __init__(self,root=ROOT,publisher=None):self.root=Path(root);self.publisher=publisher;self.token=secrets.token_urlsafe(32);self.state={'status':'idle','message':'Listo para cargar una cuponera'};self.busy=threading.Lock()
    def start(self,name,payload):
        if not self.busy.acquire(False):raise ValueError('Ya se está publicando otra cuponera')
        self.state={'status':'running','message':'Archivo recibido; iniciando validación…'}
        def worker():
            try:
                programs=import_and_publish(self.root,name,payload,lambda message:self.state.update(message=message),self.publisher)
                self.state={'status':'complete','message':'Cuponera publicada en GitHub. El despliegue de la página puede tardar unos minutos.','programs':programs}
            except Exception as error:self.state={'status':'error','message':str(error) if isinstance(error,(ValueError,RuntimeError)) else 'No se completó la carga. Revisa que el archivo sea una cuponera .xlsx válida.'}
            finally:self.busy.release()
        threading.Thread(target=worker,daemon=True).start()

def make_handler(app):
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(app.root/'sitio'),**kwargs)
        def log_message(self,*args):pass
        def end_headers(self):
            self.send_header('Cache-Control','no-store');self.send_header('X-Frame-Options','DENY');self.send_header('X-Content-Type-Options','nosniff');super().end_headers()
        def response(self,code,value):
            body=json.dumps(value,ensure_ascii=False).encode();self.send_response(code);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        def authorized(self):
            expected='http://'+self.headers.get('Host','')
            return self.headers.get('Host','') in {'127.0.0.1:'+str(self.server.server_port),'localhost:'+str(self.server.server_port)} and self.headers.get('Origin',expected)==expected and secrets.compare_digest(self.headers.get('X-INVEX-Token',''),app.token)
        def do_GET(self):
            route=urlsplit(self.path).path
            if route=='/api/cuponera/estado':
                if not self.authorized():return self.response(403,{'message':'Abre el cargador desde CARGAR_CUPONERA.bat'})
                return self.response(200,app.state)
            if route in ['/','/index.html']:
                html=(app.root/'sitio'/'index.html').read_text(encoding='utf-8');bootstrap='<script>window.INVEX_LOCAL_UPLOAD='+json.dumps({'token':app.token})+';</script>'
                body=html.replace('</head>',bootstrap+'</head>').encode();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body);return
            path=(app.root/'sitio'/unquote(route).lstrip('/')).resolve()
            if not path.is_relative_to((app.root/'sitio').resolve()) or path.suffix.lower() not in {'.js','.css','.svg','.png','.html'}:return self.response(404,{'message':'Recurso no disponible'})
            return super().do_GET()
        def do_POST(self):
            if urlsplit(self.path).path!='/api/cuponera':return self.response(404,{})
            if not self.authorized():return self.response(403,{'message':'Carga no autorizada. Abre CARGAR_CUPONERA.bat.'})
            try:length=int(self.headers.get('Content-Length','0'))
            except ValueError:return self.response(400,{'message':'Tamaño inválido'})
            if not 0<length<=MAX_UPLOAD:return self.response(413,{'message':'Selecciona un Excel de hasta 50 MB'})
            try:
                filename=unquote(self.headers.get('X-File-Name','cuponera.xlsx'));payload=self.rfile.read(length)
                if len(payload)!=length:raise ValueError('La transferencia quedó incompleta')
                app.start(filename,payload);return self.response(202,{'message':'Carga iniciada'})
            except ValueError as error:return self.response(409,{'message':str(error)})
    return Handler

def main(open_browser=True,port=8771):
    app=UploadApp();url='http://127.0.0.1:'+str(port)+'/#productividad'
    try:server=ThreadingHTTPServer(('127.0.0.1',port),make_handler(app))
    except OSError:
        print('El puerto del cargador ya está en uso. Abre '+url,flush=True)
        if open_browser:webbrowser.open(url)
        return 0
    print('INVEX · Carga y publicación de cuponera\n'+url+'\nMantén esta ventana abierta mientras cargas el archivo. Ctrl+C para cerrar.',flush=True)
    if open_browser:webbrowser.open(url)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
    return 0
if __name__=='__main__':raise SystemExit(main())
