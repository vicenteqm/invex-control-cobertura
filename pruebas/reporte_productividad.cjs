const fs=require('fs'),vm=require('vm'),assert=require('assert');const sandbox={window:{}};vm.runInNewContext(fs.readFileSync('sitio/reporte-productividad.js','utf8'),sandbox);const build=sandbox.window.INVEX_PRODUCTIVITY_REPORT.build;
const row=(id,hour,income,approved,guaranteed,finalized)=>['2026-10-01','CPRO','EJECUTIVA','REGION','',id,'TIENDA',hour,income,approved,guaranteed,finalized,0,''];
const sheets=build([row('WM 1','10:00',100,30,10,28),row('WM 2','10:00',100,40,0,29),row('SAMS 3','10:00',20,4,6,3),row('SAMS 3','11:00',10,8,0,2),row('SAMS 3','12:00',0,0,0,0)],{from:'2026-10-01',to:'2026-10-31',hasApprovals:true,hasFinalized:true,sourceName:'PRUEBA'});
assert.equal(sheets.length,8);assert.equal(sheets[0].name,'RESUMEN');assert.equal(sheets[2].name,'WALMART');assert.equal(sheets[3].name,'SAMS');
assert.equal(sheets[0].charts.length,4);assert.equal(sheets[2].rows[0][14],'NO PRODUCTIVA');assert.equal(sheets[2].rows[1][14],'PRODUCTIVA');
assert.equal(sheets[3].rows[0][13],'NO PRODUCTIVA');assert.equal(sheets[3].rows[1][13],'PRODUCTIVA');assert.equal(sheets[3].rows[2][13],'NO PRODUCTIVA');
assert.equal(typeof sheets[2].rows[0][0],'number');assert.equal(sheets[2].rows[0][12],.3);assert.equal(sheets[2].rows[0][13],.28);assert.equal(sheets[0].grid[17][2].value,70);assert.equal(sheets[0].charts[0].series.length,3);assert.equal(sheets[0].charts[1].series.length,2);
assert.ok(sheets[0].grid[6][1].formula.includes('SUMIFS'));assert.ok(sheets[0].grid[6][1].formula.includes('$B$3'));
console.log('Ocho hojas, fechas, fórmulas, cuatro gráficas y reglas de productividad verificadas.');

assert.equal(sheets[0].charts[0].categories.length,11);assert.ok(sheets[2].rows.every(r=>Number(r[6].slice(0,2))>=9&&Number(r[6].slice(0,2))<=19));

const regression=build([row('SAMS 9','10:00',10,1,9,1),row('SAMS 9','11:00',10,5,0,3)],{from:'2026-10-01',to:'2026-10-31',hasApprovals:true,hasFinalized:true,sourceName:'PRUEBA'});
assert.equal(regression[3].rows[0][11],.1);assert.equal(regression[3].rows[1][11],.5);assert.equal(regression[3].rows[0][13],'NO PRODUCTIVA');assert.equal(regression[3].rows[1][13],'PRODUCTIVA');
assert.ok(!regression[3].headers.includes('Aprobadas totales'));assert.equal(regression[0].grid[17][10].value,6);assert.ok(regression[0].grid[7][10].formula.includes("'SAMS'!$I$2"));assert.ok(regression[0].grid[7][11].formula.includes("'SAMS'!$K$2"));
console.log('SAMS: solo aprobadas sin garantía, máximo horario correcto y garantizadas separadas.');

assert.equal(sheets[1].name,'HORARIOS POR DÍA');assert.equal(sheets[1].rows[0][1],'Jueves');assert.equal(sheets[1].rows[0][0],'WALMART');assert.equal(sheets[1].rows[0][3],57/200);assert.equal(sheets[1].rows[1][0],'SAMS');assert.equal(sheets[1].rows[1][2],'11:00 - 11:59');assert.equal(sheets[1].rows[1][3],.8);

assert.equal(sheets[4].name,'HORARIOS POR TIENDA');
assert.equal(sheets[5].name,'HORARIOS POR CÉLULA');
assert.equal(sheets[6].name,'HORARIOS POR TEAM LEADER');
assert.equal(sheets[7].name,'HORARIOS POR REGIÓN');
assert.equal(sheets[4].rows.filter(r=>r[0]==='WALMART').length,1);
assert.ok(sheets[4].rows.some(r=>r[1]==='WM 2 · TIENDA'&&r[4]===.29));
assert.ok(!sheets[4].rows.some(r=>r[1]==='WM 1 · TIENDA'));
assert.ok(sheets[6].rows.every(r=>r[1]==='Sin asignar'));
console.log('Desgloses independientes por tienda, CÉLULA, Team Leader y región verificados.');

const small=build([row('WM 890','18:00',1,1,0,1)],{from:'2026-10-01',to:'2026-10-31',hasApprovals:true,hasFinalized:true,sourceName:'PRUEBA'})[4];
assert.equal(small.rows[0][4],1);assert.equal(small.rows[0][5],1);assert.equal(small.rows[0][7],1);assert.equal(small.rows[0][8],'POCOS REGISTROS (<10 ingresos)');
assert.equal(sheets[1].rows[0][4],200);assert.equal(sheets[1].rows[0][6],57);assert.equal(sheets[1].rows[0][7],'10 O MÁS INGRESOS');
console.log('Porcentaje con numerador, denominador y señal de pocos registros verificados.');
