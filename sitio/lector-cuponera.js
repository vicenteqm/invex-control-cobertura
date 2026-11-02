'use strict';
(()=>{
const decode=new TextDecoder(),NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main';
function xml(text){const document=new DOMParser().parseFromString(text,'application/xml');if(document.getElementsByTagName('parsererror').length)throw new Error('El Excel contiene una hoja XML inválida.');return document;}
async function zip(file){
 const buffer=await file.arrayBuffer(),bytes=new Uint8Array(buffer),v=new DataView(buffer);let end=-1;
 for(let i=bytes.length-22;i>=Math.max(0,bytes.length-65557);i--)if(v.getUint32(i,true)===0x06054b50){end=i;break;}
 if(end<0)throw new Error('Selecciona un archivo Excel .xlsx válido.');
 const count=v.getUint16(end+10,true),offset=v.getUint32(end+16,true),entries=new Map();let pos=offset,total=0;
 for(let i=0;i<count;i++){
  if(pos+46>bytes.length||v.getUint32(pos,true)!==0x02014b50)throw new Error('El Excel está incompleto.');
  const method=v.getUint16(pos+10,true),size=v.getUint32(pos+24,true),compressed=v.getUint32(pos+20,true),len=v.getUint16(pos+28,true),extra=v.getUint16(pos+30,true),comment=v.getUint16(pos+32,true),local=v.getUint32(pos+42,true);const name=decode.decode(bytes.subarray(pos+46,pos+46+len));total+=size;
  if(total>200*1024*1024)throw new Error('El Excel descomprimido es demasiado grande.');
  if(entries.has(name))throw new Error('El Excel contiene archivos internos duplicados.');entries.set(name,{method,size,compressed,local});pos+=46+len+extra+comment;
 }
 const cache=new Map();return async name=>{
  if(cache.has(name))return cache.get(name);const e=entries.get(name);if(!e)return null;
  if(e.local+30>bytes.length||v.getUint32(e.local,true)!==0x04034b50)throw new Error('El Excel contiene una entrada inválida.');
  const start=e.local+30+v.getUint16(e.local+26,true)+v.getUint16(e.local+28,true);if(start+e.compressed>bytes.length)throw new Error('El Excel está incompleto.');let data=bytes.subarray(start,start+e.compressed);
  if(e.method===8){if(typeof DecompressionStream==='undefined')throw new Error('Usa una versión reciente de Edge o Chrome para cargar el Excel.');const stream=new Blob([data]).stream().pipeThrough(new DecompressionStream('deflate-raw'));data=new Uint8Array(await new Response(stream).arrayBuffer());}
  else if(e.method!==0)throw new Error('El tipo de compresión del Excel no es compatible.');
  if(data.length!==e.size)throw new Error('No se pudo validar el contenido del Excel.');const result=decode.decode(data);cache.set(name,result);return result;
 };
}
function rows(document,shared){return [...document.getElementsByTagNameNS(NS,'row')].map(row=>{const cells=[];for(const c of row.getElementsByTagNameNS(NS,'c')){const ref=c.getAttribute('r')||'',letters=ref.match(/^[A-Z]+/)?.[0];if(!letters)continue;let index=0;for(const l of letters)index=index*26+l.charCodeAt(0)-64;const type=c.getAttribute('t'),raw=c.getElementsByTagNameNS(NS,'v')[0]?.textContent;let value=null;if(type==='s')value=shared[Number(raw)]??null;else if(type==='inlineStr')value=[...c.getElementsByTagNameNS(NS,'t')].map(t=>t.textContent).join('');else if(type==='str'||type==='d')value=raw??null;else if(raw!==undefined)value=Number(raw);cells[index-1]=value;}return {number:Number(row.getAttribute('r')),cells};});}
function date(value){if(typeof value==='number'&&value>20000&&value<100000)return new Date(Math.round((value-25569)*86400000)).toISOString().slice(0,10);if(typeof value==='string'&&/^\d{4}-\d{2}-\d{2}/.test(value))return value.slice(0,10);return null;}
const norm=value=>String(value??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').trim().toUpperCase();
function count(value){if(value===null||value===undefined)return null;if(typeof value!=='number'||!Number.isSafeInteger(value)||value<0)throw new Error('La hoja P0 tiene conteos inválidos. Revisa los valores y vuelve a guardar el Excel.');return value;}
async function readPrograms(file,stores){
 if(!file.name.toLowerCase().endsWith('.xlsx')||file.size>50*1024*1024)throw new Error('Selecciona una cuponera .xlsx de hasta 50 MB.');
 const get=await zip(file),bookText=await get('xl/workbook.xml'),relsText=await get('xl/_rels/workbook.xml.rels');if(!bookText||!relsText)throw new Error('El archivo no es un Excel válido.');
 const book=xml(bookText),rels=xml(relsText),paths=new Map();for(const r of rels.getElementsByTagName('Relationship')){const target=r.getAttribute('Target');if(r.getAttribute('TargetMode')==='External')continue;const path=target.startsWith('/')?target.slice(1):'xl/'+target;if(path.includes('..')||path.includes('://'))continue;paths.set(r.getAttribute('Id'),path);}
 const sheets=new Map();for(const s of book.getElementsByTagNameNS(NS,'sheet'))sheets.set(s.getAttribute('name'),paths.get(s.getAttribute('r:id')));
 if(!sheets.has('P0')||!sheets.has('Hoja1'))throw new Error('La cuponera debe tener las hojas P0 y Hoja1.');
 const sharedText=await get('xl/sharedStrings.xml'),shared=sharedText?[...xml(sharedText).getElementsByTagNameNS(NS,'si')].map(si=>[...si.getElementsByTagNameNS(NS,'t')].map(t=>t.textContent).join('')):[];
 const detailText=await get(sheets.get('Hoja1')),p0Text=await get(sheets.get('P0'));if(!detailText||!p0Text)throw new Error('Faltan hojas del Excel.');const detail=rows(xml(detailText),shared),header=detail.find(r=>r.number===1)?.cells||[],position=header.findIndex(h=>norm(h)==='FECHA CREACION');if(position<0)throw new Error('Hoja1 no contiene Fecha Creación.');
 const observed=new Set(detail.filter(r=>r.number>1).map(r=>date(r.cells[position])).filter(Boolean));const p0=rows(xml(p0Text),shared),dateRow=p0.find(r=>r.number===2)?.cells||[],heads=p0.find(r=>r.number===3)?.cells||[],dates=[];
 dateRow.forEach((value,index)=>{const day=date(value);if(day&&observed.has(day)){if(norm(heads[index-1])!=='ING'||norm(heads[index])!=='APS'||norm(heads[index+2])!=='P0')throw new Error('El bloque diario de P0 no tiene el formato esperado.');dates.push([day,index]);}});
 if(!dates.length)throw new Error('No se identificaron fechas reales con datos en la cuponera.');
 const start=p0.find(r=>norm(r.cells[1])==='REGION'&&norm(r.cells[2])==='DET'&&norm(r.cells[3])==='TIENDA');if(!start)throw new Error('No se encontró la tabla por tienda de P0.');
 const lookup=new Map();for(const store of stores){const det=store.id.split(' ').at(-1);if(!lookup.has(det))lookup.set(det,[]);lookup.get(det).push(store);}
 const result={};let unmatched=0;
 for(const row of p0.filter(r=>r.number>start.number)){const c=row.cells;if(!/^\d+(?:\.0+)?$/.test(String(c[2]??'')))continue;const det=String(Number(c[2]));let candidates=lookup.get(det)||[];if(candidates.length>1)candidates=candidates.filter(s=>norm(s.name)===norm(c[3]));if(candidates.length!==1){unmatched++;continue;}const key=candidates[0].id;if(result[key])throw new Error('La cuponera tiene una tienda duplicada: '+key);const days={};for(const [day,i]of dates){const p0=count(c[i+2]),ahorra=count(c[i+4]);if(p0!==null&&ahorra!==null)days[day]={p0,ahorra,approved:count(c[i]),income:count(c[i-1])};}result[key]=days;}
 const col=name=>header.findIndex(h=>norm(h)===name),activation=col('OPCION DE ACTIVACION'),detCol=col('DET'),folio=col('FOLIO FICO');
 if(activation>=0&&detCol>=0){const seen=new Set();for(const days of Object.values(result))for(const record of Object.values(days))record.app=0;for(const row of detail.filter(r=>r.number>1)){const c=row.cells,day=date(c[position]),det=String(Number(c[detCol])),candidates=(lookup.get(det)||[]).filter(s=>result[s.id]?.[day]);if(candidates.length!==1)continue;const key=candidates[0].id,identity=folio>=0?String(c[folio]??'').trim():'';if(!identity)continue;const token=key+'|'+day+'|'+identity;if(norm(c[activation]).replace(/[–—]/g,'-').replace(/\s+/g,' ')==='SI SE REALIZO - FINALIZAR TRAMITE'&&!seen.has(token)){result[key][day].app++;seen.add(token);}}}
 if(!Object.keys(result).length)throw new Error('Las tiendas del archivo no coinciden con la base del tablero.');
 return {status:'available',sourceName:file.name,sourceModifiedAt:new Date(file.lastModified||Date.now()).toISOString(),importedAt:new Date().toISOString(),dates:dates.map(([day])=>day).sort(),stores:result,unmatchedStores:unmatched,basis:'Carga en navegador, solo para imágenes. Día completo; sin acumulados semanales.'};
}
window.INVEX_CUPONERA_READER={readPrograms};
})();
