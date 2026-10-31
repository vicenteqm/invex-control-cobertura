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
   const regions=[...new Set(assigned.map(s=>s.region||'Sin región'))].sort((a,b)=>a.localeCompare(b,'es',{numeric:true}));
   const regionName=regions.length===1?regions[0]:'REGIONES '+regions.map(r=>r.replace(/^REGI[OÓ]N\s*/i,'')).join(' / ');
   groups.find(x=>x.partner===g.partner).rows.push({key:name,name:regionName,regions,stores:g.count,income,numerator,rate:numerator/income,score:context.metric==='income'?income:numerator/income});
  }
 }
 for(const g of groups){g.rows.sort((a,b)=>b.score-a.score||b.income-a.income||a.name.localeCompare(b.name,'es'));g.rows.forEach((r,i)=>r.rank=i&&Math.abs(r.score-g.rows[i-1].score)<1e-12?g.rows[i-1].rank:i+1);}
 return groups;
}
function downloadComparison(groups,context){
 const metricLabel=context.metric==='standard'?'Aprobadas':labels[context.metric];
 const canvas=document.createElement('canvas'),count=Math.max(1,...groups.map(g=>g.rows.length));canvas.width=1800;canvas.height=620+count*112;const ctx=canvas.getContext('2d');
 const text=(v,x,y,size=20,color='#20202a',weight='normal',align='left')=>{ctx.font=weight+' '+size+'px Calibri, Arial';ctx.fillStyle=color;ctx.textAlign=align;ctx.fillText(String(v),x,y);};
 const box=(x,y,w,h,color,r=14)=>{ctx.fillStyle=color;ctx.beginPath();ctx.roundRect(x,y,w,h,r);ctx.fill();};
 function wrapped(v,x,y,width,size=19,maxLines=4,color='#20202a'){const lines=[];let line='';ctx.font='bold '+size+'px Calibri, Arial';for(const word of v.split(' ')){if(line&&ctx.measureText(line+' '+word).width>width){lines.push(line);line=word;}else line+=(line?' ':'')+word;}if(line)lines.push(line);lines.slice(0,maxLines).forEach((l,i)=>text(l,x,y+i*(size+4),size,color,'bold'));}
 const bg=ctx.createLinearGradient(0,0,1800,canvas.height);bg.addColorStop(0,'#171323');bg.addColorStop(1,'#0c0b13');ctx.fillStyle=bg;ctx.fillRect(0,0,1800,canvas.height);
 for(let i=0;i<24;i++){ctx.fillStyle=i%2?'#ffffff06':'#ffb66a0c';ctx.fillRect(1420+(i%8)*40,20+Math.floor(i/8)*35,14,14);}
 box(38,32,142,54,'#ffb365',8);text('INVEX',109,70,32,'#171323','bold','center');text('COMPETENCIA ENTRE CÉDULAS',206,72,34,'#fff','bold');
 text('RANKING DE PRODUCTIVIDAD',40,119,18,'#c5b7d4','bold');
 box(38,140,535,44,'#30263e',8);text(context.from+' al '+context.to+'   |   09:00–19:59',57,170,22,'#f5eefb');
 box(590,140,315,44,'#30263e',8);text(metricLabel.toUpperCase(),747,170,21,'#ffca91','bold','center');
 const widths=[54,325,85,115,115,145];
 groups.forEach((g,n)=>{const x=38+n*885,w=839,accent=n?'#71cfdf':'#ffca55',soft=n?'#e4f5f8':'#fff2c9';
  box(x,210,w,canvas.height-280,'#f8f7fa',20);box(x,210,w,55,accent,14);ctx.fillStyle=accent;ctx.fillRect(x,242,w,23);text(g.partner==='WM'?'WALMART':'SAMS',x+22,247,28,'#17212b','bold');text(g.rows.length+' CÉDULAS',x+w-22,245,18,'#17212b','bold','right');
  const lead=g.rows[0];box(x+18,283,w-36,135,soft,12);
  text(lead?'PRIMER LUGAR':'SIN REGISTROS',x+35,312,16,'#665e50','bold');
  if(lead){wrapped(lead.name,x+35,345,505,21,3);text(context.metric==='income'?fmt(lead.income):fmt(100*lead.rate)+'%',x+w-35,359,43,'#17212b','bold','right');text(lead.stores+' tiendas · '+fmt(lead.numerator)+' '+metricLabel.toLowerCase(),x+w-35,394,18,'#665e50','normal','right');}
  let left=x;['POS.','CÉDULA / REGIONES','TIENDAS','INGRESOS',metricLabel.toUpperCase(),context.metric==='income'?'VOLUMEN':'PRODUCTIVIDAD'].forEach((h,j)=>{text(h,left+widths[j]/2,451,j===4||j===5?14:15,'#797181','bold','center');left+=widths[j];});
  const top=lead?.score||1;
  g.rows.forEach((r,i)=>{const y=470+i*112;box(x+12,y,w-24,103,r.rank===1?soft:i%2?'#eeedf2':'#fff',9);box(x+23,y+22,33,33,r.rank<=3?accent:'#e3e1e8',7);text(r.rank,x+39,y+46,20,'#20202a','bold','center');wrapped(r.name,x+68,y+28,306,18,3);
   let dx=x+widths[0]+widths[1];for(const [j,v]of [fmt(r.stores),fmt(r.income),fmt(r.numerator),context.metric==='income'?fmt(r.income):fmt(100*r.rate)+'%'].entries()){text(v,dx+widths[j+2]/2,y+44,j===3?25:22,'#20202a',j===3?'bold':'normal','center');dx+=widths[j+2];}
   box(x+68,y+85,w-95,5,'#dfdce5',2);if(r.score>0)box(x+68,y+85,(w-95)*r.score/top,5,r.rank<=3?accent:'#b5aebf',2);
  });
 });
 text('Tiendas operando · '+(context.metric==='income'?'Mayor volumen de ingresos':'Porcentaje = '+metricLabel.toLowerCase()+' / ingresos')+' · Empates comparten posición',38,canvas.height-44,19,'#d0c4dc');
 text('Fuente: '+context.source.sourceName+' · Corte: '+(context.source.lastRecordAt||'Sin fecha').replace('T',' '),38,canvas.height-17,17,'#a598b2');
 canvas.toBlob(blob=>{if(!blob)return;const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='INVEX_Comparativa_CEDULAS_'+context.metric+'_'+context.from+'_'+context.to+'.png';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);},'image/png');
}
function render(target,context){
 target.replaceChildren();const groups=compare(context),button=document.createElement('button');button.type='button';button.textContent='Descargar comparativa de CÉDULAS · PNG';button.id='download-competition';button.disabled=!groups.some(g=>g.rows.length);button.addEventListener('click',()=>downloadComparison(groups,context));target.append(button);
 const info=document.createElement('p');info.className='note';info.textContent='Las CÉDULAS se identifican por sus regiones. La comparación respeta los demás filtros y omite la selección individual de CÉDULA.';target.append(info);
 for(const group of groups){const article=document.createElement('article');article.className='productivity-competition';const title=document.createElement('h4');title.textContent=group.partner==='WM'?'WALMART':'SAMS';article.append(title);if(group.rows[0]){const lead=document.createElement('div');lead.className='competition-spotlight';const caption=document.createElement('span');caption.textContent='PRIMER LUGAR';const name=document.createElement('strong');name.textContent=group.rows[0].name;const score=document.createElement('b');score.textContent=context.metric==='income'?fmt(group.rows[0].income)+' ingresos':fmt(group.rows[0].rate*100)+'%';lead.append(caption,name,score);article.append(lead);}
  if(!group.rows.length){const p=document.createElement('p');p.textContent='Sin registros para estos filtros.';article.append(p);target.append(article);continue;}
  const wrap=document.createElement('div');wrap.className='table-wrap';const table=document.createElement('table'),head=document.createElement('thead'),header=document.createElement('tr');for(const label of ['Posición','CÉDULA / REGIONES','Tiendas','Ingresos',context.metric==='standard'?'Aprobadas':labels[context.metric],context.metric==='income'?'Resultado':'Productividad %']){const th=document.createElement('th');th.textContent=label;header.append(th);}head.append(header);table.append(head);const body=document.createElement('tbody');
  for(const r of group.rows){const row=document.createElement('tr');if(r.rank===1)row.className='competition-leader';for(const value of [r.rank,r.name,r.stores,r.income,r.numerator,context.metric==='income'?fmt(r.income):fmt(r.rate*100)+'%']){const td=document.createElement('td');td.textContent=value;row.append(td);}body.append(row);}table.append(body);wrap.append(table);article.append(wrap);target.append(article);
 }
}
window.INVEX_PRODUCTIVITY_IMAGES={aggregate,compare,render};
})();
