"""Descarga MAAT con sesión HTTP y actualiza el concentrado mensual de forma atómica."""
import argparse
import csv
import io
import json
import logging
import os
from datetime import datetime, date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin,urlparse
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'.build-deps'))
import requests

LOGIN='https://invex.maatai.com/admin/login/?next=/admin/'
DASHBOARD='https://invex.maatai.com/admin/records/attendancedashboard/'
MAPPINGS={'MODULO BETTER HOUSE GALERIAS ZACATECAS MAAT 2.0':25,'MODULO BH CH TUXTLA AMBAR':752,'MODULO BH CH PLAZA PUERTA ARAGON 179':20,'MODULO BETTER CH VERACRUZ AMERICAS':20,'MODULO BH CH TAMPICO MADERO 036':110,'MODULO BH CH TUXTLA CRYSTAL 013':13,'MODULO BETTER HOUSE CH ACAPULCO CENTRO':265,'MODULO BETTER HOUSE CH FRESNILLO':123,'MODULO BH SC HAROLD MONCLOVA 1007':1007}

class Links(HTMLParser):
    def __init__(self):super().__init__();self.csrf=None;self.export=None
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='input' and attrs.get('name')=='csrfmiddlewaretoken':self.csrf=attrs.get('value')
        if tag=='a' and 'export-csv' in attrs.get('href',''):self.export=attrs['href']

def parse_csv(text):
    if not text.strip() or text.lstrip().startswith('<'):raise ValueError('La descarga no es un CSV válido')
    try:dialect=csv.Sniffer().sniff(text[:8192],delimiters=',;\t')
    except csv.Error:dialect=csv.excel
    reader=csv.DictReader(io.StringIO(text.lstrip('\ufeff')),dialect=dialect)
    headers=reader.fieldnames or []
    if 'Fecha' not in headers or not any(h in headers for h in ('Ejecutivo','USUARIO','Usuario')):raise ValueError('CSV MAAT sin Fecha o Ejecutivo / Usuario')
    return headers,list(reader)

def read_csv(path):return parse_csv(Path(path).read_text(encoding='utf-8-sig'))

def date_key(value):
    from engine import _parse_fecha_completa
    parsed=_parse_fecha_completa(value)
    if parsed is None:raise ValueError('Fecha inválida en CSV MAAT')
    return date(*parsed).isoformat()

def merge_csv(headers,records,destination,period):
    records=[dict(r) for r in records if date_key(r['Fecha']).startswith(period+'-')]
    if not records:raise ValueError('La descarga no contiene registros del periodo '+period)
    if destination.exists():old_headers,old=read_csv(destination)
    else:old_headers,old=headers,[]
    dates={date_key(r['Fecha']) for r in records}
    result=[r for r in old if date_key(r['Fecha']) not in dates]+records
    fields=list(dict.fromkeys(old_headers+headers+['Segundo punto de venta']))
    for record in result:
        if record.get('Punto de venta') in MAPPINGS:record['Segundo punto de venta']=MAPPINGS[record['Punto de venta']]
    destination.parent.mkdir(parents=True,exist_ok=True)
    tmp=destination.with_suffix('.tmp')
    with tmp.open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(result)
    tmp.replace(destination)
    return len(records),len(result)

def download(destination,period,username=None,password=None):
    username=username or os.environ.get('MAAT_USER');password=password or os.environ.get('MAAT_PASSWORD')
    if not username or not password:raise ValueError('Faltan credenciales MAAT; configure MAAT_USER y MAAT_PASSWORD')
    with requests.Session() as session:
        logging.info('MAAT [1/4]: Iniciando sesión con las credenciales guardadas')
        response=session.get(LOGIN,timeout=30);response.raise_for_status()
        parser=Links();parser.feed(response.text)
        if not parser.csrf:raise ValueError('No se encontró el formulario de acceso MAAT')
        response=session.post(LOGIN,data={'username':username,'password':password,'csrfmiddlewaretoken':parser.csrf,'next':'/admin/'},headers={'Referer':LOGIN},timeout=30);response.raise_for_status()
        logging.info('MAAT [2/4]: Accediendo a %s',DASHBOARD)
        response=session.get(DASHBOARD,timeout=30);response.raise_for_status()
        if '/login/' in response.url:raise ValueError('MAAT rechazó el inicio de sesión')
        parser=Links();parser.feed(response.text)
        if not parser.export:raise ValueError('No se encontró Exportar CSV; revisar permisos o cambios en MAAT')
        url=urljoin(DASHBOARD,parser.export)
        if urlparse(url).hostname!='invex.maatai.com':raise ValueError('El enlace de exportación apunta a otro servidor')
        logging.info('MAAT [3/4]: Descargando la exportación CSV del tablero de asistencia')
        response=session.get(url,timeout=60);response.raise_for_status()
        headers,records=parse_csv(response.content.decode('utf-8-sig'))
        logging.info('MAAT [4/4]: Validando y actualizando el concentrado del periodo %s',period)
        return merge_csv(headers,records,Path(destination),period)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--destino',type=Path,required=True);parser.add_argument('--periodo',required=True);args=parser.parse_args()
    downloaded,total=download(args.destino,args.periodo);print(json.dumps(dict(descargados=downloaded,concentrado=total)))
if __name__=='__main__':main()
