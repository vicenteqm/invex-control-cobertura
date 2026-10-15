"""Importación manual de fuentes: validar, recalcular y publicar sin descargas."""
import json
import logging
import shutil
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.build-deps'))

def select_file(kind):
    import tkinter as tk
    from tkinter import filedialog
    labels={'asistencias':'asistencia mensual','tiendas':'base de tiendas','horas':'horas productivas'}
    window=tk.Tk();window.withdraw()
    try:
        return filedialog.askopenfilename(title='INVEX - Selecciona el Excel de '+labels[kind],filetypes=[('Excel','*.xlsx')])
    finally:window.destroy()

def save_config(path,config):
    temporary=path.with_suffix('.tmp.json')
    temporary.write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
    temporary.replace(path)

def import_file(kind,source,config,root):
    from actualizar import generate
    from procesar_cobertura import latest
    from fuentes_tiendas import sync_base
    source=Path(source).resolve()
    if not source.is_file() or source.suffix.lower()!='.xlsx':raise ValueError('Selecciona un archivo Excel .xlsx existente')
    period=config['period']
    base=latest(root/config['base_folder'],config.get('base_pattern','*BASE*TIENDAS*.xlsx'))
    attendance=latest(root/config['attendance_folder'],config.get('attendance_pattern','ASISTENCIA*.xlsx'))
    generated=root/'datos'/'asistencias'/('ASISTENCIA_INVEX_'+period+'.xlsx')
    if config.get('download_pandape') and generated.exists():attendance=generated
    # Validar la fuente completa antes de reemplazar una copia de trabajo.
    if kind=='tiendas':
        generate(source,attendance,period)
        sync_base(config,root,source)
        return
    if kind=='asistencias':
        generate(base,source,period)
        target=root/'datos'/'asistencias'/('ASISTENCIA_INVEX_'+period+'.xlsx')
        config['attendance_folder']='datos/asistencias'
        config['attendance_pattern']=target.name
    elif kind=='horas':
        from horas_productivas import read_productivity
        stores=generate(base,attendance,period)['stores']
        result=read_productivity(source,period,stores)
        if result.get('status')!='available':raise ValueError('El Excel no contiene horas productivas del periodo configurado')
        target=root/'datos'/'fuentes'/'horas_productivas'/'Horas Productivas Actual.xlsx'
        config['productive_hours_folder']='datos/fuentes/horas_productivas'
        config['productive_hours_pattern']=target.name
    else:raise ValueError('Tipo de archivo desconocido')
    target.parent.mkdir(parents=True,exist_ok=True)
    if source!=target.resolve():
        temporary=target.with_suffix('.tmp.xlsx')
        try:shutil.copyfile(source,temporary);temporary.replace(target)
        finally:
            if temporary.exists():temporary.unlink()

def main(kind):
    selected=select_file(kind)
    if not selected:
        print('Selección cancelada. No se modificaron ni publicaron datos.',flush=True);return 3
    import msvcrt
    (ROOT/'registros').mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO,format='%(asctime)s | %(levelname)s | %(message)s',handlers=[logging.FileHandler(ROOT/'registros'/'actualizacion.log',encoding='utf-8'),logging.StreamHandler()])
    with (ROOT/'registros'/'proceso.lock').open('a+b') as lock:
        lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0)
        try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        except OSError:
            print('Ya hay otra actualización en curso. Espera a que termine.');return 3
        try:
            path=ROOT/'configuracion'/'config.local.json'
            config=json.loads(path.read_text(encoding='utf-8'))
            print('1/3 Validando Excel para el periodo '+config['period']+'...',flush=True)
            import_file(kind,selected,config,ROOT)
            save_config(path,config)
            local=dict(config,publish=True,download_pandape=False,download_maat=False)
            generated=ROOT/'datos'/'asistencias'/('ASISTENCIA_INVEX_'+config['period']+'.xlsx')
            if kind!='asistencias' and config.get('download_pandape') and generated.exists():
                local['attendance_folder']='datos/asistencias'
                local['attendance_pattern']=generated.name
            # Usar las copias locales al actualizar una única fuente.
            local.pop('base_source_file',None)
            print('2/3 Recalculando con los archivos locales. 3/3 Publicando en GitHub...',flush=True)
            from procesar_cobertura import run
            status=run(local,skip_download=True)
            if status.get('downloadError'):raise ValueError('No se completó el proceso')
            print('ACTUALIZACIÓN PUBLICADA. GitHub Pages puede tardar unos minutos en reflejarla.',flush=True)
            return 0
        except Exception as error:
            print('NO SE COMPLETÓ LA ACTUALIZACIÓN: '+str(error),file=sys.stderr)
            print('Puedes volver a ejecutar este mismo archivo para reintentar.',flush=True)
            return 1
        finally:
            lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
