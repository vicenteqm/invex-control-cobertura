"""Acceso MAAT del EXE por HTTPS; no expone contraseña en el navegador."""
from urllib.parse import urljoin,urlsplit

def download(destination,period,user,password):
    import requests
    from descarga_asistencia import LOGIN,Links,daily_dashboard_url,parse_csv,validate_daily_records,merge_csv
    def trusted(url):
        p=urlsplit(url)
        if p.scheme!='https' or p.hostname!='invex.maatai.com' or p.port not in (None,443):
            raise ValueError('MAAT redirigió fuera de su origen autorizado')
        return url
    # Se cierran cookies al terminar. No se desactiva la validación TLS.
    with requests.Session() as session:
        def get(url):
            response=session.get(trusted(url),timeout=45,allow_redirects=False)
            for _ in range(5):
                if not response.is_redirect:break
                response=session.get(trusted(urljoin(response.url,response.headers['Location'])),timeout=45,allow_redirects=False)
            response.raise_for_status();return response
        login=get(LOGIN);parser=Links();parser.feed(login.text)
        if not parser.csrf:raise ValueError('MAAT no mostró el formulario de acceso esperado')
        result=session.post(trusted(login.url),data={'username':user,'password':password,'csrfmiddlewaretoken':parser.csrf,'next':'/admin/'},headers={'Referer':login.url},timeout=45,allow_redirects=False)
        result.raise_for_status()
        if result.status_code not in (302,303):raise ValueError('MAAT no aceptó el acceso; solicita al responsable actualizarlo')
        trusted(urljoin(result.url,result.headers['Location']))
        url,day=daily_dashboard_url(period);dashboard=get(url)
        if '/login' in dashboard.url:raise ValueError('MAAT no confirmó la sesión')
        parser=Links();parser.feed(dashboard.text)
        if not parser.export:raise ValueError('MAAT no mostró la exportación de asistencias')
        export=get(urljoin(dashboard.url,parser.export))
        export.encoding='utf-8-sig';headers,rows=parse_csv(export.text)
        validate_daily_records(rows,day)
        return merge_csv(headers,rows,destination,period)
