"""Descarga de fichajes INVEX desde Pandape, sin credenciales en el código."""
import os
import json
import time
from pathlib import Path
from cobertura_actual import local_now

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

def download(config, root):
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait,Select
    from selenium.webdriver.support import expected_conditions as EC
    from secretos_locales import read_credentials
    username=os.environ.get('PANDAPE_USER');password=os.environ.get('PANDAPE_PASSWORD')
    if not username or not password:username,password=read_credentials(root/'.private'/'pandape.json')
    now=local_now()
    if config['period']!=now.strftime('%Y-%m'):raise ValueError('La descarga diaria de Pandape requiere configurar el mes actual')
    folder=root/'inputs'/'pandape'/'descargas'/now.strftime('%Y%m%d_%H%M%S_%f')
    folder.mkdir(parents=True)
    options=webdriver.ChromeOptions()
    options.add_argument('--headless=new');options.add_argument('--window-size=1440,1000')
    options.add_experimental_option('prefs',{'download.default_directory':str(folder.resolve()),'download.prompt_for_download':False,'download.directory_upgrade':True})
    driver=webdriver.Chrome(options=options)
    stage='abrir_login'
    try:
        driver.set_page_load_timeout(60)
        driver.execute_cdp_cmd('Browser.setDownloadBehavior',{'behavior':'allow','downloadPath':str(folder.resolve())})
        wait=WebDriverWait(driver,45)
        driver.get('https://login.pandape.com/Account/Login')
        if '403' in driver.title or 'Forbidden' in driver.title:
            raise RuntimeError('El servidor rechaza el acceso automático con HTTP 403')
        stage='campos_login'
        wait.until(EC.visibility_of_element_located((By.ID,'Username'))).send_keys(username)
        driver.find_element(By.ID,'Password').send_keys(password)
        driver.find_element(By.ID,'btLogin').click()
        stage='autenticar'
        wait.until(lambda d:'login.pandape.com/Account/Login' not in d.current_url)
        driver.get('https://betterlatinoamericano.hcm.pandape.com/FichajesOrganizacion/Empleados')
        for field,value in [('SearchModel_MyTeam','2'),('company_group_type_id','5E99FE99531EB996'),('company_group_id','B96EFA026EDE5683')]:
            stage='filtro_'+field
            wait.until(lambda d: any(o.get_attribute('value')==value for o in d.find_elements(By.CSS_SELECTOR,'#'+field+' option')))
            Select(driver.find_element(By.ID,field)).select_by_value(value)
        wait.until(EC.element_to_be_clickable((By.ID,'exportButton'))).click()
        stage='fechas_exportacion'
        for field in ('date-start','date-end'):
            element=wait.until(EC.visibility_of_element_located((By.ID,field)));element.clear();element.send_keys(now.strftime('%d/%m/%Y'))
        driver.find_element(By.ID,'btnExportReportPopupOk').click()
        stage='generar_reporte'
        WebDriverWait(driver,180).until(EC.element_to_be_clickable((By.ID,'getOfflineReportFromDeafultPopUp'))).click()
        stage='descargar_reporte'
        return wait_download(folder)
    except Exception as error:
        private=root/'inputs'/'pandape'
        driver.save_screenshot(str(private/'diagnostico.png'))
        from urllib.parse import urlsplit
        location=urlsplit(driver.current_url)
        (private/'diagnostico.json').write_text(json.dumps({'stage':stage,'error':type(error).__name__,'page':location.netloc+location.path,'title':driver.title}),encoding='utf-8')
        reason='HTTP 403: el servidor rechazó el acceso automático antes de iniciar sesión' if '403' in driver.title or 'Forbidden' in driver.title else type(error).__name__
        raise RuntimeError('Pandape: '+stage+' ('+reason+')') from None
    finally:driver.quit()
