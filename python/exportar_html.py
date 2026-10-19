"""Genera un único HTML con los datos y módulos del tablero, sin depender de Pages."""
import base64
import re
import subprocess
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

def generar(root):
    root=Path(root).resolve();sitio=root/'sitio'
    html=(sitio/'index.html').read_text(encoding='utf-8')
    scripts=[]
    def asset(ref):
        ruta=(sitio/urlsplit(ref).path).resolve()
        if ruta.parent!=sitio:raise ValueError('Recurso fuera de la carpeta sitio')
        return ruta
    def script(match):
        scripts.append(asset(match[1]));return ''
    html=re.sub(r'<script\b[^>]*\bsrc="([^"]+)"[^>]*>\s*</script>',script,html,flags=re.I)
    def estilo(match):
        return '<style>'+asset(match[1]).read_text(encoding='utf-8')+'</style>'
    html=re.sub(r'<link\b[^>]*rel="stylesheet"[^>]*href="([^"]+)"[^>]*>',estilo,html,flags=re.I)
    icon=base64.b64encode((sitio/'favicon.svg').read_bytes()).decode('ascii')
    html=re.sub(r'<link\b[^>]*rel="icon"[^>]*>',lambda m:'<link rel="icon" href="data:image/svg+xml;base64,'+icon+'">',html,flags=re.I)
    extra=''.join('<style>'+(sitio/name).read_text(encoding='utf-8')+'</style>' for name in ['asistencia.css','operacion.css'])
    html=html.replace('</head>',extra+'</head>')
    scripts.extend([sitio/'operacion-data.js',sitio/'operacion.js'])
    contenido=['<script>window.INVEX_PORTABLE=true;</script>']
    for path in scripts:
        text=path.read_text(encoding='utf-8')
        text=re.sub(r'</script',lambda m:'<\\/script',text,flags=re.I)
        contenido.append('<script>'+text+'</script>')
    html=html.replace('</body>','\n'.join(contenido)+'</body>')
    final=root/'INVEX_ACTUALIZADO.html';temporary=final.with_suffix('.tmp.html')
    temporary.write_text(html,encoding='utf-8');temporary.replace(final)
    paquete=root/'INVEX_ACTUALIZADO.zip';tmp_zip=paquete.with_suffix('.tmp.zip')
    with zipfile.ZipFile(tmp_zip,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(final,arcname=final.name)
    tmp_zip.replace(paquete)
    return final

def guardar_enlace(root):
    root=Path(root)
    from publicar_github import repository_from_remote
    remote=subprocess.check_output(['git','remote','get-url','origin'],cwd=root,text=True).strip()
    owner,name=repository_from_remote(remote)
    sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    fijo=f'https://github.com/{owner}/{name}/raw/{sha}/INVEX_ACTUALIZADO.zip'
    reciente=f'https://github.com/{owner}/{name}/raw/refs/heads/main/INVEX_ACTUALIZADO.zip'
    folder=root/'registros';folder.mkdir(exist_ok=True)
    (folder/'enlace-html.txt').write_text('Descargar este corte:\n'+fijo+'\n\nDescargar la última versión:\n'+reciente+'\n',encoding='utf-8')
    print('HTML para compartir: '+fijo,flush=True)
    return fijo

if __name__=='__main__':print(generar(Path(__file__).resolve().parents[1]))
