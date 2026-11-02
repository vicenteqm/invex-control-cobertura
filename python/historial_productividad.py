"""Conserva los agregados publicados de cada mes sin cambiar sus metadatos."""
import json


def preserve(path, current):
    history = {}
    if path.exists():
        previous = json.loads(path.read_text(encoding='utf-8').split('=', 1)[1].strip().removesuffix(';'))
        history.update(previous.get('productiveHoursHistory', {}))
        source = previous.get('productiveHours', {})
        if source.get('status') == 'available':
            history[source['period']] = source
    if current.get('status') == 'available':
        history[current['period']] = current
    return history
