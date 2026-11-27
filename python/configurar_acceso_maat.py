"""Entrada local enmascarada; no imprime ni registra credenciales."""
from pathlib import Path
import sys,json
import tkinter as tk
from tkinter import ttk,messagebox
from secretos_locales import read_credentials,save_credentials

ROOT=Path(__file__).resolve().parents[1]

def main():
    w=tk.Tk();w.title('INVEX · Actualizar acceso MAAT');w.geometry('520x300');w.resizable(False,False)
    box=ttk.Frame(w,padding=20);box.pack(fill='both',expand=True)
    ttk.Label(box,text='Nuevo acceso MAAT',font=('Calibri',17,'bold')).pack(anchor='w')
    ttk.Label(box,text='La contraseña se guardará cifrada en este equipo. No se mostrará en el chat.',wraplength=470).pack(anchor='w',pady=8)
    user=tk.StringVar();password=tk.StringVar();confirmation=tk.StringVar()
    try:user.set(read_credentials(ROOT/'.private/maat.json')[0])
    except Exception:pass
    for label,var,mask in [('Usuario / correo',user,False),('Nueva contraseña',password,True),('Confirmar contraseña',confirmation,True)]:
        row=ttk.Frame(box);row.pack(fill='x',pady=4)
        ttk.Label(row,text=label,width=22).pack(side='left')
        ttk.Entry(row,textvariable=var,show='*' if mask else '').pack(side='left',fill='x',expand=True)
    def save():
        if not user.get().strip() or not password.get():messagebox.showerror('INVEX','Completa el usuario y la contraseña.',parent=w);return
        if password.get()!=confirmation.get():messagebox.showerror('INVEX','Las contraseñas no coinciden.',parent=w);return
        save_credentials(ROOT/'.private/maat.json',user.get().strip(),password.get())
        if len(sys.argv)>1:
            (ROOT/'registros'/sys.argv[1]).write_text(json.dumps({'saved':True}),encoding='utf-8')
        password.set('');confirmation.set('');w.destroy()
    ttk.Button(box,text='Guardar acceso cifrado',command=save).pack(pady=12)
    w.mainloop()

if __name__=='__main__':main()
