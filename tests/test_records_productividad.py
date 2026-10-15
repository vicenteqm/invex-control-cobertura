import csv
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'.build-deps'))
from horas_productivas import read_records_productivity,PeriodNotFound

class RecordsTests(unittest.TestCase):
    def test_company_creation_date_and_approval_categories(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'records_report_20261001_20261015.csv'
            headers=['Lugar de venta','Segundo lugar de venta','Aprobación','F. Creación','Nombre del cliente']
            with p.open('w',encoding='utf-8-sig',newline='') as f:
                writer=csv.writer(f);writer.writerow(headers)
                for company,status,stamp in [('WALMART','Aprobada','2026-10-01 14:02:00'),('WALMART','Aprobada con Garantía','2026-10-01 14:03:00'),('WALMART','Pendiente','2026-10-15 10:00:00'),('SAMS CLUB','Aprobada','2026-10-01 14:00:00'),('WALMART','Aprobada','2026-09-30 14:00:00')]:
                    writer.writerow([company,'123 TIENDA',status,stamp,'PRIVATE CUSTOMER'])
            result=read_records_productivity(p,'2026-10',[])
            self.assertEqual(result['total'],3)
            self.assertEqual(result['capturedDays'],list(range(1,16)))
            s=result['stores'][0]
            self.assertEqual(s['days']['1'][14],2)
            self.assertEqual(s['approvedDays']['1'][14],1)
            self.assertEqual(s['guaranteedDays']['1'][14],1)
            self.assertEqual(sum(s['days']['2']),0)
            self.assertNotIn('16',s['days'])
            self.assertNotIn('PRIVATE',str(result))
            with self.assertRaises(PeriodNotFound):read_records_productivity(p,'2026-11',[])

if __name__=='__main__':unittest.main()
