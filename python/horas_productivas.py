"""Trámites Walmart por día y hora; no incluye filas TOTAL ni duplica GENERAL."""
import calendar
import math
import re
from datetime import date,datetime,timezone
from pathlib import Path
import openpyxl

class PeriodNotFound(ValueError):pass

def volume(value):
    if value is None or value=='':return 0
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0 or int(value)!=value:
        raise ValueError('Cantidad de trámites inválida en el Excel de horas productivas')
    return int(value)

def read_productivity(path,period,base_stores):
    year,month=map(int,period.split('-'));count=calendar.monthrange(year,month)[1]
    metadata={s['id']:s for s in base_stores}
    book=openpyxl.load_workbook(path,read_only=True,data_only=True)
    stores={};captured=[];hour_labels=None;warnings=[]
    try:
        for sheet in book:
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',sheet.title) or not sheet.title.startswith(period+'-'):continue
            day=date.fromisoformat(sheet.title).day
            iterator=sheet.iter_rows(values_only=True);headers=next(iterator,())
            if 'DETERMINANTE' not in headers or 'SEDE' not in headers or 'TOTAL_TRAMITES' not in headers:
                raise ValueError('Faltan encabezados en la hoja '+sheet.title)
            hourly=[(i,str(h).strip()) for i,h in enumerate(headers) if re.fullmatch(r'\d{2}:00\s*-\s*\d{2}:59',str(h or '').strip())]
            labels=[h for _,h in hourly]
            if not labels or (hour_labels is not None and hour_labels!=labels):raise ValueError('Intervalos horarios inconsistentes')
            hour_labels=labels
            pos_id=headers.index('DETERMINANTE');pos_name=headers.index('SEDE');pos_total=headers.index('TOTAL_TRAMITES')
            seen=set();totals=[0]*len(hourly);reported=None
            for row in iterator:
                raw=row[pos_id]
                if str(raw or '').strip().upper()=='TOTAL':
                    reported=volume(row[pos_total]);continue
                if raw is None:continue
                text=str(raw).strip()
                if not re.fullmatch(r'\d+(?:\.0+)?',text):raise ValueError('Determinante inválido en '+sheet.title)
                number=str(int(float(text)));key='WM '+number
                if key in seen:raise ValueError('Tienda repetida en '+sheet.title+': '+key)
                seen.add(key)
                values=[volume(row[i]) for i,_ in hourly]
                if sum(values)!=volume(row[pos_total]):raise ValueError('Total por tienda no coincide con las horas en '+sheet.title)
                info=metadata.get(key,{})
                store=stores.setdefault(key,{'id':key,'name':str(row[pos_name] or key),'region':info.get('region','Sin región en base'),'status':info.get('status','Sin coincidencia en base'),'days':{}})
                store['days'][str(day)]=values
                totals=[a+b for a,b in zip(totals,values)]
            if not seen:raise ValueError('Hoja diaria sin tiendas válidas: '+sheet.title)
            if reported is not None and reported!=sum(totals):raise ValueError('TOTAL diario no coincide en '+sheet.title)
            captured.append(day)
        if not captured:raise PeriodNotFound('El archivo no contiene hojas diarias del periodo '+period)
        total=sum(sum(v) for s in stores.values() for v in s['days'].values())
        if 'GENERAL' in book:
            rows=book['GENERAL'].iter_rows(values_only=True);headers=next(rows,())
            if 'TOTAL_TRAMITES' in headers and 'DETERMINANTE' in headers:
                pos=headers.index('TOTAL_TRAMITES');det=headers.index('DETERMINANTE')
                general=sum(volume(r[pos]) for r in rows if re.fullmatch(r'\d+(?:\.0+)?',str(r[det] or '').strip()))
                if general!=total:warnings.append('El resumen GENERAL difiere de las hojas diarias; las gráficas usan las hojas por fecha.')
    finally:book.close()
    return {'status':'available','period':period,'daysInMonth':count,'capturedDays':sorted(captured),'lastDay':max(captured),'hours':hour_labels,'stores':list(stores.values()),'sourceName':Path(path).name,'sourceModifiedAt':datetime.fromtimestamp(Path(path).stat().st_mtime,timezone.utc).isoformat(),'warnings':warnings,'total':total}

def load_productivity(config,root,period,stores):
    folder=Path(config.get('productive_hours_folder','inputs/fuentes/horas_productivas'))
    if not folder.is_absolute():folder=root/folder
    files=sorted((p for p in folder.glob('Horas Productivas*.xlsx') if not p.name.startswith('~$')),key=lambda p:p.stat().st_mtime,reverse=True)
    for path in files:
        try:return read_productivity(path,period,stores)
        except PeriodNotFound:continue
    return {'status':'missing','period':period,'message':'No se encontró un Excel de horas productivas con hojas del periodo '+period+'.'}
