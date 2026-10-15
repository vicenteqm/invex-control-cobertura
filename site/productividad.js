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
const store=control('Tienda Walmart',make('select'));store.append(new Option('Todas las Walmart del Excel',''));for(const s of [...source.stores].sort((a,b)=>a.name.localeCompare(b.name,'es')))store.append(new Option(s.name+' · '+s.id,s.id));
const reset=make('button','Limpiar filtros');reset.type='button';filters.append(reset);section.append(filters);
const error=make('p',undefined,'productivity-error');error.setAttribute('role','status');section.append(error);
const kpis=make('div',undefined,'productivity-kpis');section.append(kpis);
const charts=make('div',undefined,'productivity-charts');section.append(charts);
function panel(title,caption,wide=false){const box=make('article',undefined,'panel productivity-chart'+(wide?' productivity-wide':''));box.append(make('h3',title),make('p',caption));const body=make('div',undefined,'productivity-chart-body');box.append(body);charts.append(box);return body;}
const daily=panel('Ingresos por día','Mes completo. Los días sin hoja aparecen como Sin datos; las barras respetan los filtros.',true);
const hourly=panel('Distribución por hora','Ingresos acumulados dentro de las fechas y tiendas seleccionadas.');
const ranking=panel('Tiendas con mayor volumen','Las diez Walmart con más ingresos en la consulta.');
const heat=panel('Mapa de actividad por día y hora','Mayor intensidad indica más ingresos. — significa Sin datos; 0 es un valor reportado.',true);
const note=make('p',undefined,'productivity-footnote');section.append(note);
function draw(){
 const start=Number(from.value.slice(-2)),end=Number(to.value.slice(-2));
 if(!from.value.startsWith(source.period+'-')||!to.value.startsWith(source.period+'-')||!Number.isInteger(start)||!Number.isInteger(end)||start<1||end>source.daysInMonth||start>end){error.textContent='Selecciona un rango válido dentro del mes, con inicio anterior o igual al final.';return;}
 error.textContent='';const selected=source.stores.filter(s=>(!region.value||s.region===region.value)&&(!store.value||s.id===store.value));
 const dayHours={},hourTotals=source.hours.map(()=>0),storeTotals=[];let total=0,afternoon=0,observed=0;
 for(let d=1;d<=source.daysInMonth;d++)if(source.capturedDays.includes(d)&&d>=start&&d<=end&&selected.some(s=>s.days[d]))dayHours[d]=source.hours.map(()=>0);
 for(const s of selected){let count=0;for(const [d,values] of Object.entries(s.days)){if(!dayHours[d])continue;values.forEach((value,i)=>{dayHours[d][i]+=value;hourTotals[i]+=value;count+=value;total+=value;if(Number(source.hours[i].slice(0,2))>=14)afternoon+=value;});}storeTotals.push({s,count});}
 observed=Object.keys(dayHours).length;const maximum=Math.max(0,...hourTotals),peak=maximum>0?source.hours[hourTotals.indexOf(maximum)]:'Sin actividad';
 kpis.replaceChildren();for(const [title,value,detail] of [['Ingresos registrados',number(total),selected.length+' tiendas del Excel'],['Franja con mayor volumen',peak,maximum>0?number(maximum)+' ingresos en esta franja':'Sin ingresos en la consulta'],['Ingresos desde las 14:00',total?number(100*afternoon/total)+'%':'—',number(afternoon)+' ingresos'],['Días con datos',number(observed),'De '+(end-start+1)+' días seleccionados']]){const card=make('article',undefined,'productivity-kpi');card.append(make('span',title),make('strong',value),make('small',detail));kpis.append(card);}
 daily.replaceChildren();const grid=make('div',undefined,'productivity-daily');const dayMax=Math.max(1,...Object.values(dayHours).map(a=>a.reduce((a,b)=>a+b,0)));for(let d=1;d<=source.daysInMonth;d++){const values=dayHours[d],outside=d<start||d>end;const count=values?values.reduce((a,b)=>a+b,0):null;const item=make('div',undefined,'productivity-day'+(values?'':' no-data')+(outside?' outside':''));item.title=dayDate(d)+': '+(outside?'Fuera del filtro':count===null?'Sin datos':number(count)+' ingresos');item.setAttribute('aria-label',item.title);const rail=make('div',undefined,'productivity-rail');const fill=make('i');fill.style.height=count===null?'0%':100*count/dayMax+'%';rail.append(fill);item.append(make('small',count===null?'—':number(count)),rail,make('span',String(d).padStart(2,'0')));grid.append(item);}daily.append(grid);
 function bars(target,items,max,empty){target.replaceChildren();if(!items.length){target.append(make('p',empty,'note'));return;}for(const {label,value,sub} of items){const row=make('div',undefined,'productivity-bar-row');const name=make('div',undefined,'productivity-bar-name');name.append(make('span',label));if(sub)name.append(make('small',sub));const track=make('div',undefined,'productivity-track');const fill=make('i');fill.style.width=(max?100*value/max:0)+'%';track.append(fill);row.append(name,track,make('strong',number(value)));target.append(row);}}
 bars(hourly,source.hours.map((label,i)=>({label,value:hourTotals[i]})),maximum,'Sin actividad.');
 const top=storeTotals.sort((a,b)=>b.count-a.count||a.s.id.localeCompare(b.s.id,'es')).slice(0,10);bars(ranking,top.map(x=>({label:x.s.name,value:x.count,sub:x.s.id+' · '+x.s.region})),Math.max(0,...top.map(x=>x.count)),'No hay tiendas con esos filtros.');
 heat.replaceChildren();const table=make('table',undefined,'productivity-heatmap');const head=make('thead'),header=make('tr');const first=make('th','Día');first.scope='col';header.append(first);for(const label of source.hours){const th=make('th',label.slice(0,5));th.scope='col';header.append(th);}head.append(header);table.append(head);const body=make('tbody');const cellMax=Math.max(1,...Object.values(dayHours).flat());for(let d=1;d<=source.daysInMonth;d++){const tr=make('tr'),day=make('th',String(d).padStart(2,'0'));day.scope='row';tr.append(day);source.hours.forEach((hour,i)=>{const value=dayHours[d]?.[i]??null;const td=make('td',value===null?'—':String(value),value===null?'heat-empty':value/cellMax>0.45?'heat-strong':'');td.title=dayDate(d)+' · '+hour+': '+(value===null?'Sin datos':number(value)+' ingresos');if(value!==null)td.style.setProperty('--heat',value===0?'0':String(0.14+0.74*value/cellMax));tr.append(td);});body.append(tr);}table.append(body);heat.append(table);
 note.textContent='Universo: Walmart incluidas en el Excel de productividad, independientemente del estatus en la base de cobertura. Se suman exclusivamente las hojas por fecha; GENERAL, HORAS PICO y las filas TOTAL no se vuelven a sumar.'+(source.warnings.length?' '+source.warnings.join(' '):'');
}
for(const input of [from,to,region,store])input.addEventListener('change',draw);reset.addEventListener('click',()=>{from.value=from.min;to.value=to.max;region.value='';store.value='';draw();});draw();
})();
