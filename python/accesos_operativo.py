"""Distribución cifrada y almacenamiento DPAPI del acceso MAAT.

La clave de distribución acompaña al programa: dificulta la inspección casual,
pero no constituye una barrera frente al análisis del ejecutable.
"""
import json

def seal(access,key):
    from cryptography.fernet import Fernet
    return Fernet(key).encrypt(json.dumps(access,ensure_ascii=False).encode('utf-8'))

def unseal(token,key):
    from cryptography.fernet import Fernet
    return json.loads(Fernet(key).decrypt(token))

def install(root,bundle,config,bundled):
    payload=bundle/'acceso_maat.bin'
    if not payload.exists():return config
    revision=bundled.get('credentialRevision')
    if config.get('credentialRevision')==revision and (root/'.private/maat.json').exists():return config
    from _clave_operativa import PACKAGE_KEY
    from secretos_locales import save_credentials
    access=unseal(payload.read_bytes(),PACKAGE_KEY)
    save_credentials(root/'.private/maat.json',access['user'],access['password'])
    config.update(credentialRevision=revision,version=bundled['version'],maat_automatic=True)
    return config
