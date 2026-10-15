'use strict';
(() => {
const source=window.INVEX_DATA?.productiveHours;
if(!source)return;
const make=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
const section=make('section',undefined,'productivity-section');section.id='productividad';
const heading=make('div',undefined,'section-title');heading.append(make('h2','Horas productivas · Walmart'),make('span','INGRESOS POR DÍA Y HORA'));section.append(heading);
document.getElementById('tiendas').before(section);
const nav=document.querySelector('nav'),link=make('a','Horas productivas');link.href='#productividad';nav.querySelector('a[href="#tiendas"]').before(link);
nav.addEventListener('click',event=>{const a=event.target.closest('a');if(a)for(const l of nav.querySelectorAll('a'))l.classList.toggle('selected',a===l);});
if('IntersectionObserver' in window){const observer=new IntersectionObserver(entries=>{if(entries.some(x=>x.isIntersecting))for(const l of nav.querySelectorAll('a'))l.classList.toggle('selected',l===link);},{rootMargin:'-10% 0px -70% 0px'});observer.observe(section);}
if(source.status!=='available'){const box=make('article',undefined,'panel');box.append(make('h3',source.status==='error'?'Revisar archivo de productividad':'Sin datos de productividad para este mes'),make('p',source.message||'Ejecuta la actualización con el Excel de horas productivas.'));section.append(box);return;}
const number=n=>new Intl.NumberFormat('es-MX',{maximumFractionDigits:1}).format(n);
const dayDate=day=>source.period+'-'+String(day).padStart(2,'0');
const intro=make('div',undefined,'productivity-intro');intro.append(make('p','Volumen de ingresos registrados en cada franja horaria. Cada ingreso corresponde a un registro del Excel; no representa un importe monetario ni horas trabajadas.'),make('small','Fuente: '+source.sourceName+' · Última hoja disponible: '+dayDate(source.lastDay)+' · Archivo modificado: '+new Date(source.sourceModifiedAt).toLocaleString('es-MX',{timeZone:'America/Mexico_City'})));section.append(intro);
const filters=make('div',undefined,'productivity-filters');
function control(title,node){node.setAttribute('aria-label',title);const label=make('label');label.append(make('span',title),node);filters.append(label);return node;}
const from=control('Desde',make('input'));from.type='date';from.min=dayDate(1);from.max=dayDate(source.daysInMonth);from.value=dayDate(1);
const to=control('Hasta',make('input'));to.type='date';to.min=from.min;to.max=from.max;to.value=to.max;
const region=control('Región',make('select'));region.append(new Option('Todas las regiones',''));for(const name of [...new Set(source.stores.map(s=>s.region))].sort((a,b)=>a.localeCompare(b,'es',{numeric:true})))region.append(new Option(name,name));
const store=control('Tienda Walmart',make('select'));store.append(new Option('Todas las Walmart de la fuente',''));for(const s of [...source.stores].sort((a,b)=>a.name.localeCompare(b.name,'es')))store.append(new Option(s.name+' · '+s.id,s.id));
const reset=make('button','Limpiar filtros');reset.type='button';filters.append(reset);section.append(filters);
const approvals=control('Aprobadas',make('select'));approvals.append(new Option('Solo Aprobada','standard'),new Option('Incluir Aprobada con Garantía','guaranteed'));approvals.disabled=!source.hasApprovals;
const error=make('p',undefined,'productivity-error');error.setAttribute('role','status');section.append(error);
const kpis=make('div',undefined,'productivity-kpis');section.append(kpis);
const charts=make('div',undefined,'productivity-charts');section.append(charts);
function panel(title,caption,wide=false){const box=make('article',undefined,'panel productivity-chart'+(wide?' productivity-wide':''));box.append(make('h3',title),make('p',caption));const body=make('div',undefined,'productivity-chart-body');box.append(body);charts.append(box);return body;}
const daily=panel('Ingresos por día','Mes completo. Las fechas fuera del rango de la fuente aparecen sin datos; ambas series respetan los filtros.',true);
const hourly=panel('Distribución por hora','Ingresos acumulados dentro de las fechas y tiendas seleccionadas.');
const ranking=panel('Tiendas con mayor volumen','Las diez Walmart con más ingresos en la consulta.');
const heat=panel('Mapa de actividad por día y hora','Mayor intensidad indica más ingresos. — significa Sin datos; 0 es un valor reportado.',true);
const note=make('p',undefined,'productivity-footnote');section.append(note);
function combo(target,items){
 target.replaceChildren();const legend=make('p',undefined,'productivity-legend');legend.append(make('span','Barras: ingresos','legend-income'),make('span',source.hasApprovals?'Línea: aprobadas':'Aprobadas: sin fuente disponible','legend-approved'));target.append(legend);
 const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 1100 300');svg.setAttribute('role','img');svg.setAttribute('aria-label','Ingresos en barras y aprobadas en línea, misma escala');svg.classList.add('productivity-combo');
 const el=(tag,attrs,text)=>{const n=document.createElementNS(svg.namespaceURI,tag);for(const [k,v]of Object.entries(attrs))n.setAttribute(k,v);if(text!==undefined)n.textContent=text;svg.append(n);return n;};
 const max=Math.max(1,...items.flatMap(x=>[x.value||0,x.approved||0])),step=1020/Math.max(1,items.length),y=v=>245-210*v/max;
 for(let i=0;i<=4;i++){const v=max*i/4;el('line',{x1:55,x2:1080,y1:y(v),y2:y(v),class:'combo-grid'});el('text',{x:48,y:y(v)+4,'text-anchor':'end',class:'combo-axis'},number(v));}
 let points=[];const flush=()=>{if(points.length)el('polyline',{points:points.join(' '),class:'combo-line',fill:'none'});points=[];};
 items.forEach((item,i)=>{const x=55+step*(i+.5);const title=item.label+': '+(item.value===null?'Sin datos':number(item.value)+' ingresos'+(source.hasApprovals?' · '+number(item.approved)+' aprobadas':''));const bar=el('rect',{x:x-step*.3,y:item.value===null?245:y(item.value),width:step*.6,height:item.value===null?0:245-y(item.value),class:'combo-income'});const tip=document.createElementNS(svg.namespaceURI,'title');tip.textContent=title;bar.append(tip);el('text',{x,y:264,'text-anchor':'middle',class:'combo-axis'},item.short||item.label);if(item.value===null){flush();el('text',{x,y:237,'text-anchor':'middle',class:'combo-axis'},'—');}else if(source.hasApprovals){points.push(x+','+y(item.approved));const dot=el('circle',{cx:x,cy:y(item.approved),r:3.5,class:'combo-dot'});const t=document.createElementNS(svg.namespaceURI,'title');t.textContent=title;dot.append(t);}});flush();target.append(svg);
}
function draw(){
 const start=Number(from.value.slice(-2)),end=Number(to.value.slice(-2));
 if(!from.value.startsWith(source.period+'-')||!to.value.startsWith(source.period+'-')||!Number.isInteger(start)||!Number.isInteger(end)||start<1||end>source.daysInMonth||start>end){error.textContent='Selecciona un rango válido dentro del mes, con inicio anterior o igual al final.';return;}
 error.textContent='';const selected=source.stores.filter(s=>(!region.value||s.region===region.value)&&(!store.value||s.id===store.value));
 const dayHours={},approvedHours={},hourApproved=source.hours.map(()=>0),hourTotals=source.hours.map(()=>0),storeTotals=[];let total=0,afternoon=0,observed=0;
 for(let d=1;d<=source.daysInMonth;d++)if(source.capturedDays.includes(d)&&d>=start&&d<=end&&selected.some(s=>s.days[d]))dayHours[d]=source.hours.map(()=>0);
 for(const d of Object.keys(dayHours))approvedHours[d]=source.hours.map(()=>0);
 for(const s of selected){let count=0,approved=0;for(const [d,values] of Object.entries(s.days)){if(!dayHours[d])continue;values.forEach((value,i)=>{const a=(s.approvedDays?.[d]?.[i]||0)+(approvals.value==='guaranteed'?(s.guaranteedDays?.[d]?.[i]||0):0);approvedHours[d][i]+=a;hourApproved[i]+=a;approved+=a;dayHours[d][i]+=value;hourTotals[i]+=value;count+=value;total+=value;if(Number(source.hours[i].slice(0,2))>=14)afternoon+=value;});}storeTotals.push({s,count,approved});}
 observed=Object.keys(dayHours).length;const maximum=Math.max(0,...hourTotals),peak=maximum>0?source.hours[hourTotals.indexOf(maximum)]:'Sin actividad';
 kpis.replaceChildren();for(const [title,value,detail] of [['Ingresos registrados',number(total),selected.length+' tiendas de la fuente'],['Franja con mayor volumen',peak,maximum>0?number(maximum)+' ingresos en esta franja':'Sin ingresos en la consulta'],['Ingresos desde las 14:00',total?number(100*afternoon/total)+'%':'—',number(afternoon)+' ingresos'],['Días con datos',number(observed),'De '+(end-start+1)+' días seleccionados']]){const card=make('article',undefined,'productivity-kpi');card.append(make('span',title),make('strong',value),make('small',detail));kpis.append(card);}
 function bars(target,items,max,empty){target.replaceChildren();if(!items.length){target.append(make('p',empty,'note'));return;}for(const {label,value,sub} of items){const row=make('div',undefined,'productivity-bar-row');const name=make('div',undefined,'productivity-bar-name');name.append(make('span',label));if(sub)name.append(make('small',sub));const track=make('div',undefined,'productivity-track');const fill=make('i');fill.style.width=(max?100*value/max:0)+'%';track.append(fill);row.append(name,track,make('strong',number(value)));target.append(row);}}
 combo(daily,Array.from({length:source.daysInMonth},(_,i)=>{const d=i+1;return {label:dayDate(d),short:String(d).padStart(2,'0'),value:dayHours[d]?dayHours[d].reduce((a,b)=>a+b,0):null,approved:approvedHours[d]?.reduce((a,b)=>a+b,0)||0};}));
 combo(hourly,source.hours.map((label,i)=>({label,short:label.slice(0,2),value:observed?hourTotals[i]:null,approved:hourApproved[i]})));
 const top=storeTotals.sort((a,b)=>b.count-a.count||a.s.id.localeCompare(b.s.id,'es')).slice(0,10);bars(ranking,top.map(x=>({label:x.s.name,value:x.count,sub:x.s.id+' · '+x.s.region})),Math.max(0,...top.map(x=>x.count)),'No hay tiendas con esos filtros.');
 if(source.hasApprovals)combo(ranking,top.map(x=>({label:x.s.id+' · '+x.s.name,short:x.s.id.replace('WM ',''),value:observed?x.count:null,approved:x.approved})));
 heat.replaceChildren();const table=make('table',undefined,'productivity-heatmap');const head=make('thead'),header=make('tr');const first=make('th','Día');first.scope='col';header.append(first);for(const label of source.hours){const th=make('th',label.slice(0,5));th.scope='col';header.append(th);}head.append(header);table.append(head);const body=make('tbody');const cellMax=Math.max(1,...Object.values(dayHours).flat());for(let d=1;d<=source.daysInMonth;d++){const tr=make('tr'),day=make('th',String(d).padStart(2,'0'));day.scope='row';tr.append(day);source.hours.forEach((hour,i)=>{const value=dayHours[d]?.[i]??null;const td=make('td',value===null?'—':String(value),value===null?'heat-empty':value/cellMax>0.45?'heat-strong':'');td.title=dayDate(d)+' · '+hour+': '+(value===null?'Sin datos':number(value)+' ingresos');if(value!==null)td.style.setProperty('--heat',value===0?'0':String(0.14+0.74*value/cellMax));tr.append(td);});body.append(tr);}table.append(body);heat.append(table);
 if(source.sourceType==='records'){intro.querySelector('p').textContent='Ingresos: registros de módulos Walmart, agrupados por fecha y hora de creación. '+source.approvalBasis;intro.querySelector('small').textContent='Fuente: '+source.sourceName+' · Último ingreso: '+source.lastRecordAt.replace('T',' ')+' · El último día puede estar incompleto.';}
 note.textContent=source.sourceType==='records'?'Se cuenta una fila por ingreso de módulo Walmart. '+source.approvalBasis+' '+(approvals.value==='guaranteed'?'La línea incluye Aprobada y Aprobada con Garantía.':'La línea incluye únicamente el resultado Aprobada.')+' Total de aprobadas en la consulta: '+number(hourApproved.reduce((a,b)=>a+b,0))+'. Las fechas posteriores al rango exportado se muestran sin datos.':'Universo: Walmart incluidas en el Excel de productividad. Se suman exclusivamente las hojas por fecha, sin duplicar filas TOTAL.';
}
for(const input of [from,to,region,store,approvals])input.addEventListener('change',draw);reset.addEventListener('click',()=>{from.value=from.min;to.value=to.max;region.value='';store.value='';approvals.value='standard';draw();});draw();
})();
