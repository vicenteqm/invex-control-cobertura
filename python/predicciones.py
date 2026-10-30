"""Pronóstico descriptivo de volumen; sin datos personales ni servicios externos."""
from datetime import date,timedelta
from statistics import mean
from math import sqrt

def estimate(history,target,mode):
    if mode=='weekday':
        same=[value for day,value in history if day.weekday()==target.weekday()][-4:]
        if len(same)>=2:return mean(same)
    return mean([value for _,value in history[-7:]]) if history else 0

def build(source,today=None):
    today=today or date.today()
    if source.get('status')!='available' or not source.get('period'):return {'status':'unavailable'}
    period=source['period'];last_observed=source.get('lastDay',0)
    if source.get('lastRecordAt'):
        last_observed=min(last_observed,date.fromisoformat(source['lastRecordAt'][:10]).day)
    days=sorted({int(d) for d in source.get('capturedDays',[]) if date.fromisoformat(f'{period}-{int(d):02}')<today and int(d)<=last_observed})
    if len(days)<7:return {'status':'insufficient','message':'Se requieren al menos siete días completos con datos para estimar ingresos.'}
    cutoff=date.fromisoformat(f'{period}-{days[-1]:02}');future=[cutoff+timedelta(days=i) for i in range(1,8)];result=[]
    for store in source.get('stores',[]):
        if str(store.get('status','')).strip().upper()!='OPERANDO':continue
        # Missing store-days remain missing, never assumed zero.
        history=[(date.fromisoformat(f'{period}-{d:02}'),sum(store['days'][str(d)])) for d in days if str(d) in store.get('days',{})]
        if len(history)<7:continue
        scores={}
        for mode in ('average','weekday'):
            errors=[history[i][1]-estimate(history[:i],history[i][0],mode) for i in range(max(7,len(history)-7),len(history))]
            scores[mode]=(mean(abs(e) for e in errors) if errors else None,errors)
        mode=min(scores,key=lambda m:scores[m][0] if scores[m][0] is not None else float('inf'))
        mae,errors=scores[mode];spread=1.64*sqrt(mean(e*e for e in errors)) if errors else None
        forecast=[]
        for day in future:
            value=estimate(history,day,mode)
            forecast.append({'date':day.isoformat(),'value':round(value,1),'low':round(max(0,value-spread),1) if spread is not None else None,'high':round(value+spread,1) if spread is not None else None})
        result.append({k:store.get(k,'Sin asignar') for k in ('id','name','region','executive','cpro','chain')}|{'model':mode,'history':[{'date':d.isoformat(),'value':v} for d,v in history],'forecast':forecast,'mae':round(mae,1) if mae is not None else None,'validationDays':len(errors)})
    return {'status':'available' if result else 'insufficient','cutoff':cutoff.isoformat(),'asOf':today.isoformat(),'staleDays':max(0,(today-cutoff).days-1),'dates':[d.isoformat() for d in future],'stores':result,'method':'Por tienda se elige promedio de los últimos siete días o promedio del mismo día de semana, según el menor error en hasta siete días históricos. El rango orientativo usa la dispersión de esos errores; no es una garantía ni un intervalo de confianza calibrado.'}
