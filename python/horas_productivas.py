"""Trámites Walmart por día y hora; no incluye filas TOTAL ni duplica GENERAL."""
import calendar
import csv
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
        if 'DETALLE' in book:return read_detailed_workbook(book,path,period,base_stores)
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
                store=stores.setdefault(key,{'id':key,'name':str(row[pos_name] or key),'region':info.get('region','Sin región en base'),'executive':info.get('executive','Sin asignar'),'cpro':info.get('cpro','Sin asignar'),'status':info.get('status','Sin coincidencia en base'),'days':{}})
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

def productivity_cut(result):
    """Corte real de los datos, independiente de cuándo se copió el archivo."""
    return (int(result.get('lastDay') or 0),str(result.get('lastRecordAt') or ''))


def latest_productivity(config,root,period,stores):
    folder=Path(config.get('productive_hours_folder','datos/fuentes/horas_productivas'))
    if not folder.is_absolute():folder=root/folder
    files=sorted((p for p in folder.glob(config.get('productive_hours_pattern','Horas Productivas*.xlsx')) if not p.name.startswith('~$')),key=lambda p:p.stat().st_mtime,reverse=True)
    manual=root/'datos'/'fuentes'/'horas_productivas'/'Horas Productivas Actual.xlsx'
    if manual.is_file() and manual.resolve() not in {p.resolve() for p in files}:files.append(manual)
    candidates=[]
    for path in files:
        try:candidates.append((path,read_productivity(path,period,stores)))
        except PeriodNotFound:continue
    return max(candidates,key=lambda item:productivity_cut(item[1])) if candidates else None


def load_productivity(config,root,period,stores):
    selected=latest_productivity(config,root,period,stores)
    if selected:return selected[1]
    records_folder=Path(config.get('productive_records_folder','datos/fuentes/records'))
    if not records_folder.is_absolute():records_folder=root/records_folder
    for path in sorted(records_folder.glob('records_report_*.csv'),key=lambda p:p.stat().st_mtime,reverse=True):
        try:return read_records_productivity(path,period,stores)
        except PeriodNotFound:continue
    return {'status':'missing','period':period,'message':'No se encontró un Excel de horas productivas con hojas del periodo '+period+'.'}


