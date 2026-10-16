"""Accesos portables en JSON legible, sin cifrado ligado a Windows."""
import json
import os
from pathlib import Path

def leer_maat(config,root):
    manual=config.get('maat_manual_login',False)
    usuario=os.environ.get('MAAT_USER');clave=os.environ.get('MAAT_PASSWORD')
    if not manual and (not usuario or not clave):
        ruta=Path(root)/'configuracion'/'accesos.json'
        if ruta.exists():
            try:
                datos=json.loads(ruta.read_text(encoding='utf-8-sig'))
                maat=datos.get('maat',{})
                usuario=usuario or maat.get('usuario');clave=clave or maat.get('contrasena')
            except (ValueError,AttributeError):raise ValueError('Revisa el formato de configuracion/accesos.json') from None
    if not manual and (not isinstance(usuario,str) or not usuario.strip() or not isinstance(clave,str) or not clave):
        raise ValueError('Completa usuario y contrasena de MAAT en configuracion/accesos.json o en MAAT_USER y MAAT_PASSWORD')
    return usuario,clave,manual

def preparar(root):
    ruta=Path(root)/'configuracion'/'accesos.json'
    ruta.parent.mkdir(parents=True,exist_ok=True)
    if not ruta.exists():ruta.write_text(json.dumps({'maat':{'usuario':'','contrasena':''}},ensure_ascii=False,indent=2),encoding='utf-8')
    return ruta
