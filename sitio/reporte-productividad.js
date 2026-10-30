'use strict';
(()=>{
function build(rows,context){
 const groups={WM:new Map(),SAMS:new Map()};
 for(const row of rows){const key=String(row[5]),partner=key.startsWith('SAMS ')?'SAMS':key.startsWith('WM ')?'WM':null;if(!partner)continue;
  let store=groups[partner].get(key);if(!store){store={name:row[6],id:key.replace(/^(WM|SAMS)\s+/,''),region:row[3],cpro:row[1],executive:row[2],hours:new Map()};groups[partner].set(key,store);}
  let h=store.hours.get(row[7]);if(!h){h={income:0,standard:context.hasApprovals?0:null,guaranteed:context.hasApprovals?0:null,finalized:context.hasFinalized?0:null};store.hours.set(row[7],h);}
  h.income+=row[8]||0;if(h.standard!==null)h.standard+=row[9]||0;if(h.guaranteed!==null)h.guaranteed+=row[10]||0;if(h.finalized!==null)h.finalized+=row[11]||0;
 }
 const headers=['Tienda','Determinante','Región','CPRO','CÉDULA','Hora','Ingresos','Aprobadas sin garantía','Aprobadas con garantía','Aprobadas totales','Aprobadas finalizadas','Aprobación %','Productividad finalizada %','Evaluación'];
 const sheets=[];
 for(const [partner,label]of [['WM','WALMART'],['SAMS','SAMS']]){
  const output=[];
  for(const s of [...groups[partner].values()].sort((a,b)=>a.id.localeCompare(b.id,'es',{numeric:true}))){
   const hours=[...s.hours].sort((a,b)=>a[0].localeCompare(b[0]));
   const rates=hours.filter(([,h])=>h.income>0&&h.standard!==null).map(([,h])=>(h.standard+h.guaranteed)/h.income);
   const maximum=rates.length?Math.max(...rates):null;
   for(const [hour,h]of hours){
    const approved=h.standard===null?null:h.standard+h.guaranteed;
    const approvalRate=approved===null||!h.income?null:approved/h.income;
    const finalRate=h.finalized===null||!h.income?null:h.finalized/h.income;
    const evaluated=partner==='WM'?h.finalized!==null:approved!==null;
    const productive=partner==='WM'?finalRate!==null&&finalRate>0.28:approvalRate!==null&&maximum>0&&Math.abs(approvalRate-maximum)<1e-12;
    output.push([s.name,s.id,s.region,s.cpro,s.executive,hour,h.income,h.standard,h.guaranteed,approved,h.finalized,approvalRate,finalRate,evaluated?(productive?'PRODUCTIVA':'NO PRODUCTIVA'):null]);
   }
  }
  sheets.push({name:label,headers,rows:output,percentColumns:[11,12]});
 }
 return sheets;
}
window.INVEX_PRODUCTIVITY_REPORT={build};
})();
