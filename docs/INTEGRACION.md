# Integración del tablero anterior

Actualización: el mes actual ahora se calcula desde los Excel mediante `procesar_cobertura.py` y el motor original. Pandape/MAAT ya está activado con descarga automática. La importación del HTML descrita abajo se conserva únicamente para meses históricos. Consulta [SISTEMA_HORARIO.md](SISTEMA_HORARIO.md) para el flujo actual.

El módulo Seguimiento operativo añade únicamente funciones complementarias, en la misma página y con el diseño de INVEX:

- Alertas operativas por ejecutiva y semáforo del día.
- Reincidencias, días rojos y riesgo por falta de usuario.
- Calendario mensual por tienda y comparativo de semáforos entre tiendas.
- Tendencia mensual y ranking de ejecutivas y tiendas.
- Movimientos históricos: altas, bajas y rotación del origen.
- Identificación histórica de tiendas sin sublíder asignado.

Los KPI actuales, la tabla de plantilla, los filtros y la asistencia siguen en sus secciones originales. No se incluye otro tablero completo ni un iframe. El sistema actual incorpora el cruce Pandape/MAAT, cambios de tienda, checadas y huecos horarios calculados por el motor.

## Origen y fechas

`control-cobertura.html` contiene capturas de agosto, septiembre y octubre de 2026. La captura de octubre tiene corte operativo al día 8 y un universo diferente al de los Excel actuales. El módulo muestra ese corte, identifica los datos como históricos y conserva las clasificaciones calculadas por el tablero anterior. No aplica esas clasificaciones a los datos actuales ni mezcla ambos universos.

Se conservan los nombres de las ejecutivas para agrupar la gestión. Los nombres y registros individuales de promotores, usuarios, teléfonos y datos MAAT no se exportan. El HTML original solo se lee para extraer el bloque JSON `meses-data`; su JavaScript no se ejecuta ni se copia.

El calendario usa el número real de días de cada mes; corrige la metadata del origen que indicaba 31 días para septiembre. Un día fuera del corte aparece sin captura, no como una falta o alerta nueva.

La tendencia diaria es el promedio simple de cobertura entre tiendas con datos. El promedio mensual, los días rojos, las reincidencias y la rotación son valores del origen, no un nuevo cálculo basado en los Excel actuales. Los filtros se aplican a todos los contenidos del módulo; el filtro de semáforo elige las tiendas según el día operativo seleccionado.

## Actualización mediante Python

Para importar únicamente el histórico:

```powershell
python python/importar_operacion.py --tablero "C:/ruta/control-cobertura.html"
```

Para procesar los Excel y volver a importar el tablero en una sola ejecución:

```powershell
python python/actualizar.py --base "C:/ruta/base.xlsx" --asistencia "C:/ruta/asistencia.xlsx" --periodo 2026-10 --tablero "C:/ruta/control-cobertura.html"
```

`--tablero` es opcional. Sin ese argumento, se actualizan los datos actuales y se conserva la captura histórica anterior. El histórico se refresca únicamente al importar un HTML con datos nuevos. `--publicar` envía ambos archivos de datos mediante Git autenticado; no necesita incluir el HTML original de 25 MB en el repositorio.

## Tablas de horarios en Cobertura

Al final de Cobertura se muestran faltantes por bloque y tienda a la izquierda, y personal activo agrupado por el texto HORARIO a la derecha. Ambas consultas permiten buscar tienda y filtrar región; el selector de bloque filtra solamente los faltantes.

`python/turnos_cobertura.py` reproduce las medidas DAX: metas estándar para plantilla requerida entre 1 y 13 (apertura redondea hacia arriba y cierre hacia abajo), clasificación CONTAINSSTRING de todo el texto HORARIO con prioridad 14:00/15:00/13:00 para Cierre y luego 10:00/11:00/09:00 para Apertura. Los demás horarios son Intermedio / Atípico. Se utiliza la misma población elegible y el mismo faltante por tienda/perfil de los KPI.

El reparto se limita al faltante global y favorece Cierre cuando los huecos empatan. Si la suma de huecos es inferior al faltante global, la diferencia queda sin asignación y se informa en la tabla. No se fuerza a un turno. PLANTILLA BETTER corresponde a la plantilla requerida del tablero.

Excepciones confirmadas: WM 5296, apertura 10:00–16:00 y cierre 13:00–19:00; SAMS 4968, ambos bloques 11:00–20:00. Solo modifican los textos horarios; no se proporcionaron metas especiales. El usuario confirmó que no se agregan otras excepciones por ahora. El ejecutor regenera los datos de estas tablas en cada actualización válida.
