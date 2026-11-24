"""Reparto de faltantes equivalente a las medidas DAX entregadas por INVEX."""

SPECIAL_HOURS={
    'WM 5296':{'Apertura':'10:00 - 16:00','Cierre':'13:00 - 19:00'},
    'SAMS 4968':{'Apertura':'11:00 - 20:00','Cierre':'11:00 - 20:00'},
}

def scheduled_hours(store_id):
    if store_id in SPECIAL_HOURS:return dict(SPECIAL_HOURS[store_id])
    if store_id.strip().upper().startswith('SAMS '):
        return {'Apertura':'11:00 - 20:00','Cierre':'11:00 - 20:00'}
    return {'Apertura':'11:00 - 17:00','Cierre':'15:00 - 21:00'}

def operational_shift(schedule):
    # CONTAINSSTRING sobre todo el texto, en el mismo orden que el DAX.
    if any(hour in schedule for hour in ('14:00','15:00','13:00')):return 'Cierre'
    if any(hour in schedule for hour in ('10:00','11:00','09:00')):return 'Apertura'
    return 'Intermedio / Atípico'

def enrich(stores):
    for store in stores:
        required=store['required']
        opening=(required+1)//2 if 1<=required<=13 else 0
        closing=required//2 if 1<=required<=13 else 0
        if store['id'].strip().upper().split(' ',1)[0] in ('WM','WALMART'):
            opening,closing=closing,opening
        counts={'Apertura':0,'Cierre':0,'Intermedio / Atípico':0}
        for schedule,total in store.get('activeSchedules',{}).items():
            counts[operational_shift(schedule)]+=total
        gaps=allocate(store['gap'],opening,closing,counts['Apertura'],counts['Cierre'])
        store['shiftCoverage']={
            'targets':{'Apertura':opening,'Cierre':closing},'active':counts,'gaps':gaps,
            'hours':scheduled_hours(store['id']),
            'unallocated':store['gap']-sum(gaps.values()),
        }
        if 'journeySchedules' in store and store['id'] not in SPECIAL_HOURS:
            enrich_journeys(store)

def full_time_hours(store):
    import re
    if store['id'] in SPECIAL_HOURS:return SPECIAL_HOURS[store['id']]['Apertura']
    if store['id'].upper().startswith('SAMS '):return '11:00 - 20:00'
    starts=set()
    for schedule,total in store.get('journeySchedules',{}).get('MEDIO TIEMPO',{}).items():
        match=re.search(r'(?<!\d)(\d{1,2}):(\d{2})(?!\d)',schedule)
        if total and match:starts.add((int(match[1]),int(match[2])))
    ten=(10,0) in starts;eleven=(11,0) in starts
    if ten and eleven:return 'Por confirmar · hay medios tiempos con entrada a las 10:00 y 11:00'
    if ten:return '11:00 - 20:00'
    if eleven:return '10:00 - 19:00'
    return 'Tiempo completo · horario por confirmar'

def enrich_journeys(store):
    required=store['required'];journeys=store['journeySchedules']
    full=sum(journeys.get('TIEMPO COMPLETO',{}).values())
    full_target=required if store['id'].upper().startswith('SAMS ') else (required+2)//3
    half_target=required-full_target
    opening=half_target//2 if store['id'].upper().startswith(('WM ','WALMART ')) else (half_target+1)//2
    closing=half_target-opening
    counts={'Apertura':0,'Cierre':0}
    for schedule,n in journeys.get('MEDIO TIEMPO',{}).items():
        block=operational_shift(schedule)
        if block in counts:counts[block]+=n
    full_gap=min(store['gap'],max(0,full_target-full))
    gaps=allocate(store['gap']-full_gap,opening,closing,counts['Apertura'],counts['Cierre'])
    gaps['Tiempo completo']=full_gap
    hours=scheduled_hours(store['id'])
    hours['Tiempo completo']=full_time_hours(store)
    store['shiftCoverage']={
        'targets':{'Apertura':opening,'Cierre':closing,'Tiempo completo':full_target},
        'active':{**counts,'Tiempo completo':full},'gaps':gaps,'hours':hours,
        'unallocated':store['gap']-sum(gaps.values()),
        'rule':'Un tiempo completo por cada tres plazas, redondeando hacia arriba; SAMS conserva tiempo completo.',
    }

def allocate(global_gap, opening_target, closing_target, opening_active, closing_active):
    values=(global_gap,opening_target,closing_target,opening_active,closing_active)
    if any(not isinstance(v,int) or isinstance(v,bool) or v<0 for v in values):
        raise ValueError('Metas, activos y faltantes deben ser enteros no negativos')
    opening=max(0,opening_target-opening_active)
    closing=max(0,closing_target-closing_active)
    if opening+closing<=global_gap:return {'Apertura':opening,'Cierre':closing}
    if opening>closing:
        return {'Apertura':min(opening,global_gap),'Cierre':max(0,global_gap-min(opening,global_gap))}
    return {'Apertura':max(0,global_gap-min(closing,global_gap)),'Cierre':min(closing,global_gap)}
