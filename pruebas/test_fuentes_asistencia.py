import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from fuentes_asistencia import current_generated, mark_source


class SourcesTests(unittest.TestCase):
    def test_source_change_invalidates_generated_roster(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'source.xlsx'; generated=Path(folder)/'generated.xlsx'
            source.write_bytes(b'roster 1'); generated.write_bytes(b'generated')
            config={'attendance_linked_roster':True}
            self.assertFalse(current_generated(config,source,generated))
            mark_source(source,generated)
            self.assertTrue(current_generated(config,source,generated))
            source.write_bytes(b'roster 2')
            self.assertFalse(current_generated(config,source,generated))
