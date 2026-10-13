import unittest
from registro_maat import aggregate,coverage_category

class RegistrationTests(unittest.TestCase):
    def test_categories_and_transfer_do_not_duplicate_cohort(self):
        def employee(p,m,target=None):return {'registro_por_dia':{'1':{'registra_pandape':p,'registra_maat':m,'se_movio_de_tienda':bool(target),'tienda_maat_key':target,'hora_entrada_maat':'10:00' if m else None,'hora_salida_maat':'20:00' if m else None}}}
        raw={'stores':{'A':{'close':1200,'empleados_activos':[employee(True,True,'B'),employee(True,False),employee(False,True),employee(False,False)],'externos_maat':[]},'B':{'close':1200,'empleados_activos':[],'externos_maat':[]}}}
        r=aggregate(raw,1,{1});a=r['A']['1'];b=r['B']['1']
        self.assertEqual(a['cohort'],dict(total=4,pandape=2,maat=2,both=1,none=1))
        self.assertEqual(b['cohort']['total'],0);self.assertEqual(b['incoming'],1);self.assertEqual(b['both'],1)
        self.assertEqual(b['status'],'COMPLETO');self.assertEqual(b['scheduleCoverage'],'CUBIERTA_TODO_EL_DIA')
    def test_original_schedule_categories(self):
        self.assertEqual(coverage_category(None,None,1200),'SIN_COBERTURA')
        self.assertEqual(coverage_category(720,1200,1200),'SOLO_TARDE')
        self.assertEqual(coverage_category(600,1100,1200),'PERDIO_COBERTURA_TARDE')
        self.assertEqual(coverage_category(600,1170,1200),'CUBIERTA_TODO_EL_DIA')
        self.assertEqual(coverage_category(600,1170,'20:00'),'CUBIERTA_TODO_EL_DIA')
