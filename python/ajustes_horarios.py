"""Ajustes privados persistentes; solo sus agregados se publican."""
import hashlib
import json
import re
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'configuracion/ajustes_horarios.local.json'
BLOCKS=('Tiempo completo','Apertura','Cierre')

def person_key(employee):
    return hashlib.sha256(employee.encode('utf-8')).hexdigest()

def load(path=None):
    path=Path(path) if path is not None else PATH
    if not path.exists():return {'people':{},'stores':{}}
    data=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data.get('people'),dict) or not isinstance(data.get('stores'),dict):
        raise ValueError('Formato inválido en los ajustes locales de horarios')
    return data

def save(data,path=None):
    path=Path(path) if path is not None else PATH
    path.parent.mkdir(parents=True,exist_ok=True)
    data['updatedAt']=datetime.now(timezone.utc).isoformat()
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(path)

def validate_schedule(value):
    value=' '.join(value.strip().split())
    times=re.findall(r'(?<!\d)(\d{1,2}):(\d{2})(?!\d)',value)
    if len(times)!=2:raise ValueError('Escribe un horario con entrada y salida, por ejemplo L - D 11:00 - 20:00')
    minutes=[]
    for h,m in times:
        if int(h)>23 or int(m)>59:raise ValueError('Hora inválida')
        minutes.append(int(h)*60+int(m))
    if minutes[1]<=minutes[0]:raise ValueError('La salida debe ser posterior a la entrada')
    return value

def split_schedule(value):
    matches=list(re.finditer(r'(?<!\d)(\d{1,2}):(\d{2})(?!\d)',value))
    if len(matches)!=2:return 'L - D','',''
    days=value[:matches[0].start()].strip(' ·-') or 'L - D'
    return days, matches[0].group(),matches[1].group()

def compose_schedule(days,entry,exit):
    if not entry.strip() or not exit.strip():raise ValueError('Indica la entrada y la salida en la misma fila, por ejemplo 11:00 y 20:00')
    if not re.fullmatch(r'\d{1,2}:\d{2}',entry.strip()) or not re.fullmatch(r'\d{1,2}:\d{2}',exit.strip()):
        raise ValueError('Usa el formato HH:MM en entrada y salida, por ejemplo 11:00')
    return validate_schedule((days.strip() or 'L - D')+' '+entry.strip()+' - '+exit.strip())

def effective_person(data,employee,store,schedule,journey):
    item=data['people'].get(person_key(employee),{})
    if item.get('store')!=store:return schedule,journey
    return item.get('schedule',schedule),item.get('journey',journey)

def apply_store(data,store,scope='general'):
    item=data['stores'].get(store['id'],{}).get(scope)
    if not item:return
    from turnos_cobertura import allocate,operational_shift
    targets=item['targets']
    if sum(targets.values())!=store['required']:
        store['scheduleOverrideWarning']='La plantilla cambió; revisar las metas manuales guardadas.'
        return
    full=sum(store.get('journeySchedules',{}).get('TIEMPO COMPLETO',{}).values())
    counts={'Apertura':0,'Cierre':0,'Tiempo completo':full}
    for schedule,n in store.get('journeySchedules',{}).get('MEDIO TIEMPO',{}).items():
        b=operational_shift(schedule)
        if b in counts:counts[b]+=n
    full_gap=min(store['gap'],max(0,targets['Tiempo completo']-full))
    gaps=allocate(store['gap']-full_gap,targets['Apertura'],targets['Cierre'],counts['Apertura'],counts['Cierre'])
    gaps['Tiempo completo']=full_gap
    store['shiftCoverage']={'targets':dict(targets),'active':counts,'gaps':gaps,'hours':dict(item['hours']),
        'unallocated':store['gap']-sum(gaps.values()),'manual':True}

def sources(root=ROOT):
    from procesar_cobertura import latest
    from fuentes_asistencia import current_generated
    config=json.loads((root/'configuracion/config.local.json').read_text(encoding='utf-8'))
    def folder(key):
        p=Path(config[key]);return p if p.is_absolute() else root/p
    base=latest(folder('base_folder'),config.get('base_pattern','*BASE*TIENDAS*.xlsx'))
    attendance=latest(folder('attendance_folder'),config.get('attendance_pattern','ASISTENCIA*.xlsx'))
    generated=root/'datos/asistencias'/('ASISTENCIA_INVEX_'+config['period']+'.xlsx')
    if current_generated(config,attendance,generated):attendance=generated
    return config,base,attendance

def catalog(root=ROOT):
    import openpyxl
    from actualizar import generate,columns,norm,store_identifier,contract_group
    from plantilla_elegible import profile
    config,base,attendance=sources(root)
    result=generate(base,attendance,config['period'])
    stores={s['id']:s for s in result['stores']};people=[];seen=set();data=load()
    book=openpyxl.load_workbook(attendance,read_only=True,data_only=True)
    try:
        sheet=book['Hoja1'];_,h=columns(sheet)
        for row in sheet.iter_rows(min_row=2,values_only=True):
            def get(k):return row[h[k]] if k in h else None
            if norm(get('ESTATUS'))!='ACTIVO' or profile(get('PERFIL DE PUESTO BANCO')) is None:continue
            key=store_identifier(get('SOCIO'),get('DETERMINANTE'),get('SOCIO Y NUMERO DE TIENDA'),stores)
            if key not in stores or stores[key]['status']!='OPERANDO':continue
            payroll=norm(get('NUM DE NOMINA'));name=norm(get('NOMBRE COMPLETO'))
            employee=payroll+'|'+name if payroll and payroll!='PENDIENTE' else name
            identity=person_key(employee)
            if identity in seen:continue
            seen.add(identity)
            original=str(get('HORARIO') or '').strip();journey=norm(get('JORNADA'))
            schedule,current_journey=effective_person(data,employee,key,original,journey)
            people.append(dict(key=identity,store=key,name=name,role=norm(get('PERFIL DE PUESTO BANCO')),
                schedule=schedule,journey=current_journey,original=original,originalJourney=journey,
                contract=contract_group(get('TIPO DE CONTRATO')),manual=data['people'].get(identity,{}).get('store')==key))
    finally:book.close()
    return result,people

def recalculate_publish(root=ROOT):
    import msvcrt
    (root/'registros').mkdir(exist_ok=True)
    with (root/'registros/proceso.lock').open('a+b') as lock:
        lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0)
        try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        except OSError:raise ValueError('Hay una actualización en proceso. Espera a que termine y vuelve a publicar') from None
        try:return _recalculate_publish(root)
        finally:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)

def _recalculate_publish(root):
    from actualizar import generate,publish_data
    config,base,attendance=sources(root)
    path=root/'sitio/data.js'
    data=json.loads(path.read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'))
    if data['period']!=config['period']:raise ValueError('Actualiza primero el periodo del tablero con el ejecutor general')
    fresh=generate(base,attendance,config['period'])
    data['stores']=fresh['stores'];data['scheduleAdjustedAt']=datetime.now(timezone.utc).isoformat()
    tmp=path.with_suffix('.tmp');tmp.write_text('window.INVEX_DATA = '+json.dumps(data,ensure_ascii=False,allow_nan=False)+';\n',encoding='utf-8');tmp.replace(path)
    # No cambia el corte de MAAT/Pandape ni se presenta una descarga nueva.
    publish_data(root)
