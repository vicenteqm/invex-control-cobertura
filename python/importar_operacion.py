"""Extrae solo agregados operativos del tablero anterior, sin ejecutar su código."""
import argparse
import calendar
import json
import math
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEMAPHORES = {'ALARMANTE', 'CRITICA', 'RIESGO', 'OPTIMA', 'SIN_DATOS'}

class EmbeddedMonths(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reading = False
        self.parts = []
    def handle_starttag(self, tag, attrs):
        self.reading = tag == 'script' and dict(attrs).get('id') == 'meses-data' if not self.reading else self.reading
    def handle_endtag(self, tag):
        if tag == 'script': self.reading = False
    def handle_data(self, data):
        if self.reading: self.parts.append(data)

def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('El histórico contiene un indicador numérico inválido')
    return value

def sanitize_months(payload):
    months = {}
    for period, original in payload.items():
        parsed = datetime.strptime(period, '%Y-%m')
        days_in_month = calendar.monthrange(parsed.year, parsed.month)[1]
        reference = int(original['meta']['reference_day'])
        if not 1 <= reference <= days_in_month:
            raise ValueError('Día de corte fuera del mes')
        stores = []
        for key, raw in original['stores'].items():
            info = raw['info']
            if info.get('estatus', 'OPERANDO') != 'OPERANDO': continue
            days = []
            for day, record in raw['dias'].items():
                day = int(day)
                if not 1 <= day <= reference: continue
                semaphore = record.get('semaforo', 'SIN_DATOS')
                if semaphore not in SEMAPHORES: raise ValueError('Semáforo desconocido')
                # Lista blanca: no exporta empleados, usuarios, turnos nominales ni MAAT.
                days.append(dict(day=day, semaphore=semaphore, coverage=number(record.get('cobertura_pct', 0)), present=number(record.get('presentes', 0)), absent=number(record.get('faltantes_hoy', 0)), rest=number(record.get('descansos_hoy', 0)), pending=number(record.get('pendientes_hoy', 0)), users=number(record.get('usuarios_activos', 0)), userRisk=record.get('riesgo_usuario') is True))
                days[-1]['gaps']=[dict(start=str(interval['inicio']),end=str(interval['fin'])) for interval in record.get('gaps',[])]
                days[-1]['covered']=[dict(start=str(interval['inicio']),end=str(interval['fin'])) for interval in record.get('covered',[])]
            subleader = str(info.get('sublider') or '').strip().upper()
            stores.append(dict(id=str(key), name=str(info.get('tienda_nombre') or key), zone=str(info.get('zona') or 'Sin zona'), region=str(info.get('region') or 'Sin región'), executive=str(info.get('ejecutiva') or 'Sin asignar'), required=number(raw.get('plantilla_autorizada',0)), recurrence=str(raw.get('reincidencia') or 'ESTABLE'), redDays=number(raw.get('dias_rojo_mes',0)), monthlyCoverage=number(raw.get('promedio_cobertura_mes',0)), hires=number(raw.get('altas_mes',0)), departures=number(raw.get('bajas_mes',0)), rotation=number(raw.get('rotacion_pct',0)), noSubleader=subleader in ('','PENDIENTE','N/A','SIN SUBLIDER','SIN ASIGNAR'), days=sorted(days,key=lambda d:d['day'])))
        months[period] = dict(referenceDay=reference, daysInMonth=days_in_month, cutoffTime=str(original['meta'].get('hora_corte') or ''), stores=stores)
    if not months: raise ValueError('No se encontraron periodos operativos')
    return months

def import_board(source):
    parser = EmbeddedMonths()
    parser.feed(source.read_text(encoding='utf-8'))
    if not parser.parts: raise ValueError('No se encontró el bloque meses-data en el HTML')
    return dict(importedAt=datetime.now(timezone.utc).isoformat(), sourceName=source.name, sourceModifiedAt=datetime.fromtimestamp(source.stat().st_mtime,timezone.utc).isoformat(), months=sanitize_months(json.loads(''.join(parser.parts))))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tablero', type=Path, required=True)
    args = parser.parse_args()
    data = import_board(args.tablero)
    output = ROOT / 'sitio' / 'operacion-data.js'
    tmp = output.with_suffix('.tmp')
    tmp.write_text('window.INVEX_OPERACION = '+json.dumps(data,ensure_ascii=False,allow_nan=False)+';\n',encoding='utf-8')
    tmp.replace(output)
    print(json.dumps({period:dict(tiendas=len(month['stores']),corte=month['referenceDay']) for period,month in data['months'].items()},ensure_ascii=False))

if __name__ == '__main__': main()