def read_detailed_workbook(book,path,period,base_stores):
    year,month=map(int,period.split('-'));days=calendar.monthrange(year,month)[1]
    metadata={s['id']:s for s in base_stores};stores={};seen=set();dates=[]
    hours=[f'{h:02}:00 - {h:02}:59' for h in range(24)]
    it=book['DETALLE'].iter_rows(values_only=True);headers=next(it,())
    required={'CADENA','DETERMINANTE','SEDE','FOLIO','FECHA HORA CREACION','Aprobación','Estatus del proceso','ESTATUS BANCO','Aprobadas finalizadas'}
    if not required.issubset(headers):raise ValueError('DETALLE: faltan columnas requeridas')
    for values in it:
        r=dict(zip(headers,values));chain=str(r['CADENA'] or '').strip()
        partner={'Walmart':'WM',"Sam's":'SAMS','SAMS':'SAMS'}.get(chain)
        if not partner:continue # blank rows and explanatory footer are not records
        stamp=r['FECHA HORA CREACION']
        if not isinstance(stamp,datetime):
            try:stamp=datetime.fromisoformat(str(stamp))
            except ValueError:raise ValueError('DETALLE: fecha de creación inválida') from None
        if stamp.strftime('%Y-%m')!=period:continue
        folio=str(r['FOLIO'] or '').strip()
        if not folio or folio=='-':raise ValueError('DETALLE: falta folio')
        if folio in seen:raise ValueError('DETALLE: folio duplicado; revisar el Excel')
        seen.add(folio)
        raw=str(r['DETERMINANTE'] or '').strip()
        if not re.fullmatch(r'\d+(?:\.0+)?',raw):raise ValueError('DETALLE: determinante inválido')
        key=partner+' '+str(int(float(raw)));info=metadata.get(key,{})
        s=stores.setdefault(key,{'id':key,'chain':'Walmart' if partner=='WM' else 'SAMS','name':str(r['SEDE'] or key),'region':info.get('region','Sin región en base'),'executive':info.get('executive','Sin asignar'),'cpro':info.get('cpro','Sin asignar'),'status':info.get('status','Sin coincidencia en base'),'days':{},'approvedDays':{},'guaranteedDays':{},'finalizedDays':{},'metricsDays':{}})
        d=str(stamp.day);h=stamp.hour;dates.append(stamp)
        for field in ('days','approvedDays','guaranteedDays','finalizedDays'):s[field].setdefault(d,[0]*24)
        s['days'][d][h]+=1
        approval=str(r['Aprobación'] or 'Sin dato').strip();process=str(r['Estatus del proceso'] or 'Sin dato').strip()
        if approval=='Aprobada':s['approvedDays'][d][h]+=1
        if approval=='Aprobada con Garantía':s['guaranteedDays'][d][h]+=1
        final=volume(r['Aprobadas finalizadas'])
        if final not in (0,1) or final!=int(approval in ('Aprobada','Aprobada con Garantía') and process=='Finalizado'):raise ValueError('DETALLE: aprobadas finalizadas no coincide con aprobación y proceso')
        s['finalizedDays'][d][h]+=final
        metrics=s['metricsDays'].setdefault(d,{'approval':{},'process':{},'bank':{}})
        for field,label in [('approval',approval),('process',process),('bank',str(r['ESTATUS BANCO'] or 'Sin dato').strip())]:metrics[field][label]=metrics[field].get(label,0)+1
    if not dates:raise PeriodNotFound('DETALLE sin registros del periodo '+period)
    total=len(seen);sheets=[];warnings=[]
    approval_fields=['Aprobada con Garantía','Pendiente','Rechazada','Aprobada','Otras aprobaciones','Aprobadas finalizadas']
    def totals(selected,day=None,hour=None):
        result={'TOTAL_TRAMITES':0,**{k:0 for k in approval_fields}}
        for s in selected:
            for d,values in s['days'].items():
                if day is not None and int(d)!=day:continue
                result['TOTAL_TRAMITES']+=sum(values) if hour is None else values[hour]
                # Approval summary validation is by day/store; peak is validated by volume.
                if hour is None:
                    a=s['metricsDays'][d]['approval']
                    for k,n in a.items():result[k if k in approval_fields[:4] else 'Otras aprobaciones']+=n
                    result['Aprobadas finalizadas']+=sum(s['finalizedDays'][d])
        return result
    for sheet in book:
        if sheet.title=='DETALLE':sheets.append({'name':sheet.title,'role':'Fuente por folio','total':total,'matches':True});continue
        day=None
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}',sheet.title):
            if not sheet.title.startswith(period+'-'):continue
            day=date.fromisoformat(sheet.title).day
        elif sheet.title not in ('GENERAL','HORAS PICO'):
            warnings.append('Hoja sin estructura reconocida: '+sheet.title);sheets.append({'name':sheet.title,'role':'Sin estructura reconocida','total':None,'matches':False});continue
        rows=sheet.iter_rows(values_only=True);hs=next(rows,())
        if sheet.title=='HORAS PICO':
            hs=next(rows,());reported=0;ok=True
            for row in rows:
                r=dict(zip(hs,row));label=str(r.get('RANGO HORA') or '')
                if not isinstance(r.get('LUGAR'),(int,float)):continue
                if not re.fullmatch(r'\d{2}:00 - \d{2}:59',label):continue
                n=volume(r['TOTAL_TRAMITES']);reported+=n
                ok=ok and n==totals(stores.values(),hour=int(label[:2]))['TOTAL_TRAMITES']
            ok=ok and reported==total
        else:
            reported=0;ok=True
            for row in rows:
                r=dict(zip(hs,row));raw=str(r.get('DETERMINANTE') or '')
                if not re.fullmatch(r'\d+(?:\.0+)?',raw):continue
                partner={'Walmart':'WM',"Sam's":'SAMS','SAMS':'SAMS'}.get(str(r.get('CADENA')))
                if not partner:continue
                key=str(partner)+' '+str(int(float(raw)));s=stores.get(key)
                expected=totals([s] if s else [],day=day)
                reported+=volume(r['TOTAL_TRAMITES'])
                for col in ['TOTAL_TRAMITES']+approval_fields:
                    if col in hs:ok=ok and volume(r[col])==expected[col]
                for col in hs:
                    if re.fullmatch(r'\d{2}:00 - \d{2}:59',str(col)):ok=ok and volume(r[col])==totals([s] if s else [],day=day,hour=int(col[:2]))['TOTAL_TRAMITES']
            ok=ok and reported==totals(stores.values(),day=day)['TOTAL_TRAMITES']
        sheets.append({'name':sheet.title,'role':'Validación de resumen' if day is None else 'Validación diaria','total':reported,'matches':ok})
        if not ok:warnings.append('La hoja '+sheet.title+' difiere de DETALLE; se conserva el conteo por folio de DETALLE.')
    captured=sorted({d.day for d in dates})
    return {'status':'available','period':period,'daysInMonth':days,'capturedDays':captured,'lastDay':max(captured),'hours':hours,'stores':list(stores.values()),'sourceName':Path(path).name,'sourceModifiedAt':datetime.fromtimestamp(Path(path).stat().st_mtime,timezone.utc).isoformat(),'warnings':warnings,'total':total,'hasApprovals':True,'hasFinalized':True,'sourceType':'workbook-detail','lastRecordAt':max(dates).isoformat(),'approvalBasis':'Resultados del Excel agrupados por fecha y hora de creación. Finalizadas es un subconjunto de las aprobadas, no un ingreso adicional.','sheets':sheets}


