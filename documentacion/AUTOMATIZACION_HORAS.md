# Horas productivas automáticas

1. Guarda la BPI actualizada `.xlsx` en `datos/fuentes/bpi/`. Debe incluir la hoja principal y PROIND. Se elige por fecha de modificación; no se usan los archivos temporales `~$` de Excel.
2. Abre `ACTUALIZAR_INVEX.bat`. Si el reporte mensual está abierto en Excel, el ejecutor guarda una versión con fecha y hora y usa esa versión para publicar, sin cerrar el archivo que estás consultando.
3. El ejecutor descarga la asistencia diaria MAAT y los fichajes Pandape. Reutiliza la sesión de Pandape; si venció, espera el ingreso manual.
4. En Edge visible abre `https://invex.maatai.com/admin/records/recordreportoptimized/`, inicia sesión con el acceso local de MAAT y descarga desde el primer hasta el último día del mes de ejecución (Ciudad de México). No solicita fechas.
5. Conserva la descarga original y crea Records_corregido.csv aplicando estas coincidencias exactas, normalizadas por espacios, acentos y mayúsculas:

| Columna C: Lugar de venta | Columna D: Segundo lugar de venta |
| --- | --- |
| MODULO BETTER HOUSE CH ACAPULCO CENTRO | 265 |
| MODULO BETTER HOUSE CH FRESNILLO | 123 |
| MODULO BETTER HOUSE GALERIAS ZACATECAS MAAT 2.0 | 25 |
| MODULO BETTER NUEVO LAREDO HIPODROMO | 110 |
| MODULO BH CH TUXTLA CRYSTAL 013 | 13 |
| MODULO BH SC HAROLD MONCLOVA 1007 | 1007 |

Las demás filas se conservan. El filtrado sirve para localizar módulos, no para eliminar las otras tiendas. El cruce de horas conserva la lógica del proyecto original: FOLIO de BPI contra Folio FICO de Records; tienda y ejecutivo desde la BPI; primera fecha de creación y estado más reciente de Records; únicamente Walmart y Sam's. Las correcciones D permanecen disponibles en la copia de Records para otros cruces.

6. Genera GENERAL, las hojas diarias con registros, HORAS PICO y DETALLE, con encabezados negros, texto blanco, cuerpo blanco y negro, Calibri 9 y celdas centradas.
7. Verifica que los resúmenes coincidan con DETALLE y guarda `resultados/horas_productivas/AAAA/Horas Productivas Mes.xlsx`. El mismo mes se reemplaza; los años quedan separados. El rango solicitado incluye el mes completo, pero el reporte contiene únicamente registros disponibles.
8. Actualiza el tablero y publica los agregados en GitHub. Las fuentes BPI, Records, Excel generado, credenciales y registros de ejecución quedan locales.

Un fallo de descarga, BPI inválida, falta de coincidencias o diferencias entre resúmenes impide sustituir el reporte y publicar datos parciales. Al cambiar de mes, el rango de Records cambia automáticamente; el periodo de cobertura y sus fuentes mensuales deben corresponder a ese mes. El proceso lo comprueba antes de descargar.

Los ejecutores individuales de asistencias, tiendas y horas productivas mantienen su selector y no vuelven a descargar fuentes.

## Carpetas del proyecto

Los módulos están en `python/`, los Excel y descargas en `datos/`, los reportes en `resultados/`, la página en `sitio/`, los manuales en `documentacion/`, las pruebas en `pruebas/`, los eventos en `registros/` y las capturas locales en `vistas_previas/`. Los accesos `.bat` siguen en la raíz.
