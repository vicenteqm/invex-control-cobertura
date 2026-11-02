import sys,json,tempfile,unittest,threading,time,urllib.request,urllib.error
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from cargador_cuponera import import_and_publish,UploadApp,make_handler
from http.server import ThreadingHTTPServer
from test_p0_ahorra import ProgramTests
class UploadTests(unittest.TestCase):
 def root(self,folder):
  r=Path(folder);(r/'sitio').mkdir();(r/'configuracion').mkdir();(r/'configuracion/config.local.json').write_text('{"period":"2026-10","mantener":true}')
  (r/'sitio/index.html').write_text('<html><head></head><body>INVEX</body></html>')
  (r/'sitio/data.js').write_text('window.INVEX_DATA = '+json.dumps({'stores':[{'id':'WM 1','name':'Tienda uno'}],'period':'2026-10','updatedAt':'corte original','productiveHours':{'total':77}})+';');return r
 def test_valid_import_publishes_and_preserves_productivity(self):
  with tempfile.TemporaryDirectory() as folder:
   r=self.root(folder);p=r/'new.xlsx';ProgramTests().fixture(p);calls=[]
   result=import_and_publish(r,'cuponera.xlsx',p.read_bytes(),lambda _:None,lambda root:calls.append(root))
   data=json.loads((r/'sitio/data.js').read_text().split('=',1)[1].strip().rstrip(';'));self.assertEqual(data['productiveHours']['total'],77);self.assertEqual(data['updatedAt'],'corte original');self.assertEqual(result['sourceName'],'cuponera.xlsx');self.assertEqual(len(calls),1)
   config=json.loads((r/'configuracion/config.local.json').read_text());self.assertTrue(Path(config['p0_ahorra_source']).exists());self.assertTrue(config['mantener'])
 def test_invalid_file_does_not_replace_data_or_config(self):
  with tempfile.TemporaryDirectory() as folder:
   r=self.root(folder);previous=(r/'sitio/data.js').read_bytes();config=(r/'configuracion/config.local.json').read_bytes()
   with self.assertRaises(Exception):import_and_publish(r,'wrong.xlsx',b'not an excel',lambda _:None,lambda _:self.fail('No debe publicar'))
   self.assertEqual((r/'sitio/data.js').read_bytes(),previous);self.assertEqual((r/'configuracion/config.local.json').read_bytes(),config)
 def test_api_requires_local_token_and_rejects_other_origins(self):
  with tempfile.TemporaryDirectory() as folder:
   r=self.root(folder);app=UploadApp(r,lambda _:None);server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(app));threading.Thread(target=server.serve_forever,daemon=True).start();url='http://127.0.0.1:'+str(server.server_port)
   try:
    html=urllib.request.urlopen(url).read().decode();self.assertIn(app.token,html)
    for headers in [{},{'X-INVEX-Token':app.token,'Origin':'https://otro-sitio.example'}]:
     with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(urllib.request.Request(url+'/api/cuponera/estado',headers=headers))
     self.assertEqual(error.exception.code,403)
    response=urllib.request.urlopen(urllib.request.Request(url+'/api/cuponera/estado',headers={'X-INVEX-Token':app.token}));self.assertEqual(json.loads(response.read())['status'],'idle')
    with self.assertRaises(urllib.error.HTTPError):urllib.request.urlopen(url+'/configuracion/config.local.json')
   finally:server.shutdown();server.server_close()
if __name__=='__main__':unittest.main()
