import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from descarga_pandape import authenticated_page,session_options
from descarga_pandape import wait_report_ready

class SessionTests(unittest.TestCase):
    def test_report_wait_detects_ready_and_server_errors(self):
        button=SimpleNamespace(is_displayed=lambda:True,is_enabled=lambda:True)
        driver=SimpleNamespace(find_elements=lambda by,key:[button] if key=='getOfflineReportFromDeafultPopUp' else [])
        self.assertIs(wait_report_ready(driver,1),button)
        error=SimpleNamespace(is_displayed=lambda:True,text='No hay datos para generar el reporte.')
        driver.find_elements=lambda by,key:[error] if key=='offlineReportFinalNoDataMessage' else []
        with self.assertRaisesRegex(ValueError,'No hay datos'):wait_report_ready(driver,1)

    def test_identity_redirect_is_not_authenticated(self):
        def page(url,login=False,filters=True):return SimpleNamespace(current_url=url,find_elements=lambda *args:[SimpleNamespace(is_displayed=lambda:True)] if (args[-1]=='Username' and login) or (args[-1]=='SearchModel_MyTeam' and filters) else [])
        self.assertFalse(authenticated_page(page('https://secure.holmeshr.com/Account/Login')))
        self.assertFalse(authenticated_page(page('https://login.pandape.com/Account/Login')))
        self.assertFalse(authenticated_page(page('https://betterlatinoamericano.holmeshr.com/Account/Login')))
        self.assertFalse(authenticated_page(page('https://unrelated.example/home')))
        self.assertFalse(authenticated_page(page('https://betterlatinoamericano.holmeshr.com/FichajesOrganizacion/Empleados',filters=False)))
        self.assertFalse(authenticated_page(page('https://betterlatinoamericano.holmeshr.com/',True)))
        self.assertTrue(authenticated_page(page('https://betterlatinoamericano.holmeshr.com/')))
        self.assertTrue(authenticated_page(page('https://betterlatinoamericano.hcm.pandape.com/FichajesOrganizacion/Empleados')))

    def test_profile_is_private_stable_and_disables_password_saving(self):
        import tempfile
        class Options:
            def __init__(self):self.args=[];self.prefs={}
            def add_argument(self,arg):self.args.append(arg)
            def add_experimental_option(self,key,value):self.prefs[key]=value
            def set_capability(self,key,value):pass
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);webdriver=SimpleNamespace(EdgeOptions=Options,ChromeOptions=Options)
            a=session_options(webdriver,root,'edge',root/'downloads1')
            b=session_options(webdriver,root,'edge',root/'downloads2')
            self.assertEqual(a.args[0],b.args[0])
            self.assertIn('.private',a.args[0])
            self.assertFalse(a.prefs['prefs']['profile.password_manager_enabled'])
