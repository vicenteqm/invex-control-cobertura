"""Motor local de la aplicación compartible de registro Pandape / MAAT."""
import json
import os
import shutil
import sys
from pathlib import Path

INTERVAL_SECONDS = 15 * 60


def resources():
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1])) / 'paquete_operativo'


def local_folder():
    return Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'INVEX' / 'Seguimiento operativo'


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp.json')
    temporary.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    temporary.replace(path)


def initialize(root, bundle=None):
    bundle = bundle or resources()
    for folder in ['.private', 'fuentes', 'datos', 'datos/pandape']:
        (root / folder).mkdir(parents=True, exist_ok=True)
    if not (root / 'config.json').exists():
        config = json.loads((bundle / 'config.json').read_text(encoding='utf-8'))
        for name in ['base.xlsx', 'asistencia.xlsx', 'ultimo-corte.json']:
            destination = root / ('fuentes' if name.endswith('.xlsx') else '') / name
            shutil.copyfile(bundle / name, destination)
        atomic_json(root / 'config.json', config)
    config=json.loads((root / 'config.json').read_text(encoding='utf-8'))
    if (bundle/'acceso_maat.bin').exists():
        from accesos_operativo import install
        config=install(root,bundle,config,json.loads((bundle/'config.json').read_text(encoding='utf-8')))
        atomic_json(root/'config.json',config)
    return config


def read_snapshot(root):
    path = root / 'ultimo-corte.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else None

def import_attendance(root,config,source,progress=lambda *args:None,services=None):
    """Validate and recalculate from a new roster without network access."""
    from cobertura_actual import local_now,process
    from actualizar import generate
    from fuentes_asistencia import fingerprint
    import re
    services=services or {};source=Path(source)
    now=local_now();period=now.strftime('%Y-%m')
    months=['ENERO','FEBRERO','MARZO','ABRIL','MAYO','JUNIO','JULIO','AGOSTO','SEPTIEMBRE','OCTUBRE','NOVIEMBRE','DICIEMBRE']
    named=[i+1 for i,name in enumerate(months) if name in source.stem.upper()]
    iso=re.search(r'(20\d{2})[-_](\d{2})(?:\D|$)',source.stem)
    dated=re.search(r'(\d{2})[-_](\d{2})[-_](20\d{2})',source.stem)
    if ((named and now.month not in named) or (iso and f'{iso[1]}-{iso[2]}'!=period)
            or (dated and f'{dated[3]}-{dated[2]}'!=period)):
        raise ValueError('El archivo debe corresponder a '+period+'. Selecciona la asistencia del mes actual.')
    if source.suffix.lower()!='.xlsx':raise ValueError('Selecciona un archivo Excel .xlsx')
    progress(15,'Validando la nueva asistencia')
    base=root/'fuentes/base.xlsx'
    services.get('generate',generate)(base,source,period)
    maat=root/'datos'/('asistencia_maat_'+period.replace('-','_')+'.csv')
    previous=read_snapshot(root) or {}
    progress(55,'Recalculando personal y cruce con MAAT guardado')
    result=services.get('process',process)(base,source,period,maat if maat.exists() else None,output_root=root)
    previous_sources=previous.get('sourceFreshness',{}) if previous.get('period')==period else {}
    result.update(period=period,maatStatus='available' if maat.exists() else 'not_configured',partialUpdate=True,
        sourceName='Asistencia cargada: '+source.name,attendanceImportedAt=now.isoformat(),
        sourceFreshness={'maat':previous_sources.get('maat',{'status':'not_loaded','updatedAt':None}),
            'pandape':{'status':'imported','updatedAt':now.isoformat(),'day':now.day}})
    # No reemplaza la fuente ni el corte si falla la validación o el cálculo.
    progress(90,'Guardando la nueva fuente de asistencia')
    target=root/'fuentes/asistencia.xlsx';staged=target.with_suffix('.nueva.xlsx')
    shutil.copyfile(source,staged)
    new_config=dict(config,period=period,attendance_linked_roster=True,
        attendanceImport={'name':source.name,'at':now.isoformat(),'sha256':fingerprint(source)})
    try:
        staged.replace(target);atomic_json(root/'config.json',new_config);atomic_json(root/'ultimo-corte.json',result)
    finally:staged.unlink(missing_ok=True)
    config.clear();config.update(new_config)
    progress(100,'Asistencia cargada y datos recalculados')
    return result


