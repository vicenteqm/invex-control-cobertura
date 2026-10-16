"""Proceso único para descarga, análisis y actualización horaria del panel INVEX."""
import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'.build-deps'))
from actualizar import generate
from cobertura_actual import process, local_now

ROOT=Path(__file__).resolve().parents[1]

def latest(folder,pattern):
    files=[p for p in Path(folder).glob(pattern) if not p.name.startswith('~$')]
    if not files:raise ValueError('No se encontró el Excel en '+str(folder))
    return max(files,key=lambda p:p.stat().st_mtime)

def load_history():
    path=ROOT/'sitio'/'operacion-data.js'
    if not path.exists():return dict(months={})
    text=path.read_text(encoding='utf-8');prefix='window.INVEX_OPERACION = '
    if not text.startswith(prefix):raise ValueError('Archivo de operación con formato inesperado')
    return json.loads(text[len(prefix):].strip().removesuffix(';'))

def run(config,skip_download=False,pandape_report=None):
    config=dict(config)
    from fuentes_tiendas import sync_base
    synced=sync_base(config,ROOT)
    if synced:logging.info('Base de tiendas sincronizada desde el archivo vinculado: %s',synced.name)
    for key in ('attendance_folder','base_folder'):
        if not Path(config[key]).is_absolute():config[key]=str(ROOT/config[key])
    attendance=latest(config['attendance_folder'],config.get('attendance_pattern','ASISTENCIA*.xlsx'))
    base=latest(config['base_folder'],config.get('base_pattern','*BASE*TIENDAS*.xlsx'))
    logging.info('Base de tiendas seleccionada: %s · modificada: %s',base.name,time.strftime('%d/%m/%Y %H:%M:%S',time.localtime(base.stat().st_mtime)))
    period=config.get('period') or local_now().strftime('%Y-%m')
    if config.get('automate_productive_hours') and not skip_download:
        from automatizar_horas_productivas import rango_mes,ultima_bpi,validar_bpi
        if period!=rango_mes()[0].strftime('%Y-%m'):raise ValueError('Actualiza el periodo y las fuentes mensuales antes de iniciar el proceso del mes actual')
        validar_bpi(ultima_bpi(ROOT/'datos'/'fuentes'/'bpi'))
    month_names=['ENERO','FEBRERO','MARZO','ABRIL','MAYO','JUNIO','JULIO','AGOSTO','SEPTIEMBRE','OCTUBRE','NOVIEMBRE','DICIEMBRE']
    found_months=[i+1 for i,name in enumerate(month_names) if name in attendance.stem.upper()]
    iso_month=re.search(r'\d{4}-\d{2}',attendance.stem)
    if (found_months and int(period[-2:]) not in found_months) or (iso_month and iso_month.group()!=period):
        raise ValueError('El periodo configurado no coincide con el archivo de asistencia')
    maat=ROOT/'datos'/('asistencia_maat_'+period.replace('-','_')+'.csv')
    download_error=None
    if config.get('download_maat') and not skip_download:
        try:
            logging.info('Primera etapa: actualización MAAT en Edge visible')
            from descarga_asistencia import download_visible as download
            manual_maat=config.get('maat_manual_login',False)
            username=os.environ.get('MAAT_USER');password=os.environ.get('MAAT_PASSWORD')
            # Compatibilidad con este equipo; otros equipos pueden usar su propio entorno.
            if not manual_maat and (not username or not password) and (ROOT/'.private'/'maat.json').exists():
                from secretos_locales import read_credentials
                username,password=read_credentials(ROOT/'.private'/'maat.json')
            fresh,total=download(maat,period,username,password,manual_login=manual_maat)
            logging.info('MAAT: %s registros descargados; %s en concentrado',fresh,total)
        except Exception as error:
            download_error=type(error).__name__+': '+str(error)
            logging.error('No se descargó MAAT: %s',download_error)
    pandape_status='not_configured';pandape_result=None
    generated=ROOT/'datos'/'asistencias'/('ASISTENCIA_INVEX_'+period+'.xlsx')
    if config.get('download_pandape') or pandape_report:
        if skip_download and not pandape_report:
            if generated.exists():attendance=generated
            pandape_status='local'
        else:
            from descarga_pandape import download as download_pandape
            from generar_asistencia import generate as generate_attendance
            logging.info('Procesando reporte Pandape seleccionado y generando asistencia' if pandape_report else 'Descargando fichajes Pandape y generando asistencia')
            try:
                report=Path(pandape_report).resolve() if pandape_report else download_pandape(config,ROOT)
                if period!=local_now().strftime('%Y-%m'):raise ValueError('El reporte diario requiere configurar el mes actual')
                baseline=generated if generated.exists() and generated.stat().st_mtime>attendance.stat().st_mtime else attendance
                pandape_result=generate_attendance(baseline,report,generated,local_now().date())
                attendance=generated;pandape_status='available'
                logging.info('Pandape: %s',json.dumps(pandape_result))
            except Exception as error:
                # Se detiene el cálculo: no se presenta una captura anterior como recién descargada.
                detail=str(error) if isinstance(error,ValueError) or (isinstance(error,RuntimeError) and str(error).startswith('Pandape: ')) else type(error).__name__
                failure=dict(processedAt=local_now().isoformat(),period=period,pandape='error',stage='pandape',error=detail)
                (ROOT/'registros'/'ultimo-proceso.json').write_text(json.dumps(failure,indent=2),encoding='utf-8')
                raise RuntimeError('Falló la descarga o generación de asistencia Pandape; se conserva el tablero anterior ('+detail+')') from None
    if config.get('automate_productive_hours') and not skip_download:
        from automatizar_horas_productivas import ejecutar as generar_horas
        logging.info('Iniciando Records mensual → corrección de tiendas → BPI → horas productivas')
        generar_horas(config,ROOT)
    result=generate(base,attendance,period)
    from horas_productivas import load_productivity
    try:
        result['productiveHours']=load_productivity(config,ROOT,period,result['stores'])
        logging.info('Horas productivas Walmart: %s',result['productiveHours']['status'])
    except Exception as error:
        logging.error('No se procesaron las horas productivas: %s',error)
        result['productiveHours']={'status':'error','period':period,'message':'El Excel de horas productivas no pudo validarse. Revisa el archivo y el registro del proceso.'}
    logging.info('Calculando cobertura y cruce diario Pandape / MAAT')
    # Si falla la descarga no se presenta el concentrado viejo como actualizado.
    maat_path=maat if maat.exists() and not download_error else None
    month=process(base,attendance,period,maat_path)
    # Detalle completo para revisión local; nunca forma parte del sitio publicado.
    month['maatStatus']='error' if download_error else 'available' if maat_path else 'not_configured'
    month['maatError']=download_error
    historical=load_history();historical['months'][period]=month;historical['currentPeriod']=period
    historical['processedAt']=month['processedAt'];historical['sourceName']=attendance.name+' + '+base.name
    targets=[(ROOT/'sitio'/'data.js','window.INVEX_DATA',result),(ROOT/'sitio'/'operacion-data.js','window.INVEX_OPERACION',historical)]
    for path,variable,data in targets:
        tmp=path.with_suffix('.tmp');tmp.write_text(variable+' = '+json.dumps(data,ensure_ascii=False,allow_nan=False)+';\n',encoding='utf-8')
    for path,_,_ in targets:path.with_suffix('.tmp').replace(path)
    if config.get('publish'):
        logging.info('Publicando los datos y el detalle por promotor en GitHub')
        from actualizar import publish_data
        publish_data(ROOT)
    current_days=[next((d for d in s['days'] if d['day']==month['referenceDay']),{}) for s in month['stores']]
    status=dict(processedAt=month['processedAt'],period=period,referenceDay=month['referenceDay'],stores=len(month['stores']),alarmantes=sum(d.get('semaphore')=='ALARMANTE' for d in current_days),criticas=sum(d.get('semaphore')=='CRITICA' for d in current_days),maat=month['maatStatus'],maatDays=month['maatDays'],downloadError=download_error)
    status['pandape']=pandape_status;status['pandapeResult']=pandape_result
    if config.get('automate_productive_hours') and not skip_download:
        status['productiveHoursSource']={k:config[k] for k in ('productive_hours_folder','productive_hours_pattern')}
    (ROOT/'registros'/'ultimo-proceso.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
    logging.info('Proceso completado: %s',json.dumps(status,ensure_ascii=False))
    return status

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--config',type=Path,default=ROOT/'configuracion'/'config.local.json');parser.add_argument('--sin-descarga',action='store_true');parser.add_argument('--reporte-pandape',type=Path,help='Reporte del día actual exportado desde Pandape');args=parser.parse_args()
    (ROOT/'registros').mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO,format='%(asctime)s | %(levelname)s | %(message)s',handlers=[logging.FileHandler(ROOT/'registros'/'actualizacion.log',encoding='utf-8'),logging.StreamHandler()])
    config=json.loads(args.config.read_text(encoding='utf-8'))
    # Un bloqueo del sistema operativo evita procesos simultáneos y se libera al salir.
    import msvcrt
    with (ROOT/'registros'/'proceso.lock').open('a+b') as lock:
        lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0)
        try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        except OSError:logging.info('Ya hay una actualización en curso');raise SystemExit(3)
        try:
            status=run(config,args.sin_descarga,args.reporte_pandape)
            if status.get('productiveHoursSource'):
                config.update(status['productiveHoursSource'])
                temporary=args.config.with_suffix('.tmp.json');temporary.write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8');temporary.replace(args.config)
            if status['downloadError']:raise SystemExit(2)
        except Exception as error:
            logging.error('%s',error)
            raise SystemExit(1) from None
        finally:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)

if __name__=='__main__':main()
