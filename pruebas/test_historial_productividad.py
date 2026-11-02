import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
from historial_productividad import preserve


class HistoryTests(unittest.TestCase):
    def test_keeps_old_month_when_current_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'data.js'
            october = {'period': '2026-10', 'status': 'available', 'stores': [{'id': 'WM 1'}]}
            path.write_text('window.INVEX_DATA = ' + json.dumps({'productiveHours': october}) + ';', encoding='utf-8')
            self.assertEqual(preserve(path, {'period': '2026-11', 'status': 'error'}), {'2026-10': october})
            november = {'period': '2026-11', 'status': 'available'}
            self.assertEqual(preserve(path, november), {'2026-10': october, '2026-11': november})
