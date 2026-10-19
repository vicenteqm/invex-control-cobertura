import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from exportar_html import generar

class PortableTests(unittest.TestCase):
    def test_standalone_keeps_data_and_escapes_script_end(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);site=root/'sitio';site.mkdir()
            (site/'index.html').write_text('<html><head><link rel="stylesheet" href="styles.css"><script defer src="data.js?v=1"></script><script defer src="app.js"></script></head><body><div id="kpis"></div></body></html>')
            for name in ['styles.css','asistencia.css','operacion.css']:(site/name).write_text('body{color:black}')
            (site/'favicon.svg').write_text('<svg/>')
            (site/'data.js').write_text('window.INVEX_DATA={"name":"</script><script>bad()</script>"};')
            for name in ['app.js','operacion-data.js','operacion.js']:(site/name).write_text('// '+name)
            text=generar(root).read_text(encoding='utf-8')
            self.assertNotIn('src="',text)
            self.assertNotIn('<script>bad()',text)
            self.assertIn('<\\/script>',text)
            self.assertLess(text.index('window.INVEX_PORTABLE=true'),text.index('window.INVEX_DATA='))
            self.assertLess(text.index('id="kpis"'),text.index('window.INVEX_DATA='))
