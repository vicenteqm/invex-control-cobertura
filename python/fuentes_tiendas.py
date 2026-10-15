"""Importa una base validada y sincroniza futuras ediciones del mismo archivo."""
from pathlib import Path
import shutil
import openpyxl
from actualizar import columns,required

BASE_HEADERS=['SOCIO','NUMERO DE TIENDA/DETERMINANTE','TIENDA','REGION','CIUDAD','ESTADO','ESTATUS','PROMOTORES REQUERIDOS','SUBLIDER']

def is_base(path):
    book=openpyxl.load_workbook(path,read_only=True,data_only=True)
    try:
        _,headers=columns(book.active)
        return all(k in headers for k in BASE_HEADERS)
    finally:book.close()

def sync_base(config,root,source=None):
    selected=source or config.get('base_source_file')
    if not selected:return None
    path=Path(selected)
    if not path.is_absolute():path=root/path
    if not path.is_file():raise ValueError('No se encuentra la base de tiendas vinculada: '+str(path)+'. Vuelve a seleccionarla con ACTUALIZAR_BASE_TIENDAS.bat.')
    if not is_base(path):raise ValueError('El archivo seleccionado no tiene las columnas de la base de tiendas INVEX')
    folder=root/'datos'/'fuentes'/'base_tiendas';folder.mkdir(parents=True,exist_ok=True)
    target=folder/'BASE_TIENDAS_ACTUAL.xlsx'
    if path.resolve()!=target.resolve():
        temporary=target.with_suffix('.tmp.xlsx')
        try:shutil.copy2(path,temporary);temporary.replace(target)
        finally:
            if temporary.exists():temporary.unlink()
    if source:
        config['base_source_file']=str(path.resolve()) if path.resolve()!=target.resolve() else str(target.relative_to(root))
        config['base_folder']='datos/fuentes/base_tiendas';config['base_pattern']=target.name
    return target
