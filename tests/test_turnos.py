import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
import unittest
from turnos_cobertura import allocate,enrich,operational_shift,scheduled_hours,SPECIAL_HOURS

class ShiftAllocationTests(unittest.TestCase):
    def test_walmart_prioritizes_afternoon_without_affecting_other_partners(self):
        for required in range(1,14):
            stores=[dict(id=key,required=required,gap=required,activeSchedules={}) for key in ['WM 100','WALMART 101','SAMS 102','CH 103']]
            enrich(stores)
            for store in stores[:2]:
                self.assertEqual(store['shiftCoverage']['targets'],{'Apertura':required//2,'Cierre':(required+1)//2})
                self.assertEqual(sum(store['shiftCoverage']['gaps'].values()),required)
            for store in stores[2:]:
                self.assertEqual(store['shiftCoverage']['targets'],{'Apertura':(required+1)//2,'Cierre':required//2})

    def test_sams_full_time_preserves_special_hours(self):
        self.assertEqual(scheduled_hours('SAMS 6248'),{'Apertura':'11:00 - 20:00','Cierre':'11:00 - 20:00'})
        for key,hours in SPECIAL_HOURS.items():self.assertEqual(scheduled_hours(key),hours)
        self.assertEqual(scheduled_hours('WM 6248'),{'Apertura':'11:00 - 17:00','Cierre':'15:00 - 21:00'})
    def test_classification_matches_containsstring_priority(self):
        self.assertEqual(operational_shift('L - D 11:00 - 15:00'),'Cierre')
        self.assertEqual(operational_shift('L - D 11:00 - 20:00'),'Apertura')
        self.assertEqual(operational_shift('L - D 10:30 - 19:30'),'Intermedio / Atípico')

    def test_targets_and_hour_exceptions(self):
        stores=[dict(id='WM 5296',required=5,gap=1,activeSchedules={'11:00 - 17:00':2,'14:00 - 20:00':2}),dict(id='SAMS 4968',required=1,gap=1,activeSchedules={})]
        enrich(stores)
        self.assertEqual(stores[0]['shiftCoverage']['targets'],{'Apertura':2,'Cierre':3})
        self.assertEqual(stores[0]['shiftCoverage']['gaps'],{'Apertura':0,'Cierre':1})
        self.assertEqual(stores[0]['shiftCoverage']['hours']['Cierre'],'13:00 - 19:00')
        self.assertEqual(stores[1]['shiftCoverage']['hours']['Cierre'],'11:00 - 20:00')
        self.assertEqual(stores[1]['shiftCoverage']['targets'],{'Apertura':1,'Cierre':0})
    def test_tie_prioritizes_closing(self):
        self.assertEqual(allocate(1,2,2,1,1),{'Apertura':0,'Cierre':1})

    def test_larger_opening_gap_has_priority(self):
        self.assertEqual(allocate(2,4,2,1,1),{'Apertura':2,'Cierre':0})

    def test_budget_covers_both_holes(self):
        self.assertEqual(allocate(5,3,3,2,1),{'Apertura':1,'Cierre':2})

    def test_does_not_duplicate_vacancies(self):
        for gap in range(7):
            for opening in range(7):
                for closing in range(7):
                    actual=allocate(gap,opening,closing,0,0)
                    self.assertEqual(sum(actual.values()),min(gap,opening+closing))
