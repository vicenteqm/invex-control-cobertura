"""Descarga de fichajes INVEX desde Pandape, sin credenciales en el código."""
import os
import json
import logging
import shutil
import time
from pathlib import Path
from urllib.parse import urlsplit
from cobertura_actual import local_now

TENANT_HOSTS={'betterlatinoamericano.hcm.pandape.com','betterlatinoamericano.holmeshr.com'}
FICHAJES_URL='https://betterlatinoamericano.holmeshr.com/FichajesOrganizacion/Empleados'

def authenticated_page(driver):
    """An identity-provider redirect is not a successful login."""
    location=urlsplit(driver.current_url)
    return (location.scheme=='https' and location.hostname in TENANT_HOSTS
            and not location.path.lower().startswith(('/account/','/connect/'))
            and not any(e.is_displayed() for e in driver.find_elements('id','Username'))
            and any(e.is_displayed() for e in driver.find_elements('id','SearchModel_MyTeam')))

def session_options(webdriver,root,browser,folder):
    options=webdriver.EdgeOptions() if browser=='edge' else webdriver.ChromeOptions()
    profile=root/'.private'/('pandape_perfil_'+browser)
    profile.mkdir(parents=True,exist_ok=True)
    options.add_argument('--user-data-dir='+str(profile.resolve()))
    options.add_argument('--window-size=1440,1000')
    options.set_capability('goog:loggingPrefs',{'browser':'ALL'})
    options.add_experimental_option('prefs',{'download.default_directory':str(folder.resolve()),'download.prompt_for_download':False,'download.directory_upgrade':True,'credentials_enable_service':False,'profile.password_manager_enabled':False})
    return options

def ensure_session(driver,username,browser,timeout=300):
    from selenium.webdriver.support.ui import WebDriverWait
    if authenticated_page(driver):
        logging.info('[2/7] Sesión guardada disponible; se continúa sin pedir contraseña')
        return
    logging.info('[2/7] Inicia sesión en %s. Marca Permanecer conectado si está disponible; se guardará la sesión en el perfil local del ejecutor.',browser.title())
    logging.info('El ejecutor no escribe ni guarda la contraseña. Esperando tu ingreso hasta cinco minutos.')
    def ready(d):
        if authenticated_page(d):return True
        location=urlsplit(d.current_url)
        if location.hostname=='betterlatinoamericano.holmeshr.com' and location.path=='/' and not any(e.is_displayed() for e in d.find_elements('id','Username')):
            d.get(FICHAJES_URL)
            return authenticated_page(d)
        # Only prepare the username on the known identity providers.
        if urlsplit(d.current_url).hostname not in {'login.pandape.com','secure.holmeshr.com'}:return False
        for e in d.find_elements('id','Username'):
            if username and e.is_displayed() and not e.get_attribute('value'):e.send_keys(username)
        return False
    WebDriverWait(driver,timeout).until(ready)
    logging.info('Sesión iniciada; Edge conservará las cookies en el perfil privado al cerrarse')

def prepare_session(config,root):
    """Open only Pandape, without downloading, calculating or publishing."""
    from selenium import webdriver
    browser=config.get('pandape_browser','edge').lower()
    if browser not in ('edge','chrome'):raise ValueError('Usa edge o chrome para Pandape')
    folder=root/'datos'/'pandape';folder.mkdir(parents=True,exist_ok=True)
    options=session_options(webdriver,root,browser,folder)
    driver=webdriver.Edge(options=options) if browser=='edge' else webdriver.Chrome(options=options)
    try:
        driver.set_page_load_timeout(60)
        driver.get(FICHAJES_URL)
        ensure_session(driver,os.environ.get('PANDAPE_USER') or config.get('pandape_user'),browser)
        print('Sesión guardada para el ejecutor. Puedes usar ACTUALIZAR_INVEX.bat.',flush=True)
    finally:driver.quit()
def wait_download(folder, timeout=180):
    deadline=time.monotonic()+timeout
    previous=None
    while time.monotonic()<deadline:
        files=[p for p in Path(folder).glob('Reporte*') if p.is_file() and p.suffix.lower() in ('.xlsx','.xls','.csv')]
        partial=list(Path(folder).glob('*.crdownload'))
        if len(files)==1 and not partial:
            signature=(files[0].name,files[0].stat().st_size)
            if signature==previous and signature[1]>0:return files[0]
            previous=signature
        time.sleep(1)
    raise TimeoutError('Pandape no entregó un reporte nuevo dentro del tiempo permitido')


