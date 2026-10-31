'use strict';
(()=>{
const labels={income:'Ingresos',standard:'Aprobadas sin garantía',guaranteed:'Garantizadas',finalized:'Finalizadas'};
const field={income:'days',standard:'approvedDays',guaranteed:'guaranteedDays',finalized:'finalizedDays'};
const fmt=n=>new Intl.NumberFormat('es-MX',{maximumFractionDigits:1}).format(n);
function aggregate(stores,source,from,to,metric){
 const start=Number(from.slice(-2)),end=Number(to.slice(-2));
 return ['WM','SAMS'].map(partner=>{
  const selected=stores.filter(s=>s.id.startsWith(partner+' '));
  const rows=Array.from({length:11},(_,n)=>{const h=n+9,counts={income:0,standard:source.hasApprovals?0:null,guaranteed:source.hasApprovals?0:null,finalized:source.hasFinalized?0:null};
   for(const s of selected)for(const [day,values]of Object.entries(s.days)){if(Number(day)<start||Number(day)>end||!source.capturedDays.includes(Number(day)))continue;counts.income+=values[h]||0;for(const mode of ['standard','guaranteed','finalized'])if(counts[mode]!==null)counts[mode]+=s[field[mode]]?.[day]?.[h]||0;}
   return {hour:source.hours[h],...counts,selected:counts[metric],rate:counts.income&&counts[metric]!==null?counts[metric]/counts.income:null};
  });
  const totals={};for(const mode of ['income','standard','guaranteed','finalized'])totals[mode]=rows.some(r=>r[mode]===null)?null:rows.reduce((sum,r)=>sum+r[mode],0);
  const ordered=rows.filter(r=>r.income>0&&r.selected!==null).sort((a,b)=>(metric==='income'?b.income-a.income:b.rate-a.rate)||b.income-a.income||a.hour.localeCompare(b.hour));
  return {partner,count:selected.length,rows,totals,best:ordered[0]||null};
 });
}
function compare(context){
 const stores=context.comparisonStores||context.stores;
 const names=[...new Set(stores.map(s=>s.executive||'Sin asignar'))].filter(name=>name!=='Sin asignar');
 const groups=['WM','SAMS'].map(partner=>({partner,rows:[]}));
 for(const name of names){const assigned=stores.filter(s=>s.executive===name);
  for(const g of aggregate(assigned,context.source,context.from,context.to,context.metric)){
   const numerator=g.totals[context.metric],income=g.totals.income;
   if(!g.count||!income||numerator===null)continue;
   groups.find(x=>x.partner===g.partner).rows.push({name,stores:g.count,income,numerator,rate:numerator/income,score:context.metric==='income'?income:numerator/income});
  }
 }
 for(const g of groups){g.rows.sort((a,b)=>b.score-a.score||b.income-a.income||a.name.localeCompare(b.name,'es'));g.rows.forEach((r,i)=>r.rank=i&&Math.abs(r.score-g.rows[i-1].score)<1e-12?g.rows[i-1].rank:i+1);}
 return groups;
}
function downloadComparison(groups,context){
 const canvas=document.createElement('canvas'),count=Math.max(1,...groups.map(g=>g.rows.length));canvas.width=1800;canvas.height=440+count*100;const ctx=canvas.getContext('2d');ctx.fillStyle='#fff';ctx.fillRect(0,0,canvas.width,canvas.height);
 const text=(value,x,y,size=20,color='#151515',weight='normal',align='left')=>{ctx.font=weight+' '+size+'px Calibri, Arial';ctx.fillStyle=color;ctx.textAlign=align;ctx.fillText(String(value),x,y);};
 function wrapped(value,x,y,width){let line='',row=0;for(const word of value.split(' ')){ctx.font='bold 20px Calibri, Arial';if(line&&ctx.measureText(line+' '+word).width>width){text(line,x,y+row*25,20,'#151515','bold');line=word;row++;}else line+=(line?' ':'')+word;}if(line)text(line,x,y+row*25,20,'#151515','bold');}
 ctx.fillStyle='#111';ctx.fillRect(0,0,1800,112);text('INVEX',38,52,37,'#fff','bold');text('COMPETENCIA DE PRODUCTIVIDAD ENTRE CÉDULAS',220,50,28,'#fff','bold');text(context.from+' al '+context.to+' · 09:00–19:59 · Tiendas operando',38,89,22,'#fff');
 text('Clasificación por '+labels[context.metric],38,154,29,'#151515','bold');
 text(context.metric==='income'?'Gana el mayor volumen de ingresos.':'Clasificación por porcentaje: '+labels[context.metric].toLowerCase()+' / ingresos. Se divide la suma de los registros; no se promedian porcentajes.',38,194,20,'#555');
 text('Los conteos y las tiendas se muestran para contextualizar el tamaño de cada cédula. Las garantías se cuentan por separado.',38,228,20,'#555');
 const widths=[55,319,80,125,125,135];
 groups.forEach((g,n)=>{const x=38+n*885,w=839;ctx.fillStyle=n?'#dcecf5':'#ffedb5';ctx.fillRect(x,264,w,52);text(g.partner==='WM'?'WALMART':'SAMS',x+16,299,27,'#151515','bold');ctx.fillStyle='#111';ctx.fillRect(x,316,w,45);
  let left=x;['Pos.','CÉDULA','Tiendas','Ingresos',labels[context.metric].split(' ')[0],context.metric==='income'?'Resultado':'Productividad'].forEach((label,j)=>{text(label,left+widths[j]/2,346,j===5?16:18,'#fff','bold','center');left+=widths[j];});
  if(!g.rows.length)text('Sin registros para estos filtros.',x+18,411,21,'#555');
  const top=g.rows[0]?.score||1;
  g.rows.forEach((r,i)=>{const y=361+i*100;ctx.fillStyle=r.rank===1?'#dbecd7':i%2?'#f1f1f1':'#fff';ctx.fillRect(x,y,w,100);text(r.rank,x+27,y+42,25,'#151515','bold','center');wrapped(r.name,x+65,y+30,299);let dx=x+widths[0]+widths[1];
   for(const [j,value]of [fmt(r.stores),fmt(r.income),fmt(r.numerator),context.metric==='income'?fmt(r.income):fmt(r.rate*100)+'%'].entries()){text(value,dx+widths[j+2]/2,y+43,j===3?23:21,'#151515',j===3?'bold':'normal','center');dx+=widths[j+2];}
   ctx.fillStyle='#e2e2e2';ctx.fillRect(x+65,y+83,w-86,5);ctx.fillStyle=r.rank===1?'#739e6b':'#b0b6bd';ctx.fillRect(x+65,y+83,(w-86)*Math.max(0,r.score/top),5);
  });
 });
 text('Fuente: '+context.source.sourceName+' · Último registro: '+(context.source.lastRecordAt||'Sin fecha').replace('T',' '),38,canvas.height-26,18,'#555');
 canvas.toBlob(blob=>{if(!blob)return;const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='INVEX_Comparativa_CEDULAS_'+context.metric+'_'+context.from+'_'+context.to+'.png';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);},'image/png');
}
function render(target,context){
 target.replaceChildren();const groups=compare(context),button=document.createElement('button');button.type='button';button.textContent='Descargar comparativa de CÉDULAS · PNG';button.id='download-competition';button.disabled=!groups.some(g=>g.rows.length);button.addEventListener('click',()=>downloadComparison(groups,context));target.append(button);
 const info=document.createElement('p');info.className='note';info.textContent='Medida: '+labels[context.metric]+'. Se comparan las cédulas disponibles con los demás filtros; la selección individual de CÉDULA se omite. Sin asignar no participa.';target.append(info);
 for(const group of groups){const article=document.createElement('article');article.className='productivity-competition';const title=document.createElement('h4');title.textContent=group.partner==='WM'?'WALMART':'SAMS';article.append(title);
  if(!group.rows.length){const p=document.createElement('p');p.textContent='Sin registros para estos filtros.';article.append(p);target.append(article);continue;}
  const wrap=document.createElement('div');wrap.className='table-wrap';const table=document.createElement('table'),head=document.createElement('thead'),header=document.createElement('tr');for(const label of ['Posición','CÉDULA','Tiendas','Ingresos',labels[context.metric],context.metric==='income'?'Resultado':'Productividad %']){const th=document.createElement('th');th.textContent=label;header.append(th);}head.append(header);table.append(head);const body=document.createElement('tbody');
  for(const r of group.rows){const row=document.createElement('tr');if(r.rank===1)row.className='competition-leader';for(const value of [r.rank,r.name,r.stores,r.income,r.numerator,context.metric==='income'?fmt(r.income):fmt(r.rate*100)+'%']){const td=document.createElement('td');td.textContent=value;row.append(td);}body.append(row);}table.append(body);wrap.append(table);article.append(wrap);target.append(article);
 }
}
window.INVEX_PRODUCTIVITY_IMAGES={aggregate,compare,render};
})();
