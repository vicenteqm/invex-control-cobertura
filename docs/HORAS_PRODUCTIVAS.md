# Horas productivas Walmart y SAMS

Guarda el Excel en productive_hours_folder de configuracion/config.local.json y ejecuta ACTUALIZAR_INVEX.bat. El procesador lo integra al completar la actualización; --sin-descarga recalcula con las fuentes locales siguiendo las reglas de asistencia existentes. El periodo se cambia explícitamente junto con las fuentes mensuales.

## Prioridad de fuentes

El Excel Horas Productivas*.xlsx más reciente del periodo tiene prioridad sobre el CSV records. DETALLE aporta los folios únicos, ingresos y estados. GENERAL, las hojas diarias YYYY-MM-DD y HORAS PICO validan los conteos; no se suman de nuevo. La tabla Hojas del Excel muestra la validación del archivo completo, independientemente de los filtros. Las notas al pie no se interpretan como registros ni instrucciones.

Cadena y determinante identifican la tienda: WM 123 y SAMS 123 son unidades distintas. La región procede de la base de tiendas. El universo conserva las tiendas de la fuente independientemente de su estatus de cobertura.

## Indicadores

- Ingresos: un folio de DETALLE, agrupado por fecha y hora de creación.
- Aprobada y Aprobada con Garantía: categorías independientes de Aprobación.
- Aprobadas finalizadas: aprobada o con garantía y proceso Finalizado. Es un subconjunto, no un ingreso adicional.
- Conversión a finalizada: aprobadas finalizadas / ingresos.
- Aprobación, proceso y banco: distribuciones independientes del mismo universo; no se suman entre sí.

Las gráficas por día, hora y tienda combinan ingresos en barras con las aprobadas seleccionadas en línea. Fecha, cadena, región y tienda filtran los indicadores, gráficos, estados y detalle por tienda. El calendario muestra todo el mes y distingue las fechas sin datos. El corte es la última fecha real de creación; una nota con un periodo posterior no extiende el corte. Los estados se agrupan por creación, no por fecha de aprobación.

## Actualización y privacidad

En este equipo la carpeta configurada es HORAS PRODUCTIVAS WM indicada por el usuario. En otro equipo, la predeterminada es inputs/fuentes/horas_productivas. Guarda el Excel mensual actualizado y ejecuta el actualizador. No se modifica el archivo original. Solo se publican conteos por tienda, día, hora y estado; folios, ejecutivos, clientes y el Excel permanecen locales.

El formato anterior sin DETALLE conserva la lectura de hojas diarias con DETERMINANTE, SEDE, horas y TOTAL_TRAMITES. Si no hay Excel del periodo, se usa como respaldo el CSV inputs/fuentes/records/records_report_YYYYMMDD_YYYYMMDD.csv para Walmart. No se mezclan ambas fuentes. El CSV de respaldo no se descarga automáticamente.