def access_config(root, config, interactive=False):
    clean={k:v for k,v in config.items() if k not in ('pandape_password','maat_password')}
    return dict(clean,portable_login=False,portable_app=True,pandape_interactive_entry=True,
                pandape_browser='edge',pandape_background=False)


def login(root, config):
    from descarga_pandape import prepare_session
    prepare_session(access_config(root, config), root)
    config.pop('pandape_attention_required',None)
    atomic_json(root/'config.json',config)


def refresh(root, config, progress, services=None, interactive_pandape=False):
    from cobertura_actual import local_now, process
    from descarga_asistencia import download as maat_download
    from descarga_pandape import download as pandape_download
    from generar_asistencia import generate as attendance_generate
    from fuentes_asistencia import current_generated, mark_source
    from actualizar import generate as coverage_generate
    now = local_now()
    period = now.strftime('%Y-%m')
    if config['period'] != period:
        raise ValueError('MONTH_REQUIRED: Carga la asistencia del mes actual desde Fuentes antes de actualizar.')
    services = services or {}
    progress(5, 'Validando fuentes')
    base, source = root / 'fuentes/base.xlsx', root / 'fuentes/asistencia.xlsx'
    coverage_generate(base, source, period)
    maat = root / 'datos' / ('asistencia_maat_' + period.replace('-', '_') + '.csv')
    progress(15, 'Actualizando registros MAAT')
    try:
        if config.get('maat_automatic'):
            from maat_operativo import download as automatic_download
            from secretos_locales import read_credentials
            user,password=read_credentials(root/'.private/maat.json')
            services.get('maat',automatic_download)(maat,period,user,password)
        else:services.get('maat', maat_download)(maat, period)
    except Exception as error:
        status=getattr(getattr(error,'response',None),'status_code',None)
        atomic_json(root/'datos'/'ultimo-error-maat.json',{'type':type(error).__name__,'http':status,'at':now.isoformat()})
        raise ValueError('MAAT_DOWNLOAD_FAILED: '+type(error).__name__+(' HTTP '+str(status) if status else '')) from None
    maat_updated=local_now().isoformat()
    previous=read_snapshot(root) or {}
    previous_pandape=previous.get('sourceFreshness',{}).get('pandape',{})
    pandape_updated=previous_pandape.get('updatedAt') or (previous.get('processedAt') if not previous.get('partialUpdate') else None)
    generated = root / 'datos' / ('ASISTENCIA_INVEX_' + period + '.xlsx')
    baseline = generated if current_generated({'attendance_linked_roster': True}, source, generated) else source
    attendance=baseline
    pandape_ok=False
    attention=(bool(config.get('maat_automatic')) or bool(config.get('pandape_attention_required'))) and not interactive_pandape
    if attention:
        progress(38,'MAAT descargado · Pandape espera inicio de sesión')
    else:
        progress(38,'Inicia sesión en Edge; la descarga continuará automáticamente' if interactive_pandape else 'Actualizando registros Pandape')
        try:
            report = services.get('pandape', pandape_download)(access_config(root, config,interactive_pandape), root)
            progress(72, 'Generando asistencia del día')
            services.get('attendance', attendance_generate)(baseline, report, generated, now.date())
            mark_source(source, generated)
            attendance=generated;pandape_ok=True;pandape_updated=local_now().isoformat()
            config.pop('pandape_attention_required',None)
            if interactive_pandape:config['pandape_visible_session']=True
            atomic_json(root/'config.json',config)
        except Exception as error:
            text=str(error)
            attention=any(value in text for value in ['403','CAPTCHA','PANDAPE_SESSION_REQUIRED'])
            if attention:
                config['pandape_attention_required']=True
                atomic_json(root/'config.json',config)
            atomic_json(root/'datos'/'ultimo-error-pandape.json',{'type':type(error).__name__,'at':local_now().isoformat(),'requiresAttention':attention})
    progress(85,'Cruzando Pandape y MAAT' if pandape_ok else 'Calculando registros MAAT · cruce Pandape pendiente')
    result = services.get('process', process)(base, attendance, period, maat, output_root=root)
    result['period'] = period
    result['partialUpdate']=not pandape_ok
    result['maatStatus']='available'
    result['sourceFreshness']={
        'maat':{'status':'ok','updatedAt':maat_updated,'day':now.day},
        'pandape':{'status':'ok' if pandape_ok else 'attention' if attention else 'error','updatedAt':pandape_updated,'attemptedAt':local_now().isoformat(),'day':now.day}}
    if not pandape_ok:
        # Una captura antigua del mismo día no debe cruzarse con el MAAT nuevo.
        result['attendanceDays']=[d for d in result.get('attendanceDays',[]) if d!=now.day]
    result['sourceName'] = 'Asistencia y base locales · descarga directa de Pandape / MAAT'
    progress(96, 'Guardando corte validado')
    atomic_json(root / 'ultimo-corte.json', result)
    progress(100, 'Actualización completada' if pandape_ok else 'MAAT actualizado · Pandape pendiente')
    return result


