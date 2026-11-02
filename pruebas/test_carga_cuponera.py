import sys,unittest,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
import cargador_cuponera
class LocalImagesTests(unittest.TestCase):
 def test_previous_launcher_opens_file_without_writing_sources(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);(root/'sitio').mkdir();path=root/'sitio/index.html';path.write_text('tablero');before=list(root.rglob('*'))
   with patch.object(cargador_cuponera,'ROOT',root),patch.object(cargador_cuponera.webbrowser,'open') as browser:
    self.assertEqual(cargador_cuponera.main(),0);self.assertTrue(browser.call_args.args[0].startswith('file:'))
   self.assertEqual(path.read_text(),'tablero');self.assertEqual(list(root.rglob('*')),before)
if __name__=='__main__':unittest.main()
