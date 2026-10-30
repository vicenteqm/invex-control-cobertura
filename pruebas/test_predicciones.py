import sys,unittest
from pathlib import Path
from datetime import date
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from predicciones import build
class ForecastTests(unittest.TestCase):
 def source(self,n=28):return dict(status='available',period='2026-10',lastDay=n,capturedDays=list(range(1,n+1)),stores=[dict(id='WM 1',status='OPERANDO',days={str(d):[10]*24 for d in range(1,n+1)})])
 def test_constant_series_and_month_rollover(self):
  r=build(self.source(),date(2026,10,30));s=r['stores'][0]
  self.assertEqual(r['dates'][-1],'2026-11-04');self.assertEqual(s['mae'],0);self.assertTrue(all(x['value']==240 and x['low']==240 for x in s['forecast']))
 def test_excludes_partial_and_future_days(self):
  source=self.source(31);source['stores'][0]['days']['30']=[999999]*24;source['lastRecordAt']='2026-10-28T20:00:00'
  r=build(source,date(2026,10,30));self.assertEqual(r['cutoff'],'2026-10-28');self.assertEqual(r['staleDays'],1)
  source.pop('lastRecordAt');self.assertEqual(build(source,date(2026,10,30))['cutoff'],'2026-10-29')
 def test_missing_is_not_zero_and_nonoperating_excluded(self):
  source=self.source();del source['stores'][0]['days']['12'];source['stores'].append(dict(id='WM 2',status='CERRADA',days={}))
  r=build(source,date(2026,10,30));self.assertEqual(len(r['stores']),1);self.assertEqual(len(r['stores'][0]['history']),27);self.assertEqual(r['stores'][0]['mae'],0)
 def test_short_history_and_unvalidated(self):
  self.assertEqual(build(self.source(6),date(2026,10,30))['status'],'insufficient')
  s=build(self.source(7),date(2026,10,30))['stores'][0];self.assertIsNone(s['mae']);self.assertIsNone(s['forecast'][0]['low'])
if __name__=='__main__':unittest.main()