def registration_view(month, day, region='', executive='', search=''):
    """Mismas poblaciones y asignación a destino que Seguimiento operativo."""
    day = str(day)
    maat = month.get('maatLoaded') and month.get('maatStatus') != 'error' and int(day) in month.get('maatDays', [])
    pandape = int(day) in month.get('attendanceDays', [])
    q = search.strip().casefold()
    stores = [s for s in month.get('stores', []) if (not region or s.get('region') == region)
              and (not executive or s.get('executive') == executive)
              and (not q or q in (s['id'] + ' ' + s['name']).casefold())]
    totals = dict(total=0, pandape=0, maat=0, both=0, none=0)
    for s in stores:
        cohort = s.get('registration', {}).get(day, {}).get('cohort', {})
        for k in totals:
            totals[k] += cohort.get(k, 0) if maat else 0
    return stores, totals, bool(pandape and maat), bool(maat)


def people_rows(month, stores, day):
    result = []
    for store in stores:
        detail = month.get('promoterDetail', {}).get('stores', {}).get(store['id'], {})
        # La vista nominal conserva líderes y externos incluidos en el Excel ampliado.
        for group in ['personal_excel', 'externos_excel']:
            for person in detail.get(group, []):
                r = person.get('registro_por_dia', {}).get(str(day))
                if r:
                    result.append((store, person, r))
    return result


def heatmap_tiles(month, stores, day, system):
    """Mismos conteos y límites de color que los mapas del HTML."""
    maat=system=='MAAT';day=int(day)
    available=(day in month.get('maatDays',[]) and month.get('maatLoaded') and month.get('maatStatus')!='error') if maat else day in month.get('attendanceDays',[])
    result=[]
    for store in stores:
        record=store.get('registration',{}).get(str(day))
        required=store.get('required',0)
        valid=bool(available and record and required>0 and (not maat or record.get('available')))
        count=(record.get('maat',0) if maat else record.get('cohort',{}).get('pandape',0)) if valid else None
        percentage=count/required*100 if valid else None
        level='unknown' if percentage is None else 'full' if percentage>=100 else 'partial' if percentage>=50 else 'low'
        result.append({'store':store,'required':required,'count':count,'percentage':percentage,'level':level})
    return result
