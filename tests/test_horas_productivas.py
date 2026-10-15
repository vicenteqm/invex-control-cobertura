import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'.build-deps'))
import tempfile
import unittest
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
