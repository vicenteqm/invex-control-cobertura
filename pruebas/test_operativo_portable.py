import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'.build-deps'))
from operativo_portable import refresh, registration_view, atomic_json, heatmap_tiles
from cobertura_actual import local_now


class PortableTests(unittest.TestCase):
    def test_exe_upgrade_rotates_service_credentials_without_resetting_local_data(self):
        from operativo_portable import initialize
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'local';bundle=Path(directory)/'bundle';root.mkdir();bundle.mkdir()
            (root/'.private').mkdir();(root/'fuentes').mkdir()
            (root/'fuentes/asistencia.xlsx').write_bytes(b'personal-import')
            atomic_json(root/'config.json',{'period':'2026-10','custom':True})
            atomic_json(root/'ultimo-corte.json',{'keep':True})
            atomic_json(bundle/'config.json',{'period':'2026-11','version':'1.8.0','credentialRevision':'test-revision'})
            atomic_json(bundle/'accesos.json',{'maat':['service','new-test-key'],'pandape':['pandape-service','new-test-key']})
            for name in ['maat','pandape']:(root/'.private'/(name+'.json')).write_text('encrypted-placeholder')
            def read(path):return ['service','old-test-key'] if path.stem=='maat' else ['custom-user','custom-key']
            with patch('secretos_locales.read_credentials',side_effect=read),patch('secretos_locales.save_credentials') as write:
                config=initialize(root,bundle);initialize(root,bundle)
            self.assertEqual(write.call_count,1)
            self.assertEqual(config['period'],'2026-10');self.assertTrue(config['custom'])
            self.assertEqual((root/'fuentes/asistencia.xlsx').read_bytes(),b'personal-import')
            self.assertEqual(json.loads((root/'ultimo-corte.json').read_text()),{'keep':True})

    def test_import_attendance_recalculates_and_persists_without_download(self):
        from operativo_portable import import_attendance
        from fuentes_asistencia import current_generated,mark_source
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'fuentes').mkdir();(root/'datos').mkdir()
            target=root/'fuentes/asistencia.xlsx';target.write_bytes(b'old')
            generated=root/'datos/generated.xlsx';generated.write_bytes(b'old-generated');mark_source(target,generated)
            source=root/'nueva.xlsx';source.write_bytes(b'new')
            config={'period':local_now().strftime('%Y-%m')};atomic_json(root/'config.json',config)
            calls=[]
            result=import_attendance(root,config,source,services={'generate':lambda *args:None,'process':lambda *args,**kw:(calls.append(args) or {'stores':[],'attendanceDays':[1]})})
            self.assertEqual(target.read_bytes(),b'new');self.assertEqual(len(calls),1)
            self.assertIsNone(calls[0][3]);self.assertFalse(current_generated({'attendance_linked_roster':True},target,generated))
            self.assertEqual(result['sourceFreshness']['pandape']['status'],'imported')
            self.assertEqual(json.loads((root/'ultimo-corte.json').read_text())['attendanceDays'],[1])
            self.assertEqual(config['attendanceImport']['name'],'nueva.xlsx')

    def test_invalid_attendance_keeps_source_and_snapshot(self):
        from operativo_portable import import_attendance
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'fuentes').mkdir();(root/'datos').mkdir()
            (root/'fuentes/asistencia.xlsx').write_bytes(b'old');atomic_json(root/'ultimo-corte.json',{'old':True})
            source=root/'nueva.xlsx';source.write_bytes(b'new');config={'period':local_now().strftime('%Y-%m')}
            def fail(*args,**kwargs):raise ValueError('Encabezados invalidos')
            with self.assertRaises(ValueError):import_attendance(root,config,source,services={'generate':fail})
            self.assertEqual((root/'fuentes/asistencia.xlsx').read_bytes(),b'old')
            self.assertEqual(json.loads((root/'ultimo-corte.json').read_text()),{'old':True})

    def test_manual_pandape_download_uses_one_visible_session_and_clears_attention(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'fuentes').mkdir();(root/'datos').mkdir()
            (root/'fuentes/asistencia.xlsx').write_bytes(b'roster');(root/'fuentes/base.xlsx').write_bytes(b'base')
            config={'period':local_now().strftime('%Y-%m'),'pandape_attention_required':True}
            calls=[]
            def pandape(options,folder):
                calls.append(options)
                self.assertFalse(options['pandape_background']);self.assertFalse(options['portable_login'])
                self.assertTrue(options['pandape_interactive_entry']);self.assertTrue(options['portable_app'])
                return root/'report.xlsx'
            def attendance(source,report,target,day):target.write_bytes(b'generated')
            with patch('actualizar.generate'),patch('secretos_locales.read_credentials',return_value=('user','password')):
                result=refresh(root,config,lambda *args:None,{'maat':lambda *args:None,'pandape':pandape,'attendance':attendance,'process':lambda *args,**kwargs:{'attendanceDays':[local_now().day]}},interactive_pandape=True)
            self.assertEqual(len(calls),1);self.assertFalse(result['partialUpdate'])
            self.assertNotIn('pandape_attention_required',config);self.assertTrue(config['pandape_visible_session'])
            self.assertEqual(result['sourceFreshness']['pandape']['status'],'ok')

    def test_heatmaps_match_html_boundaries_and_system_availability(self):
        def store(key,required,maat,pandape):return {'id':key,'name':key,'required':required,'registration':{'1':{'available':True,'maat':maat,'cohort':{'pandape':pandape}}}}
        stores=[store('WM 1',4,4,1),store('SAMS 2',4,2,4),store('CH 3',4,1,2),store('WM 4',0,0,0)]
        month={'maatDays':[1],'attendanceDays':[1],'maatLoaded':True}
        self.assertEqual([t['level'] for t in heatmap_tiles(month,stores,1,'MAAT')],['full','partial','low','unknown'])
        self.assertEqual([t['level'] for t in heatmap_tiles(month,stores,1,'Pandape')],['low','full','partial','unknown'])
        month['maatDays']=[]
        self.assertTrue(all(t['level']=='unknown' for t in heatmap_tiles(month,stores,1,'MAAT')))
        self.assertEqual(heatmap_tiles(month,stores,1,'Pandape')[1]['percentage'],100)

    def test_day_without_maat_is_not_reported_as_absent(self):
        month={'maatLoaded':True,'maatDays':[1],'attendanceDays':[1,2], 'stores':[
            {'id':'WM 1','name':'Uno','region':'R','executive':'E','registration':{'1':{'cohort':{'total':2,'pandape':1,'maat':2,'both':1,'none':0}}}}]}
        _,totals,p,m=registration_view(month,2)
        self.assertFalse(p);self.assertFalse(m);self.assertEqual(totals['none'],0)
        _,totals,p,m=registration_view(month,1)
        self.assertTrue(p);self.assertTrue(m);self.assertEqual(totals['total'],2)
        self.assertEqual(totals['maat'],2)

    def test_maat_failure_keeps_last_valid_cut(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'fuentes').mkdir();(root/'datos').mkdir()
            (root/'fuentes/asistencia.xlsx').write_bytes(b'roster')
            (root/'fuentes/base.xlsx').write_bytes(b'base')
            prior={'processedAt':'previous','period':local_now().strftime('%Y-%m')}
            atomic_json(root/'ultimo-corte.json',prior)
            def failure(*args):raise RuntimeError('server rejected')
            with patch('actualizar.generate'),patch('secretos_locales.read_credentials',return_value=('user','password')):
                with self.assertRaisesRegex(ValueError,'MAAT_DOWNLOAD_FAILED'):refresh(root,{'period':prior['period']},lambda *args:None,{'maat':failure,'pandape':failure})
            self.assertEqual(json.loads((root/'ultimo-corte.json').read_text(encoding='utf-8')),prior)

    def test_maat_refreshes_while_blocked_pandape_stays_unevaluated(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'fuentes').mkdir();(root/'datos').mkdir()
            (root/'fuentes/asistencia.xlsx').write_bytes(b'roster');(root/'fuentes/base.xlsx').write_bytes(b'base')
            day=local_now().day;period=local_now().strftime('%Y-%m')
            atomic_json(root/'ultimo-corte.json',{'processedAt':'previous','period':period})
            config={'period':period};calls={'maat':0,'pandape':0}
            def maat(*args):calls['maat']+=1
            def pandape(*args):calls['pandape']+=1;raise RuntimeError('Pandape: HTTP 403')
            def process(*args,**kwargs):
                return {'attendanceDays':[day],'maatDays':[day],'maatLoaded':True,'stores':[
                    {'id':'WM 1','name':'Uno','required':2,'registration':{str(day):{'available':True,'maat':calls['maat'],'cohort':{'total':2,'pandape':2,'maat':calls['maat'],'both':1,'none':0}}}}]}
            services={'maat':maat,'pandape':pandape,'process':process}
            with patch('actualizar.generate'),patch('secretos_locales.read_credentials',return_value=('user','password')):
                first=refresh(root,config,lambda *args:None,services)
                second=refresh(root,config,lambda *args:None,services)
            self.assertTrue(second['partialUpdate']);self.assertEqual(calls,{'maat':2,'pandape':1})
            self.assertEqual(first['stores'][0]['registration'][str(day)]['maat'],1)
            self.assertEqual(second['stores'][0]['registration'][str(day)]['maat'],2)
            _,totals,p,m=registration_view(second,day)
            self.assertFalse(p);self.assertTrue(m);self.assertEqual(totals['maat'],2)
            self.assertIsNone(heatmap_tiles(second,second['stores'],day,'Pandape')[0]['percentage'])
            self.assertEqual(heatmap_tiles(second,second['stores'],day,'MAAT')[0]['percentage'],100)
            self.assertEqual(second['sourceFreshness']['pandape']['updatedAt'],'previous')

    def test_success_commits_only_after_calculation(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'fuentes').mkdir();(root/'datos').mkdir()
            (root/'fuentes/asistencia.xlsx').write_bytes(b'roster');(root/'fuentes/base.xlsx').write_bytes(b'base')
            def attendance(source,report,target,day):target.write_bytes(b'generated')
            def process(*args,**kwargs):
                self.assertEqual(kwargs['output_root'],root)
                return {'processedAt':'new'}
            steps=[]
            with patch('actualizar.generate'),patch('secretos_locales.read_credentials',return_value=('user','password')):
                result=refresh(root,{'period':local_now().strftime('%Y-%m')},lambda n,text:steps.append(n),{'maat':lambda *args:None,'pandape':lambda *args:root/'report.xlsx','attendance':attendance,'process':process})
            self.assertEqual(steps,sorted(steps));self.assertEqual(steps[-1],100)
            self.assertEqual(json.loads((root/'ultimo-corte.json').read_text(encoding='utf-8'))['processedAt'],'new')

