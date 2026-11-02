'use strict';
(()=>{
const labels={income:'Ingresos',standard:'Aprobadas sin garantía',guaranteed:'Garantizadas',finalized:'Finalizadas'};
const logoInvex=new Image();logoInvex.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iOTQiIGhlaWdodD0iMjgiIHZpZXdCb3g9IjAgMCA5NCAyOCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTIyLjk5MzQgOS4yNzc2NEwxNS41NzU3IDkuMjM5OTFIOS45MjkyM1YyNy40NDY2SDE2LjAxMTFWMTMuNDk4N0gyMC4yNTQzQzIzLjE2OTUgMTMuNDk4NyAyMy4xODU0IDE2LjE0MzQgMjMuMjExMSAxOC42MzcxVjI3LjQzODdIMjkuMjMxNlYxOC42MjkyQzI5LjIzMTYgMTAuODQ4MSAyNi43NjM2IDkuMjY5NjkgMjIuOTkzNCA5LjI2OTY5VjkuMjc3NjRaTTQ0LjAyMTUgOS4yMzE5N0w0MC4xNjgyIDIyLjMwNjNMMzkuOTE2OCAyMi45MTc4QzM5LjkxNjggMjIuOTE3OCAzNi4wMzU4IDkuNTA1OTYgMzUuOTcwNSA5LjIzMTk3SDI5LjUxNjZDMjkuNjkyNyA5LjcyNDM3IDM2LjE0MDcgMjcuMTk4NSAzNi4yMjE4IDI3LjQzODdINDMuMjY3NUM0My4zNTA2IDI3LjE5ODUgNDkuNzQzMSA5LjcyNDM3IDQ5LjkzMTEgOS4yMzE5N0g0NC4wMjE1Wk04Mi4wMzA0IDE4LjE0MDhDODIuMDMwNCAxOC4xNDA4IDg3LjMxMjcgOS43Nzk5NiA4Ny42Njg5IDkuMjMxOTdIODEuMTYxNkM4MS4wNjY2IDkuNDMwNTIgNzguMTE1NyAxNS4wMDc3IDc4LjExNTcgMTUuMDA3N0M3OC4xMTU3IDE1LjAwNzcgNzUuNDA4MyA5LjQ0ODM5IDc1LjMwMzQgOS4yMzE5N0g2OC4yMDQzTDczLjg5NjMgMTguMTQwOEw3MC41MzE4IDIzLjIzOTRDNjUuMTc0MyAyMy40MTAyIDYzLjQzODYgMjMuNDEwMiA2MS43OTc5IDIzLjQxMDJINjEuMjk3MkM1Ny44NDM3IDIzLjQxMDIgNTUuNzY3NiAyMi41Mzg2IDU1LjQxNTMgMjAuMDM0OUw1NS4zODc2IDE5LjgzNjRINjguMTY0N1YxOC44NTU1QzY4LjE2NDcgMTUuNzYyMiA2Ny4yNzIyIDguNjM2MzMgNTkuMDIxMiA4LjYzNjMzQzUzLjE0OTIgOC42MzYzMyA0OS4zMDc3IDEyLjM1MzEgNDkuMzA3NyAxOC4xNDI3QzQ5LjMwNzcgMjMuODAzMyA1My41NzI3IDI3LjY2MTEgNTkuODcwMyAyNy42NzNMNjUuODA3NiAyNy41ODM2TDcxLjQ2MzkgMjcuNDM4N0g3NC45MzMzQzc1LjA0MjIgMjcuMjQwMiA3OC4xMTE4IDIxLjQyODcgNzguMTExOCAyMS40Mjg3Qzc4LjExMTggMjEuNDI4NyA4MC43MzYxIDI3LjI0MjEgODAuODQxIDI3LjQzODdIODguMDg0NkM4Ny43MDY2IDI2LjkwMjYgODIuMDI2NSAxOC4xNDA4IDgyLjAyNjUgMTguMTQwOEg4Mi4wMzA0Wk01NS40NjI4IDE2LjIxMDlDNTUuNTY5NiAxNC45ODU5IDU2LjEyNzggMTIuNjc4NyA1OC43ODM3IDEyLjY3ODdDNjEuNjE3OCAxMi42Nzg3IDYyLjEzNDQgMTQuNzgxNCA2Mi4xNzc5IDE2LjIxMDlINTUuNDYyOFpNMCAyNy40Mzg3SDYuMDI4MzlWOS4yMzE5N0gwVjI3LjQzODdaTTAgNS43OTcxMUg2LjAyODM5VjAuMzI3MTQ4SDBWNS43OTcxMVoiIGZpbGw9IndoaXRlIi8+CjxwYXRoIGQ9Ik05MC4yNDk3IDYuMzI0MDNIOTAuNzUwNEM5MS4xODE5IDYuMzI0MDMgOTEuNjAxNCA2LjMwMjE5IDkxLjYwMTQgNS43ODU5NkM5MS42MDE0IDUuMzQzMiA5MS4yMTk1IDUuMjk1NTUgOTAuODg4OSA1LjI5NTU1SDkwLjI0OTdWNi4zMjQwM1pNODkuNzc2NyA0Ljg5NDQ5SDkwLjk2NDJDOTEuNzIyMiA0Ljg5NDQ5IDkyLjA4MjQgNS4xOTYyOCA5Mi4wODI0IDUuODA1ODJDOTIuMDgyNCA2LjQxNTM2IDkxLjcxNDIgNi42MzE3NyA5MS4yMzkzIDYuNjgzNEw5Mi4xNTU2IDguMDk3MDVIOTEuNjM3MUw5MC43NjYyIDYuNzIxMTJIOTAuMjQzOFY4LjA5NzA1SDg5Ljc3NjdWNC44OTQ0OVpNOTAuODE5NyA4LjgzOTYxQzkxLjI4NDEgOC44NTU0MyA5MS43NDI3IDguNzMxNzUgOTIuMTM2NyA4LjQ4NDQyQzkyLjUzMDYgOC4yMzcxIDkyLjg0MiA3Ljg3NzM5IDkzLjAzMDggNy40NTE0MUM5My4yMTk3IDcuMDI1NDIgOTMuMjc3NSA2LjU1MjU3IDkzLjE5NjcgNi4wOTM0M0M5My4xMTYgNS42MzQzIDkyLjkwMDUgNS4yMDk4MiA5Mi41Nzc3IDQuODc0MzdDOTIuMjU0OSA0LjUzODkzIDkxLjgzOTcgNC4zMDc4MSA5MS4zODUyIDQuMjEwNjRDOTAuOTMwNyA0LjExMzQ3IDkwLjQ1NzYgNC4xNTQ2NyA5MC4wMjY1IDQuMzI4OTZDODkuNTk1NSA0LjUwMzI1IDg5LjIyNjIgNC44MDI3IDg4Ljk2NTkgNS4xODg5MkM4OC43MDU2IDUuNTc1MTQgODguNTY2MSA2LjAzMDU0IDg4LjU2NTUgNi40OTY3NkM4OC41NjU1IDcuODIzMDUgODkuNTU1IDguODM3NjMgOTAuODA5OCA4LjgzNzYzTDkwLjgxOTcgOC44Mzk2MVpNOTAuODA5OCAzLjc2MDc5QzkxLjM0OTcgMy43NjA0IDkxLjg3NzcgMy45MjA2OSA5Mi4zMjY4IDQuMjIxMzlDOTIuNzc1OSA0LjUyMjA5IDkzLjEyNiA0Ljk0OTY4IDkzLjMzMjggNS40NTAwNkM5My41Mzk2IDUuOTUwNDQgOTMuNTkzOSA2LjUwMTExIDkzLjQ4ODYgNy4wMzI0MUM5My4zODM0IDcuNTYzNyA5My4xMjM0IDguMDUxNzUgOTIuNzQxNiA4LjQzNDc4QzkyLjM1OTggOC44MTc4MSA5MS44NzMzIDkuMDc4NjEgOTEuMzQzNyA5LjE4NDE5QzkwLjgxNDEgOS4yODk3NyA5MC4yNjUyIDkuMjM1MzkgODkuNzY2NCA5LjAyNzkxQzg5LjI2NzcgOC44MjA0MyA4OC44NDE0IDguNDY5MiA4OC41NDE3IDguMDE4NjRDODguMjQyIDcuNTY4MDggODguMDgyMiA3LjAzODQ1IDg4LjA4MjYgNi40OTY3NkM4OC4wODA1IDYuMTM2ODggODguMTQ5NiA1Ljc4MDE2IDg4LjI4NTkgNS40NDcyNkM4OC40MjIyIDUuMTE0MzcgODguNjIzIDQuODExOTIgODguODc2NyA0LjU1NzQ0Qzg5LjEzMDMgNC4zMDI5NiA4OS40MzE4IDQuMTAxNTEgODkuNzYzNiAzLjk2NDc2QzkwLjA5NTUgMy44MjgwMSA5MC40NTEgMy43NTg2OCA5MC44MDk4IDMuNzYwNzlaIiBmaWxsPSJ3aGl0ZSIvPgo8L3N2Zz4K';
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
function programTotals(stores,context){
 const programs=context.programsOverride||context.source.programs,dates=(context.source.capturedDays||[]).map(d=>context.source.period+'-'+String(d).padStart(2,'0')).filter(d=>d>=context.from&&d<=context.to);
 let p0=0,ahorra=0,pairs=0;const available=new Set();
 if(programs?.status==='available')for(const store of stores)for(const day of dates){const record=programs.stores?.[store.id]?.[day];if(!record)continue;p0+=record.p0;ahorra+=record.ahorra;pairs++;available.add(day);}
 return {p0:pairs?p0:null,ahorra:pairs?ahorra:null,partial:pairs>0&&pairs<stores.length*dates.length,dates:[...available].sort()};
}
const programText=(p,key)=>p[key]===null?'—':fmt(p[key])+(p.partial?'*':'');
function compare(context){
 const stores=context.comparisonStores||context.stores;
 const names=[...new Set(stores.map(s=>s.executive||'Sin asignar'))].filter(name=>name!=='Sin asignar');
 const groups=['WM','SAMS'].map(partner=>({partner,rows:[]}));
 for(const name of names){const assigned=stores.filter(s=>s.executive===name);
  for(const g of aggregate(assigned,context.source,context.from,context.to,context.metric)){
   const numerator=g.totals[context.metric],income=g.totals.income;const programs=programTotals(assigned.filter(s=>s.id.startsWith(g.partner+' ')),context);
   if(!g.count||!income||numerator===null)continue;
   const regions=[...new Set(assigned.map(s=>s.region||'Sin región'))].sort((a,b)=>a.localeCompare(b,'es',{numeric:true}));
   const regionName=regions.length===1?regions[0]:'REGIONES '+regions.map(r=>r.replace(/^REGI[OÓ]N\s*/i,'')).join(' / ');
   groups.find(x=>x.partner===g.partner).rows.push({programs,key:name,name:regionName,regions,stores:g.count,income,numerator,rate:numerator/income,score:context.metric==='income'?income:numerator/income});
  }
 }
 for(const g of groups){g.rows.sort((a,b)=>b.score-a.score||b.income-a.income||a.name.localeCompare(b.name,'es'));g.rows.forEach((r,i)=>r.rank=i&&Math.abs(r.score-g.rows[i-1].score)<1e-12?g.rows[i-1].rank:i+1);}
 return groups;
}
async function downloadComparison(groups,context){
 try{await logoInvex.decode();}catch{alert('No fue posible cargar el logo de INVEX. Vuelve a cargar la página.');return;}
 const metricLabel=context.metric==='standard'?'Aprobadas':labels[context.metric];
 const canvas=document.createElement('canvas'),count=Math.max(1,...groups.map(g=>g.rows.length));canvas.width=1800;canvas.height=708+count*112;const ctx=canvas.getContext('2d');
 const text=(v,x,y,size=20,color='#111111',weight='normal',align='left')=>{ctx.font=weight+' '+size+'px Calibri, Arial';ctx.fillStyle=color;ctx.textAlign=align;ctx.fillText(String(v),x,y);};
 const box=(x,y,w,h,color,r=14)=>{ctx.fillStyle=color;ctx.beginPath();ctx.roundRect(x,y,w,h,r);ctx.fill();};
 function wrapped(v,x,y,width,size=19,maxLines=4,color='#111111'){const lines=[];let line='';ctx.font='bold '+size+'px Calibri, Arial';for(const word of v.split(' ')){if(line&&ctx.measureText(line+' '+word).width>width){lines.push(line);line=word;}else line+=(line?' ':'')+word;}if(line)lines.push(line);lines.slice(0,maxLines).forEach((l,i)=>text(l,x,y+i*(size+4),size,color,'bold'));}
 const bg=ctx.createLinearGradient(0,0,1800,canvas.height);bg.addColorStop(0,'#111111');bg.addColorStop(1,'#050505');ctx.fillStyle=bg;ctx.fillRect(0,0,1800,canvas.height);
 for(let i=0;i<24;i++){ctx.fillStyle=i%2?'#ffffff06':'#ff3b941a';ctx.fillRect(1420+(i%8)*40,20+Math.floor(i/8)*35,14,14);}
 const glow=ctx.createRadialGradient(160,110,0,160,110,600);glow.addColorStop(0,'#ff2c8d42');glow.addColorStop(1,'#ff2c8d00');ctx.fillStyle=glow;ctx.fillRect(0,0,900,500);
 const blueGlow=ctx.createRadialGradient(1680,100,0,1680,100,550);blueGlow.addColorStop(0,'#ff77b63b');blueGlow.addColorStop(1,'#ff77b600');ctx.fillStyle=blueGlow;ctx.fillRect(900,0,900,500);
 ctx.drawImage(logoInvex,782.5,22,235,70);
 ctx.strokeStyle='#ff5aa27a';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(430,66);ctx.lineTo(720,66);ctx.moveTo(1080,66);ctx.lineTo(1370,66);ctx.stroke();
 text('COMPETENCIA ENTRE CÉLULAS',900,142,39,'#fff','bold','center');
 text('RANKING DE PRODUCTIVIDAD',900,176,18,'#ff9bc9','bold','center');
 box(467,195,535,44,'#21151c',8);text(context.from+' al '+context.to+'   |   09:00–19:59',734.5,225,22,'#ffffff','normal','center');
 box(1018,195,315,44,'#ff4a9c',8);text(metricLabel.toUpperCase(),1175.5,225,21,'#0d0d0d','bold','center');
 ctx.fillStyle='#ff4299';ctx.fillRect(40,137,295,4);ctx.fillRect(1465,137,295,4);
 const widths=[54,325,85,115,115,145];
 ctx.save();ctx.translate(0,60);
 groups.forEach((g,n)=>{const x=38+n*885,w=839,accent=n?'#ff8fbd':'#ff4299',soft=n?'#ffe5f0':'#ffe5f0';
  box(x,210,w,canvas.height-368,'#ffffff',20);box(x,210,w,55,accent,14);ctx.fillStyle=accent;ctx.fillRect(x,242,w,23);text(g.partner==='WM'?'WALMART':'SAMS',x+22,247,28,'#111111','bold');text(g.rows.length+' CÉLULAS',x+w-22,245,18,'#111111','bold','right');
  const lead=g.rows[0];box(x+18,283,w-36,135,soft,12);ctx.strokeStyle=accent;ctx.lineWidth=3;ctx.beginPath();ctx.roundRect(x+18,283,w-36,135,12);ctx.stroke();
  text(lead?'PRIMER LUGAR':'SIN REGISTROS',x+35,312,16,'#644451','bold');
  if(lead){wrapped(lead.name,x+35,345,505,21,3);text(context.metric==='income'?fmt(lead.income):fmt(100*lead.rate)+'%',x+w-35,359,54,'#111111','bold','right');text(lead.stores+' tiendas · '+fmt(lead.numerator)+' '+metricLabel.toLowerCase(),x+w-35,394,18,'#644451','normal','right');}
  if(lead)text('P0: '+programText(lead.programs,'p0')+'   ·   AHORRA+: '+programText(lead.programs,'ahorra'),x+35,394,18,'#644451','bold');
  let left=x;['POS.','CÉLULA / REGIONES','TIENDAS','INGRESOS',metricLabel.toUpperCase(),context.metric==='income'?'VOLUMEN':'PRODUCTIVIDAD'].forEach((h,j)=>{text(h,left+widths[j]/2,451,j===4||j===5?14:15,'#74616b','bold','center');left+=widths[j];});
  const top=lead?.score||1;
  g.rows.forEach((r,i)=>{const y=470+i*112;box(x+12,y,w-24,103,r.rank===1?soft:i%2?'#fff5f9':'#fff',9);if(r.rank===1)box(x+12,y+10,5,83,accent,2);box(x+18,y+18,43,43,r.rank===1?accent:r.rank===2?'#ffbbd7':r.rank===3?'#ffdae9':'#f1e7ec',7);text(r.rank,x+39.5,y+47,23,'#111111','bold','center');wrapped(r.name,x+68,y+28,306,18,3);
   let dx=x+widths[0]+widths[1];for(const [j,v]of [fmt(r.stores),fmt(r.income),fmt(r.numerator),context.metric==='income'?fmt(r.income):fmt(100*r.rate)+'%'].entries()){text(v,dx+widths[j+2]/2,y+44,j===3?28:22,'#111111',j===3?'bold':'normal','center');dx+=widths[j+2];}
   text('P0: '+programText(r.programs,'p0')+'     AHORRA+: '+programText(r.programs,'ahorra'),x+68,y+94,16,'#825b6f','bold');
   box(x+68,y+100,w-95,3,'#f2e2ea',1);if(r.score>0)box(x+68,y+100,(w-95)*r.score/top,3,r.rank<=3?accent:'#e1c4d2',1);
  });
 });
 ctx.restore();
 text('Tiendas operando · '+(context.metric==='income'?'Mayor volumen de ingresos':'Porcentaje = '+metricLabel.toLowerCase()+' / ingresos')+' · Empates comparten posición',38,canvas.height-72,19,'#f5d7e6');
 const programDates=[...new Set(groups.flatMap(g=>g.rows.flatMap(r=>r.programs.dates)))].sort();
 text('P0 y Ahorra+: día completo · '+(programDates.length?'Datos del '+programDates[0]+' al '+programDates.at(-1):'Sin datos en el rango seleccionado')+' · * Cobertura parcial del periodo o de las tiendas',38,canvas.height-44,17,'#f5d7e6');
 text('Fuente: '+context.source.sourceName+' · Corte: '+(context.source.lastRecordAt||'Sin fecha').replace('T',' ')+((context.programsOverride||context.source.programs)?.sourceName?' · P0/Ahorra+: '+(context.programsOverride||context.source.programs).sourceName:''),38,canvas.height-17,17,'#d7a9be');
 canvas.toBlob(blob=>{if(!blob)return;const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='INVEX_Comparativa_CELULAS_'+context.metric+'_'+context.from+'_'+context.to+'.png';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);},'image/png');
}
function render(target,context){
 target.replaceChildren();const groups=compare(context),button=document.createElement('button');button.type='button';button.textContent='Descargar comparativa de CÉLULAS · PNG';button.id='download-competition';button.disabled=!groups.some(g=>g.rows.length);button.addEventListener('click',()=>downloadComparison(groups,context));target.append(button);
 const info=document.createElement('p');info.className='note';info.textContent='Las CÉLULAS se identifican por sus regiones. La comparación respeta los demás filtros y omite la selección individual de CÉLULA. P0 y Ahorra+ son conteos de día completo; * indica cobertura parcial y — indica que no hay datos. No modifican la clasificación de productividad.';target.append(info);
 for(const group of groups){const article=document.createElement('article');article.className='productivity-competition';const title=document.createElement('h4');title.textContent=group.partner==='WM'?'WALMART':'SAMS';article.append(title);if(group.rows[0]){const lead=document.createElement('div');lead.className='competition-spotlight';const caption=document.createElement('span');caption.textContent='PRIMER LUGAR';const name=document.createElement('strong');name.textContent=group.rows[0].name;const score=document.createElement('b');score.textContent=context.metric==='income'?fmt(group.rows[0].income)+' ingresos':fmt(group.rows[0].rate*100)+'%';lead.append(caption,name,score);article.append(lead);}
  if(!group.rows.length){const p=document.createElement('p');p.textContent='Sin registros para estos filtros.';article.append(p);target.append(article);continue;}
  const wrap=document.createElement('div');wrap.className='table-wrap';const table=document.createElement('table'),head=document.createElement('thead'),header=document.createElement('tr');for(const label of ['Posición','CÉLULA / REGIONES','Tiendas','Ingresos',context.metric==='standard'?'Aprobadas':labels[context.metric],context.metric==='income'?'Resultado':'Productividad %','P0','Ahorra+']){const th=document.createElement('th');th.textContent=label;header.append(th);}head.append(header);table.append(head);const body=document.createElement('tbody');
  for(const r of group.rows){const row=document.createElement('tr');if(r.rank===1)row.className='competition-leader';for(const value of [r.rank,r.name,r.stores,r.income,r.numerator,context.metric==='income'?fmt(r.income):fmt(r.rate*100)+'%',programText(r.programs,'p0'),programText(r.programs,'ahorra')]){const td=document.createElement('td');td.textContent=value;row.append(td);}body.append(row);}table.append(body);wrap.append(table);article.append(wrap);target.append(article);
 }
}
window.INVEX_PRODUCTIVITY_IMAGES={aggregate,compare,programTotals,render};
})();
