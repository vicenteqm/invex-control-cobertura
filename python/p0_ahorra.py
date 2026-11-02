"""Importa únicamente agregados diarios por tienda de P0 y Ahorra+."""
from pathlib import Path
from datetime import date,datetime,timezone
import re,unicodedata,logging
import openpyxl

def norm(value):
    return ''.join(c for c in unicodedata.normalize('NFKD',str(value or '').upper().strip()) if not unicodedata.combining(c))

def number(value):
    if value is None:return None
    if isinstance(value,bool) or not isinstance(value,(int,float)) or value<0 or int(value)!=value:raise ValueError('P0/Ahorra+: conteo inválido en hoja P0')
    return int(value)

def read_programs(path,base_stores):
    path=Path(path);book=openpyxl.load_workbook(path,read_only=True,data_only=True)
    try:
        if 'P0' not in book or 'Hoja1' not in book:raise ValueError('P0/Ahorra+: faltan hojas P0 o Hoja1')
        it=book['Hoja1'].iter_rows(values_only=True);headers=next(it);position=headers.index('Fecha Creación');available=set();details=[]
        for row in it:
            stamp=row[position]
            if not stamp:continue
            try:stamp=stamp.date() if isinstance(stamp,datetime) else stamp if isinstance(stamp,date) else date.fromisoformat(str(stamp)[:10])
            except ValueError:continue
            available.add(stamp.isoformat());details.append((stamp.isoformat(),row))
        rows=list(book['P0'].iter_rows(values_only=True));dates=[]
        for i,stamp in enumerate(rows[1]):
            if not isinstance(stamp,(datetime,date)):continue
            day=stamp.date().isoformat() if isinstance(stamp,datetime) else stamp.isoformat()
            if day in available:
                if i<1 or norm(rows[2][i-1])!='ING' or norm(rows[2][i])!='APS' or norm(rows[2][i+2])!='P0':raise ValueError('P0/Ahorra+: bloque diario no reconocido')
                dates.append((day,i))
        if not dates:raise ValueError('P0/Ahorra+: sin fechas reales identificadas')
        start=next((i for i,r in enumerate(rows) if len(r)>4 and norm(r[1])=='REGION' and norm(r[2])=='DET' and norm(r[3])=='TIENDA'),None)
        if start is None:raise ValueError('P0/Ahorra+: falta tabla por tienda')
        lookup={}
        for store in base_stores:lookup.setdefault(store['id'].split(' ')[-1],[]).append(store)
        result={};unmatched=[];ambiguous=[];counts={day:dict(p0=0,ahorra=0) for day,_ in dates}
        for row in rows[start+1:]:
            raw=row[2]
            if not isinstance(raw,(int,float)) and not re.fullmatch(r'\d+(?:\.0)?',str(raw or '')):continue
            det=str(int(float(raw)));candidates=lookup.get(det,[])
            if len(candidates)>1:candidates=[s for s in candidates if norm(s.get('name'))==norm(row[3])]
            if len(candidates)!=1:
                (ambiguous if candidates else unmatched).append(det);continue
            key=candidates[0]['id']
            if key in result:raise ValueError('P0/Ahorra+: tienda duplicada '+key)
            days={}
            for day,i in dates:
                p0=number(row[i+2]);ahorra=number(row[i+4]);aps=number(row[i]);income=number(row[i-1])
                if p0 is None or ahorra is None:continue
                days[day]=dict(p0=p0,ahorra=ahorra,approved=aps,income=income)
                counts[day]['p0']+=p0;counts[day]['ahorra']+=ahorra
            result[key]=days
        columns={norm(h):i for i,h in enumerate(headers)}
        if all(h in columns for h in ['OPCION DE ACTIVACION','DET','FOLIO FICO']):
            for days in result.values():
                for record in days.values():record['app']=0
            seen=set()
            for day,row in details:
                raw=row[columns['DET']]
                if not re.fullmatch(r'\d+(?:\.0+)?',str(raw or '')):continue
                candidates=[s for s in lookup.get(str(int(float(raw))),[]) if day in result.get(s['id'],{})]
                if len(candidates)!=1:continue
                key=candidates[0]['id'];folio=str(row[columns['FOLIO FICO']] or '').strip();token=(key,day,folio)
                success=re.sub(r'\s+',' ',norm(row[columns['OPCION DE ACTIVACION']]).replace('–','-').replace('—','-'))=='SI SE REALIZO - FINALIZAR TRAMITE'
                if folio and success and token not in seen:result[key][day]['app']+=1;seen.add(token)
        needed=['FOLIO FICO','DET','HORA CREACION','APROBACION','ESTATUS DEL PROCESO','PROGRAMA CERO ACEPTADO','COMPLEMENTO DENTAL ACEPTADO','OPCION DE ACTIVACION']
        if all(h in columns for h in needed):
            for days in result.values():
                for record in days.values():record['aligned']=dict(approved=0,p0=0,ahorra=0,app=0)
            seen=set()
            for day,row in details:
                raw=row[columns['DET']]
                if not re.fullmatch(r'\d+(?:\.0+)?',str(raw or '')):continue
                candidates=[s for s in lookup.get(str(int(float(raw))),[]) if day in result.get(s['id'],{})]
                if len(candidates)!=1:continue
                key=candidates[0]['id'];folio=str(row[columns['FOLIO FICO']] or '').removesuffix('.0').strip()
                if not folio.isdigit() or folio in seen:continue
                seen.add(folio)
                hour=str(row[columns['HORA CREACION']] or '')
                try:hour=int(hour.split(':')[0])
                except ValueError:continue
                if not 9<=hour<=19 or norm(row[columns['APROBACION']])!='APROBADA':continue
                record=result[key][day]['aligned'];record['approved']+=1
                final=norm(row[columns['ESTATUS DEL PROCESO']])=='FINALIZADO'
                record['p0']+=int(final and norm(row[columns['PROGRAMA CERO ACEPTADO']])=='ACEPTADO')
                record['ahorra']+=int(final and norm(row[columns['COMPLEMENTO DENTAL ACEPTADO']])=='ACEPTADO')
                record['app']+=int(re.sub(r'\s+',' ',norm(row[columns['OPCION DE ACTIVACION']]).replace('–','-').replace('—','-'))=='SI SE REALIZO - FINALIZAR TRAMITE')
        return dict(status='available',sourceName=path.name,sourceModifiedAt=datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat(),dates=sorted(day for day,_ in dates),stores=result,unmatchedStores=len(unmatched),ambiguousStores=len(ambiguous),basis='Día completo. P0 y Ahorra+ de tabla por tienda. APP: Sí se realizó - Finalizar Trámite, folios únicos. Alcances sobre APS de la cuponera; sin acumulados semanales.')
    finally:book.close()

def load_programs(config,root,base_stores):
    linked=config.get('p0_ahorra_source');folder=Path(root)/'datos'/'fuentes'/'p0_ahorra'
    paths=[Path(linked)] if linked else sorted(folder.glob('*.xlsx'),key=lambda p:p.stat().st_mtime,reverse=True)
    if not paths:return dict(status='unavailable',message='Sin archivo P0/Ahorra+ configurado')
    try:return read_programs(paths[0],base_stores)
    except Exception as error:
        logging.warning('No se incorporaron P0/Ahorra+: %s',error)
        return dict(status='error',message='No se pudo validar el archivo P0/Ahorra+. No se muestran conteos antiguos como actuales.')
