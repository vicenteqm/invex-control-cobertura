import sys,tempfile,unittest
import json
from unittest.mock import patch
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'python'),str(Path(__file__).resolve().parents[1]/'.build-deps')]
from ajustes_horarios import effective_person,person_key,save,load,validate_schedule,apply_store
from test_actualizar import CalculationTests,module

class ScheduleOverrideTests(unittest.TestCase):
    def test_generated_contract_views_inherit_general_saved_hours(self):
        with tempfile.TemporaryDirectory() as directory:
            base,attendance=CalculationTests().make_files(directory);path=Path(directory)/'ajustes.json'
            hours={'Tiempo completo':'L - D 11:00 - 21:00','Apertura':'11:00 - 17:00','Cierre':'15:00 - 21:00'}
            save({'people':{},'stores':{'WM 1':{'general':{'targets':{'Tiempo completo':1,'Apertura':0,'Cierre':1},'hours':hours}}}},path)
            store=module.generate(base,attendance,'2026-10',path)['stores'][0]
            for view in [store,*store['contracts'].values()]:self.assertEqual(view['shiftCoverage']['hours'],hours)

    def test_days_entry_exit_are_one_schedule(self):
        from ajustes_horarios import split_schedule,compose_schedule
        self.assertEqual(split_schedule('L - V 11:00 - 20:00'),('L - V','11:00','20:00'))
        self.assertEqual(split_schedule('Tiempo completo · horario por confirmar'),('L - D','',''))
        self.assertEqual(compose_schedule('L - V','11:00','20:00'),'L - V 11:00 - 20:00')
        for entry,exit in [('11:00',''),('','21:00'),('11','21'),('21:00','11:00')]:
            with self.assertRaises(ValueError):compose_schedule('L - V',entry,exit)

    def test_publication_preserves_record_cutoff_and_does_not_publish_private_catalog(self):
        from ajustes_horarios import _recalculate_publish
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);base,attendance=CalculationTests().make_files(directory)
            (root/'sitio').mkdir();path=root/'sitio/data.js'
            data={'period':'2026-10','updatedAt':'2026-10-01T12:00:00Z','cutoff':'2026-10-01','productiveHours':{'keep':True}}
            path.write_text('window.INVEX_DATA = '+json.dumps(data)+';',encoding='utf-8')
            with patch('ajustes_horarios.sources',return_value=({'period':'2026-10'},base,attendance)),patch('actualizar.publish_data') as publish:
                _recalculate_publish(root);publish.assert_called_once_with(root)
            result=json.loads(path.read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'))
            self.assertEqual(result['updatedAt'],data['updatedAt']);self.assertEqual(result['productiveHours'],data['productiveHours'])
            self.assertIn('scheduleAdjustedAt',result);self.assertNotIn('NOMBRE PRIVADO',str(result))

    def test_person_override_survives_recalculation_without_editing_excel(self):
        with tempfile.TemporaryDirectory() as directory:
            base,attendance=CalculationTests().make_files(directory);before=attendance.read_bytes()
            path=Path(directory)/'ajustes.json';data={'people':{person_key('001|NOMBRE PRIVADO'):{'store':'WM 1','schedule':'L - D 10:00 - 19:00','journey':'TIEMPO COMPLETO'}},'stores':{}}
            save(data,path)
            for _ in range(2):
                result=module.generate(base,attendance,'2026-10',path)
                store=result['stores'][0]
                self.assertEqual(store['active'],2)
                self.assertEqual(store['journeySchedules']['TIEMPO COMPLETO'],{'L - D 10:00 - 19:00':1})
                self.assertNotIn('NOMBRE PRIVADO',str(result))
            self.assertEqual(attendance.read_bytes(),before)
            self.assertEqual(effective_person(load(path),'001|NOMBRE PRIVADO','WM 2','old','MEDIO TIEMPO'),('old','MEDIO TIEMPO'))

    def test_manual_store_targets_and_hours_and_changed_roster(self):
        data={'people':{},'stores':{'WM 1':{'general':{'targets':{'Tiempo completo':2,'Apertura':1,'Cierre':1},'hours':{'Tiempo completo':'10:00 - 19:00','Apertura':'11:00 - 17:00','Cierre':'14:00 - 20:00'}}}}}
        store={'id':'WM 1','required':4,'gap':1,'journeySchedules':{'TIEMPO COMPLETO':{'10:00 - 19:00':1},'MEDIO TIEMPO':{'11:00 - 17:00':1,'14:00 - 20:00':1}}}
        apply_store(data,store)
        self.assertEqual(store['shiftCoverage']['gaps'],{'Apertura':0,'Cierre':0,'Tiempo completo':1})
        self.assertEqual(store['shiftCoverage']['hours']['Tiempo completo'],'10:00 - 19:00')
        other=dict(store);other.pop('shiftCoverage');apply_store(data,other,'salary')
        self.assertEqual(other['shiftCoverage']['hours']['Tiempo completo'],'10:00 - 19:00')
        data['stores']['WM 1']['salary']={**data['stores']['WM 1']['general'],'hours':{'Tiempo completo':'11:00 - 21:00','Apertura':'11:00 - 17:00','Cierre':'15:00 - 21:00'}}
        apply_store(data,other,'salary')
        self.assertEqual(other['shiftCoverage']['hours']['Tiempo completo'],'11:00 - 21:00')
        store['required']=5;apply_store(data,store);self.assertIn('scheduleOverrideWarning',store)

    def test_schedule_validation(self):
        self.assertEqual(validate_schedule(' L - D 10:00 - 19:00 '),'L - D 10:00 - 19:00')
        for value in ['sin definir','24:00 - 30:00','19:00 - 10:00','10:80 - 19:00']:
            with self.assertRaises(ValueError):validate_schedule(value)