def wait_page_idle(driver,timeout=45):
    """Los filtros recargan la página; no exportar durante esa navegación."""
    from selenium.webdriver.support.ui import WebDriverWait
    stable_since=None
    def idle(d):
        nonlocal stable_since
        ready=d.execute_script("return document.readyState === 'complete' && (!window.jQuery || window.jQuery.active === 0)")
        signature=d.current_url if ready else None
        if not signature:
            stable_since=None
            return False
        if stable_since is None or stable_since[0]!=signature:
            stable_since=(signature,time.monotonic())
            return False
        return time.monotonic()-stable_since[1]>=1.5
    WebDriverWait(driver,timeout,poll_frequency=.25).until(idle)


def report_dialog_visible(driver):
    return any(e.is_displayed() for e in driver.find_elements('id','OfflineReportGeneratedPopUp'))


def submit_export(driver,timeout=15):
    """El cambio de fecha puede consumir el primer clic al cerrar el calendario."""
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
    for attempt in range(3):
        button=WebDriverWait(driver,timeout).until(EC.element_to_be_clickable(('id','btnExportReportPopupOk')))
        button.click()
        def accepted(d):
            return report_dialog_visible(d)
        try:
            WebDriverWait(driver,3).until(accepted)
            return
        except TimeoutException:
            logging.warning('Pandape: el diálogo sigue abierto; confirmando Exportar (intento %s/3)',attempt+1)
    raise ValueError('Pandape no confirmó la solicitud de exportación; el diálogo sigue abierto')


def wait_report_ready(driver,timeout=600):
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.common.exceptions import TimeoutException
    next_notice=time.monotonic()+30
    missing_since=None
    def ready(d):
        nonlocal next_notice,missing_since
        for field in ('offlineReportFinalRetryMessage','offlineReportIntitalRetryMessage','offlineReportFinalNoDataMessage'):
            for element in d.find_elements('id',field):
                if element.is_displayed():raise ValueError('Pandape: '+element.text.strip())
        for element in d.find_elements('id','getOfflineReportFromDeafultPopUp'):
            if element.is_displayed() and element.is_enabled():return element
        if not report_dialog_visible(d):
            if missing_since is None:missing_since=time.monotonic()
            if time.monotonic()-missing_since>5:
                d.get('https://betterlatinoamericano.holmeshr.com/Reportes/ReportesDescargados')
                wait_page_idle(d)
                rows=d.find_elements('css selector','table[aria-label="Reportes generados"] tbody tr')
                if rows and 'En proceso' in rows[0].text:
                    raise ValueError('Pandape recibió la solicitud, pero el último reporte sigue En proceso en Reportes generados y no permite descargarlo. Se conserva el tablero anterior; no es un fallo de GitHub ni HTTP 403.')
                raise ValueError('La ventana de generación cerró sin entregar el archivo. Revisa el estado en Reportes generados de Pandape; se conserva el tablero anterior.')
        else:missing_since=None
        if time.monotonic()>=next_notice:
            logging.info('Pandape sigue generando el reporte en el servidor; esperando el enlace de descarga')
            next_notice=time.monotonic()+30
        return False
    try:return WebDriverWait(driver,timeout,poll_frequency=1).until(ready)
    except TimeoutException:
        raise ValueError('Pandape aceptó la exportación, pero no entregó el enlace en 10 minutos. Revisa Reportes generados en Pandape; se conserva el tablero anterior.') from None

