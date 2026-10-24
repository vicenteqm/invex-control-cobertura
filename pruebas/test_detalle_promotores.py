import sys
import unittest
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'python'),str(Path(__file__).resolve().parents[1]/'.build-deps')]
from detalle_promotores import export_attendance,attach_excel_detail,rows,public_detail


class ExpandedExcelTests(unittest.TestCase):
    def test_active_variants_are_included_only_in_export_copy(self):
        statuses=['ACTIVO','ACTIVO/TEAM','ACTIVO/SWAT','ACTIVO/COMODIN','ACTIVO COMODIN','BAJA','PENDIENTE']
        source=[[None]*23 for _ in range(len(statuses)+1)]
        for row,status in zip(source[1:],statuses):row[10]=status
        expanded=export_attendance(source)
        self.assertEqual([r[10] for r in source[1:]],statuses)
        self.assertEqual([r[10] for r in expanded[1:]],['ACTIVO']*5+['BAJA','PENDIENTE'])

    def test_excel_uses_expanded_population_once_without_changing_kpis(self):
        def person(name,role):return {'nombre':name,'puesto':role,'registro_por_dia':{'23':{'registra_pandape':True,'registra_maat':True,'estatus_registro':'COMPLETO'}}}
        promoter=person('Prueba promotor','PROMOTOR DE CREDITO')
        team=person('Prueba team','TEAM LIDER');swat=person('Prueba swat','LIDER SWAT')
        raw={'meta':{'period':'2026-10','reference_day':23,'maat_cargado':True},'stores':{'WM 1':{'info':{},'empleados_activos':[promoter],'dias':{'23':{'presentes':1}},'externos_maat':[]}}}
        expanded={'stores':{'WM 1':{'empleados_activos':[promoter,team,swat],'externos_maat':[]}}}
        attach_excel_detail(raw,expanded)
        exported=rows(raw,23)
        self.assertEqual(len(exported),3)
        self.assertEqual([r[2] for r in exported],['PROMOTOR DE CREDITO','TEAM LIDER','LIDER SWAT'])
        self.assertEqual(len(raw['stores']['WM 1']['empleados_activos']),1)
        self.assertEqual(raw['stores']['WM 1']['dias']['23']['presentes'],1)
        public=public_detail(raw)['stores']['WM 1']
        self.assertEqual(len(public['personal_excel']),3)
        self.assertEqual(len(public['empleados_activos']),1)
        raw['meta']['attendance_days']=[22]
        exported=rows(raw,23)
        self.assertTrue(all(row[12]=='Sin evaluar' and row[18]=='Sin evaluar' for row in exported))
        self.assertTrue(all(row[15]=='Sí' for row in exported))
