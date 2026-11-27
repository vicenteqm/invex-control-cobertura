import sys,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'python'),str(Path(__file__).resolve().parents[1]/'.build-deps')]
from accesos_operativo import seal,unseal,install
from cryptography.fernet import Fernet,InvalidToken

class ProtectedAccessTests(unittest.TestCase):
    def test_automatic_refresh_downloads_maat_without_opening_pandape(self):
        from operativo_portable import refresh
        from cobertura_actual import local_now
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'fuentes').mkdir();(root/'datos').mkdir()
            (root/'fuentes/base.xlsx').write_bytes(b'base');(root/'fuentes/asistencia.xlsx').write_bytes(b'roster')
            config={'period':local_now().strftime('%Y-%m'),'maat_automatic':True}
            seen=[]
            def maat(*args):seen.append(args)
            def no_pandape(*args):raise AssertionError('No debe abrirse Pandape automáticamente')
            with patch('actualizar.generate'),patch('secretos_locales.read_credentials',return_value=('service','test-key')):
                result=refresh(root,config,lambda *args:None,{'maat':maat,'pandape':no_pandape,'process':lambda *args,**kw:{'attendanceDays':[]}})
            self.assertEqual(len(seen),1);self.assertEqual(len(seen[0]),4)
            self.assertEqual(result['maatStatus'],'available')

    def test_authenticated_encryption_without_plaintext(self):
        key=Fernet.generate_key();access={'user':'test-user','password':'test-only-password'}
        token=seal(access,key);self.assertNotIn(b'test-only-password',token)
        self.assertEqual(unseal(token,key),access)
        with self.assertRaises(InvalidToken):unseal(token,Fernet.generate_key())

    def test_installs_only_maat_and_preserves_local_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'app';bundle=Path(directory)/'bundle';root.mkdir();bundle.mkdir();(root/'.private').mkdir()
            key=Fernet.generate_key();(bundle/'acceso_maat.bin').write_bytes(seal({'user':'service','password':'test-key'},key))
            config={'period':'2026-10','attendanceImport':{'name':'personal.xlsx'}}
            packaged={'version':'2.0.0','credentialRevision':'new-test'}
            def write(path,*access):path.write_text('encrypted-test')
            with patch.dict(sys.modules,{'_clave_operativa':SimpleNamespace(PACKAGE_KEY=key)}),patch('secretos_locales.save_credentials',side_effect=write) as save:
                install(root,bundle,config,packaged);install(root,bundle,config,packaged)
                self.assertEqual(save.call_count,1);self.assertEqual(save.call_args.args[0].name,'maat.json')
            self.assertEqual(config['period'],'2026-10');self.assertTrue(config['maat_automatic'])
            self.assertEqual(config['attendanceImport']['name'],'personal.xlsx')
