'use strict';
(()=>{
const make=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
function mount(target,options){
 const box=make('div');box.className='cuponera-upload';box.append(make('h4','Actualizar cuponera para todos'));
 const source=make('p');source.className='note';box.append(source);
 const refresh=programs=>{source.textContent=programs?.status==='available'?'Cuponera actual: '+programs.sourceName+' · Fechas: '+programs.dates[0]+' al '+programs.dates.at(-1):'No hay una cuponera válida publicada.';};refresh(options.source.programs);
 const local=window.INVEX_LOCAL_UPLOAD;
 if(!local?.token){
  box.append(make('p','Abre CARGAR_CUPONERA.bat en la carpeta del proyecto. Se abrirá este mismo tablero con el selector de archivo y la publicación habilitados. Mantén la ventana del cargador abierta.'));
  const link=make('a','Abrir cargador local');link.href='http://127.0.0.1:8771/#productividad';link.className='cuponera-local-link';box.append(link);target.append(box);return;
 }
 const label=make('label','Selecciona la cuponera actualizada (.xlsx)');label.htmlFor='cuponera-file';const input=make('input');input.type='file';input.accept='.xlsx';input.id='cuponera-file';input.setAttribute('aria-label','Seleccionar cuponera para publicar');
 const button=make('button','Cargar y publicar en GitHub');button.type='button';button.disabled=true;button.id='publish-cuponera';
 const status=make('p','La carga actualiza P0 y Ahorra+ para todos. No descarga ni modifica Pandape o MAAT.');status.setAttribute('role','status');status.setAttribute('aria-live','polite');
 box.append(label,input,button,status);target.append(box);
 input.addEventListener('change',()=>{button.disabled=!input.files.length;status.textContent=input.files.length?'Seleccionado: '+input.files[0].name:'Selecciona una cuponera .xlsx';});
 button.addEventListener('click',async()=>{
  const file=input.files[0];if(!file)return;if(!file.name.toLowerCase().endsWith('.xlsx')||file.size>50*1024*1024){status.textContent='Selecciona un archivo .xlsx de hasta 50 MB.';return;}
  input.disabled=true;button.disabled=true;status.textContent='Enviando archivo al cargador local…';
  try{
   const response=await fetch('/api/cuponera',{method:'POST',headers:{'X-INVEX-Token':local.token,'X-File-Name':encodeURIComponent(file.name),'Content-Type':'application/octet-stream'},body:file});const reply=await response.json();if(!response.ok)throw new Error(reply.message||'No se pudo iniciar la carga');
   for(;;){await new Promise(resolve=>setTimeout(resolve,1000));const current=await fetch('/api/cuponera/estado',{headers:{'X-INVEX-Token':local.token},cache:'no-store'});if(!current.ok)throw new Error('No se pudo consultar el cargador local. Mantén su ventana abierta.');const job=await current.json();status.textContent=job.message;
    if(job.status==='error')throw new Error(job.message);
    if(job.status==='complete'){
     refresh(job.programs);options.source.programs=job.programs;options.onUpdated(job.programs);status.textContent=job.message+' Datos de '+job.programs.dates[0]+' al '+job.programs.dates.at(-1)+'.';break;
    }
   }
  }catch(error){status.textContent=error.message||'No se completó la carga. Revisa el cargador local.';}
  finally{input.disabled=false;button.disabled=!input.files.length;}
 });
}
window.INVEX_CUPONERA_UPLOAD={mount};
})();
