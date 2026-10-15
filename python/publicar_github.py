"""Publica el proyecto en un repositorio nuevo usando Git Credential Manager."""
import json
import os
import re
import subprocess
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'.build-deps'))
import requests

ROOT=Path(__file__).resolve().parents[1]
FILES=['.gitignore','.github','site','tests','README.md','docs','python','ACTUALIZAR_INVEX.bat','ACTUALIZAR_CON_REPORTE.bat','ACTUALIZAR_BASE_TIENDAS.bat','ACTUALIZAR_ASISTENCIAS.bat','ACTUALIZAR_HORAS_PRODUCTIVAS.bat','CONFIGURAR_EQUIPO.bat','requirements.txt','requirements-build.txt']

def repository_from_remote(remote):
    match=re.fullmatch(r'(?:https://github\.com/|git@github\.com:)([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?',remote)
    if not match:raise ValueError('Configura origin con la URL de tu repositorio GitHub, sin tokens en la URL')
    return match.groups()

def main():
    remote=subprocess.run(['git','remote','get-url','origin'],cwd=ROOT,text=True,capture_output=True,check=True).stdout.strip()
    owner,name=repository_from_remote(remote)
    env=dict(os.environ,GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never')
    credential=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',text=True,capture_output=True,env=env,cwd=ROOT,timeout=30)
    if credential.returncode:
        raise RuntimeError('Git Credential Manager no tiene una sesión de GitHub disponible; se requiere iniciar sesión')
    values=dict(line.split('=',1) for line in credential.stdout.splitlines() if '=' in line)
    token=values.get('password')
    if not token:raise RuntimeError('No hay credencial Git disponible')
    session=requests.Session();session.headers.update({'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})
    def api(method,path,expected=(200,),**kwargs):
        response=session.request(method,'https://api.github.com'+path,timeout=45,**kwargs)
        if response.status_code not in expected:raise RuntimeError('GitHub rechazó '+method+' '+path+' (HTTP '+str(response.status_code)+')')
        return response.json() if response.content else None
    api('GET','/user')
    if '--estado' in sys.argv:
        runs=api('GET','/repos/'+owner+'/'+name+'/actions/runs?per_page=3')
        print(json.dumps([{'id':r['id'],'status':r['status'],'conclusion':r['conclusion'],'url':r['html_url']} for r in runs['workflow_runs']],indent=2))
        response=requests.get('https://'+owner+'.github.io/'+name+'/',timeout=30)
        print('HTTP del tablero: '+str(response.status_code))
        return
    info=api('GET','/repos/'+owner+'/'+name)
    print('Repositorio: '+info['html_url'],flush=True)
    def git(*args):subprocess.run(['git',*args],cwd=ROOT,env=env,check=True)
    # Solo archivos de implementación y datos agregados; nunca fuentes o secretos.
    git('add','--',*FILES)
    git('add','-u')
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines()
    if any(p.startswith(('inputs/','.private/','logs/','.build-deps/','configuracion/','previews/')) or p.endswith(('.xlsx','.xlsm','.csv')) or p=='config.local.json' for p in staged):raise RuntimeError('El índice contiene archivos privados; publicación detenida')
    if staged:git('commit','-m','Publicar tablero de cobertura INVEX y proceso de actualización')
    git('branch','-M','main')
    remotes=subprocess.check_output(['git','remote'],cwd=ROOT,text=True).splitlines()
    if 'origin' not in remotes:git('remote','add','origin',info['clone_url'])
    git('push','-u','origin','main')
    pages=api('GET','/repos/'+owner+'/'+name+'/pages',expected=(200,404))
    pages_created=not pages or not pages.get('html_url')
    if pages_created:
        pages=api('POST','/repos/'+owner+'/'+name+'/pages',expected=(201,202),json={'build_type':'workflow'})
    print('Pages configurado: '+str(pages.get('html_url','despliegue pendiente')),flush=True)
    # Pages puede habilitarse después del primer push; se vuelve a solicitar el despliegue.
    if pages_created or not any(p.startswith('site/') or p=='.github/workflows/pages.yml' for p in staged):
        api('POST','/repos/'+owner+'/'+name+'/actions/workflows/pages.yml/dispatches',expected=(204,),json={'ref':'main'})
    else:
        print('Publicación solicitada por el push; se evita duplicar el despliegue.',flush=True)
    (ROOT/'logs').mkdir(exist_ok=True)
    (ROOT/'logs'/'publicacion.json').write_text(json.dumps({'repository':info['html_url'],'pages':pages.get('html_url'),'status':'deployment_requested'},indent=2),encoding='utf-8')

if __name__=='__main__':
    try:main()
    except Exception as error:
        # Los errores no imprimen la respuesta ni las credenciales de Git.
        print(type(error).__name__+': '+str(error),file=sys.stderr);sys.exit(1)
