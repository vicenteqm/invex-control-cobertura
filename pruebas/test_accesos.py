import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from accesos import leer_maat,preparar

class AccessTests(unittest.TestCase):
    def test_plain_configuration_and_environment_priority(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{},clear=True):
            root=Path(folder);path=preparar(root)
            path.write_text(json.dumps({'maat':{'usuario':'usuario-prueba','contrasena':'clave-prueba'}}),encoding='utf-8')
            self.assertEqual(leer_maat({},root),('usuario-prueba','clave-prueba',False))
            os.environ['MAAT_USER']='entorno'
            self.assertEqual(leer_maat({},root)[0],'entorno')
            preparar(root)
            self.assertEqual(json.loads(path.read_text())['maat']['usuario'],'usuario-prueba')

    def test_missing_values_and_manual_login(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{},clear=True):
            root=Path(folder);preparar(root)
            with self.assertRaisesRegex(ValueError,'accesos.json'):leer_maat({},root)
            self.assertEqual(leer_maat({'maat_manual_login':True},root),(None,None,True))
