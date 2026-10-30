'use strict';
(()=>{
function build(rows,context){
 const groups={WM:new Map(),SAMS:new Map()};
 for(const row of rows){const key=String(row[5]),date=row[0],partner=key.startsWith('SAMS ')?'SAMS':key.startsWith('WM ')?'WM':null;if(!partner)continue;
  let store=groups[partner].get(key+'|'+date);if(!store){store={date,name:row[6],id:key.replace(/^(WM|SAMS)\s+/,''),region:row[3],cpro:row[1],executive:row[2],hours:new Map()};groups[partner].set(key+'|'+date,store);}
  let h=store.hours.get(row[7]);if(!h){h={income:0,standard:context.hasApprovals?0:null,guaranteed:context.hasApprovals?0:null,finalized:context.hasFinalized?0:null};store.hours.set(row[7],h);}
  h.income+=row[8]||0;if(h.standard!==null)h.standard+=row[9]||0;if(h.guaranteed!==null)h.guaranteed+=row[10]||0;if(h.finalized!==null)h.finalized+=row[11]||0;
 }
 const serial=date=>Date.parse(date+'T00:00:00Z')/86400000+25569;
 const headers=['Fecha','Tienda','Determinante','Región','CPRO','CÉDULA','Hora','Ingresos','Aprobadas sin garantía','Aprobadas con garantía','Aprobadas totales','Aprobadas finalizadas','Aprobación %','Productividad finalizada %','Evaluación'];
 const sheets=[];
 for(const [partner,label]of [['WM','WALMART'],['SAMS','SAMS']]){
  const output=[];
  for(const s of [...groups[partner].values()].sort((a,b)=>a.date.localeCompare(b.date)||a.id.localeCompare(b.id,'es',{numeric:true}))){
   const hours=[...s.hours].sort((a,b)=>a[0].localeCompare(b[0]));
   const rates=hours.filter(([,h])=>h.income>0&&h.standard!==null).map(([,h])=>(h.standard+h.guaranteed)/h.income);
   const maximum=rates.length?Math.max(...rates):null;
   for(const [hour,h]of hours){
    const approved=h.standard===null?null:h.standard+h.guaranteed;
    const approvalRate=approved===null||!h.income?null:approved/h.income;
    const finalRate=h.finalized===null||!h.income?null:h.finalized/h.income;
    const evaluated=partner==='WM'?h.finalized!==null:approved!==null;
    const productive=partner==='WM'?finalRate!==null&&finalRate>0.28:approvalRate!==null&&maximum>0&&Math.abs(approvalRate-maximum)<1e-12;
    output.push([serial(s.date),s.name,s.id,s.region,s.cpro,s.executive,hour,h.income,h.standard,h.guaranteed,approved,h.finalized,approvalRate,finalRate,evaluated?(productive?'PRODUCTIVA':'NO PRODUCTIVA'):null]);
   }
  }
  sheets.push({name:label,headers,rows:output,percentColumns:[12,13],dateColumns:[0]});
 }
 return [summary(sheets,context,serial),...sheets];
}
function summary(sheets,context,serial){
 const start=serial(context.from),end=serial(context.to),first=context.from.slice(0,7)+'-01',monthEnd=new Date(Date.UTC(Number(first.slice(0,4)),Number(first.slice(5,7)),0)).toISOString().slice(0,10);
 const cells=Array.from({length:34},()=>Array(15).fill(''));
 cells[0][0]='INVEX · RESUMEN DE HORAS PRODUCTIVAS';
 cells[1][0]='Cambia Desde y Hasta para consultar todo el mes o un rango. Los detalles contienen todas las fechas disponibles del mes para las tiendas seleccionadas.';
 cells[2][0]='Desde';cells[2][1]=start;cells[2][2]='Hasta';cells[2][3]=end;
 cells[3][0]={formula:'IF(B3>D3,"RANGO INVÁLIDO: Desde debe ser menor o igual a Hasta","Mes del reporte: '+first+' al '+monthEnd+'")',value:'Mes del reporte: '+first+' al '+monthEnd};
 const hours=[...new Set((context.hours||sheets.flatMap(s=>s.rows.map(r=>r[6]))))].sort();while(hours.length<24)hours.push(String(hours.length).padStart(2,'0')+':00 - '+String(hours.length).padStart(2,'0')+':59');hours.length=24;
 const charts=[];
 for(let chain=0;chain<2;chain++){
  const sheet=sheets[chain],offset=chain*8,prefix=chain===0?'WALMART':'SAMS',cols=chain===0?['A','B','C','D','E','F','G']:['I','J','K','L','M','N','O'];
  cells[4][offset]=prefix+(chain===0?' · Finalizadas / ingresos > 28%':' · Máximo de aprobación por hora');
  ['Hora','Ingresos','Aprobadas totales','Aprobadas finalizadas','Aprobación %','Finalizadas %','Evaluación'].forEach((v,j)=>cells[5][offset+j]=v);
  const last=Math.max(2,sheet.rows.length+1),ref=col=>"'"+sheet.name+"'!$"+col+'$2:$'+col+'$'+last;
  const values=hours.map(hour=>{const records=sheet.rows.filter(r=>r[6]===hour&&r[0]>=start&&r[0]<=end);return {income:records.reduce((a,r)=>a+r[7],0),approved:context.hasApprovals?records.reduce((a,r)=>a+r[10],0):null,finalized:context.hasFinalized?records.reduce((a,r)=>a+r[11],0):null};});
  const maximum=Math.max(0,...values.map(v=>v.income&&v.approved!==null?v.approved/v.income:0));
  hours.forEach((hour,i)=>{const row=i+7,v=values[i];cells[i+6][offset]=hour;
   ['H','K','L'].forEach((source,j)=>{const val=[v.income,v.approved,v.finalized][j];cells[i+6][offset+1+j]={formula:val===null?'""':'IF($B$3>$D$3,"",SUMIFS('+ref(source)+','+ref('A')+',">="&$B$3,'+ref('A')+',"<="&$D$3,'+ref('G')+','+cols[0]+row+'))',value:val};});
   [v.approved,v.finalized].forEach((n,j)=>cells[i+6][offset+4+j]={formula:n===null?'""':'IFERROR('+cols[j+2]+row+'/'+cols[1]+row+',"")',value:n!==null&&v.income?n/v.income:null});
   const productive=chain===0?v.income>0&&v.finalized!==null&&v.finalized/v.income>.28:v.income>0&&v.approved!==null&&maximum>0&&Math.abs(v.approved/v.income-maximum)<1e-12;
   const available=chain===0?context.hasFinalized:context.hasApprovals;
   cells[i+6][offset+6]={formula:!available?'""':chain===0?'IF('+cols[5]+row+'="","NO PRODUCTIVA",IF('+cols[5]+row+'>28%,"PRODUCTIVA","NO PRODUCTIVA"))':'IF(AND(ISNUMBER('+cols[4]+row+'),'+cols[4]+row+'>0,'+cols[4]+row+'=MAX($'+cols[4]+'$7:$'+cols[4]+'$30)),"PRODUCTIVA","NO PRODUCTIVA")',value:available?(productive?'PRODUCTIVA':'NO PRODUCTIVA'):null};
  });
  cells[30][offset]='TOTAL';for(let j=1;j<=3;j++){const key=['income','approved','finalized'][j-1];cells[30][offset+j]={formula:'SUM('+cols[j]+'7:'+cols[j]+'30)',value:values.every(v=>v[key]===null)?null:values.reduce((a,v)=>a+(v[key]||0),0)};}
  const total=values.reduce((a,v)=>a+v.income,0);for(let j=4;j<=5;j++){const key=j===4?'approved':'finalized';cells[30][offset+j]={formula:'IFERROR('+cols[j-2]+'31/'+cols[1]+'31,"")',value:total&&values[0][key]!==null?values.reduce((a,v)=>a+v[key],0)/total:null};}
  cells[32][offset]='Hora de mayor productividad';const metric=chain===0?'finalized':'approved',rates=values.map(v=>v.income&&v[metric]!==null?v[metric]/v.income:0),best=Math.max(...rates),metricCol=chain===0?cols[5]:cols[4];
  cells[32][offset+1]={formula:'IF(MAX('+metricCol+'7:'+metricCol+'30)<=0,"Sin actividad",INDEX('+cols[0]+'7:'+cols[0]+'30,MATCH(MAX('+metricCol+'7:'+metricCol+'30),'+metricCol+'7:'+metricCol+'30,0)))',value:best>0?hours[rates.indexOf(best)]:'Sin actividad'};
  charts.push({title:prefix+' · Horas productivas',categories:hours,categoryRef:"'RESUMEN'!$"+cols[0]+'$7:$'+cols[0]+'$30',series:[{name:'Ingresos',ref:"'RESUMEN'!$"+cols[1]+'$7:$'+cols[1]+'$30',values:values.map(v=>v.income)},{name:chain===0?'Aprobadas finalizadas':'Aprobadas totales',ref:"'RESUMEN'!$"+cols[chain===0?3:2]+'$7:$'+cols[chain===0?3:2]+'$30',values:values.map(v=>v[metric]||0)}],fromCol:offset,fromRow:35,toCol:offset+7,toRow:53});
  const rateCol=chain===0?cols[5]:cols[4];charts.push({title:prefix+(chain===0?' · Productividad finalizada %':' · Aprobación por hora %'),percent:true,categories:hours,categoryRef:"'RESUMEN'!$"+cols[0]+'$7:$'+cols[0]+'$30',series:[{name:chain===0?'Finalizadas / ingresos':'Aprobadas / ingresos',ref:"'RESUMEN'!$"+rateCol+'$7:$'+rateCol+'$30',values:values.map(v=>v.income&&v[metric]!==null?v[metric]/v.income:0)}],fromCol:offset,fromRow:55,toCol:offset+7,toRow:73});
 }
 cells[33][0]='Aprobadas totales = sin garantía + con garantía. Walmart se evalúa por finalizadas; SAMS por el máximo de aprobación, con todas las horas empatadas. Fuente: '+context.sourceName;
 return {name:'RESUMEN',grid:cells,headers:Array(15).fill(''),rows:[],headerRows:[0,4,5,30],dateCells:['B3','D3'],percentCells:Array.from({length:25},(_,i)=>['E','F','M','N'].map(c=>c+(i+7))).flat(),mergeRanges:['A1:O1','A2:O2','A4:O4','A5:G5','I5:O5','A34:O34'],freezeRows:0,zoom:85,charts,monthMin:serial(first),monthMax:serial(monthEnd)};
}
window.INVEX_PRODUCTIVITY_REPORT={build};
})();
