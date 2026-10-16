"""Prepara un equipo Windows sin copiar secretos ni rutas de otra computadora."""
import argparse
import json
from datetime import datetime
from pathlib import Path
import subprocess
import sys
import venv

ROOT=Path(__file__).resolve().parents[1]

def prepare(root,period):
    for name in ['configuracion','datos/fuentes/asistencias','datos/fuentes/base_tiendas','datos/fuentes/horas_productivas','datos/fuentes/bpi','datos/descargas/records','resultados/horas_productivas','registros']:
        (root/name).mkdir(parents=True,exist_ok=True)
    destination=root/'configuracion/config.local.json'
    from accesos import preparar
    preparar(root)
    if not destination.exists():
        config={'attendance_folder':'datos/fuentes/asistencias','base_folder':'datos/fuentes/base_tiendas','attendance_pattern':'ASISTENCIA*.xlsx','base_pattern':'*BASE*TIENDAS*.xlsx','productive_hours_folder':'datos/fuentes/horas_productivas','period':period,'automate_productive_hours':True,'download_maat':True,'maat_manual_login':False,'publish':False,'download_pandape':True,'pandape_visible':True,'pandape_browser':'edge','pandape_manual_login':True,'pandape_user':''}
        destination.write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
    return destination

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--instalar',action='store_true',help='Crear .venv e instalar requirements.txt')
    args=parser.parse_args()
    prepare(ROOT,datetime.now().strftime('%Y-%m'))
    if args.instalar:
        environment=ROOT/'.venv'
        python=environment/'Scripts/python.exe'
        if not python.exists():venv.EnvBuilder(with_pip=True).create(environment)
        subprocess.run([str(python),'-m','pip','install','-r',str(ROOT/'requirements.txt')],check=True,cwd=ROOT)
    print('Preparación completa. Completa los accesos de MAAT en configuracion/accesos.json, sin cifrado.')
    print('Coloca los Excel fuente en datos/fuentes/asistencias y datos/fuentes/base_tiendas.')
    print('Comprueba el periodo en configuracion/config.local.json y abre ACTUALIZAR_INVEX.bat.')
    print('La configuración existente se conserva; en equipos nuevos publicar está desactivado.')

if __name__=='__main__':main()
