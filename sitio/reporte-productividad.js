'use strict';
(()=>{
function build(rows,context){
 const groups={WM:new Map(),SAMS:new Map()};
 for(const row of rows){const key=String(row[5]),partner=key.startsWith('SAMS ')?'SAMS':key.startsWith('WM ')?'WM':null;if(!partner)continue;
  let store=groups[partner].get(key);if(!store){store={name:row[6],id:key.replace(/^(WM|SAMS)\s+/,''),region:row[3],cpro:row[1],executive:row[2],hours:new Map()};groups[partner].set(key,store);}
  let h=store.hours.get(row[7]);if(!h){h={income:0,standard:context.hasApprovals?0:null,guaranteed:context.hasApprovals?0:null,finalized:context.hasFinalized?0:null};store.hours.set(row[7],h);}
  h.income+=row[8]||0;if(h.standard!==null)h.standard+=row[9]||0;if(h.guaranteed!==null)h.guaranteed+=row[10]||0;if(h.finalized!==null)h.finalized+=row[11]||0;
 }
 const common=['Tienda','Determinante','Región','CPRO','CÉDULA'];const counts=['Ingresos','Aprobadas sin garantía','Aprobadas con garantía','Aprobadas totales','Aprobadas finalizadas'];const sheets=[],details=[];
 const ratio=(n,d)=>n===null||!d?null:n/d;
 const status=(n,d)=>n===null?null:d>0&&n/d>0.28?'PRODUCTIVA':'NO PRODUCTIVA';
 for(const [partner,label]of [['WM','WALMART'],['SAMS','SAMS']]){
  const summary=[],hourRows=[];
  for(const s of [...groups[partner].values()].sort((a,b)=>a.id.localeCompare(b.id,'es',{numeric:true}))){
   const identity=[s.name,s.id,s.region,s.cpro,s.executive];let income=0,standard=context.hasApprovals?0:null,guaranteed=context.hasApprovals?0:null,finalized=context.hasFinalized?0:null;const candidates=[];
   for(const [hour,h]of [...s.hours].sort((a,b)=>a[0].localeCompare(b[0]))){const approved=h.standard===null?null:h.standard+h.guaranteed;const approvalRate=ratio(approved,h.income),finalRate=ratio(h.finalized,h.income);
    hourRows.push([...identity,hour,h.income,h.standard,h.guaranteed,approved,h.finalized,approvalRate,finalRate,...(partner==='WM'?[status(h.finalized,h.income)]:[])]);
    income+=h.income;if(standard!==null)standard+=h.standard;if(guaranteed!==null)guaranteed+=h.guaranteed;if(finalized!==null)finalized+=h.finalized;
    if(approvalRate!==null)candidates.push({hour,rate:approvalRate,income:h.income,approved});
   }
   const totalApproved=standard===null?null:standard+guaranteed;
   const base=[...identity,income,standard,guaranteed,totalApproved,finalized];
   if(partner==='WM')summary.push([...base,ratio(finalized,income),status(finalized,income)]);
   else {const maximum=candidates.length?Math.max(...candidates.map(c=>c.rate)):null;const best=candidates.filter(c=>Math.abs(c.rate-maximum)<1e-12);summary.push([...base,ratio(totalApproved,income),maximum,best.map(c=>c.hour).join(', '),best.length?best.reduce((a,c)=>a+c.income,0):null,best.length?best.reduce((a,c)=>a+c.approved,0):null]);}
  }
  const definition=partner==='WM'?'Productividad = aprobadas finalizadas / ingresos. Productiva solo si supera 28%.':'Máximo de aprobación = mayor (aprobadas totales / ingresos) entre las horas con ingresos, acumuladas en el periodo. Se muestran todas las horas empatadas.';
  const subtitle=context.from+' al '+context.to+' · '+definition+' Aprobadas totales = sin garantía + con garantía. Fuente: '+context.sourceName;
  sheets.push({name:label,title:'INVEX · REPORTE DE PRODUCTIVIDAD '+label,subtitle,headers:[...common,...counts,...(partner==='WM'?['Productividad finalizada %','Evaluación']:['Aprobación total %','Máximo de aprobación por hora %','Hora(s) de máximo','Ingresos en horas de máximo','Aprobadas en horas de máximo'])],rows:summary,percentColumns:partner==='WM'?[10]:[10,11]});
  details.push({name:label+' HORAS',title:'INVEX · PRODUCTIVIDAD POR HORA '+label,subtitle,headers:[...common,'Hora',...counts,'Aprobación %','Productividad finalizada %',...(partner==='WM'?['Evaluación']:[])],rows:hourRows,percentColumns:[11,12]});
 }
 return [...sheets,...details];
}
window.INVEX_PRODUCTIVITY_REPORT={build};
})();
