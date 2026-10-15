import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'.build-deps'))
import json
import tempfile
import unittest
from configurar_equipo import prepare
from publicar_github import repository_from_remote

class PortabilityTests(unittest.TestCase):
    def test_new_computer_requires_no_private_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            path=prepare(root,'2026-10')
            c=json.loads(path.read_text(encoding='utf-8'))
            self.assertFalse(c['maat_manual_login'])
            self.assertTrue(c['pandape_manual_login'])
            self.assertFalse(c['publish'])
            self.assertFalse((root/'.private').exists())
            self.assertTrue((root/c['attendance_folder']).is_dir())
            self.assertFalse(Path(c['attendance_folder']).is_absolute())

    def test_existing_configuration_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);path=prepare(root,'2026-10')
            path.write_text('{"period":"2026-09","publish":true}',encoding='utf-8')
            before=path.read_bytes();prepare(root,'2026-11')
            self.assertEqual(path.read_bytes(),before)

    def test_repository_is_taken_from_origin(self):
        for remote in ['https://github.com/otra-cuenta/otro-tablero.git','git@github.com:otra-cuenta/otro-tablero.git','https://github.com/otra-cuenta/otro-tablero']:
            self.assertEqual(repository_from_remote(remote),('otra-cuenta','otro-tablero'))
        for remote in ['https://token@github.com/user/repo.git','https://otro-servidor.com/user/repo']:
            with self.assertRaises(ValueError):repository_from_remote(remote)
