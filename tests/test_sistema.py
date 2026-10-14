import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'.build-deps'))
import unittest
from datetime import datetime
from pathlib import Path
import tempfile
import engine
from descarga_asistencia import merge_csv,read_csv,date_key

class SystemTests(unittest.TestCase):
    def test_original_semaphores(self):
        self.assertEqual(engine.semaforo(0,0,0,False,100),'ALARMANTE')
        self.assertEqual(engine.semaforo(1,100,0,False,100),'CRITICA')
        self.assertEqual(engine.semaforo(3,100,0,True,0),'ALARMANTE')
        self.assertEqual(engine.semaforo(3,90,0,False,100),'OPTIMA')
        self.assertEqual(engine.semaforo(3,70,0,False,100),'RIESGO')
    def test_dates_are_normalized_before_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'maat.csv'
            headers=['Fecha','Ejecutivo','Punto de venta']
            merge_csv(headers,[{'Fecha':'12/10/2026','Ejecutivo':'uno','Punto de venta':''},{'Fecha':'11/10/2026','Ejecutivo':'dos','Punto de venta':''}],p,'2026-10')
            merge_csv(headers,[{'Fecha':'2026-10-12','Ejecutivo':'tres','Punto de venta':'MODULO BH SC HAROLD MONCLOVA 1007'}],p,'2026-10')
            _,rows=read_csv(p)
            self.assertEqual(len(rows),2)
            self.assertEqual({r['Ejecutivo'] for r in rows},{'dos','tres'})
            self.assertEqual(rows[1]['Segundo punto de venta'],'1007')
            self.assertEqual(date_key('12/10/2026'),'2026-10-12')
    def test_wrong_month_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'maat.csv';p.write_text('previo',encoding='utf-8')
            with self.assertRaises(ValueError):merge_csv(['Fecha','Ejecutivo'],[{'Fecha':'01/09/2026','Ejecutivo':'uno'}],p,'2026-10')
            self.assertEqual(p.read_text(),'previo')
    def test_engine_schedules_and_official_rest(self):
        a=[[None]*115]; row=[None]*115
        row[6]='WM 1';row[9]='Empleado';row[10]='ACTIVO';row[11]='usuario';row[15]='L-D 14:00 - 20:00';row[20]='LUNES';row[22]='F';a.append(row)
        b=[[None]*47];store=[None]*47;store[9]='WM 1';store[10]='Tienda';store[19]='OPERANDO';store[20]='10 a 20 hrs';store[25]=2;b.append(store)
        before=engine.analyze(a,b,1,reference_day_override=1,hora_corte_min=600,anio=2026,mes=10)
        after=engine.analyze(a,b,1,reference_day_override=1,hora_corte_min=900,anio=2026,mes=10)
        self.assertEqual(before['stores']['WM 1']['hoy']['pendientes_hoy'],1)
        self.assertEqual(after['stores']['WM 1']['hoy']['faltantes_hoy'],1)
        rest=engine.analyze(a,b,1,reference_day_override=1,anio=2026,mes=6)
        self.assertEqual(rest['stores']['WM 1']['hoy']['descansos_hoy'],1)
    def test_intervals_outside_store_hours_are_clipped(self):
        a=[[None]*115];row=[None]*115;row[6]='WM 1';row[9]='Empleado';row[10]='ACTIVO';row[11]='usuario';row[22:25]=['A','21:00','22:00'];a.append(row)
        b=[[None]*47];store=[None]*47;store[9]='WM 1';store[19]='OPERANDO';store[20]='10 a 20 hrs';store[25]=2;b.append(store)
        result=engine.analyze(a,b,1,reference_day_override=1,anio=2026,mes=10)['stores']['WM 1']['hoy']
        self.assertEqual(result['covered'],[])
        self.assertEqual(result['gaps'],[{'inicio':'10:00','fin':'20:00'}])

if __name__=='__main__':unittest.main()
