'use strict';
(()=>{
const make=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
function mount(target,options){
 const box=make('div');box.className='cuponera-upload cuponera-images-only';const heading=make('div');heading.className='cuponera-upload-heading';heading.append(make('h4','Cuponera para tus imágenes'),make('span','SOLO ESTA SESIÓN'));box.append(heading);
 box.append(make('p','Carga la cuponera actualizada para agregar P0 y Ahorra+ al cuadro comparativo y al PNG.'));
 const source=make('p');source.className='note';box.append(source);
 const refresh=programs=>{source.textContent=programs?.status==='available'?'Archivo: '+programs.sourceName+' · Fechas: '+programs.dates[0]+' al '+programs.dates.at(-1):'Sin cuponera disponible para este cuadro.';};refresh(options.source.programs);
 const label=make('label','Selecciona la cuponera (.xlsx)');label.htmlFor='cuponera-file';const input=make('input');input.type='file';input.accept='.xlsx';input.id='cuponera-file';input.setAttribute('aria-label','Seleccionar cuponera para imágenes');
 const actions=make('div');actions.className='cuponera-upload-actions';const button=make('button','Cargar para generar imágenes');button.type='button';button.disabled=true;button.id='load-cuponera-images';const reset=make('button','Usar datos publicados');reset.type='button';reset.className='cuponera-reset';reset.disabled=true;actions.append(button,reset);
 const status=make('p','El archivo se procesa en tu navegador. No se sube ni publica en GitHub.');status.setAttribute('role','status');status.setAttribute('aria-live','polite');box.append(label,input,actions,status);target.append(box);
 input.addEventListener('change',()=>{button.disabled=!input.files.length;status.textContent=input.files.length?'Seleccionado: '+input.files[0].name:'Selecciona una cuponera .xlsx';});
 button.addEventListener('click',async()=>{const file=input.files[0];if(!file)return;button.disabled=true;input.disabled=true;status.textContent='Leyendo la cuponera y validando las tiendas…';
  try{const programs=await window.INVEX_CUPONERA_READER.readPrograms(file,window.INVEX_DATA.stores);options.onUpdated(programs);refresh(programs);reset.disabled=false;status.textContent='Cuponera lista para generar imágenes. '+Object.keys(programs.stores).length+' tiendas vinculadas.'+(programs.unmatchedStores?' '+programs.unmatchedStores+' tiendas sin coincidencia.':'');}
  catch(error){status.textContent=error.message||'No se pudo leer la cuponera; se conservan los datos anteriores.';}
  finally{input.disabled=false;button.disabled=!input.files.length;}
 });
 reset.addEventListener('click',()=>{options.onUpdated(null);refresh(options.source.programs);input.value='';button.disabled=true;reset.disabled=true;status.textContent='Se restauraron los datos publicados para las imágenes.';});
}
window.INVEX_CUPONERA_UPLOAD={mount};
})();
