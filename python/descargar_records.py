"""Descarga mensual de Records mediante Edge visible y el acceso local de MAAT."""
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin,urlparse

URL='https://invex.maatai.com/admin/records/recordreportoptimized/'

def acceso_local(config,root):
    usuario=os.environ.get('MAAT_USER');clave=os.environ.get('MAAT_PASSWORD')
    manual=config.get('maat_manual_login',False)
    if not manual and (not usuario or not clave):
        from secretos_locales import read_credentials
        ruta=root/'.private'/'maat.json'
        if ruta.exists():usuario,clave=read_credentials(ruta)
    if not manual and (not usuario or not clave):raise ValueError('Falta el acceso local de MAAT. Configura MAAT_USER y MAAT_PASSWORD o el ingreso manual.')
    return usuario,clave,manual

def origen_correcto(url):
    parsed=urlparse(url)
    return parsed.scheme=='https' and parsed.hostname=='invex.maatai.com' and parsed.port in (None,443)

def descargar(config,root,inicio,fin):
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    usuario,clave,manual=acceso_local(config,root)
    carpeta=root/'datos'/'descargas'/'records'/datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    carpeta.mkdir(parents=True,exist_ok=True)
    options=webdriver.EdgeOptions()
    options.add_argument('--window-size=1440,1000')
    options.add_experimental_option('prefs',{'download.default_directory':str(carpeta.resolve()),'download.prompt_for_download':False})
    driver=webdriver.Edge(options=options)
    try:
        driver.set_page_load_timeout(60)
        wait=WebDriverWait(driver,60)
        logging.info('Records [1/4]: Abriendo el reporte MAAT en Edge')
        driver.get(URL)
        wait.until(lambda d:d.find_elements(By.ID,'id_start') or d.find_elements(By.NAME,'username'))
        if driver.find_elements(By.NAME,'username'):
            if not origen_correcto(driver.current_url) or urlparse(driver.current_url).path.rstrip('/')!='/admin/login':raise ValueError('La pantalla de acceso no corresponde a MAAT')
            form=driver.find_element(By.CSS_SELECTOR,'input[name="password"]').find_element(By.XPATH,'ancestor::form')
            if not origen_correcto(urljoin(driver.current_url,form.get_attribute('action') or '')):raise ValueError('El formulario no pertenece a MAAT')
            if usuario:driver.find_element(By.NAME,'username').send_keys(usuario)
            if manual:
                logging.info('Completa el inicio de sesión MAAT en Edge; se esperan hasta cinco minutos.')
                WebDriverWait(driver,300).until(lambda d:'/login/' not in d.current_url)
            else:
                try:
                    driver.find_element(By.NAME,'password').send_keys(clave)
                    driver.find_element(By.CSS_SELECTOR,'input[type="submit"],button[type="submit"]').click()
                    wait.until(lambda d:'/login/' not in d.current_url)
                except Exception:raise RuntimeError('MAAT no completó el acceso automático de Records') from None
            driver.get(URL)
        if not origen_correcto(driver.current_url) or urlparse(driver.current_url).path.rstrip('/')!=urlparse(URL).path.rstrip('/'):
            raise ValueError('No se abrió el reporte Records esperado')
        logging.info('Records [2/4]: Aplicando rango %s al %s',inicio.strftime('%d/%m/%Y'),fin.strftime('%d/%m/%Y'))
        for field,fecha in [('id_start',inicio),('id_end',fin)]:
            element=wait.until(EC.visibility_of_element_located((By.ID,field)))
            value=fecha.isoformat() if element.get_attribute('type')=='date' else fecha.strftime('%d/%m/%Y')
            # El control de fecha usa la propiedad nativa para evitar interpretar el formato regional de Windows.
            driver.execute_script("const e=arguments[0];Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(e,arguments[1]);e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));",element,value)
            if element.get_attribute('value')!=value:raise ValueError('MAAT no aceptó la fecha de '+field)
        logging.info('Records [3/4]: Pulsando Descargar')
        wait.until(EC.element_to_be_clickable((By.XPATH,"//button[normalize-space(.)='Descargar'] | //input[@type='submit' and @value='Descargar']"))).click()
        deadline=time.monotonic()+300;anterior=None
        while time.monotonic()<deadline:
            files=[p for p in carpeta.iterdir() if p.suffix.lower() in ('.csv','.xlsx','.xls') and p.is_file()]
            if len(files)==1 and not list(carpeta.glob('*.crdownload')):
                firma=(files[0].name,files[0].stat().st_size)
                if firma==anterior and firma[1]>0:
                    from generar_horas_productivas import leer_records
                    leer_records(files[0])
                    logging.info('Records [4/4]: Descarga validada: %s',files[0].name)
                    return files[0]
                anterior=firma
            time.sleep(1)
        raise TimeoutError('MAAT no entregó Records en cinco minutos')
    finally:
        usuario=clave=None
        driver.quit()
