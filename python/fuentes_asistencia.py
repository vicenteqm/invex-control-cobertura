"""Valida que la asistencia generada corresponda a la fuente vigente."""
import hashlib
import json


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_generated(config, source, generated):
    if not generated.exists():
        return False
    if not config.get('attendance_linked_roster'):
        return generated.stat().st_mtime > source.stat().st_mtime
    marker = generated.with_suffix('.fuente.json')
    if not marker.exists():
        return False
    return json.loads(marker.read_text(encoding='utf-8')).get('sha256') == fingerprint(source)


def mark_source(source, generated):
    generated.with_suffix('.fuente.json').write_text(json.dumps({'sha256': fingerprint(source), 'source': source.name}), encoding='utf-8')
