import sys
import unittest
from pathlib import Path
from datetime import date
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'.build-deps'))
from descarga_pandape import prepare_export_dates


class Element:
    def __init__(self,value='',kind='hidden',visible=False,click=None):
        self.value=value;self.kind=kind;self.visible=visible;self.action=click
    def is_displayed(self):return self.visible
    def is_enabled(self):return True
    def get_attribute(self,key):return self.value if key=='value' else self.kind if key=='type' else None
    def click(self):
        if self.action:self.action()
    def clear(self):
        if self.kind=='hidden':raise AssertionError('No se debe escribir en un campo oculto')
        self.value=''
    def send_keys(self,value):
        if self.kind=='hidden':raise AssertionError('No se debe escribir en un campo oculto')
        if value!='\ue004':self.value+=value


class DateExportTests(unittest.TestCase):
    def driver(self,kind='hidden',value='2026-11-17'):
        dialog=Element(visible=False);fields={key:Element(value,kind,kind!='hidden') for key in ['date-start','date-end']}
        button=Element(visible=True,click=lambda:setattr(dialog,'visible',True))
        def find(by,key):return [dialog] if key=='ExportReportPopup' else [button] if key=='exportButton' else [fields[key]] if key in fields else []
        return SimpleNamespace(find_elements=find),fields,dialog
    def test_new_hidden_iso_dates_are_valid_without_typing(self):
        driver,fields,dialog=self.driver()
        prepare_export_dates(driver,date(2026,11,17),1)
        self.assertTrue(dialog.visible);self.assertEqual(fields['date-end'].value,'2026-11-17')
    def test_old_visible_text_dates_still_work(self):
        driver,fields,_=self.driver('text','16/11/2026')
        prepare_export_dates(driver,date(2026,11,17),1)
        self.assertEqual(fields['date-start'].value,'17/11/2026')
    def test_hidden_other_date_is_selected_through_calendar_button(self):
        driver,fields,_=self.driver(value='2026-11-16');original=driver.find_elements
        def find(by,key):
            if by=='css selector':
                field='date-start' if 'date-start' in key else 'date-end'
                if '[data-date=' in key:return [Element(visible=True,click=lambda:setattr(fields[field],'value','2026-11-17'))]
                return [Element(visible=True)]
            return original(by,key)
        driver.find_elements=find
        prepare_export_dates(driver,date(2026,11,17),1)
        self.assertEqual(fields['date-end'].value,'2026-11-17')
    def test_initial_previous_month_advances_before_selecting_day(self):
        driver,fields,_=self.driver(value='2026-10-17');original=driver.find_elements
        months={'date-start':'octubre','date-end':'octubre'};moves=[]
        def find(by,key):
            if by!='css selector':return original(by,key)
            field='date-start' if 'date-start' in key else 'date-end'
            if '.dp-title' in key:return [SimpleNamespace(is_displayed=lambda:True,text=months[field])]
            if '.dp-next' in key:
                def move():months[field]='noviembre';moves.append(field)
                return [Element(visible=True,click=move)]
            if '[data-date=' in key:
                if months[field]!='noviembre':return []
                return [Element(visible=True,click=lambda:setattr(fields[field],'value','2026-11-17'))]
            return [Element(visible=True)]
        driver.find_elements=find
        prepare_export_dates(driver,date(2026,11,17),1)
        self.assertEqual(moves,['date-start','date-end'])
        self.assertTrue(all(e.value=='2026-11-17' for e in fields.values()))
