import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'python'),str(Path(__file__).resolve().parents[1]/'.build-deps')]
from actualizar_archivo import import_file

class ImportTests(unittest.TestCase):
    def test_attendance_replaces_generated_month_and_updates_selection(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'base').mkdir();(root/'base/base.xlsx').write_bytes(b'base')
            (root/'attendance').mkdir();(root/'attendance/ASISTENCIA.xlsx').write_bytes(b'old')
            source=root/'new.xlsx';source.write_bytes(b'new')
            config=dict(period='2026-10',base_folder='base',base_pattern='*.xlsx',attendance_folder='attendance')
            with patch('actualizar.generate',return_value={'stores':[]}):import_file('asistencias',source,config,root)
            target=root/'inputs/asistencias/ASISTENCIA_INVEX_2026-10.xlsx'
            self.assertEqual(target.read_bytes(),b'new')
            self.assertEqual(config['attendance_pattern'],target.name)
            source.write_bytes(b'invalid')
            with patch('actualizar.generate',side_effect=ValueError('invalid')):
                with self.assertRaises(ValueError):import_file('asistencias',source,config,root)
            self.assertEqual(target.read_bytes(),b'new')

    def test_hours_validates_period_and_sets_exact_source(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'base').mkdir();(root/'base/base.xlsx').write_bytes(b'base')
            (root/'attendance').mkdir();(root/'attendance/ASISTENCIA.xlsx').write_bytes(b'old')
            source=root/'hours.xlsx';source.write_bytes(b'hours')
            config=dict(period='2026-10',base_folder='base',base_pattern='*.xlsx',attendance_folder='attendance')
            with patch('actualizar.generate',return_value={'stores':[]}),patch('horas_productivas.read_productivity',return_value={'status':'available'}):
                import_file('horas',source,config,root)
            self.assertEqual(config['productive_hours_pattern'],'Horas Productivas Actual.xlsx')
            self.assertEqual((root/config['productive_hours_folder']/config['productive_hours_pattern']).read_bytes(),b'hours')