def read_records_productivity(path,period,base_stores):
    """Publish aggregate counts only; customer/executive identifiers stay local."""
    year,month=map(int,period.split('-'));count=calendar.monthrange(year,month)[1]
    metadata={s['id']:s for s in base_stores};stores={};dates=[]
    hours=[f'{h:02}:00 - {h:02}:59' for h in range(24)]
    required={'Lugar de venta','Segundo lugar de venta','Aprobación','F. Creación'}
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if not required.issubset(reader.fieldnames or []):raise ValueError('Records: faltan columnas de tienda, aprobación o fecha de creación')
        for row in reader:
            if 'WALMART' not in row['Lugar de venta'].upper():continue
            try:created=datetime.fromisoformat(row['F. Creación'].strip())
            except ValueError:raise ValueError('Records: fecha de creación inválida') from None
            if created.strftime('%Y-%m')!=period:continue
            match=re.match(r'\s*(\d+)\b',row['Segundo lugar de venta'])
            if not match:raise ValueError('Records: tienda Walmart sin determinante')
            key='WM '+str(int(match[1]));info=metadata.get(key,{})
            s=stores.setdefault(key,{'id':key,'name':info.get('name') or row['Segundo lugar de venta'],'region':info.get('region','Sin región en base'),'executive':info.get('executive','Sin asignar'),'cpro':info.get('cpro','Sin asignar'),'status':info.get('status','Sin coincidencia en base'),'days':{},'approvedDays':{},'guaranteedDays':{}})
            day=str(created.day);dates.append(created)
            for field in ('days','approvedDays','guaranteedDays'):s[field].setdefault(day,[0]*24)
            s['days'][day][created.hour]+=1
            status=row['Aprobación'].strip().casefold()
            if status=='aprobada':s['approvedDays'][day][created.hour]+=1
            elif status=='aprobada con garantía':s['guaranteedDays'][day][created.hour]+=1
    if not dates:raise PeriodNotFound('Records sin registros Walmart del periodo '+period)
    # The export filename declares the requested coverage, including zero-volume days.
    match=re.fullmatch(r'records_report_(\d{8})_(\d{8})',Path(path).stem)
    start=min(dates).date();end=max(dates).date()
    if match:
        start=max(date(year,month,1),datetime.strptime(match[1],'%Y%m%d').date())
        end=min(date(year,month,count),datetime.strptime(match[2],'%Y%m%d').date())
        if any(not start<=d.date()<=end for d in dates):raise ValueError('Records: fechas fuera del rango indicado en el nombre')
    captured=list(range(start.day,end.day+1))
    for s in stores.values():
        for d in captured:
            for field in ('days','approvedDays','guaranteedDays'):s[field].setdefault(str(d),[0]*24)
    return {'status':'available','period':period,'daysInMonth':count,'capturedDays':captured,'lastDay':end.day,'hours':hours,'stores':list(stores.values()),'sourceName':Path(path).name,'sourceModifiedAt':datetime.fromtimestamp(Path(path).stat().st_mtime,timezone.utc).isoformat(),'warnings':[],'total':sum(sum(v) for s in stores.values() for v in s['days'].values()),'hasApprovals':True,'sourceType':'records','lastRecordAt':max(dates).isoformat(),'approvalBasis':'Aprobación actual del registro, agrupada por F. Creación; no es la fecha en que se aprobó.'}
