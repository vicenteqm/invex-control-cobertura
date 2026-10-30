const fs=require('fs'),vm=require('vm'),assert=require('assert');const sandbox={window:{}};vm.runInNewContext(fs.readFileSync('sitio/reporte-productividad.js','utf8'),sandbox);const build=sandbox.window.INVEX_PRODUCTIVITY_REPORT.build;
const row=(id,hour,income,approved,guaranteed,finalized)=>['2026-10-01','CPRO','EJECUTIVA','REGION','',id,'TIENDA',hour,income,approved,guaranteed,finalized,0,''];
const sheets=build([row('WM 1','10:00',100,30,10,28),row('WM 2','10:00',100,40,0,29),row('SAMS 3','10:00',20,4,6,3),row('SAMS 3','11:00',10,8,0,2),row('SAMS 3','12:00',0,0,0,0)],{from:'2026-10-01',to:'2026-10-31',hasApprovals:true,hasFinalized:true,sourceName:'PRUEBA'});
assert.equal(sheets.length,3);assert.equal(sheets[0].name,'RESUMEN');assert.equal(sheets[1].name,'WALMART');assert.equal(sheets[2].name,'SAMS');
assert.equal(sheets[0].charts.length,4);assert.equal(sheets[1].rows[0][14],'NO PRODUCTIVA');assert.equal(sheets[1].rows[1][14],'PRODUCTIVA');
assert.equal(sheets[2].rows[0][14],'NO PRODUCTIVA');assert.equal(sheets[2].rows[1][14],'PRODUCTIVA');assert.equal(sheets[2].rows[2][14],'NO PRODUCTIVA');
assert.equal(typeof sheets[1].rows[0][0],'number');assert.equal(sheets[1].rows[0][12],.3);assert.equal(sheets[1].rows[0][13],.28);assert.equal(sheets[0].grid[17][2].value,70);assert.equal(sheets[0].charts[0].series.length,3);assert.equal(sheets[0].charts[1].series.length,2);
assert.ok(sheets[0].grid[6][1].formula.includes('SUMIFS'));assert.ok(sheets[0].grid[6][1].formula.includes('$B$3'));
console.log('Tres hojas, fechas, fórmulas, cuatro gráficas y reglas de productividad verificadas.');

assert.equal(sheets[0].charts[0].categories.length,11);assert.ok(sheets[1].rows.every(r=>Number(r[6].slice(0,2))>=9&&Number(r[6].slice(0,2))<=19));
