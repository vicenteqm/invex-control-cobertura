"""Records → correcciones de tiendas → BPI → Excel mensual para el tablero."""
import calendar
import json
import logging
import shutil
import tempfile
from datetime import datetime,timedelta,timezone
from pathlib import Path

MODULOS={
    'MODULO BETTER HOUSE CH ACAPULCO CENTRO':'265',
    'MODULO BETTER HOUSE CH FRESNILLO':'123',
    'MODULO BETTER HOUSE GALERIAS ZACATECAS MAAT 2.0':'25',
    'MODULO BETTER NUEVO LAREDO HIPODROMO':'110',
    'MODULO BH CH TUXTLA CRYSTAL 013':'13',
    'MODULO BH SC HAROLD MONCLOVA 1007':'1007',
}
MESES=('Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre')

def rango_mes(ahora=None):
    zona=timezone(timedelta(hours=-6))
    hoy=(ahora or datetime.now(zona)).astimezone(zona).date()
    return hoy.replace(day=1),hoy.replace(day=calendar.monthrange(hoy.year,hoy.month)[1])

def ultima_bpi(carpeta):
    files=[p for p in Path(carpeta).glob('*.xlsx') if p.is_file() and not p.name.startswith('~$')]
    if not files:raise ValueError('Coloca la BPI actualizada (.xlsx con hoja PROIND) en datos/fuentes/bpi y vuelve a ejecutar ACTUALIZAR_INVEX.bat')
    return max(files,key=lambda p:(p.stat().st_mtime_ns,p.name))

def validar_bpi(path):
    import pandas as pd
    for sheet,required in [(0,{'FOLIO','EJECUTIVO P','ESTATUS BANCO','DETERMINANTE','SEDE'}),('PROIND',{'NOMBRE','PROMOTOR'})]:
        columns={str(c).strip() for c in pd.read_excel(path,sheet_name=sheet,nrows=0).columns}
        missing=required-columns
        if missing:raise ValueError('BPI: faltan columnas en '+str(sheet)+': '+', '.join(sorted(missing)))

def corregir_records(origen,destino):
    from generar_horas_productivas import leer_records,normalizar
    tabla=leer_records(origen)
    if len(tabla.columns)<4 or normalizar(tabla.columns[2])!='LUGAR DE VENTA' or normalizar(tabla.columns[3])!='SEGUNDO LUGAR DE VENTA':
        raise ValueError('Records: las columnas C y D no son Lugar de venta y Segundo lugar de venta')
    columnas=list(tabla.columns);modulos=tabla.iloc[:,2].map(normalizar)
    mascara=modulos.isin(MODULOS)
    tabla.loc[mascara,columnas[3]]=modulos[mascara].map(MODULOS)
    # El filtro anterior era de revisión; no eliminaba las filas de las demás tiendas.
    tabla.to_csv(destino,index=False,encoding='utf-8-sig')
    return {'filas':len(tabla),'correcciones':int(mascara.sum()),'porModulo':{k:int(modulos.eq(k).sum()) for k in MODULOS}}

def ejecutar(config,root,ahora=None,descargar=None):
    from generar_horas_productivas import generar
    from horas_productivas import read_productivity
    inicio,fin=rango_mes(ahora);period=inicio.strftime('%Y-%m')
    if config.get('period')!=period:
        raise ValueError('El mes de ejecución es '+period+' pero cobertura está configurada para '+str(config.get('period'))+'. Actualiza el periodo y los Excel mensuales antes de publicar; no se mezclarán meses.')
    carpeta=root/'datos'/'fuentes'/'bpi';carpeta.mkdir(parents=True,exist_ok=True)
    bpi=ultima_bpi(carpeta);validar_bpi(bpi)
    logging.info('Horas productivas: BPI seleccionada automáticamente: %s',bpi.name)
    if descargar is None:
        from descargar_records import descargar
    records=descargar(config,root,inicio,fin)
    destino=root/'resultados'/'horas_productivas'/str(inicio.year);destino.mkdir(parents=True,exist_ok=True)
    final=destino/('Horas Productivas '+MESES[inicio.month-1]+'.xlsx')
    with tempfile.TemporaryDirectory(prefix='preparacion_',dir=destino) as temporal:
        temporal=Path(temporal);corregido=temporal/'Records_corregido.csv'
        cambios=corregir_records(records,corregido)
        logging.info('Records: %s filas conservadas; %s determinantes corregidas',cambios['filas'],cambios['correcciones'])
        preparado=temporal/'Horas Productivas.xlsx'
        generar(bpi,corregido,preparado,inicio,fin)
        resultado=read_productivity(preparado,period,[])
        if resultado.get('status')!='available':raise ValueError('El reporte no contiene horas productivas del mes de ejecución')
        if any(s.get('matches') is False for s in resultado.get('sheets',[])):raise ValueError('Los resúmenes de horas productivas no coinciden con el detalle; se conserva el Excel anterior')
        archivo_corregido=records.parent/'Records_corregido.csv'
        shutil.copy2(corregido,archivo_corregido)
        try:preparado.replace(final)
        except PermissionError:
            final=destino/(final.stem+'_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f')+final.suffix)
            preparado.replace(final)
            logging.warning('El reporte anterior está abierto en Excel; se guardó una nueva versión: %s',final.name)
    config['productive_hours_folder']=str(destino.relative_to(root))
    config['productive_hours_pattern']=final.name
    estado={'periodo':period,'inicio':inicio.isoformat(),'fin':fin.isoformat(),'bpi':bpi.name,'records':str(records.relative_to(root)),'reporte':str(final.relative_to(root)),**cambios,'ingresos':resultado['total']}
    registros=root/'registros';registros.mkdir(exist_ok=True)
    (registros/'horas-productivas.json').write_text(json.dumps(estado,ensure_ascii=False,indent=2),encoding='utf-8')
    logging.info('Horas productivas generadas y verificadas: %s',final.name)
    return final
