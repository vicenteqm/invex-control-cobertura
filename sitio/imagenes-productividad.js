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
function download(name,groups,context){
 const canvas=document.createElement('canvas');canvas.width=1800;canvas.height=1130;const ctx=canvas.getContext('2d');ctx.fillStyle='#fff';ctx.fillRect(0,0,1800,1130);
 const text=(value,x,y,size=20,color='#151515',weight='normal',align='left')=>{ctx.font=weight+' '+size+'px Calibri, Arial';ctx.fillStyle=color;ctx.textAlign=align;ctx.fillText(String(value),x,y);};
 const fit=(value,x,y,max,size=25,color='#151515',weight='bold')=>{while(size>16){ctx.font=weight+' '+size+'px Calibri, Arial';if(ctx.measureText(value).width<=max)break;size--;}text(value,x,y,size,color,weight);};
 ctx.fillStyle='#111';ctx.fillRect(0,0,1800,155);text('INVEX',38,56,38,'#fff','bold');text('CUADRO DE PRODUCTIVIDAD POR CÉDULA',220,53,27,'#fff','bold');fit(name,38,105,1720,29,'#fff');
 text(context.from+' al '+context.to+' · Horario 09:00–19:59 · Solo tiendas operando',38,195,23);
 text('Productividad por: '+labels[context.metric],38,235,24,'#111','bold');
 text(context.metric==='income'?'Las horas se comparan por cantidad de ingresos.':'Porcentaje = '+labels[context.metric].toLowerCase()+' / ingresos. Aprobadas y garantizadas se muestran por separado.',38,272,20,'#555');
 groups.forEach((group,n)=>{
  const x=38+n*885,w=839;ctx.fillStyle=n?'#e9f2f7':'#fff1c8';ctx.fillRect(x,310,w,151);
  text(group.partner==='WM'?'WALMART':'SAMS',x+16,346,27,'#111','bold');text(group.count+' tiendas · '+fmt(group.totals.income)+' ingresos',x+16,381,22);
  const best=group.best;text('Mejor hora: '+(best?best.hour:'Sin ingresos'),x+16,415,22,'#111','bold');
  text(best?(context.metric==='income'?fmt(best.income)+' ingresos':fmt(100*best.rate)+'% · '+fmt(best.selected)+' / '+fmt(best.income)+' ingresos'):'Sin datos para este periodo',x+16,446,20);
  const widths=[155,115,115,115,115,110,114],headers=['Hora','Ingresos','Aprobadas','Garantía','Finalizadas','% medida','Destacada'];
  ctx.fillStyle='#111';ctx.fillRect(x,482,w,46);let dx=x;headers.forEach((h,i)=>{text(h,dx+widths[i]/2,512,18,'#fff','bold','center');dx+=widths[i];});
  group.rows.forEach((r,i)=>{const y=528+i*40;const highlight=best&&r.income>0&&(context.metric==='income'?r.income===best.income:r.rate!==null&&Math.abs(r.rate-best.rate)<1e-12);ctx.fillStyle=highlight?'#d3ead1':i%2?'#f4f4f4':'#fff';ctx.fillRect(x,y,w,40);
   const values=[r.hour?.slice(0,5),fmt(r.income),r.standard===null?'—':fmt(r.standard),r.guaranteed===null?'—':fmt(r.guaranteed),r.finalized===null?'—':fmt(r.finalized),context.metric==='income'?'—':r.rate===null?'—':fmt(100*r.rate)+'%',highlight?'MÁXIMO':''];let left=x;
   values.forEach((v,j)=>{text(v,left+widths[j]/2,y+26,j===6?15:19,'#151515',highlight?'bold':'normal','center');left+=widths[j];});
  });
  const t=group.totals,ratio=t.income&&t[context.metric]!==null?fmt(100*t[context.metric]/t.income)+'%':'—';
  text('TOTAL',x+12,1005,20,'#111','bold');text(fmt(t.income)+' ingresos · '+(t[context.metric]===null?'Sin datos':fmt(t[context.metric]))+' '+labels[context.metric].toLowerCase(),x+12,1035,20);
  if(context.metric!=='income')text('Porcentaje acumulado: '+ratio,x+12,1064,20,'#111','bold');
 });
 text('Fuente: '+context.source.sourceName+' · Último registro: '+(context.source.lastRecordAt||'Sin fecha').replace('T',' '),38,1106,18,'#555');
 canvas.toBlob(blob=>{if(!blob)return;const url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download='INVEX_Productividad_'+name.normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-zA-Z0-9_-]/g,'_')+'_'+context.metric+'_'+context.from+'_'+context.to+'.png';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);},'image/png');
}
function render(target,context){
 target.replaceChildren();const names=[...new Set(context.stores.map(s=>s.executive||'Sin asignar'))].sort((a,b)=>a.localeCompare(b,'es'));
 if(!names.length){target.textContent='No hay cédulas disponibles con estos filtros.';return;}
 for(const name of names){const stores=context.stores.filter(s=>(s.executive||'Sin asignar')===name),groups=aggregate(stores,context.source,context.from,context.to,context.metric);const card=document.createElement('article');card.className='productivity-image-card';
  const title=document.createElement('strong');title.textContent=name;const caption=document.createElement('p');caption.textContent=stores.length+' tiendas · '+context.from+' al '+context.to+' · '+labels[context.metric];const button=document.createElement('button');button.type='button';button.textContent='Descargar cuadro PNG';button.setAttribute('aria-label','Descargar productividad de '+name);button.disabled=!groups.some(g=>g.totals.income>0);button.addEventListener('click',()=>download(name,groups,context));card.append(title,caption,button);target.append(card);
 }
}
window.INVEX_PRODUCTIVITY_IMAGES={aggregate,render};
})();
