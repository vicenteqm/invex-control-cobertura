import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'.build-deps'))
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch
from horas_productivas import read_productivity,PeriodNotFound,load_productivity

HEADERS=('DETERMINANTE','SEDE','09:00 - 09:59','14:00 - 14:59','TOTAL_TRAMITES')

class Sheet:
    def __init__(self,title,rows):self.title=title;self.rows=rows
    def iter_rows(self,**kwargs):return iter(self.rows)

class Book:
    def __init__(self,sheets):self.sheets=sheets
    def __iter__(self):return iter(self.sheets)
    def __contains__(self,name):return any(s.title==name for s in self.sheets)
    def __getitem__(self,name):return next(s for s in self.sheets if s.title==name)
    def close(self):pass

class ProductivityTests(unittest.TestCase):
    def test_generated_report_cannot_hide_manual_report_with_later_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            automatic=root/'resultados/horas_productivas/2026/Horas Productivas Octubre.xlsx'
            manual=root/'datos/fuentes/horas_productivas/Horas Productivas Actual.xlsx'
            for path in (automatic,manual):
                path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'fixture')
            config={'productive_hours_folder':str(automatic.parent),'productive_hours_pattern':automatic.name}
            def read(path,*args):return {'status':'available','lastDay':19 if path==manual else 15,'total':12967 if path==manual else 9924}
            with patch('horas_productivas.read_productivity',side_effect=read):
                self.assertEqual(load_productivity(config,root,'2026-10',[])['lastDay'],19)
            with patch('horas_productivas.read_productivity',side_effect=lambda path,*args:{'status':'available','lastDay':21 if path==automatic else 19}):
                self.assertEqual(load_productivity(config,root,'2026-10',[])['lastDay'],21)

    def fixture(self):
        return Book([Sheet('GENERAL',[HEADERS,(1,'WM UNO',3,4,7),('TOTAL',None,3,4,7)]),Sheet('2026-10-01',[HEADERS,(1,'WM UNO',3,4,7),('TOTAL',None,3,4,7)]),Sheet('2026-10-02',[HEADERS,(1,'WM UNO',0,0,0),('TOTAL',None,0,0,0)]),Sheet('2026-09-30',[HEADERS,(1,'WM UNO',100,0,100)]),Sheet('HORAS PICO',[('TITULO',),(99999,)])])

    def read(self,book,period='2026-10'):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'Horas Productivas Octubre.xlsx';path.write_bytes(b'fixture')
            with patch('horas_productivas.openpyxl.load_workbook',return_value=book):
                return read_productivity(path,period,[{'id':'WM 1','region':'REGION 1','status':'OPERANDO'}])

    def test_daily_sheets_only_no_double_counting(self):
        data=self.read(self.fixture())
        self.assertEqual(data['total'],7)
        self.assertEqual(len(data['stores']),1)
        self.assertEqual(data['capturedDays'],[1,2])
        self.assertEqual(data['daysInMonth'],31)
        self.assertEqual(data['warnings'],[])
        self.assertEqual(data['stores'][0]['region'],'REGION 1')

    def test_zero_is_distinct_from_missing(self):
        data=self.read(self.fixture())
        self.assertEqual(data['stores'][0]['days']['2'],[0,0])
        self.assertNotIn('3',data['stores'][0]['days'])

    def test_rejects_duplicate_store_and_incorrect_total(self):
        book=self.fixture();book.sheets[1].rows.insert(2,(1,'WM UNO',1,0,1))
        with self.assertRaisesRegex(ValueError,'repetida'):self.read(book)
        book=self.fixture();book.sheets[1].rows[1]=(1,'WM UNO',3,4,8)
        with self.assertRaisesRegex(ValueError,'no coincide'):self.read(book)

    def test_period_and_summary_validation(self):
        with self.assertRaises(PeriodNotFound):self.read(self.fixture(),'2026-11')
        book=self.fixture();book.sheets[0].rows[1]=(1,'WM UNO',3,5,8)
        self.assertEqual(len(self.read(book)['warnings']),1)

    def test_leap_month_and_no_source(self):
        book=Book([Sheet('2028-02-01',[HEADERS,(1,'WM UNO',1,0,1)])])
        self.assertEqual(self.read(book,'2028-02')['daysInMonth'],29)
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(load_productivity({},Path(directory),'2026-10',[])['status'],'missing')

    def detailed_fixture(self):
        h=('CADENA','DETERMINANTE','SEDE','FOLIO','FECHA HORA CREACION','Aprobación','Estatus del proceso','ESTATUS BANCO','Aprobadas finalizadas')
        rows=[h,('Walmart',1,'WM UNO','folio1',datetime(2026,10,1,14),'Aprobada','Finalizado','COMPLETO',1),("Sam's",1,'SAMS UNO','folio2',datetime(2026,10,1,15),'Aprobada con Garantía','Solicitud aprobada','RECHAZO',0),('Nota al pie',None,None,None,None,None,None,None,None)]
        summary=('CADENA','DETERMINANTE','SEDE','14:00 - 14:59','15:00 - 15:59','TOTAL_TRAMITES','Aprobada','Aprobada con Garantía','Aprobadas finalizadas')
        values=[summary,('Walmart',1,'WM UNO',1,0,1,1,0,1),("Sam's",1,'SAMS UNO',0,1,1,0,1,0),('14:00 - 14:59',999,None,None,None,None,None,None,None)]
        return Book([Sheet('DETALLE',rows),Sheet('GENERAL',values),Sheet('2026-10-01',values),Sheet('HORAS PICO',[('title',),('LUGAR','RANGO HORA','TOTAL_TRAMITES'),(1,'14:00 - 14:59',1),(2,'15:00 - 15:59',1),('2026-10-01','14:00 - 14:59',1)])])

    def test_detail_two_chains_and_all_sheets_without_duplicate_summaries(self):
        result=self.read(self.detailed_fixture())
        self.assertEqual(result['total'],2)
        self.assertEqual({s['id'] for s in result['stores']},{'WM 1','SAMS 1'})
        self.assertTrue(all(s['matches'] for s in result['sheets']))
        self.assertEqual(result['warnings'],[])
        self.assertEqual(sum(result['stores'][0]['finalizedDays']['1']),1)
        self.assertNotIn('folio1',str(result))
        self.assertEqual(result['stores'][1]['metricsDays']['1']['bank'],{'RECHAZO':1})

    def test_detail_rejects_duplicate_folio_and_inconsistent_finalized(self):
        book=self.detailed_fixture();book.sheets[0].rows.insert(2,book.sheets[0].rows[1])
        with self.assertRaisesRegex(ValueError,'duplicado'):self.read(book)
        book=self.detailed_fixture();row=list(book.sheets[0].rows[1]);row[-1]=0;book.sheets[0].rows[1]=row
        with self.assertRaisesRegex(ValueError,'finalizadas'):self.read(book)

    def test_detail_reports_summary_discrepancies(self):
        book=self.detailed_fixture();r=list(book.sheets[1].rows[1]);r[5]=10;book.sheets[1].rows=[book.sheets[1].rows[0],r]
        result=self.read(book)
        self.assertEqual(result['total'],2)
        self.assertFalse(next(s for s in result['sheets'] if s['name']=='GENERAL')['matches'])
