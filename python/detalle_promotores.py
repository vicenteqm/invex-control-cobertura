"""Excel nominal local equivalente a downloadRegistroExcel del tablero anterior."""
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment,Border,Side
from openpyxl.utils import get_column_letter

HEADERS=['Fecha','Nombre','Perfil de Puesto','Tienda','Clave de tienda','Zona','Región','Ejecutiva','Tipo de jornada','Horario asignado (texto)','Hora inicio programada','Hora fin programada','Registra Pandape','Hora entrada Pandape','Hora salida Pandape','Registra MAAT','Hora entrada MAAT','Hora salida MAAT','Estatus','Se movió de tienda (según MAAT)','Cerró jornada manualmente (MAAT)','Llegó tarde','Salió antes de su horario','Horario estimado por','No está en asistencia (agregado desde MAAT)']
LABELS={'COMPLETO':'Completo','SEGUIMIENTO_MAAT':'Falta MAAT','ALERTA_PANDAPE':'Falta Pandape','ALARMANTE':'Sin registro'}

def export_attendance(rows):
    """Amplía únicamente la población del Excel, sin modificar los KPI."""
    result=[list(row) for row in rows]
    for row in result[1:]:
        status=str(row[10] or '').strip()
        if status in ('ACTIVA',) or status.startswith(('ACTIVO/','ACTIVO ')):
            row[10]='ACTIVO'
    return result


def attach_excel_detail(raw,expanded):
    """El detalle ampliado reemplaza el del Excel, no se suma ni duplica."""
    for key,store in raw['stores'].items():
        source=expanded['stores'].get(key,store)
        store['personal_excel']=source.get('empleados_activos',[])
        store['externos_excel']=source.get('externos_maat',[])

def public_detail(raw):
    """Solo los campos nominales autorizados para la consulta del tablero."""
    fields=['registra_pandape','registra_maat','estatus_registro','tienda_maat','se_movio_de_tienda','hora_entrada_pandape','hora_salida_pandape','hora_entrada_maat','hora_salida_maat','cerro_jornada_manual','llego_tarde','minutos_tarde','salio_antes_de_horario','minutos_antes_de_hora','hora_inicio_programada','hora_fin_programada','fuente_horario_programado']
    result={'meta':{'period':raw['meta']['period']},'stores':{}}
    for key,store in raw['stores'].items():
        target={}
        for group in ['empleados_activos','externos_maat','personal_excel','externos_excel']:
            target[group]=[dict(nombre=p['nombre'],puesto=p.get('puesto'),jornada=p.get('jornada'),horario_personal=p.get('horario_personal'),registro_por_dia={str(day):{f:r.get(f) for f in fields} for day,r in p.get('registro_por_dia',{}).items() if 1<=int(day)<=raw['meta']['reference_day']}) for p in store.get(group,[])]
        result['stores'][key]=target
    return result

def rows(raw,day):
    period=raw['meta'].get('period','');date=period+'-'+str(day).zfill(2)
    output=[]
    for key,store in raw['stores'].items():
        info=store['info']
        for external,people in [(False,store.get('personal_excel',store['empleados_activos'])),(True,store.get('externos_excel',store.get('externos_maat',[])))]:
            for person in people:
                record=person.get('registro_por_dia',{}).get(str(day))
                if not record:continue
                source={'horario_personal':'Horario personal explícito','jornada_tiempo_completo':'Jornada tiempo completo (horario de tienda)'}.get(record.get('fuente_horario_programado'),'No disponible')
                output.append([date,person['nombre'],person.get('puesto') or 'No disponible',info.get('tienda_nombre') or key,key,info.get('zona',''),info.get('region',''),info.get('ejecutiva',''),person.get('jornada') or '',person.get('horario_personal') or '',record.get('hora_inicio_programada') or '',record.get('hora_fin_programada') or '', 'Sí' if record.get('registra_pandape') else 'No',record.get('hora_entrada_pandape') or '',record.get('hora_salida_pandape') or '', 'Sí' if record.get('registra_maat') else 'No',record.get('hora_entrada_maat') or '',record.get('hora_salida_maat') or '',LABELS.get(record.get('estatus_registro'),'Sin evaluar') if raw['meta'].get('maat_cargado') else 'Sin evaluar', 'Sí — '+(record.get('tienda_maat') or '') if record.get('se_movio_de_tienda') else 'No','Sí' if record.get('cerro_jornada_manual') else 'No', 'Sí — '+str(record.get('minutos_tarde') or 0)+' min' if record.get('llego_tarde') else 'No', 'Sí — '+str(record.get('minutos_antes_de_hora') or 0)+' min antes' if record.get('salio_antes_de_horario') else 'No',source,'Sí' if external else 'No'])
    return output

def export(raw,destination,day=None):
    day=day or raw['meta']['reference_day'];data=rows(raw,day)
    workbook=Workbook();sheet=workbook.active;sheet.title='Registro Pandape-MAAT'
    sheet.append(HEADERS)
    for row in data:
        sheet.append(row)
        # Todo valor de origen es texto, nunca una fórmula ejecutable.
        for cell in sheet[sheet.max_row]:cell.data_type='s'
    border=Border(*(Side(style='thin',color='E5E5E5') for _ in range(4)))
    for row in sheet:
        for cell in row:
            header=cell.row==1
            cell.font=Font(name='Calibri',size=9,color='FFFFFF' if header else '000000',bold=header)
            cell.fill=PatternFill('solid',fgColor='000000' if header else 'FFFFFF')
            cell.alignment=Alignment(horizontal='center',vertical='center',wrap_text=True)
            cell.border=border
        sheet.row_dimensions[row[0].row].height=42 if row[0].row==1 else 36
    for col,header in enumerate(HEADERS,1):
        maximum=max([len(header)]+[len(str(row[col-1] or '')) for row in data])
        sheet.column_dimensions[get_column_letter(col)].width=min(42,max(15,maximum+2))
    sheet.freeze_panes='A2';sheet.auto_filter.ref=sheet.dimensions
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    temporary=destination.with_name(destination.stem+'.tmp.xlsx');workbook.save(temporary);workbook.close();temporary.replace(destination)
    return len(data)
