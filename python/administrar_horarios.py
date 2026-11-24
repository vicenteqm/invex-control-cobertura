"""Administrador local de horarios INVEX. No expone un servidor ni editores web."""
import sys,json,threading,queue,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.build-deps'))
import tkinter as tk
from tkinter import ttk,messagebox
from ajustes_horarios import load,save,catalog,validate_schedule,recalculate_publish,BLOCKS

class Admin:
    def __init__(self,window):
        self.window=window;self.busy=False;self.events=queue.Queue();self.people=[];self.stores={}
        window.title('INVEX · Administración local de horarios');window.geometry('1200x800');window.minsize(950,650)
        style=ttk.Style();style.theme_use('clam');style.configure('Treeview',rowheight=30);style.configure('TButton',padding=9)
        tk.Label(window,text='INVEX  /  ADMINISTRACIÓN DE HORARIOS',bg='#111111',fg='white',font=('Calibri',20,'bold'),padx=20,pady=18,anchor='w').pack(fill='x')
        tools=ttk.Frame(window,padding=12);tools.pack(fill='x')
        self.buttons=[]
        self.button(tools,'Recargar fuentes',self.reload).pack(side='left')
        self.button(tools,'Recalcular y publicar en GitHub',self.publish).pack(side='right')
        self.status=tk.StringVar(value='Los ajustes se guardan solo en este equipo. Publica para reflejarlos en el tablero.')
        ttk.Label(window,textvariable=self.status,padding=10,wraplength=1100).pack(fill='x')
        self.progress=ttk.Progressbar(window,mode='indeterminate');self.progress.pack(fill='x',padx=12)
        tabs=ttk.Notebook(window);tabs.pack(fill='both',expand=True,padx=12,pady=12)
        self.staff=ttk.Frame(tabs,padding=10);self.vacancies=ttk.Frame(tabs,padding=10)
        tabs.add(self.staff,text='Personal · horario y jornada');tabs.add(self.vacancies,text='Tienda · metas y horarios buscados')
        self.search=tk.StringVar();ttk.Label(self.staff,text='Buscar persona, tienda o perfil').pack(anchor='w')
        ttk.Entry(self.staff,textvariable=self.search).pack(fill='x',pady=5);self.search.trace_add('write',lambda *_:self.render_people())
        box=ttk.Frame(self.staff);box.pack(fill='both',expand=True)
        columns=('store','name','role','journey','schedule','manual')
        self.table=ttk.Treeview(box,columns=columns,show='headings',height=10)
        for key,label,width in zip(columns,['Tienda','Persona','Perfil','Jornada','Horario efectivo','Ajuste local'],[95,230,190,155,245,90]):
            self.table.heading(key,text=label);self.table.column(key,width=width,stretch=False)
        y=ttk.Scrollbar(box,orient='vertical',command=self.table.yview);x=ttk.Scrollbar(box,orient='horizontal',command=self.table.xview)
        self.table.configure(yscrollcommand=y.set,xscrollcommand=x.set);self.table.grid(row=0,column=0,sticky='nsew');y.grid(row=0,column=1,sticky='ns');x.grid(row=1,column=0,sticky='ew');box.rowconfigure(0,weight=1);box.columnconfigure(0,weight=1)
        self.table.bind('<<TreeviewSelect>>',self.select_person)
        form=ttk.Frame(self.staff,padding=8);form.pack(fill='x')
        self.person_label=tk.StringVar(value='Selecciona una persona');ttk.Label(form,textvariable=self.person_label).grid(row=0,column=0,columnspan=4,sticky='w')
        self.schedule=tk.StringVar();self.journey=tk.StringVar()
        ttk.Label(form,text='Horario').grid(row=1,column=0,sticky='w');ttk.Entry(form,textvariable=self.schedule,width=40).grid(row=2,column=0,sticky='ew',padx=4)
        ttk.Label(form,text='Jornada').grid(row=1,column=1,sticky='w');ttk.Combobox(form,textvariable=self.journey,values=['TIEMPO COMPLETO','MEDIO TIEMPO','JORNADA REDUCIDA'],state='readonly',width=22).grid(row=2,column=1,padx=4)
        self.button(form,'Guardar persona',self.save_person).grid(row=2,column=2,padx=4)
        self.button(form,'Restaurar desde Excel',self.restore_person).grid(row=2,column=3,padx=4)
        ttk.Label(form,text='El horario del Excel original no se modifica. Un traslado de tienda no hereda el ajuste anterior.',wraplength=1000).grid(row=3,column=0,columnspan=4,sticky='w',pady=10)
        self.store=tk.StringVar();self.scope=tk.StringVar(value='General');self.scope_values={'General':'general','Sueldo base':'salary','Comisionistas':'commission'}
        ttk.Label(self.vacancies,text='Tienda').grid(row=0,column=0,sticky='w')
        self.store_select=ttk.Combobox(self.vacancies,textvariable=self.store,state='readonly',width=65);self.store_select.grid(row=1,column=0,columnspan=2,sticky='ew',pady=5)
        self.store_select.bind('<<ComboboxSelected>>',lambda _:self.select_store())
        ttk.Label(self.vacancies,text='Vista de cobertura').grid(row=0,column=2,sticky='w')
        scope_select=ttk.Combobox(self.vacancies,textvariable=self.scope,values=list(self.scope_values),state='readonly');scope_select.grid(row=1,column=2,padx=8);scope_select.bind('<<ComboboxSelected>>',lambda _:self.select_store())
        self.summary=tk.StringVar();ttk.Label(self.vacancies,textvariable=self.summary,wraplength=1000).grid(row=2,column=0,columnspan=3,sticky='w',pady=12)
        for col,label in enumerate(['Bloque','Meta de personas','Horario que se busca']):ttk.Label(self.vacancies,text=label).grid(row=3,column=col,sticky='w',padx=5)
        self.targets={};self.hours={}
        for row,block in enumerate(BLOCKS,4):
            self.targets[block]=tk.StringVar();self.hours[block]=tk.StringVar()
            ttk.Label(self.vacancies,text=block).grid(row=row,column=0,sticky='w',pady=8)
            ttk.Spinbox(self.vacancies,from_=0,to=100,textvariable=self.targets[block],width=12).grid(row=row,column=1,sticky='w')
            ttk.Entry(self.vacancies,textvariable=self.hours[block],width=48).grid(row=row,column=2,sticky='ew')
        self.button(self.vacancies,'Guardar metas y horarios',self.save_store).grid(row=7,column=1,pady=15)
        self.button(self.vacancies,'Restaurar regla automática',self.restore_store).grid(row=7,column=2,pady=15)
        ttk.Label(self.vacancies,text='Las tres metas deben sumar la plantilla requerida general. Primero se cubre tiempo completo. Si cambia la plantilla del Excel, se recupera la regla automática hasta revisar las metas guardadas.',wraplength=1000).grid(row=8,column=0,columnspan=3,sticky='w',pady=10)
        self.vacancies.columnconfigure(2,weight=1)
        window.protocol('WM_DELETE_WINDOW',self.close);window.after(100,self.poll);self.reload()

    def button(self,parent,text,command):
        b=ttk.Button(parent,text=text,command=command);self.buttons.append(b);return b

    def reload(self):
        if self.busy:return
        try:
            result,self.people=catalog();self.stores={s['id']:s for s in result['stores'] if s['status']=='OPERANDO'}
            self.store_labels={s['id']+' · '+s['name']:s['id'] for s in self.stores.values()}
            self.store_select['values']=sorted(self.store_labels)
            if self.store.get() not in self.store_labels and self.store_labels:self.store.set(sorted(self.store_labels)[0])
            self.render_people();self.select_store()
        except Exception as e:messagebox.showerror('No se pudieron leer las fuentes',str(e))

    def render_people(self):
        previous=self.table.selection();self.table.delete(*self.table.get_children());q=self.search.get().strip().upper()
        for p in self.people:
            if q and q not in ' '.join(str(p[x]) for x in ('name','store','role')).upper():continue
            self.table.insert('', 'end',iid=p['key'],values=[p['store'],p['name'],p['role'],p['journey'],p['schedule'],'Sí' if p['manual'] else 'No'])
        if previous and self.table.exists(previous[0]):self.table.selection_set(previous[0]);self.select_person()

    def person(self):
        selection=self.table.selection()
        if not selection:raise ValueError('Selecciona una persona')
        return next(p for p in self.people if p['key']==selection[0])

    def select_person(self,event=None):
        try:p=self.person()
        except ValueError:return
        self.person_label.set(p['name']+' · '+p['store']);self.schedule.set(p['schedule']);self.journey.set(p['journey'])

    def edited(self):
        self.reload();self.status.set('Cambios guardados en este equipo. Pulsa «Recalcular y publicar en GitHub» para compartirlos.')

    def save_person(self):
        if self.busy:return
        try:
            p=self.person();schedule=validate_schedule(self.schedule.get())
            if self.journey.get() not in ('TIEMPO COMPLETO','MEDIO TIEMPO','JORNADA REDUCIDA'):raise ValueError('Selecciona una jornada')
            data=load();data['people'][p['key']]={'store':p['store'],'schedule':schedule,'journey':self.journey.get()};save(data);self.edited()
        except Exception as e:messagebox.showerror('Revisar ajuste',str(e))

    def restore_person(self):
        if self.busy:return
        try:
            p=self.person();data=load();data['people'].pop(p['key'],None);save(data);self.edited()
        except Exception as e:messagebox.showerror('Revisar ajuste',str(e))

    def current_store(self):
        s=self.stores[self.store_labels[self.store.get()]];scope=self.scope_values[self.scope.get()]
        return s,scope,s if scope=='general' else {**s,**s['contracts'][scope]}

    def select_store(self):
        if not self.stores:return
        s,scope,current=self.current_store();shift=current['shiftCoverage']
        warning=current.get('scheduleOverrideWarning','')
        self.summary.set(f"Plantilla requerida: {s['required']} · Activos en esta vista: {current['active']} · Vacantes: {current['gap']} · "+('Ajuste local' if shift.get('manual') else 'Regla automática')+' '+warning)
        for block in BLOCKS:self.targets[block].set(str(shift['targets'].get(block,0)));self.hours[block].set(shift['hours'].get(block,''))

    def save_store(self):
        if self.busy:return
        try:
            s,scope,current=self.current_store();targets={b:int(self.targets[b].get()) for b in BLOCKS}
            if any(n<0 for n in targets.values()) or sum(targets.values())!=s['required']:raise ValueError('Las metas deben ser enteros no negativos y sumar '+str(s['required']))
            hours={}
            for b in BLOCKS:
                value=self.hours[b].get().strip()
                hours[b]=validate_schedule(value) if targets[b]>0 else value
            data=load();data['stores'].setdefault(s['id'],{})[scope]={'targets':targets,'hours':hours};save(data);self.edited()
        except Exception as e:messagebox.showerror('Revisar metas y horarios',str(e))

    def restore_store(self):
        if self.busy:return
        try:
            s,scope,_=self.current_store();data=load();data['stores'].get(s['id'],{}).pop(scope,None);save(data);self.edited()
        except Exception as e:messagebox.showerror('Revisar ajuste',str(e))

    def publish(self):
        if self.busy:return
        self.busy=True
        for b in self.buttons:b.state(['disabled'])
        self.progress.start();self.status.set('Recalculando horarios y publicando en GitHub. No se descargan MAAT ni Pandape…')
        def work():
            try:
                recalculate_publish();self.events.put((True,'Publicado en GitHub. La página se actualizará cuando termine el despliegue de Pages.'))
            except Exception as e:
                (ROOT/'registros').mkdir(exist_ok=True)
                (ROOT/'registros/administrar_horarios.log').write_text(traceback.format_exc(),encoding='utf-8')
                self.events.put((False,'No se completó la publicación: '+str(e)+'. Tus ajustes siguen guardados; puedes reintentar.'))
        threading.Thread(target=work,daemon=True).start()

    def poll(self):
        try:
            ok,message=self.events.get_nowait();self.busy=False;self.progress.stop()
            for b in self.buttons:b.state(['!disabled'])
            self.reload();self.status.set(message)
            if not ok:messagebox.showerror('Publicación pendiente',message)
        except queue.Empty:pass
        self.window.after(150,self.poll)

    def close(self):
        if self.busy:messagebox.showinfo('Proceso en curso','Espera a que termine la publicación.');return
        self.window.destroy()

if __name__=='__main__':
    window=tk.Tk();Admin(window);window.mainloop()
