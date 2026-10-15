"""Migra una instalación anterior a carpetas con nombres en español."""
import json
from pathlib import Path

CAMBIOS={'inputs':'datos','logs':'registros','site':'sitio','tests':'pruebas','docs':'documentacion','previews':'vistas_previas'}

def organizar(root):
    root=Path(root).resolve()
    for viejo,nuevo in CAMBIOS.items():
        origen=(root/viejo).resolve();destino=(root/nuevo).resolve()
        if origen.parent!=root or destino.parent!=root:raise ValueError('Destino fuera del proyecto')
        if origen.is_dir():
            if destino.exists():raise ValueError('Existen ambas carpetas '+viejo+' y '+nuevo+'. Revisa su contenido antes de migrar.')
            origen.rename(destino)
    path=root/'configuracion'/'config.local.json'
    if path.exists():
        config=json.loads(path.read_text(encoding='utf-8'))
        for key,value in list(config.items()):
            if not isinstance(value,str):continue
            for viejo,nuevo in CAMBIOS.items():
                if value.startswith(viejo+'/'):value=nuevo+value[len(viejo):]
                old=(root/viejo).as_posix()+'/'
                if value.replace('\\','/').startswith(old):value=(root/nuevo).as_posix()+'/'+value.replace('\\','/')[len(old):]
            config[key]=value
        temporary=path.with_suffix('.tmp.json');temporary.write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8');temporary.replace(path)
    for name in ['datos/fuentes/bpi','datos/descargas/records','resultados/horas_productivas','registros']:
        (root/name).mkdir(parents=True,exist_ok=True)

if __name__=='__main__':organizar(Path(__file__).resolve().parents[1])
