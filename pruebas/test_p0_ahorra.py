import sys,tempfile,unittest
from pathlib import Path
from datetime import datetime
import openpyxl
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from p0_ahorra import read_programs,load_programs
class ProgramTests(unittest.TestCase):
 def fixture(self,path):
  b=openpyxl.Workbook();s=b.active;s.title='P0';r=b.create_sheet('Hoja1');r.append(['Fecha Creación']);r.append(['2026-10-26']);r.append(['2026-10-27'])
  for i,day in [(7,26),(14,27),(21,28)]:
   s.cell(2,i,datetime(2026,10,day));s.cell(3,i-1,'ING');s.cell(3,i,'APS');s.cell(3,i+2,'P0');s.cell(3,i+4,'AHORRA+')
  s.cell(30,2,'REGIÓN');s.cell(30,3,'DET');s.cell(30,4,'TIENDA');s.cell(31,3,1);s.cell(31,4,'Tienda uno')
  for i,p0,a in [(7,5,8),(14,4,9),(21,999,999)]:
   s.cell(31,i-1,100);s.cell(31,i,20);s.cell(31,i+2,p0);s.cell(31,i+4,a)
  s.cell(4,4,'REGION 1');s.cell(4,9,9999);s.cell(32,2,'TOTALES');s.cell(32,9,9999);b.save(path);b.close()
 def test_only_daily_store_rows_and_observed_dates(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'P0.xlsx';self.fixture(path);r=read_programs(path,[{'id':'WM 1','name':'Tienda uno'}]);self.assertEqual(r['dates'],['2026-10-26','2026-10-27']);self.assertEqual(r['stores']['WM 1']['2026-10-26']['p0'],5);self.assertEqual(r['stores']['WM 1']['2026-10-27']['ahorra'],9)
 def test_missing_file_is_unavailable_or_error(self):
  with tempfile.TemporaryDirectory() as root:
   self.assertEqual(load_programs({},root,[])['status'],'unavailable');self.assertEqual(load_programs({'p0_ahorra_source':str(Path(root)/'missing.xlsx')},root,[])['status'],'error')
if __name__=='__main__':unittest.main()
