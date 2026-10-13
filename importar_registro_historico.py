"""Recupera agregados de registro de los meses históricos del ZIP anterior."""
import argparse
import json
import zipfile
from pathlib import Path
from importar_operacion import EmbeddedMonths
from registro_maat import aggregate

ROOT=Path(__file__).resolve().parent
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--zip',required=True,type=Path);args=parser.parse_args()
    path=ROOT/'site'/'operacion-data.js';prefix='window.INVEX_OPERACION = '
    data=json.loads(path.read_text(encoding='utf-8')[len(prefix):].strip().removesuffix(';'))
    with zipfile.ZipFile(args.zip) as archive:
        embedded=EmbeddedMonths();embedded.feed(archive.read('control_cobertura.html').decode('utf-8-sig'));raws=json.loads(''.join(embedded.parts))
    for period,month in data['months'].items():
        if period==data.get('currentPeriod') or period not in raws:continue
        raw=raws[period]
        if not raw['meta'].get('maat_cargado'):continue
        raw['meta']['period']=period;maat_days=set();pandape_days=set()
        for store in raw['stores'].values():
            for person in store['empleados_activos']+store.get('externos_maat',[]):
                for day,record in person.get('registro_por_dia',{}).items():
                    if not 1<=int(day)<=month['daysInMonth']:continue
                    if record.get('registra_maat'):maat_days.add(int(day))
                    if record.get('registra_pandape'):pandape_days.add(int(day))
        registration=aggregate(raw,month['daysInMonth'],maat_days)
        for store in month['stores']:store['registration']=registration[store['id']]
        month.update(maatLoaded=True,maatDays=sorted(maat_days),attendanceDays=sorted(pandape_days))
        directory=ROOT/'inputs'/'historico';directory.mkdir(exist_ok=True)
        (directory/('analisis_'+period+'.json')).write_text(json.dumps(raw,ensure_ascii=False),encoding='utf-8')
        print('Registro histórico incorporado: '+period)
    temporary=path.with_suffix('.tmp');temporary.write_text(prefix+json.dumps(data,ensure_ascii=False,allow_nan=False)+';\n',encoding='utf-8');temporary.replace(path)
if __name__=='__main__':main()
