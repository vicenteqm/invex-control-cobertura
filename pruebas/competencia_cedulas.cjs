const fs=require('fs'),vm=require('vm'),assert=require('assert');const context={window:{}};vm.runInNewContext(fs.readFileSync('sitio/imagenes-productividad.js','utf8'),context);const compare=context.window.INVEX_PRODUCTIVITY_IMAGES.compare;
const hour=n=>Array.from({length:24},(_,i)=>i===10?n:0),store=(name,id,income,result)=>({id,name:id,executive:name,days:{1:hour(income)},approvedDays:{1:hour(result)},guaranteedDays:{1:hour(0)},finalizedDays:{1:hour(result)}});
const stores=[store('A','WM 1',100,20),store('B','WM 2',10,8),store('C','WM 3',1,1),store('C','WM 4',100,10),store('D','SAMS 1',20,10)];const source={capturedDays:[1],hasApprovals:true,hasFinalized:true,hours:Array.from({length:24},(_,i)=>String(i).padStart(2,'0')+':00')};let c={stores,source,from:'2026-10-01',to:'2026-10-01',metric:'finalized'};
let rows=compare(c)[0].rows;assert.equal(rows[0].name,'B');assert.equal(rows[2].name,'C');assert.equal(rows[2].rate,11/101);assert.equal(compare(c)[1].rows[0].name,'D');
c.metric='income';rows=compare(c)[0].rows;assert.equal(rows[0].name,'C');assert.equal(rows[0].income,101);
c.metric='finalized';c.stores=[store('A','WM 1',10,5),store('B','WM 2',20,10)];rows=compare(c)[0].rows;assert.equal(rows[0].rank,1);assert.equal(rows[1].rank,1);
console.log('Ranking ponderado, separación de socios, volumen y empates verificados.');
