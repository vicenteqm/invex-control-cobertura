"""Construye el paquete privado para compartir la aplicación operativa INVEX."""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--dependencias',type=Path,required=True)
    parser.add_argument('--salida',type=Path,default=ROOT)
    args=parser.parse_args()
    sys.path.insert(0,str(ROOT/'python'))
    from secretos_locales import read_credentials
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
    (bundle/'config.json').write_text(json.dumps({'period':config['period'],'attendance_linked_roster':True,'version':'1.5.0'},ensure_ascii=False),encoding='utf-8')
    # Estos accesos solo se incluyen en el paquete privado solicitado, nunca en Git.
    credentials={name:read_credentials(ROOT/'.private'/(name+'.json')) for name in ['maat','pandape']}
    if not all(len(v)==2 and all(v) for v in credentials.values()):raise ValueError('Falta un acceso configurado')
    (bundle/'accesos.json').write_text(json.dumps(credentials),encoding='utf-8')
    output=args.salida.resolve();output.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ)
    env['PYTHONPATH']=os.pathsep.join([str(args.dependencias.resolve()),str(ROOT/'.build-deps'),str(ROOT/'python')])
    command=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onefile','--windowed',
             '--name','INVEX Registro Operativo','--distpath',str(output),'--workpath',str(stage/'build'),
             '--specpath',str(stage),'--paths',str(ROOT/'python'),'--paths',str(ROOT/'.build-deps'),'--collect-submodules','selenium',
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
    guide=ROOT/'documentacion'/'USO_APLICACION_OPERATIVA.txt'
    guide.parent.mkdir(exist_ok=True)
    guide.write_text('INVEX - REGISTRO OPERATIVO\n\nAbre INVEX Registro Operativo.exe. No requiere Python, Git ni Excel.\nRequiere Windows 10/11 de 64 bits, Microsoft Edge e Internet.\n\nActualizar ahora descarga MAAT, exporta Pandape, genera la asistencia y cruza los registros en este equipo. La actualización automática se ejecuta cada 15 minutos mientras la aplicación permanece abierta.\n\nSi Pandape solicita verificación o rechaza el acceso automático, pulsa Actualizar Pandape y completa el ingreso en Edge. La misma ventana continúa con los filtros y la exportación al detectar la sesión iniciada. No se eluden CAPTCHA ni HTTP 403. MAAT sigue actualizándose aunque Pandape esté pendiente. Se muestran las horas de cada fuente por separado. El cruce y el mapa Pandape del día quedan sin evaluar hasta completar su descarga.\n\nLos accesos de servicio están incluidos por autorización del responsable del proyecto. Comparte este paquete únicamente con las personas autorizadas. La sesión del navegador se crea por separado en cada equipo. No se incluye acceso de publicación de GitHub.\n\nLos datos de este equipo se guardan en %LOCALAPPDATA%/INVEX/Seguimiento operativo. Usa Fuentes para reemplazar la base o la asistencia. Al cambiar de mes es necesario cargar la asistencia del nuevo periodo. Las fuentes iniciales corresponden a '+config['period']+'.\n\nLos KPI cuentan personas únicas del día. El registro no equivale a presencia instantánea. Los movimientos se asignan al destino MAAT, como en Seguimiento operativo. El detalle nominal ampliado conserva líderes y externos; su población puede ser mayor que la plantilla operativa de los KPI.\n',encoding='utf-8-sig')
    print('EJECUTABLE PRIVADO: '+str(output/'INVEX Registro Operativo.exe'))


if __name__=='__main__':main()
