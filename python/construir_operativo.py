"""Construye el paquete privado para compartir la aplicación operativa INVEX."""
import argparse
import json
import os
import shutil
import subprocess
import sys
import secrets
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--dependencias',type=Path,required=True)
    parser.add_argument('--salida',type=Path,default=ROOT)
    args=parser.parse_args()
    sys.path.insert(0,str(ROOT/'python'))
    from procesar_cobertura import latest
    stage=ROOT/'resultados'/'construccion_operativo';bundle=stage/'paquete_operativo'
    bundle.mkdir(parents=True,exist_ok=True)
    config=json.loads((ROOT/'configuracion/config.local.json').read_text(encoding='utf-8'))
    base=latest(ROOT/config['base_folder'],config.get('base_pattern','*BASE*TIENDAS*.xlsx'))
    attendance=latest(ROOT/config['attendance_folder'],config.get('attendance_pattern','ASISTENCIA*.xlsx'))
    shutil.copyfile(base,bundle/'base.xlsx');shutil.copyfile(attendance,bundle/'asistencia.xlsx')
    text=(ROOT/'sitio/operacion-data.js').read_text(encoding='utf-8')
    published=json.loads(text.split('=',1)[1].strip().removesuffix(';'))
    month=published['months'][config['period']]
    month['period']=config['period']
    (bundle/'ultimo-corte.json').write_text(json.dumps(month,ensure_ascii=False),encoding='utf-8')
    from secretos_locales import read_credentials
    from accesos_operativo import seal
    from cryptography.fernet import Fernet
    user,password=read_credentials(ROOT/'.private/maat.json')
    key=Fernet.generate_key();key_file=stage/'_clave_operativa.py'
    key_file.write_text('PACKAGE_KEY = '+repr(key)+'\n',encoding='utf-8')
    (bundle/'acceso_maat.bin').write_bytes(seal({'user':user,'password':password},key))
    del password
    (bundle/'config.json').write_text(json.dumps({'period':config['period'],'attendance_linked_roster':True,'version':'2.0.0','maat_automatic':True,'credentialRevision':secrets.token_hex(16)},ensure_ascii=False),encoding='utf-8')
    # Ningún JSON de contraseña en texto dentro del paquete.
    (bundle/'accesos.json').unlink(missing_ok=True)
    output=args.salida.resolve();output.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ)
    env['PYTHONPATH']=os.pathsep.join([str(args.dependencias.resolve()),str(ROOT/'.build-deps'),str(ROOT/'python')])
    command=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onefile','--windowed',
             '--name','INVEX Registro Operativo','--distpath',str(output),'--workpath',str(stage/'build'),
             '--specpath',str(stage),'--paths',str(ROOT/'python'),'--paths',str(ROOT/'.build-deps'),'--paths',str(stage),'--hidden-import','_clave_operativa','--collect-submodules','selenium',
             '--add-data',str(bundle)+os.pathsep+'paquete_operativo',str(ROOT/'python/aplicacion_operativa.py')]
    # El runtime de Python carga este archivo al crear cualquier contexto TLS.
    # Se conserva su validación HTTPS también dentro del ejecutable.
    import ssl
    tls_policy=Path(ssl.__file__).parent/'codex-rejected-cas.pem'
    if tls_policy.exists():command[-1:-1]=['--add-data',str(tls_policy)+os.pathsep+'.']
    try:subprocess.run(command,env=env,cwd=ROOT,check=True)
    finally:
        # No queda un JSON de contraseñas legible en la carpeta de construcción.
        (bundle/'accesos.json').unlink(missing_ok=True)
        key_file.unlink(missing_ok=True)
    guide=ROOT/'documentacion'/'USO_APLICACION_OPERATIVA.txt'
    guide.parent.mkdir(exist_ok=True)
    guide.write_text('INVEX REGISTRO OPERATIVO 2.0\nMAAT se actualiza automaticamente cada 15 minutos. Actualizar Pandape requiere ingreso manual. Cargar nueva asistencia conserva su funcion.\nEl acceso MAAT viaja cifrado y se guarda con DPAPI de Windows por usuario. No se muestra ni se guarda en texto plano. Esta proteccion dificulta la inspeccion casual; no impide el analisis tecnico del ejecutable. Comparte solo con personal autorizado. No incluye clave de Pandape ni token GitHub.\n',encoding='utf-8-sig')
    print('EJECUTABLE PRIVADO: '+str(output/'INVEX Registro Operativo.exe'))


if __name__=='__main__':main()
