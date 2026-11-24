'use strict';
(() => {
  const data=window.INVEX_DATA;
  if(!data?.stores)return;
  const make=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
  const section=document.getElementById('cobertura');
  const wrap=make('div',undefined,'coverage-shifts');
  const controls=make('div',undefined,'shift-controls');
  const region=make('select');region.setAttribute('aria-label','Región de las tablas de horarios');
  region.append(new Option('Todas las regiones',''));
  const baseStores=data.stores.filter(s=>s.status==='OPERANDO');
  let stores=baseStores;
  for(const name of [...new Set(stores.map(s=>s.region))].sort((a,b)=>a.localeCompare(b,'es',{numeric:true})))region.append(new Option(name,name));
  const search=make('input');search.type='search';search.placeholder='Buscar socio, tienda o región';search.setAttribute('aria-label','Buscar tienda en las tablas de horarios');
  const block=make('select');block.setAttribute('aria-label','Bloque de vacantes');block.append(new Option('Todos los turnos',''),new Option('Tiempo completo','Tiempo completo'),new Option('Apertura','Apertura'),new Option('Cierre','Cierre'));
  const reset=make('button','Limpiar');reset.type='button';
  controls.append(search,region,block,reset);
  const heading=make('div',undefined,'shift-heading');heading.append(make('h3','Distribución por horario'),make('p','Personal con estatus ACTIVO · promotores y sublíderes de tiendas operando.'));
  const panels=make('div',undefined,'shift-panels');
  function panel(title,subtitle,headers){const box=make('article',undefined,'panel shift-panel');box.append(make('h3',title),make('p',subtitle));const scroll=make('div',undefined,'table-wrap shift-scroll');const table=make('table');const head=make('thead'),tr=make('tr');for(const h of headers){const th=make('th',h);th.scope='col';tr.append(th);}head.append(tr);const body=make('tbody');table.append(head,body);scroll.append(table);const foot=make('p',undefined,'note');box.append(scroll,foot);panels.append(box);return {body,foot};}
  const missing=panel('Horarios con personal faltante','Vacantes por tienda y bloque de turno',['Bloque','Horario','Personal requerido','Socio y tienda','Región']);
  const active=panel('Horarios con personal activo','Personal por horario, tipo de contrato y tienda',['Horario','Tipo de contrato','Personal activo','Socio y tienda','Región']);
  function draw(){const q=search.value.trim().toLocaleLowerCase('es');const selected=stores.filter(s=>(!window.INVEX_COVERAGE_SELECTION||window.INVEX_COVERAGE_SELECTION.includes(s.id))&&(!region.value||s.region===region.value)&&(!q||[s.id,s.name,s.region].join(' ').toLocaleLowerCase('es').includes(q)));missing.body.replaceChildren();active.body.replaceChildren();let vacancies=0,assigned=0,unallocated=0,visibleTotal=0;for(const s of selected.filter(s=>s.gap>0).sort((a,b)=>b.gap-a.gap||a.id.localeCompare(b.id,'es',{numeric:true}))){vacancies+=s.gap;const shifts=s.shiftCoverage;if(!shifts)continue;unallocated+=shifts.unallocated||0;assigned+=Object.values(shifts.gaps).reduce((n,x)=>n+x,0);for(const b of block.value?[block.value]:['Tiempo completo','Apertura','Cierre']){const n=shifts.gaps[b]||0;if(!n)continue;visibleTotal+=n;const tr=make('tr');for(const value of [b,shifts.hours[b],n,s.id+' · '+s.name,s.region])tr.append(make('td',String(value)));missing.body.append(tr);}}
    missing.foot.textContent='Total mostrado: '+visibleTotal+' plazas · '+assigned+' asignadas a bloques de '+vacancies+' vacantes totales.'+(unallocated?' '+unallocated+' vacantes sin asignación a un bloque según las metas; revisar tienda/perfil.':'')+' Primero se cubre la meta de tiempo completo; los medios tiempos se reparten entre apertura y cierre. Solo se muestran bloques con faltantes.';
    let total=0;for(const s of [...selected].sort((a,b)=>a.id.localeCompare(b.id,'es',{numeric:true})))for(const [schedule,n] of Object.entries(s.activeSchedules||{}).sort((a,b)=>a[0].localeCompare(b[0],'es'))){if(!n)continue;const contracts=s.activeScheduleContracts?.[schedule]||{'Sin detalle de contrato':n};for(const [contract,count] of Object.entries(contracts).sort((a,b)=>a[0].localeCompare(b[0],'es'))){if(!count)continue;total+=count;const tr=make('tr');for(const value of [schedule,contract,count,s.id+' · '+s.name,s.region])tr.append(make('td',String(value)));active.body.append(tr);}}
    const expected=selected.reduce((n,s)=>n+s.active,0);active.foot.textContent='Total: '+total+' personas activas · '+selected.length+' tiendas.'+(total!==expected?' Faltan horarios en los datos publicados; ejecuta la actualización.':' Coincide con el personal activo de las tiendas filtradas.');
    for(const {body} of [missing,active])if(!body.children.length){const tr=make('tr'),cell=make('td','Sin resultados con estos filtros.');cell.colSpan=5;tr.append(cell);body.append(tr);}
  }
  window.addEventListener('invex:coverage-filter',()=>{stores=baseStores.map(s=>window.INVEX_COVERAGE_STORE?window.INVEX_COVERAGE_STORE(s):s);draw();});
  for(const n of [search,region,block])n.addEventListener(n===search?'input':'change',draw);reset.addEventListener('click',()=>{search.value='';region.value='';block.value='';draw();});wrap.append(heading,controls,panels);section.insertBefore(wrap,document.getElementById("coverage-store-maps"));draw();
})();