def download(config, root):
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait,Select
    from selenium.webdriver.support import expected_conditions as EC
    username=os.environ.get('PANDAPE_USER') or config.get('pandape_user')
    now=local_now()
    if config['period']!=now.strftime('%Y-%m'):raise ValueError('La descarga diaria de Pandape requiere configurar el mes actual')
    folder=root/'datos'/'pandape'/'descargas'/now.strftime('%Y%m%d_%H%M%S_%f')
    folder.mkdir(parents=True)
    browser=config.get('pandape_browser','chrome').lower()
    if browser not in ('chrome','edge'):raise ValueError('Navegador Pandape no admitido: usa chrome o edge')
    options=session_options(webdriver,root,browser,folder)
    visible=True
    driver=webdriver.Edge(options=options) if browser=='edge' else webdriver.Chrome(options=options)
    stage='abrir_login'
    try:
        logging.info('[1/7] Abriendo %s%s y acceso Pandape',browser.title(),' visible' if visible else '')
        driver.set_page_load_timeout(60)
        driver.execute_cdp_cmd('Browser.setDownloadBehavior',{'behavior':'allow','downloadPath':str(folder.resolve())})
        wait=WebDriverWait(driver,45)
        # Go to the protected page first so a saved login can be reused.
        driver.get(FICHAJES_URL)
        if '403' in driver.title or 'Forbidden' in driver.title:
            raise RuntimeError('El servidor rechaza el acceso automático con HTTP 403')
        stage='ingreso_manual'
        ensure_session(driver,username,browser)
        logging.info('[3/7] Abriendo Fichajes de empleados')
        driver.get(FICHAJES_URL)
        from generar_asistencia import normalized
        for field,label in [('SearchModel_MyTeam','COMPAÑÍA'),('company_group_type_id','DEPARTAMENTO'),('company_group_id','INVEX')]:
            stage='filtro_'+field
            logging.info('[4/7] Aplicando filtro: %s',label)
            wanted=normalized(label)
            def matching(d):
                return next((o for o in d.find_elements(By.CSS_SELECTOR,'#'+field+' option') if normalized(o.text)==wanted),False)
            option=wait.until(matching)
            Select(driver.find_element(By.ID,field)).select_by_value(option.get_attribute('value'))
            wait.until(lambda d: normalized(Select(d.find_element(By.ID,field)).first_selected_option.text)==wanted)
            wait_page_idle(driver)
        logging.info('[5/7] Exportando los fichajes del día %s',now.strftime('%d/%m/%Y'))
        stage='abrir_exportacion'
        if not any(el.is_displayed() for el in driver.find_elements(By.ID,'date-start')):
            wait.until(lambda d:next((e for e in d.find_elements(By.ID,'exportButton') if e.is_displayed() and e.is_enabled()),False)).click()
        stage='fechas_exportacion'
        for field in ('date-start','date-end'):
            element=wait.until(EC.visibility_of_element_located((By.ID,field)));element.clear();element.send_keys(now.strftime('%d/%m/%Y'))
            from selenium.webdriver.common.keys import Keys
            element.send_keys(Keys.TAB)
            if element.get_attribute('value')!=now.strftime('%d/%m/%Y'):raise ValueError('Pandape no aceptó la fecha del reporte en '+field)
        submit_export(driver)
        stage='generar_reporte'
        logging.info('[6/7] Esperando el reporte de Pandape y descargando el Excel')
        wait_report_ready(driver).click()
        stage='descargar_reporte'
        report=wait_download(folder)
        from generar_asistencia import summarize
        summarize(report,now.date())
        current=root/'datos'/'pandape'/'Reporte_Pandape_actual.xlsx'
        if report.suffix.lower()!='.xlsx':raise ValueError('La exportación debe ser un Excel XLSX')
        temporary=current.with_suffix('.tmp.xlsx');shutil.copyfile(report,temporary);temporary.replace(current)
        logging.info('[7/7] Reporte validado y reemplazado: %s',current.name)
        return current
    except Exception as error:
        private=root/'datos'/'pandape'
        from urllib.parse import urlsplit
        title='';page='';screenshot=False
        try:
            title=driver.title;location=urlsplit(driver.current_url);page=location.netloc+location.path
            screenshot=driver.save_screenshot(str(private/'diagnostico.png'))
            (private/'diagnostico-pagina.html').write_text(driver.page_source,encoding='utf-8')
            (private/'diagnostico-navegador.json').write_text(json.dumps(driver.get_log('browser'),ensure_ascii=False,indent=2),encoding='utf-8')
        except Exception:pass
        (private/'diagnostico.json').write_text(json.dumps({'stage':stage,'error':type(error).__name__,'page':page,'title':title,'screenshotAvailable':screenshot}),encoding='utf-8')
        reason='El navegador se cerró o perdió la conexión; vuelve a iniciar el ejecutor y conserva la ventana abierta' if type(error).__name__ in ('InvalidSessionIdException','NoSuchWindowException') else 'HTTP 403: el servidor rechazó el acceso automático antes de iniciar sesión' if '403' in title or 'Forbidden' in title else 'No se completó el ingreso manual dentro de cinco minutos' if stage=='ingreso_manual' and type(error).__name__=='TimeoutException' else 'CAPTCHA: se requiere completar el inicio de sesión en el navegador' if stage=='verificacion_humana' else str(error) if isinstance(error,ValueError) else type(error).__name__
        raise RuntimeError('Pandape: '+stage+' ('+reason+')') from None
    finally:
        try:driver.quit()
        except Exception:pass
