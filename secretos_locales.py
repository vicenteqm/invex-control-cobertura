"""Credenciales cifradas por Windows para la cuenta local; nunca se publican."""
import base64
import ctypes
import json
from ctypes import wintypes

class Blob(ctypes.Structure):
    _fields_=[('size',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_byte))]

def protect(data,decrypt=False):
    buffer=ctypes.create_string_buffer(data);source=Blob(len(data),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_byte)));output=Blob()
    crypt=ctypes.WinDLL('crypt32',use_last_error=True)
    function=crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    if not function(ctypes.byref(source),None,None,None,None,1,ctypes.byref(output)):raise ctypes.WinError(ctypes.get_last_error())
    try:return ctypes.string_at(output.data,output.size)
    finally:ctypes.WinDLL('kernel32',use_last_error=True).LocalFree(output.data)

def save_credentials(path,username,password):
    path.parent.mkdir(exist_ok=True)
    encrypted=protect(json.dumps([username,password]).encode('utf-8'))
    path.write_text(json.dumps({'encrypted':base64.b64encode(encrypted).decode('ascii')}),encoding='utf-8')

def read_credentials(path):return json.loads(protect(base64.b64decode(json.loads(path.read_text(encoding='utf-8'))['encrypted']),True).decode('utf-8'))
