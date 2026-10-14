"""Ejecutor local del flujo INVEX, con verificación y resultado legible."""
import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.build-deps'))

def check():
    if sys.version_info<(3,10):raise ValueError('Se requiere Python 3.10 o posterior')
    path=ROOT/'configuracion'/'config.local.json'
    if not path.exists():raise ValueError('Falta config.local.json: configura las carpetas y el periodo antes de actualizar')
    config=json.loads(path.read_text(encoding='utf-8'))
    for key in ('attendance_folder','base_folder'):
        if not (ROOT/Path(config.get(key,'__missing__'))).is_dir():raise ValueError('No existe la carpeta configurada: '+key)
    required=['openpyxl','requests']
    if config.get('download_pandape') or config.get('download_maat'):required.append('selenium')
    missing=[name for name in required if importlib.util.find_spec(name) is None]
    if missing:raise ValueError('Faltan dependencias: '+', '.join(missing)+'. Instala con: python -m pip install -r requirements.txt')
    if config.get('publish') and not shutil.which('git'):raise ValueError('Se requiere Git para publicar la actualización')
    return config

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--comprobar',action='store_true',help='Verifica la configuración sin descargar ni publicar')
    parser.add_argument('--seleccionar-reporte',action='store_true',help='Elegir el reporte descargado sin intentar acceder a Pandape')
    parser.add_argument('--reporte-pandape',type=Path,help='Reporte auténtico del día descargado desde Pandape')
    parser.add_argument('reporte',nargs='?',type=Path,help='Permite arrastrar un reporte diario sobre el BAT')
    args=parser.parse_args()
    try:
        config=check()
        print('Periodo: '+str(config.get('period','mes actual')),flush=True)
        print('Configuración y dependencias disponibles.',flush=True)
        if args.comprobar:return 0
        report=args.reporte_pandape or args.reporte
        if args.seleccionar_reporte and not report:
            print('Selecciona el Excel de fichajes del día descargado desde Pandape.',flush=True)
            try:
                import tkinter as tk
                from tkinter import filedialog
                window=tk.Tk();window.withdraw()
                try:selected=filedialog.askopenfilename(title='INVEX - Reporte Pandape del día',initialdir=str(Path.home()/'Downloads'),filetypes=[('Excel','*.xlsx')])
                finally:window.destroy()
            except Exception:
                selected=input('Pega la ruta completa del Excel (Enter para cancelar): ').strip().strip('"')
            if not selected:
                print('Selección cancelada. No se descargaron ni actualizaron datos.',flush=True)
                return 3
            report=Path(selected)
        if report and not report.is_file():raise ValueError('No existe el reporte Pandape seleccionado')
        if report:print('Reporte seleccionado: '+report.name+'; se omitirá la descarga automática de Pandape.',flush=True)
        print('Iniciando MAAT visible → Pandape → Excel de asistencia → cálculo → tablero.',flush=True)
        if config.get('publish'):print('Se publicará en GitHub si el proceso termina correctamente.',flush=True)
        command=[sys.executable,'-X','utf8',str(ROOT/'python'/'procesar_cobertura.py')]
        if report:command.extend(['--reporte-pandape',str(report.resolve())])
        result=subprocess.run(command,cwd=ROOT)
        if result.returncode==0:
            print('\nACTUALIZACIÓN TERMINADA.',flush=True)
            if config.get('publish'):print('GitHub recibió los datos. Pages puede tardar unos minutos en mostrarlos.',flush=True)
        elif result.returncode==3:print('\nYa hay otra actualización en curso. Espera a que termine.',flush=True)
        elif result.returncode==2:print('\nEl cálculo terminó con un fallo de MAAT. Revisa el registro antes de compartir los datos.',flush=True)
        else:
            print('\nLA ACTUALIZACIÓN NO SE COMPLETÓ. Revisa logs/actualizacion.log.',flush=True)
            print('Si Pandape rechaza el acceso con HTTP 403, no se actualiza el tablero.',flush=True)
            print('Puedes descargar el reporte del día desde Pandape y arrastrarlo sobre ACTUALIZAR_INVEX.bat.',flush=True)
        return result.returncode
    except (ValueError,OSError,json.JSONDecodeError) as error:
        print('No se puede iniciar: '+str(error),file=sys.stderr);return 1

if __name__=='__main__':sys.exit(main())
