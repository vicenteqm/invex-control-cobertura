const fs=require('fs'),vm=require('vm'),assert=require('assert');const sandbox={window:{}};vm.runInNewContext(fs.readFileSync('sitio/reporte-productividad.js','utf8'),sandbox);const build=sandbox.window.INVEX_PRODUCTIVITY_REPORT.build;
const row=(id,hour,income,approved,guaranteed,finalized)=>['2026-10-01','CPRO','EJECUTIVA','REGION','',id,'TIENDA',hour,income,approved,guaranteed,finalized,0,''];
const sheets=build([row('WM 1','10:00',100,30,10,28),row('WM 2','10:00',100,40,0,29),row('SAMS 3','10:00',20,4,6,3),row('SAMS 3','11:00',10,8,0,2),row('SAMS 3','12:00',0,0,0,0)],{from:'2026-10-01',to:'2026-10-31',hasApprovals:true,hasFinalized:true,sourceName:'PRUEBA'});
assert.equal(sheets.length,2);assert.equal(sheets[0].name,'WALMART');assert.equal(sheets[1].name,'SAMS');
assert.equal(sheets[0].rows[0][13],'NO PRODUCTIVA');assert.equal(sheets[0].rows[1][13],'PRODUCTIVA');
assert.equal(sheets[1].rows[0][13],'NO PRODUCTIVA');assert.equal(sheets[1].rows[1][13],'PRODUCTIVA');assert.equal(sheets[1].rows[2][13],'NO PRODUCTIVA');
const missing=build([row('WM 1','10:00',0,0,0,0)],{hasApprovals:false,hasFinalized:false});assert.equal(missing[0].rows[0][13],null);
console.log('Dos hojas: umbral Walmart, máximo SAMS, ceros y datos ausentes verificados.');
