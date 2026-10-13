"""Agregados públicos del registro diario; el detalle nominal permanece local."""
import engine

def coverage_category(start,end,close):
    if isinstance(close,str):close=engine.to_min(close)
    if close is None:close=1200
    if start is None:return 'SIN_COBERTURA'
    if start>=720:return 'SOLO_TARDE'
    return 'CUBIERTA_TODO_EL_DIA' if end is not None and end>=close-30 else 'PERDIO_COBERTURA_TARDE'

def aggregate(raw,days,available):
    stores=raw['stores'];result={}
    for key,store in stores.items():
        result[key]={str(day):dict(available=day in available,population=len(store['empleados_activos']),people=0,pandape=0,maat=0,both=0,none=0,movedOut=0,incoming=0,external=0,late=0,earlyDeparture=0,manualClosing=0,firstStart=None,lastEnd=None,cohort=dict(total=0,pandape=0,maat=0,both=0,none=0)) for day in range(1,days+1)}
    for key,store in stores.items():
        for employee in store['empleados_activos']+store.get('externos_maat',[]):
            external=employee in store.get('externos_maat',[])
            for day,record in employee.get('registro_por_dia',{}).items():
                day=str(day)
                if day not in result[key]:continue
                p=bool(record.get('registra_pandape'));m=bool(record.get('registra_maat'))
                cohort=result[key][day]['cohort'];cohort['total']+=1
                for field,value in [('pandape',p),('maat',m),('both',p and m),('none',not p and not m)]:cohort[field]+=value
                target=record.get('tienda_maat_key') if record.get('se_movio_de_tienda') else key
                if target!=key:result[key][day]['movedOut']+=1
                if target not in result:continue
                bucket=result[target][day];bucket['people']+=1;bucket['external']+=external
                bucket['incoming']+=target!=key
                for field,value in [('pandape',p),('maat',m),('both',p and m),('none',not p and not m)]:bucket[field]+=value
                for field,source in [('late','llego_tarde'),('earlyDeparture','salio_antes_de_horario'),('manualClosing','cerro_jornada_manual')]:bucket[field]+=bool(record.get(source))
                systems=['maat'] if target!=key else ['pandape','maat']
                for system in systems:
                    start=engine.to_min(record.get('hora_entrada_'+system));end=engine.to_min(record.get('hora_salida_'+system))
                    if start is None:continue
                    bucket['firstStart']=start if bucket['firstStart'] is None else min(start,bucket['firstStart'])
                    if end is not None:bucket['lastEnd']=end if bucket['lastEnd'] is None else max(end,bucket['lastEnd'])
    for key,records in result.items():
        for bucket in records.values():
            p=bucket['pandape']>0;m=bucket['maat']>0
            bucket['status']='COMPLETO' if p and m else 'SIN_REGISTRO_MAAT' if p else 'SIN_REGISTRO_PANDAPE' if m else 'CRITICA'
            bucket['scheduleCoverage']=coverage_category(bucket['firstStart'],bucket['lastEnd'],stores[key]['close'])
    return result
