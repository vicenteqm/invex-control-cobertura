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
        counts={'Apertura':0,'Cierre':0,'Intermedio / Atípico':0}
        for schedule,total in store.get('activeSchedules',{}).items():
            counts[operational_shift(schedule)]+=total
        gaps=allocate(store['gap'],opening,closing,counts['Apertura'],counts['Cierre'])
        store['shiftCoverage']={
            'targets':{'Apertura':opening,'Cierre':closing},'active':counts,'gaps':gaps,
            'hours':scheduled_hours(store['id']),
            'unallocated':store['gap']-sum(gaps.values()),
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
