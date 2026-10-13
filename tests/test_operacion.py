import unittest
import importar_operacion as module

class HistoricalTests(unittest.TestCase):
    def payload(self):
        return {'2026-09':{'meta':{'reference_day':30,'days_in_month':31},'stores':{'WM 1':{'info':{'tienda_nombre':'Tienda','estatus':'OPERANDO','ejecutiva':'Ejecutiva prueba'},'dias':{'1':{'cobertura_pct':50,'semaforo':'RIESGO','presentes':2,'turnos':[{'empleado':'Dato privado'}]},'31':{'cobertura_pct':0,'semaforo':'ALARMANTE'}},'empleados_activos':[{'nombre':'Dato privado','registro_por_dia':{'1':{'usuario':'privado','registra_maat':True}}}]}}}}
    def test_whitelist_and_calendar(self):
        result=module.sanitize_months(self.payload())
        month=result['2026-09']
        self.assertEqual(month['daysInMonth'],30)
        self.assertEqual(len(month['stores'][0]['days']),1)
        self.assertEqual(month['stores'][0]['days'][0]['semaphore'],'RIESGO')
        for text in ['Dato privado','registro_por_dia','registra_maat','turnos']:
            self.assertNotIn(text,str(result))
    def test_script_is_not_executed(self):
        parser=module.EmbeddedMonths()
        parser.feed('<script>alert("no ejecutar")</script><script id="meses-data" type="application/json">{"ok":1}</script>')
        self.assertEqual(''.join(parser.parts),'{"ok":1}')
    def test_invalid_cutoff(self):
        payload=self.payload();payload['2026-09']['meta']['reference_day']=31
        with self.assertRaises(ValueError):module.sanitize_months(payload)

if __name__ == '__main__':unittest.main()
