# Horas productivas Walmart

La sección está dentro de la misma página, después de Cobertura. Presenta volumen diario, distribución por franja horaria, diez tiendas con mayor volumen y un mapa de actividad por día y hora. Incluye filtros de fechas, región y tienda. Los números son trámites, no horas trabajadas ni duración de los trámites.

## Actualización

`python/procesar_cobertura.py` lee la carpeta indicada por `productive_hours_folder` en `configuracion/config.local.json`. En este equipo se configuró la carpeta HORAS PRODUCTIVAS WM proporcionada por el usuario. El archivo original no se modifica ni se sube a GitHub; solo se publican conteos por tienda, día y hora.

Guarda los cambios del Excel en esa carpeta y ejecuta ACTUALIZAR_INVEX.bat. El proceso actualiza también estas gráficas cuando completa la actualización. Para recalcular con las fuentes locales sin iniciar MAAT/Pandape puedes usar `python python/procesar_cobertura.py --sin-descarga`; esta opción sigue la selección de asistencia local que ya utiliza el proceso.

En otro equipo la carpeta predeterminada es `inputs/fuentes/horas_productivas/`. También puedes configurar una ruta propia.

## Archivo mensual

Se buscan archivos `Horas Productivas*.xlsx` y se elige el más reciente que tenga hojas del periodo configurado. Por ejemplo, para octubre de 2026 las hojas deben llamarse `2026-10-01`, `2026-10-02`, etc. En noviembre puede guardarse `Horas Productivas Noviembre.xlsx` en la misma carpeta, con las hojas `2026-11-DD`. El periodo de todo el tablero se cambia explícitamente junto con las fuentes mensuales de plantilla y asistencia; esta integración no lo cambia automáticamente.

El calendario siempre muestra desde el día 1 hasta el último del mes (28, 29, 30 o 31). Los días sin hoja aparecen como Sin datos; los ceros reportados se conservan como ceros. La pantalla muestra la última hoja disponible y la fecha de modificación del archivo.

## Cálculo y validaciones

Cada hoja diaria contiene DETERMINANTE, SEDE, intervalos `HH:00 - HH:59` y TOTAL_TRAMITES. Se validan cantidades enteras no negativas, tiendas no repetidas por día y concordancia entre columnas horarias y totales. La fila TOTAL se verifica pero no se suma como una tienda. GENERAL y HORAS PICO no se agregan otra vez. El resumen GENERAL se contrasta con los días; si difiere, se advierte y se usan las hojas diarias.

Se identifica cada determinante como WM y se toma su región de la base de tiendas. El universo de productividad es el del Excel: no se excluyen automáticamente tiendas por el estatus de cobertura, para conservar la concordancia con la fuente. Las gráficas explican ese universo.

Si falta el archivo del periodo o no puede validarse, la sección muestra el problema y no presenta los datos de otro mes como actuales. El resto del tablero puede procesarse normalmente.

## Records y aprobaciones
Coloca el CSV records_report_YYYYMMDD_YYYYMMDD.csv en inputs/fuentes/records. El ejecutor selecciona el más reciente del periodo y lo usa para ambas series, con prioridad sobre el Excel de horas. No suma varios exports superpuestos. Cuenta cada fila de módulo Walmart por F. Creación, y separa Aprobada de Aprobada con Garantía. La página permite incluir las de garantía. La línea muestra el resultado actual agrupado por fecha de creación, no por fecha de aprobación. El último día puede estar incompleto. Solo se publican agregados por tienda/día/hora; el archivo original permanece local. Para refrescar, reemplaza el CSV por una exportación mensual completa y ejecuta el actualizador. No se ha agregado una descarga automática de este reporte.
