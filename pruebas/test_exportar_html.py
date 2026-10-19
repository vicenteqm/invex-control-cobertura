import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from exportar_html import generar,guardar_copia_local
import json

class PortableTests(unittest.TestCase):
    def test_local_copies_exist_even_without_github_and_replace_previous(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);config=root/'configuracion';config.mkdir()
            (config/'config.local.json').write_text(json.dumps({'html_output_folder':'copias'}))
            source=root/'INVEX_ACTUALIZADO.html';source.write_text('corte nuevo')
            result=guardar_copia_local(root,source,'INVEX_2026-10-19_10-24.html')
            self.assertEqual(result.read_text(),'corte nuevo')
            self.assertEqual((root/'copias/INVEX_ACTUALIZADO.html').read_text(),'corte nuevo')
            source.write_text('siguiente corte')
            guardar_copia_local(root,source,'INVEX_2026-10-19_11-00.html')
            self.assertEqual(result.read_text(),'corte nuevo')
            self.assertEqual((root/'copias/INVEX_ACTUALIZADO.html').read_text(),'siguiente corte')
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
            class Scripts(HTMLParser):
                count=0
                def handle_starttag(self,tag,attrs):
                    if tag=='script':self.count+=1
            parsed=Scripts();parsed.feed(text)
            self.assertEqual(parsed.count,5)
            self.assertIn('<\\/script>',text)
            self.assertLess(text.index('window.INVEX_PORTABLE=true'),text.index('window.INVEX_DATA='))
            self.assertLess(text.index('id="kpis"'),text.index('window.INVEX_DATA='))
