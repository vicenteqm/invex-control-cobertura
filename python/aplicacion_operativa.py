"""Interfaz Windows del registro operativo INVEX."""
import argparse
import json
import queue
import shutil
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime
from operativo_portable import (initialize, local_folder, read_snapshot, refresh, login,
                                registration_view, people_rows, heatmap_tiles, INTERVAL_SECONDS, atomic_json)

PINK = '#ed2479'
STATUSES = {'COMPLETO': 'Ambos sistemas', 'SIN_REGISTRO_MAAT': 'Falta MAAT',
            'SIN_REGISTRO_PANDAPE': 'Falta Pandape', 'CRITICA': 'Sin registro'}
PEOPLE_STATUSES = {'COMPLETO': 'Ambos sistemas', 'SEGUIMIENTO_MAAT': 'Falta MAAT',
                   'ALERTA_PANDAPE': 'Falta Pandape', 'ALARMANTE': 'Sin registro'}


def pretty_date(value):
    try:return datetime.fromisoformat(value).strftime('%d/%m/%Y %H:%M')
    except (ValueError, TypeError):return 'Sin corte disponible'


class Application:
    def __init__(self, window, root, auto=True):
        self.window, self.root = window, root
        self.config = initialize(root)
        self.snapshot = read_snapshot(root)
        if self.snapshot:self.snapshot.setdefault('period',self.config['period'])
        self.events = queue.Queue()
        self.busy = False
        self.next_update = time.monotonic() + INTERVAL_SECONDS
        self.store_export, self.people_export = [], []
        window.title('INVEX · Registro Pandape / MAAT · 1.5')
        window.geometry('1280x820');window.minsize(850, 560);window.configure(bg='#111111')
        style = ttk.Style();style.theme_use('clam')
        style.configure('.', font=('Calibri', 11))
        style.configure('TFrame', background='#f6f6f7')
        style.configure('TLabel', background='#f6f6f7', foreground='#171717')
        style.configure('TButton', padding=(14, 9))
        style.configure('Accent.TButton', background=PINK, foreground='white')
        style.map('Accent.TButton', background=[('active', '#c71c62')])
        style.configure('Treeview', rowheight=30, background='white', fieldbackground='white')
        style.configure('Treeview.Heading', background='#161616', foreground='white', font=('Calibri', 10, 'bold'))
        style.map('Treeview.Heading', background=[('active', '#333333')])
        header = tk.Frame(window, bg='#111111', padx=18, pady=8);header.pack(fill='x')
        tk.Label(header, text='INVEX', font=('Calibri', 24, 'bold'), fg='white', bg='#111111').pack(side='left')
        tk.Label(header, text='PANDAPE / MAAT', font=('Calibri', 12), fg='#ff8bb9', bg='#111111').pack(side='left', padx=20)
        outer=ttk.Frame(window);outer.pack(fill='both',expand=True)
        self.body_canvas=tk.Canvas(outer,bg='#f6f6f7',highlightthickness=0)
        outer_scroll=ttk.Scrollbar(outer,orient='vertical',command=self.body_canvas.yview)
        outer_horizontal=ttk.Scrollbar(outer,orient='horizontal',command=self.body_canvas.xview)
        self.body_canvas.configure(yscrollcommand=outer_scroll.set,xscrollcommand=outer_horizontal.set)
        self.body_canvas.grid(row=0,column=0,sticky='nsew');outer_scroll.grid(row=0,column=1,sticky='ns');outer_horizontal.grid(row=1,column=0,sticky='ew')
        outer.rowconfigure(0,weight=1);outer.columnconfigure(0,weight=1)
        body=ttk.Frame(self.body_canvas,padding=12)
        self.body_item=self.body_canvas.create_window((0,0),window=body,anchor='nw')
        body.bind('<Configure>',lambda event:self.body_canvas.configure(scrollregion=self.body_canvas.bbox('all')))
        self.body_canvas.bind('<Configure>',lambda event:self.body_canvas.itemconfigure(self.body_item,width=max(event.width,body.winfo_reqwidth(),980)))
        bar = ttk.Frame(body);bar.pack(fill='x')
        self.update_button = ttk.Button(bar, text='Actualizar ahora', style='Accent.TButton', command=self.update);self.update_button.pack(side='left')
        self.login_button = ttk.Button(bar, text='Actualizar Pandape', command=self.open_login);self.login_button.pack(side='left', padx=8)
        self.sources_button = ttk.Button(bar, text='Fuentes', command=self.sources);self.sources_button.pack(side='left')
        self.auto = tk.BooleanVar(value=auto)
        ttk.Checkbutton(bar, text='Actualizar cada 15 minutos', variable=self.auto).pack(side='right')
        self.progress = ttk.Progressbar(body, maximum=100);self.progress.pack(fill='x', pady=(12, 4))
        self.status = ttk.Label(body, text='Listo para actualizar',wraplength=1100);self.status.pack(anchor='w')
        self.cut = ttk.Label(body, text='',wraplength=1100);self.cut.pack(anchor='w', pady=(3, 0))
        self.next_label = ttk.Label(body);self.next_label.pack(anchor='w', pady=(0, 8))
        filters = ttk.Frame(body);filters.pack(fill='x', pady=6)
        self.filters = {}
        for col, (key, title, width) in enumerate([('day', 'Día de registro', 15), ('region', 'Región', 20), ('executive', 'CÉLULA / Ejecutiva RH', 23), ('partner', 'Socio', 13)]):
            frame = ttk.Frame(filters);frame.grid(row=0, column=col, sticky='ew', padx=(0, 10))
            ttk.Label(frame, text=title).pack(anchor='w')
            box = ttk.Combobox(frame, state='readonly', width=width);box.pack(fill='x')
            box.bind('<<ComboboxSelected>>', lambda event:self.draw())
            self.filters[key] = box
        filters.columnconfigure(4, weight=1)
        search = ttk.Frame(filters);search.grid(row=0, column=4, sticky='ew')
        ttk.Label(search, text='Buscar tienda o persona').pack(anchor='w')
        self.query = tk.StringVar();entry = ttk.Entry(search, textvariable=self.query);entry.pack(fill='x')
        self.query.trace_add('write', lambda *args:self.draw())
        ttk.Button(search,text='Limpiar filtros',command=self.clear_filters).pack(anchor='e',pady=(5,0))
        cards = ttk.Frame(body);cards.pack(fill='x', pady=12)
        self.kpis = []
        for i, title in enumerate(['Registrados en Pandape', 'Registrados en MAAT', 'Completos en ambos', 'Sin registro en ambos']):
            card = tk.Frame(cards, bg='white', highlightbackground='#e3e3e6', highlightthickness=1, padx=15, pady=10)
            card.grid(row=0, column=i, sticky='nsew', padx=(0, 8));cards.columnconfigure(i, weight=1)
            label = tk.Label(card, text='—', bg='white', fg=PINK, font=('Calibri', 25, 'bold'));label.pack(anchor='w')
            tk.Label(card, text=title, bg='white', fg='#333333', font=('Calibri', 11)).pack(anchor='w')
            self.kpis.append(label)
        self.note = ttk.Label(body, text='', wraplength=1180);self.note.pack(anchor='w', pady=(0, 8))
        workspace=ttk.Frame(body,height=440);workspace.pack(fill='both',expand=True);workspace.pack_propagate(False)
        navigation=tk.Frame(workspace,bg='#161616',width=176,padx=8,pady=8);navigation.pack(side='left',fill='y',padx=(0,10));navigation.pack_propagate(False)
        tk.Label(navigation,text='CONSULTAS',bg='#161616',fg='#ff8bb9',font=('Calibri',11,'bold')).pack(anchor='w',padx=8,pady=(0,10))
        self.page_host=ttk.Frame(workspace);self.page_host.pack(side='left',fill='both',expand=True)
        self.pages={};self.nav_buttons={};self.map_frames={};self.active_page=None
        def page(key,title):
            frame=ttk.Frame(self.page_host,padding=4);self.pages[key]=frame
            button=tk.Button(navigation,text=title,anchor='w',wraplength=150,bg='#252525',fg='white',activebackground='#ed2479',activeforeground='white',relief='flat',font=('Calibri',12),padx=10,pady=12,command=lambda:self.show_page(key))
            button.pack(fill='x',pady=4);self.nav_buttons[key]=button;return frame
        self.tables = []
        self.headers = [
            ['Tienda', 'Nombre', 'Región', 'CÉLULA / Ejecutiva RH', 'Activos', 'Pandape', 'MAAT', 'Ambos', 'Sin registro', 'Entraron a cubrir', 'Salieron a cubrir', 'Estatus', 'Retardos', 'Salidas anticipadas'],
            ['Nombre', 'Puesto', 'Tienda', 'Región', 'Pandape entrada', 'Pandape salida', 'MAAT entrada', 'MAAT salida', 'Estatus', 'Destino MAAT', 'Observaciones']]
        for i, title in enumerate(['Registro por tienda', 'Detalle por persona']):
            frame=page('table'+str(i),title)
            ttk.Button(frame, text='Descargar Excel', command=lambda index=i:self.export(index)).pack(anchor='e', pady=(0, 6))
            table_frame = ttk.Frame(frame);table_frame.pack(fill='both', expand=True)
            tree = ttk.Treeview(table_frame, columns=list(range(len(self.headers[i]))), show='headings', selectmode='browse')
            for c, name in enumerate(self.headers[i]):
                tree.heading(c, text=name);tree.column(c, width=190 if c in (0,1,3) else 125, minwidth=65)
            vertical = ttk.Scrollbar(table_frame, orient='vertical', command=tree.yview)
            horizontal = ttk.Scrollbar(table_frame, orient='horizontal', command=tree.xview)
            tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
            tree.grid(row=0, column=0, sticky='nsew');vertical.grid(row=0, column=1, sticky='ns');horizontal.grid(row=1, column=0, sticky='ew')
            table_frame.rowconfigure(0, weight=1);table_frame.columnconfigure(0, weight=1)
            tree.tag_configure('pending', background='#fff0f5');self.tables.append(tree)
        for system in ['MAAT','Pandape']:
            frame=page('map'+system,'Mapa '+system)
            ttk.Label(frame,text='Registro '+system+' por tienda',font=('Calibri',17,'bold')).pack(anchor='w',pady=(0,5))
            ttk.Label(frame,text='Personas únicas del día / plantilla requerida. Verde: completa; amarillo: 50% o más; rojo: menos de 50%.',wraplength=900).pack(anchor='w',pady=(0,7))
            holder=ttk.Frame(frame);holder.pack(fill='both',expand=True)
            canvas=tk.Canvas(holder,bg='#f6f6f7',highlightthickness=0)
            scroll=ttk.Scrollbar(holder,orient='vertical',command=canvas.yview);canvas.configure(yscrollcommand=scroll.set)
            canvas.pack(side='left',fill='both',expand=True);scroll.pack(side='right',fill='y')
            inner=ttk.Frame(canvas);item=canvas.create_window((0,0),window=inner,anchor='nw')
            inner.bind('<Configure>',lambda event,c=canvas:c.configure(scrollregion=c.bbox('all')))
            def resize(event,c=canvas,item=item):c.itemconfigure(item,width=event.width)
            canvas.bind('<Configure>',resize)
            self.map_frames[system]=(canvas,inner)
        self.window.bind_all('<MouseWheel>',self.scroll_wheel,add='+')
        self.window.bind_all('<Shift-MouseWheel>',self.scroll_horizontal,add='+')
        self.window.bind('<Next>',lambda event:self.body_canvas.yview_scroll(1,'pages'))
        self.window.bind('<Prior>',lambda event:self.body_canvas.yview_scroll(-1,'pages'))
        self.show_page('table0')
        self.load_filters();self.draw()
        window.after(100, self.poll);window.after(1000, self.tick)
        if auto:window.after(1200, self.update)

    def load_filters(self):
        if not self.snapshot:return
        s = self.snapshot
        days = sorted(set(s.get('maatDays', []) + s.get('attendanceDays', [])))
        box = self.filters['day'];old = box.get();box['values'] = [s['period']+'-'+str(d).zfill(2) for d in days]
        latest=box['values'][-1] if days else ''
        box.set(latest if not old or old==getattr(self,'latest_day',None) else old if old in box['values'] else latest)
        self.latest_day=latest
        for key, field in [('region', 'region'), ('executive', 'executive')]:
            box = self.filters[key];old = box.get()
            box['values'] = ['Todas'] + sorted({str(t.get(field) or 'Sin asignar') for t in s['stores']})
            box.set(old if old in box['values'] else 'Todas')

        box=self.filters['partner'];old=box.get();box['values']=['Todos','WALMART','SAMS','CHEDRAUI','OTROS'];box.set(old if old in box['values'] else 'Todos')

    def clear_filters(self):
        self.filters['region'].set('Todas');self.filters['executive'].set('Todas');self.filters['partner'].set('Todos');self.query.set('');self.draw()

    def show_page(self,key):
        for frame in self.pages.values():frame.pack_forget()
        self.pages[key].pack(fill='both',expand=True);self.active_page=key
        for name,button in self.nav_buttons.items():button.configure(bg=PINK if name==key else '#252525')
        if key.startswith('map'):self.window.after_idle(self.draw_maps)

    def scroll_wheel(self,event):
        widget=self.window.winfo_containing(event.x_root,event.y_root)
        ancestor=widget
        while ancestor and ancestor!=self.window:
            if isinstance(ancestor,ttk.Treeview):return
            ancestor=getattr(ancestor,'master',None)
        units=-int(event.delta/120) or (-1 if event.delta>0 else 1)
        if self.active_page and self.active_page.startswith('map'):
            canvas,inner=self.map_frames[self.active_page[3:]]
            ancestor=widget;inside=False
            while ancestor and ancestor!=self.window:
                if ancestor==canvas:inside=True;break
                ancestor=getattr(ancestor,'master',None)
            first,last=canvas.yview()
            if inside and ((units>0 and last<.999) or (units<0 and first>.001)):
                canvas.yview_scroll(units,'units');return 'break'
        self.body_canvas.yview_scroll(units,'units');return 'break'

    def scroll_horizontal(self,event):
        units=-int(event.delta/120) or (-1 if event.delta>0 else 1)
        if self.active_page and self.active_page.startswith('table'):
            self.tables[int(self.active_page[-1])].xview_scroll(units,'units')
        else:self.body_canvas.xview_scroll(units,'units')
        return 'break'

    def select_store(self,key):
        self.query.set(key);self.show_page('table0')

    def draw_maps(self):
        if not self.snapshot or not self.filters['day'].get():return
        region=self.filters['region'].get();executive=self.filters['executive'].get()
        stores,_,_,_=registration_view(self.snapshot,int(self.filters['day'].get()[-2:]),'' if region=='Todas' else region,'' if executive=='Todas' else executive)
        stores=self.filter_partner(stores)
        query=self.query.get().strip().casefold()
        if query:stores=[s for s in stores if query in (s['id']+' '+s['name']).casefold()]
        colors={'full':'#daf0d6','partial':'#fff0bb','low':'#ffd6db','unknown':'#e7e7eb'}
        for system,(canvas,inner) in self.map_frames.items():
            for widget in inner.winfo_children():widget.destroy()
            tiles=heatmap_tiles(self.snapshot,stores,int(self.filters['day'].get()[-2:]),system)
            if not tiles:ttk.Label(inner,text='Sin tiendas para los filtros seleccionados.').pack(anchor='w',pady=15)
            for prefix,title in [('SAMS','SAMS'),('WM','WALMART'),('CH','CHEDRAUI'),('OTROS','OTROS SOCIOS')]:
                selected=[t for t in tiles if (t['store']['id'].split(' ')[0]==prefix if prefix!='OTROS' else t['store']['id'].split(' ')[0] not in ('SAMS','WM','CH'))]
                if not selected:continue
                ttk.Label(inner,text=title,font=('Calibri',15,'bold')).pack(anchor='w',pady=(16,7),padx=6)
                grid=ttk.Frame(inner);grid.pack(fill='x',padx=4)
                columns=max(2,min(5,max(1,canvas.winfo_width())//210))
                for i,t in enumerate(selected):
                    s=t['store'];card=tk.Frame(grid,bg=colors[t['level']],padx=10,pady=8,cursor='hand2');card.grid(row=i//columns,column=i%columns,sticky='nsew',padx=4,pady=4);grid.columnconfigure(i%columns,weight=1)
                    text=[(s['id'],11,'bold'),(s['name'],11,'normal'),('Sin evaluar' if t['percentage'] is None else f"{t['percentage']:.1f}%",18,'bold'),('Sin datos / sin plantilla' if t['count'] is None else str(t['count'])+' de '+str(t['required'])+' registraron',10,'normal')]
                    for value,size,weight in text:
                        label=tk.Label(card,text=value,bg=colors[t['level']],fg='#222222',font=('Calibri',size,weight),wraplength=190,anchor='w',justify='left',cursor='hand2');label.pack(anchor='w');label.bind('<Button-1>',lambda event,key=s['id']:self.select_store(key))
                    card.bind('<Button-1>',lambda event,key=s['id']:self.select_store(key))
            canvas.configure(scrollregion=canvas.bbox('all'))

    def filter_partner(self,stores):
        selected=self.filters['partner'].get();prefix={'WALMART':'WM','SAMS':'SAMS','CHEDRAUI':'CH'}.get(selected)
        return [s for s in stores if not selected or selected=='Todos' or (s['id'].split(' ')[0]==prefix if prefix else s['id'].split(' ')[0] not in ('WM','SAMS','CH'))]

    def draw(self):
        if not self.snapshot or not self.filters['day'].get():return
        month = self.snapshot;day = int(self.filters['day'].get()[-2:])
        region = self.filters['region'].get();executive = self.filters['executive'].get()
        stores, _, p, m = registration_view(month, day, '' if region=='Todas' else region, '' if executive=='Todas' else executive)
        stores=self.filter_partner(stores)
        totals={key:sum(s.get('registration',{}).get(str(day),{}).get('cohort',{}).get(key,0) for s in stores) if m else 0 for key in ['total','pandape','maat','both','none']}
        sources=month.get('sourceFreshness',{})
        if sources:
            maat_date=pretty_date(sources.get('maat',{}).get('updatedAt'))
            p_source=sources.get('pandape',{});p_date=pretty_date(p_source.get('updatedAt'))
            self.cut.configure(text='Día consultado: '+self.filters['day'].get()+'  ·  MAAT actualizado: '+maat_date+'  ·  Pandape: '+p_date+(' · pendiente de actualizar' if p_source.get('status')!='ok' else ''))
        else:self.cut.configure(text='Último corte validado: '+pretty_date(month.get('processedAt'))+'  ·  Día consultado: '+self.filters['day'].get())
        for i, key in enumerate(['pandape', 'maat', 'both', 'none']):
            self.kpis[i].configure(text=str(totals[key])+' / '+str(totals['total']) if (m if key=='maat' else p) else '—')
        self.note.configure(text=('Una persona se cuenta una vez por día; las salidas y regresos del descanso no duplican el registro. '+str(len(stores))+' tiendas filtradas.') if p else 'Cruce sin evaluar: falta captura del día en '+('Pandape.' if m else 'MAAT. Se conserva el último corte validado.'))
        self.store_export = []
        query = self.query.get().strip().casefold()
        for s in stores:
            if query and query not in (s['id']+' '+s['name']).casefold():continue
            r = s.get('registration', {}).get(str(day), {})
            self.store_export.append([s['id'],s['name'],s.get('region',''),s.get('executive',''),r.get('population',0),r.get('pandape',0) if p else '—',r.get('maat',0) if m else '—',r.get('both',0) if p else '—',r.get('none',0) if p else '—',r.get('incoming',0) if m else '—',r.get('movedOut',0) if m else '—',STATUSES.get(r.get('status'),'Sin datos') if p else 'Sin evaluar',r.get('late',0) if m else '—',r.get('earlyDeparture',0) if m else '—'])
        self.people_export = []
        for s, person, r in people_rows(month, stores, day):
            if query and query not in (str(person['nombre'])+' '+s['id']+' '+s['name']).casefold():continue
            notices = []
            if r.get('llego_tarde'):notices.append('Retardo')
            if r.get('salio_antes_de_horario'):notices.append('Salida anticipada')
            if r.get('cerro_jornada_manual'):notices.append('Cierre manual')
            self.people_export.append([person['nombre'],person.get('puesto',''),s['id'],s.get('region',''),(r.get('hora_entrada_pandape') or '—') if p else 'Sin evaluar',(r.get('hora_salida_pandape') or '—') if p else 'Sin evaluar',r.get('hora_entrada_maat') or '—',r.get('hora_salida_maat') or '—',PEOPLE_STATUSES.get(r.get('estatus_registro'),'Sin datos') if p else 'Sin evaluar',r.get('tienda_maat') or '',', '.join(notices)])
        for table, rows in zip(self.tables, [self.store_export, self.people_export]):
            table.delete(*table.get_children())
            for row in rows:table.insert('', 'end', values=row)
        self.draw_maps()

    def export(self, index):
        rows = [self.store_export, self.people_export][index]
        filename = filedialog.asksaveasfilename(parent=self.window, defaultextension='.xlsx', filetypes=[('Excel','*.xlsx')], initialfile='INVEX_Registro_'+self.filters['day'].get()+'.xlsx')
        if not filename:return
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Alignment, Font, PatternFill
            book = Workbook();sheet = book.active;sheet.title = 'Registro'
            sheet.append(self.headers[index])
            for row in rows:sheet.append(row)
            for row in sheet:
                for cell in row:
                    cell.font = Font(name='Calibri', size=9, color='FFFFFF' if cell.row==1 else '000000', bold=cell.row==1)
                    cell.fill = PatternFill('solid', fgColor='000000' if cell.row==1 else 'FFFFFF')
                    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            for column in sheet.columns:sheet.column_dimensions[column[0].column_letter].width=24
            sheet.freeze_panes='A2';sheet.auto_filter.ref=sheet.dimensions;book.save(filename);book.close()
            self.status.configure(text='Excel guardado correctamente')
        except Exception:messagebox.showerror('INVEX','No se pudo guardar el Excel. Comprueba que no esté abierto y que la carpeta permita escritura.')

    def set_busy(self, busy):
        self.busy = busy
        for button in [self.update_button,self.login_button,self.sources_button]:button.configure(state='disabled' if busy else 'normal')

    def update(self,interactive=False):
        if self.busy:return
        self.set_busy(True);self.progress['value']=0
        self.started = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        self.status.configure(text='Iniciando actualización · '+self.started)
        def worker():
            try:
                result=refresh(self.root,self.config,lambda n,text:self.events.put(('progress',n,text)),interactive_pandape=interactive)
                self.events.put(('success',result))
            except Exception as error:
                import traceback
                atomic_json(self.root/'datos/ultimo-error-proceso.json',{'at':datetime.now().isoformat(),'type':type(error).__name__,'trace':traceback.format_exc()})
                text=str(error)
                kind='session' if ('PANDAPE_SESSION_REQUIRED' in text or ('Pandape:' in text and ('403' in text or 'CAPTCHA' in text))) else 'month' if 'MONTH_REQUIRED' in text else 'maat' if 'MAAT_DOWNLOAD_FAILED' in text else 'error'
                self.events.put((kind,type(error).__name__))
        threading.Thread(target=worker,daemon=True).start()

    def open_login(self):
        self.update(interactive=True)

    def sources(self):
        dialog=tk.Toplevel(self.window);dialog.title('INVEX · Fuentes locales');dialog.geometry('570x230')
        ttk.Label(dialog,text='Carga una fuente cuando recibas una plantilla o base nueva.',wraplength=530).pack(padx=18,pady=12)
        ttk.Label(dialog,text='Periodo de asistencia: '+self.config['period']).pack()
        def choose(kind):
            selected=filedialog.askopenfilename(parent=dialog,filetypes=[('Excel','*.xlsx')])
            if not selected:return
            from actualizar import generate
            from cobertura_actual import local_now
            period=local_now().strftime('%Y-%m') if kind=='asistencia' else self.config['period']
            try:
                source=Path(selected)
                generate(source if kind=='base' else self.root/'fuentes/base.xlsx', source if kind=='asistencia' else self.root/'fuentes/asistencia.xlsx',period)
                target=self.root/'fuentes'/(kind+'.xlsx');shutil.copyfile(source,target)
                if kind=='asistencia':self.config['period']=period;atomic_json(self.root/'config.json',self.config)
                self.status.configure(text='Fuente validada. Pulsa Actualizar ahora para recalcular.');dialog.destroy()
            except Exception:messagebox.showerror('INVEX','La fuente no es válida. Revisa el tipo de archivo, el mes y los encabezados.',parent=dialog)
        ttk.Button(dialog,text='Cargar asistencia',command=lambda:choose('asistencia')).pack(pady=8)
        ttk.Button(dialog,text='Cargar base de tiendas',command=lambda:choose('base')).pack()

    def poll(self):
        while not self.events.empty():
            event=self.events.get();kind=event[0]
            if kind=='progress':self.progress['value']=event[1];self.status.configure(text=event[2]+' · Inició '+self.started);continue
            self.set_busy(False);self.next_update=time.monotonic()+INTERVAL_SECONDS
            if kind=='success':
                self.snapshot=event[1];self.load_filters();self.draw();self.progress['value']=100
                self.status.configure(text=('MAAT actualizado. Pandape pendiente: pulsa Actualizar Pandape e inicia sesión en Edge. MAAT seguirá actualizándose cada 15 minutos.' if self.snapshot.get('partialUpdate') else 'Actualización completada')+' · '+datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
            elif kind=='login':self.status.configure(text='Sesión Pandape guardada en este equipo');self.window.after(200,self.update)
            elif kind=='session':
                self.status.configure(text='Pandape requiere atención: completa el ingreso cuando esté disponible. La actualización de MAAT continúa cada 15 minutos.')
            elif kind=='month':self.status.configure(text='Carga la asistencia del mes actual desde Fuentes. Se conserva el corte anterior.')
            elif kind=='maat':self.status.configure(text='No se pudo descargar MAAT. Revisa Internet y el acceso de servicio. Se conserva el corte anterior.')
            else:self.status.configure(text='No se completó la actualización ('+event[1]+'). Consulta datos/ultimo-error-proceso.json en la carpeta local de la aplicación. Se conserva el corte anterior.')
        self.window.after(150,self.poll)

    def tick(self):
        left=max(0,int(self.next_update-time.monotonic()))
        self.next_label.configure(text='Actualización en proceso' if self.busy else 'Próxima actualización en '+str(left//60).zfill(2)+':'+str(left%60).zfill(2) if self.auto.get() else 'Actualización automática pausada')
        if not self.busy and self.auto.get() and left==0:self.update()
        self.window.after(1000,self.tick)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--autoprueba',type=Path);parser.add_argument('--datos',type=Path);parser.add_argument('--comprobar-maat',type=Path);parser.add_argument('--comprobar-pandape',type=Path);parser.add_argument('--sin-actualizar',action='store_true')
    args=parser.parse_args();root=args.datos or local_folder()
    if args.comprobar_pandape:
        config=initialize(root)
        from operativo_portable import access_config
        from descarga_pandape import download
        try:
            download(access_config(root,config),root);outcome={'ok':True}
        except Exception as error:
            import traceback
            outcome={'ok':False,'type':type(error).__name__,'trace':traceback.format_exc()}
        atomic_json(args.comprobar_pandape,outcome);return
    if args.comprobar_maat:
        initialize(root)
        from descarga_asistencia import download
        from secretos_locales import read_credentials
        from cobertura_actual import local_now
        try:
            credentials=read_credentials(root/'.private/maat.json')
            result=download(root/'datos/prueba_maat.csv',local_now().strftime('%Y-%m'),*credentials)
            outcome={'ok':True,'records':result[0]}
        except Exception as error:
            import traceback
            outcome={'ok':False,'type':type(error).__name__,'http':getattr(getattr(error,'response',None),'status_code',None),'trace':traceback.format_exc()}
        atomic_json(args.comprobar_maat,outcome);return
    root.mkdir(parents=True,exist_ok=True)
    import msvcrt
    lock=(root/'aplicacion.lock').open('a+b');lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0)
    try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    except OSError:
        messagebox.showinfo('INVEX','La aplicación ya está abierta en este equipo.');return
    window=tk.Tk();app=Application(window,root,auto=not bool(args.autoprueba) and not args.sin_actualizar)
    if args.autoprueba:
        def check():
            try:
                assert app.snapshot and len(app.tables)==2
                assert len(app.pages)==4 and set(app.map_frames)=={'MAAT','Pandape'}
                assert len(app.tables[0].get_children())==len(app.store_export)
                assert app.window.winfo_width()>=850
                window.geometry('1000x620');window.update_idletasks()
                assert app.body_canvas.yview()[1]<1,'Falta desplazamiento general en ventana pequeña'
                app.body_canvas.yview_moveto(1);window.update_idletasks()
                assert app.body_canvas.yview()[0]>0
                app.body_canvas.yview_moveto(0)
                app.show_page('mapMAAT');window.update_idletasks();app.draw_maps()
                assert app.map_frames['MAAT'][1].winfo_children()
                app.show_page('mapPandape');window.update_idletasks()
                app.clear_filters();app.show_page('table0')
                atomic_json(args.autoprueba,dict(ok=True,period=app.snapshot['period'],stores=len(app.store_export),people=len(app.people_export),intervalSeconds=INTERVAL_SECONDS,maps=list(app.map_frames)))
            finally:window.destroy()
        window.after(800,check)
    window.mainloop()


if __name__=='__main__':
    try:main()
    except Exception:
        messagebox.showerror('INVEX','No se pudo abrir la aplicación. Extrae el archivo completo y comprueba los permisos de tu usuario.')
        raise
