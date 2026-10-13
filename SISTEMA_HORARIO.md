# Sistema operativo integrado

`procesar_cobertura.py` reemplaza el procesador anterior. Lee `config.local.json`, descarga MAAT, sustituye los registros de las fechas descargadas en el concentrado mensual, procesa los Excel con `engine.py` y genera ambos archivos de datos del panel. Conserva los demás meses históricos.

```powershell
python procesar_cobertura.py
```

`--sin-descarga` permite procesar únicamente los archivos locales. No activa MAAT si no existe un concentrado. Las dependencias son openpyxl, requests y Selenium, además de Chrome para Pandape. MAAT usa sesión HTTP con CSRF. Pandape conserva los filtros de equipo y grupo del descargador recibido y solicita el reporte del día actual.

## Flujo de Pandape replicado desde cob.zip

`descarga_pandape.py` descarga el reporte en una carpeta nueva por ejecución y espera a que termine la descarga. `generar_asistencia.py` replica en Python la macro CRUCE del libro original: consolida las tres parejas de entradas/salidas, obtiene la primera entrada y última salida por nombre y cruza los nombres sin depender del orden de sus palabras, mayúsculas o acentos. Se actualizan los colaboradores ACTIVO y PENDIENTE del día actual.

Se conserva la regla original de retardo: el minuto de entrada entre 05 y 15 genera R; otras entradas generan A. Sin horas, se evalúa D o F según el descanso oficial. Los colaboradores sin coincidencia conservan la etiqueta original `no encontrado`, que no debe interpretarse automáticamente como falta. Las capturas V e I se conservan. La columna de descanso se busca por encabezado, corrigiendo la referencia incorrecta a antigüedad en la macro; la columna de cruce se reutiliza en lugar de duplicarse cada hora.

La asistencia generada queda en `inputs/asistencias/ASISTENCIA_INVEX_AAAA-MM.xlsx`. Se parte del Excel de la carpeta configurada o de la asistencia generada, según cuál tenga la modificación más reciente. Así se conserva el acumulado y se pueden incorporar cambios de plantilla del Excel fuente. Los archivos originales permanecen intactos. No se necesita Excel instalado ni habilitar VBA; se conserva el XLSM original en `inputs/pandape/` como referencia local.

Si falla Pandape o la generación, el proceso se detiene y conserva el tablero anterior. La configuración `download_pandape` activa este paso. Las credenciales se obtienen de PANDAPE_USER/PANDAPE_PASSWORD o de `.private/pandape.json`, cifrado para la cuenta de Windows. El diagnóstico local está en `inputs/pandape/diagnostico.json` y su captura de pantalla en la misma carpeta; ambos se excluyen de publicación.

Prueba real del 13 de octubre de 2026: el acceso de Chrome automático recibió `403 Forbidden` antes del formulario de autenticación. El navegador integrado sí mostró el formulario. La descarga automática de Pandape todavía no está operativa; requiere resolver el acceso admitido por el servicio. No se modifica la seguridad ni se simula una descarga exitosa. Para procesar un reporte auténtico del día descargado desde el navegador se puede ejecutar `python procesar_cobertura.py --reporte-pandape "ruta/Reportede.xlsx"`. Esta opción también ejecuta MAAT y actualiza el tablero si todas las validaciones pasan. No usar reportes de días anteriores con esta opción.

## Funciones del motor original

Se conserva el motor recibido: presencia por entrada/salida, cobertura frente a plantilla autorizada, usuarios activos, semáforos, descansos oficiales, turnos aún no iniciados, huecos de cobertura, altas, bajas, rotación, reincidencias, Pandape/MAAT por día, cambio de tienda, cobertura externa, cierre manual, entrada tardía y salida anticipada. La interfaz consulta agregados por tienda; los registros nominales no se publican.
El detalle nominal completo del último cálculo queda en `inputs/analisis_actual.json`, disponible para revisión local y excluido de Git. Los intervalos se recortan al horario de apertura y cierre para evitar duraciones negativas fuera de ese rango.
Si MAAT contiene un día que aún no está capturado en el Excel, se muestran únicamente sus registros y el cruce de Pandape permanece sin evaluar. No se convierte ausencia de datos en falta de registro.
El motor original considera estatus ACTIVO para sus indicadores operativos; los KPI de plantilla existentes conservan su definición de promotores y sublíderes elegibles. El nombre completo de las ejecutivas se conserva para agrupar la gestión.

El adaptador identifica columnas por encabezados y luego entrega al motor su esquema original; una columna obligatoria ausente detiene la generación. Usa los días reales del mes y la zona America/Mexico_City. La regla de hora de corte se aplica únicamente cuando el día de asistencia corresponde a hoy. Un corte histórico no se recalcula como si su turno empezara en la hora actual. Los días sin captura global se excluyen de la tendencia y días rojos.

## Fuentes y credenciales

Las carpetas y el periodo están en `config.local.json`, excluido de Git. Los Excel originales permanecen intactos. Los CSV de MAAT se guardan en `inputs/`, también excluido. Se aplican los mismos nueve mapeos de puntos de venta del descargador original. Las fechas se normalizan antes de sustituir registros, evitando duplicados por formatos DD/MM/AAAA y AAAA-MM-DD.

Las credenciales de MAAT se leen desde MAAT_USER y MAAT_PASSWORD, o desde `.private/maat.json`, cifrado por Windows para la cuenta local. No hay contraseñas ni tokens GitHub escritos en el código nuevo. La publicación utiliza Git autenticado, solo si `publish` está activado. Está activada en la configuración local y el remoto es `vicenteqm/invex-control-cobertura`. Un proceso válido envía los archivos agregados del tablero y GitHub Actions despliega Pages; si falla Pandape, se conserva la publicación anterior.

## Ejecución cada hora y fallos

La automatización de este chat ejecuta el procesador cada hora en este equipo. Requiere que Codex y el equipo estén disponibles. Evita procesos simultáneos mediante bloqueo del sistema operativo. El registro está en `logs/actualizacion.log` y el último resultado en `logs/ultimo-proceso.json`.

Si falla MAAT, se actualizan los cálculos válidos de los Excel y el panel indica que el cruce no está disponible; no presenta el concentrado antiguo como una descarga exitosa. Si falla una validación de los Excel o el motor, conserva los datos publicados anteriores. Un código de salida 2 indica fallo de descarga y 1 fallo del procesamiento.

El flujo completo es Pandape → asistencia mensual → MAAT → análisis → tablero → publicación, cuando esta última esté configurada. La base de tiendas sigue siendo un Excel local: el ZIP no contiene un descargador para ella. Los reportes de Pandape son diarios, igual que en el sistema anterior; una fecha sin ejecución no se recupera automáticamente. Cambiar el mes requiere revisar `period`, el Excel de plantilla y las carpetas en la configuración local.
