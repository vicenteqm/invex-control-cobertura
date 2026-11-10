"""Puestos que integran la plantilla operativa de cobertura."""
import unicodedata


def profile(value):
    text = ''.join(c for c in unicodedata.normalize('NFKD', str(value or '').upper()) if not unicodedata.combining(c))
    text = ' '.join(text.split()).replace('COMICIONISTA', 'COMISIONISTA').replace('PRONOTOR', 'PROMOTOR')
    if text in ('PROMOTOR DE CREDITO', 'PROMOTOR COMISIONISTA'):
        return 'promotor'
    if text in ('SUBLIDER', 'SUBLIDER COMISIONISTA'):
        return 'sublider'
    return None
