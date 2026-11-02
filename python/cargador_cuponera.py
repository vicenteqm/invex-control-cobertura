"""Compatibilidad del acceso anterior: abre el tablero para generar imágenes locales."""
from pathlib import Path
import webbrowser
ROOT=Path(__file__).resolve().parents[1]
def main(open_browser=True,port=None):
    url=(ROOT/'sitio'/'index.html').as_uri()+'#productividad'
    print('Carga de cuponera solo para imágenes. Selecciona el archivo en el apartado del cuadro comparativo. No se publica la carga.',flush=True)
    if open_browser:webbrowser.open(url)
    return 0
if __name__=='__main__':raise SystemExit(main())
