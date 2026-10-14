"""Descarga de fichajes INVEX desde Pandape, sin credenciales en el código."""
import os
import json
import logging
import shutil
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
    username=os.environ.get('PANDAPE_USER') or config.get('pandape_user');password=os.environ.get('PANDAPE_PASSWORD')
    manual_login=config.get('pandape_manual_login',True)
    if not manual_login and (not username or not password):
        raise ValueError('El acceso automático requiere PANDAPE_USER y PANDAPE_PASSWORD en el entorno; no se leen credenciales cifradas')
    now=local_now()
    if config['period']!=now.strftime('%Y-%m'):raise ValueError('La descarga diaria de Pandape requiere configurar el mes actual')
    folder=root/'inputs'/'pandape'/'descargas'/now.strftime('%Y%m%d_%H%M%S_%f')
    folder.mkdir(parents=True)
    browser=config.get('pandape_browser','chrome').lower()
    if browser not in ('chrome','edge'):raise ValueError('Navegador Pandape no admitido: usa chrome o edge')
    options=webdriver.EdgeOptions() if browser=='edge' else webdriver.ChromeOptions()
    visible=manual_login or config.get('pandape_visible',False)
    if not visible:options.add_argument('--headless=new')
    options.add_argument('--window-size=1440,1000')
    options.add_experimental_option('prefs',{'download.default_directory':str(folder.resolve()),'download.prompt_for_download':False,'download.directory_upgrade':True})
    driver=webdriver.Edge(options=options) if browser=='edge' else webdriver.Chrome(options=options)
    stage='abrir_login'
    try:
        logging.info('[1/7] Abriendo %s%s y acceso Pandape',browser.title(),' visible' if visible else '')
        driver.set_page_load_timeout(60)
        driver.execute_cdp_cmd('Browser.setDownloadBehavior',{'behavior':'allow','downloadPath':str(folder.resolve())})
        wait=WebDriverWait(driver,45)
        driver.get('https://login.pandape.com/Account/Login')
        if '403' in driver.title or 'Forbidden' in driver.title:
            raise RuntimeError('El servidor rechaza el acceso automático con HTTP 403')
        stage='campos_login'
        logging.info('[2/7] Preparando el correo; escribe tú la contraseña y pulsa Entrar' if manual_login and username else '[2/7] Escribe tu correo y contraseña en Edge y pulsa Entrar' if manual_login else '[2/7] Iniciando sesión con las credenciales del entorno')
        user_field=wait.until(EC.visibility_of_element_located((By.ID,'Username')))
        if username:user_field.send_keys(username)
        stage='autenticar'
        if manual_login:
            stage='ingreso_manual'
            logging.info('Esperando tu ingreso en %s hasta 5 minutos. El ejecutor no escribe ni envía la contraseña.',browser.title())
            WebDriverWait(driver,300).until(lambda d:'login.pandape.com/Account/Login' not in d.current_url)
        else:
            driver.find_element(By.ID,'Password').send_keys(password)
            driver.find_element(By.ID,'btLogin').click()
            wait.until(lambda d:'login.pandape.com/Account/Login' not in d.current_url or 'validación de captcha' in d.find_element(By.TAG_NAME,'body').text.lower())
        if 'login.pandape.com/Account/Login' in driver.current_url:
            if not visible:raise RuntimeError('CAPTCHA: Pandape requiere verificación humana en el navegador visible')
            stage='verificacion_humana'
            logging.warning('Pandape pide verificación CAPTCHA. Completa el inicio de sesión en la ventana del navegador. El ejecutor espera hasta 5 minutos y continúa cuando entres; no resuelve la verificación automáticamente.')
            WebDriverWait(driver,300).until(lambda d:'login.pandape.com/Account/Login' not in d.current_url)
        logging.info('[3/7] Abriendo Fichajes de empleados')
        driver.get('https://betterlatinoamericano.hcm.pandape.com/FichajesOrganizacion/Empleados')
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
        logging.info('[5/7] Exportando los fichajes del día %s',now.strftime('%d/%m/%Y'))
        stage='abrir_exportacion'
        notices=driver.find_elements(By.XPATH,"//*[normalize-space(text())='Problema administrativo']")
        for notice in notices:
            if not notice.is_displayed():continue
            logging.warning('Pandape muestra un aviso administrativo de la cuenta; se cierra únicamente el aviso para continuar con la exportación')
            for ancestor in reversed(notice.find_elements(By.XPATH,'ancestor::*')):
                text=ancestor.text
                if len(text)>2000:continue
                buttons=ancestor.find_elements(By.CSS_SELECTOR,'button, [role="button"], [data-dismiss], [data-bs-dismiss], .close')
                close=next((b for b in buttons if b.is_displayed() and ((b.get_attribute('aria-label') or '').lower() in ('close','cerrar') or b.get_attribute('data-dismiss') or b.get_attribute('data-bs-dismiss') or b.text.strip() in ('×','✕','✖','X'))),None)
                if close:
                    close.click();wait.until(EC.invisibility_of_element(notice));break
            else:
                logging.warning('Cierra el aviso administrativo con la X en Edge; el ejecutor espera hasta 2 minutos')
                WebDriverWait(driver,120).until(EC.invisibility_of_element(notice))
        if not any(el.is_displayed() for el in driver.find_elements(By.ID,'date-start')):
            wait.until(EC.element_to_be_clickable((By.ID,'exportButton'))).click()
        stage='fechas_exportacion'
        for field in ('date-start','date-end'):
            element=wait.until(EC.visibility_of_element_located((By.ID,field)));element.clear();element.send_keys(now.strftime('%d/%m/%Y'))
            from selenium.webdriver.common.keys import Keys
            element.send_keys(Keys.TAB)
            if element.get_attribute('value')!=now.strftime('%d/%m/%Y'):raise ValueError('Pandape no aceptó la fecha del reporte en '+field)
        driver.find_element(By.ID,'btnExportReportPopupOk').click()
        stage='generar_reporte'
        logging.info('[6/7] Esperando el reporte de Pandape y descargando el Excel')
        WebDriverWait(driver,180).until(EC.element_to_be_clickable((By.ID,'getOfflineReportFromDeafultPopUp'))).click()
        stage='descargar_reporte'
        report=wait_download(folder)
        from generar_asistencia import summarize
        summarize(report,now.date())
        current=root/'inputs'/'pandape'/'Reporte_Pandape_actual.xlsx'
        if report.suffix.lower()!='.xlsx':raise ValueError('La exportación debe ser un Excel XLSX')
        temporary=current.with_suffix('.tmp.xlsx');shutil.copyfile(report,temporary);temporary.replace(current)
        logging.info('[7/7] Reporte validado y reemplazado: %s',current.name)
        return current
    except Exception as error:
        private=root/'inputs'/'pandape'
        from urllib.parse import urlsplit
        title='';page='';screenshot=False
        try:
            title=driver.title;location=urlsplit(driver.current_url);page=location.netloc+location.path
            screenshot=driver.save_screenshot(str(private/'diagnostico.png'))
        except Exception:pass
        (private/'diagnostico.json').write_text(json.dumps({'stage':stage,'error':type(error).__name__,'page':page,'title':title,'screenshotAvailable':screenshot}),encoding='utf-8')
        reason='El navegador se cerró o perdió la conexión; vuelve a iniciar el ejecutor y conserva la ventana abierta' if type(error).__name__ in ('InvalidSessionIdException','NoSuchWindowException') else 'HTTP 403: el servidor rechazó el acceso automático antes de iniciar sesión' if '403' in title or 'Forbidden' in title else 'No se completó el ingreso manual dentro de cinco minutos' if stage=='ingreso_manual' and type(error).__name__=='TimeoutException' else 'CAPTCHA: se requiere completar el inicio de sesión en el navegador' if stage=='verificacion_humana' else str(error) if isinstance(error,ValueError) else type(error).__name__
        raise RuntimeError('Pandape: '+stage+' ('+reason+')') from None
    finally:
        try:driver.quit()
        except Exception:pass
