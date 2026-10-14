# Consulta automática del detalle

## Ingreso manual y procesamiento automático

Prueba del 13 de octubre de 2026: se verificaron el ingreso manual en Edge, los filtros Compañía/Departamento/INVEX y la descarga diaria. El reporte de 531 personas permitió 342 coincidencias con la asistencia; MAAT descargó 1,907 registros. La actualización y publicación terminaron a las 14:18. El lector reconoce reportes diarios con dos pares Ent./Sal., además de los reportes con tres o cuatro pares. Un reporte ya validado queda como `Reporte_Pandape_actual.xlsx`.

La configuración actual utiliza Edge visible y `pandape_manual_login: true`. Al abrir `ACTUALIZAR_INVEX.bat`, el programa prepara únicamente el correo. El usuario escribe la contraseña, pulsa Entrar y completa cualquier verificación solicitada por Pandape. El ejecutor espera hasta cinco minutos y, al detectar el ingreso, aplica los filtros, exporta los fichajes del día, valida y reemplaza el reporte actual, genera la asistencia, cruza MAAT y publica. No hay que pulsar Exportar ni modificar filtros manualmente.

El aviso «Problema administrativo» de Pandape puede cubrir el botón Exportar. El programa cierra únicamente ese aviso cuando encuentra su botón de cierre; no contacta al departamento administrativo ni modifica la cuenta. Si no identifica el cierre, solicita al usuario cerrar el aviso y espera. El aviso de la cuenta puede requerir seguimiento por parte de su administrador.

Cada ejecución nueva abre una sesión del navegador y requiere el ingreso manual. Por tanto, la tarea horaria no es desatendida mientras se use este modo. Se mantiene el modo de reporte descargado manualmente como alternativa.

El ejecutor muestra Chrome visible cuando `pandape_visible` es `true` en la configuración local. El descargador informa siete pasos en la consola, aplica los filtros Compañía → Departamento → INVEX por su texto visible y valida el reporte del día antes de reemplazar `inputs/pandape/Reporte_Pandape_actual.xlsx`. Después genera la asistencia mensual, descarga MAAT, calcula y publica. La descarga original de cada ejecución se conserva en su propia carpeta. Un fallo de acceso, filtro, descarga o validación conserva el reporte válido anterior. No se eluden rechazos del servidor ni desafíos de seguridad.

En la prueba con Chrome visible del 13 de octubre de 2026, el formulario abrió pero Pandape rechazó el inicio de sesión con «Error en la validación de Captcha». En ese caso el ejecutor mantiene Chrome abierto hasta cinco minutos para que el usuario complete el acceso personalmente. Continúa al detectar la salida de la pantalla de inicio de sesión; si no se completa, termina con un aviso y conserva los datos. Por tanto, no se garantiza una descarga desatendida cada hora cuando Pandape exige esa verificación.

El detalle por promotor ahora se publica automáticamente dentro de los datos del tablero, según la solicitud del usuario. Los visitantes pueden consultar nombres, checadas, jornadas y estatus sin cargar archivos. Cada procesamiento válido lo regenera y lo publica junto con los KPI. Solo se incluyen los campos de consulta autorizados; usuarios de acceso, nóminas, teléfonos, contraseñas y archivos fuente quedan fuera. Esta configuración sustituye las instrucciones anteriores de carga local para la consulta web.

# Sistema operativo integrado

## Registro Pandape / MAAT

El Excel de detalle por promotor replica las 23 columnas de `downloadRegistroExcel` del HTML anterior y agrega la fecha del corte. El reporte de fichajes se cruza por nombre con la asistencia mensual; después el motor cruza USUARIO de asistencia con Ejecutivo/Usuario de MAAT por día, y asigna la información de tienda mediante socio/determinante. Incluye jornada, horario asignado y programado, indicadores y horas de ambos sistemas, estatus, cambios de tienda, cierre manual, retardo, salida anticipada, origen del horario y externos MAAT.

Cada procesamiento válido genera además `inputs/Detalle_promotores_AAAA-MM_DD.xlsx` mediante `detalle_promotores.py`, con Calibri 9, centrado horizontal/vertical, encabezados negros con texto blanco y datos blancos con texto negro. El archivo nominal se conserva localmente. La descarga de promotores del tablero genera los mismos campos con el mismo diseño y respeta los filtros aplicados tras cargar el análisis local.

Se recuperaron los cuatro KPI del tablero del ZIP: registrados en Pandape, registrados en MAAT, completos en ambos y sin registro en ningún sistema, con numerador, total y porcentaje. El universo incluye personal activo y externos MAAT de las tiendas filtradas. Una persona trasladada se cuenta una sola vez en los KPI; sus registros por tienda se atribuyen al destino de cobertura.

La vista incluye tiendas sin ningún registro, estatus por tienda, cobertura por horario (mediodía y tolerancia de cierre de 30 minutos), movimientos, retardos, salidas anticipadas y cierre manual. Permite filtrar estatus, consultar cada tienda y descargar la consulta en Excel XLSX real o imagen PNG. Los días sin datos de un sistema quedan sin evaluar. Los históricos de agosto y septiembre se recuperaron de los datos incrustados en el ZIP; `importar_registro_historico.py --zip ruta/cob.zip` permite repetir su incorporación sin reemplazar el periodo actual.

El detalle por promotor se activa cargando `inputs/analisis_actual.json` en el selector del tablero. Para los meses históricos, usa `inputs/historico/analisis_AAAA-MM.json`. Se muestran nombres, ambas parejas de horas, clasificación, destino, cambios, horarios programados y alertas; permite buscar, filtrar estatus y horarios irregulares y exportar Excel o imagen. El navegador lee el archivo localmente, sin enviarlo a un servidor. El sitio público contiene únicamente los agregados; los archivos nominales permanecen excluidos del repositorio.

## Ejecutar con doble clic en Windows

Abre `ACTUALIZAR_INVEX.bat` desde la carpeta del proyecto. El ejecutor busca Python, verifica las dependencias y configuración, y corre `procesar_cobertura.py`. La ventana permanece abierta para leer el resultado. Con `publish` activado, el proceso también envía los datos válidos a GitHub y Pages los despliega. No instala dependencias ni cambia credenciales automáticamente.

Puedes arrastrar el reporte Pandape sobre el BAT o abrir `ACTUALIZAR_CON_REPORTE.bat` para seleccionarlo. El rango del reporte debe incluir el día actual: se leen exclusivamente las filas de ese día y se detectan todos los pares Ent./Sal. por encabezados. Los días anteriores del reporte no se mezclan con la captura actual. Para verificar el entorno sin descargar ni publicar ejecuta `python python/ejecutar_actualizacion.py --comprobar`.

El BAT es un lanzador; requiere la carpeta completa, su configuración local y las credenciales cifradas para la misma cuenta de Windows. No es un ejecutable independiente ni crea otra tarea horaria.

`procesar_cobertura.py` reemplaza el procesador anterior. Lee `configuracion/config.local.json`, descarga MAAT, sustituye los registros de las fechas descargadas en el concentrado mensual, procesa los Excel con `engine.py` y genera ambos archivos de datos del panel. Conserva los demás meses históricos.

```powershell
python python/procesar_cobertura.py
```

`--sin-descarga` permite procesar únicamente los archivos locales. No activa MAAT si no existe un concentrado. Las dependencias son openpyxl, requests y Selenium, además de Chrome para Pandape. MAAT usa sesión HTTP con CSRF. Pandape conserva los filtros de equipo y grupo del descargador recibido y solicita el reporte del día actual.

## Flujo de Pandape replicado desde cob.zip

`descarga_pandape.py` descarga el reporte en una carpeta nueva por ejecución y espera a que termine la descarga. `generar_asistencia.py` replica en Python la macro CRUCE del libro original: consolida las tres parejas de entradas/salidas, obtiene la primera entrada y última salida por nombre y cruza los nombres sin depender del orden de sus palabras, mayúsculas o acentos. Se actualizan los colaboradores ACTIVO y PENDIENTE del día actual.

Se conserva la regla original de retardo: el minuto de entrada entre 05 y 15 genera R; otras entradas generan A. Sin horas, se evalúa D o F según el descanso oficial. Los colaboradores sin coincidencia conservan la etiqueta original `no encontrado`, que no debe interpretarse automáticamente como falta. Las capturas V e I se conservan. La columna de descanso se busca por encabezado, corrigiendo la referencia incorrecta a antigüedad en la macro; la columna de cruce se reutiliza en lugar de duplicarse cada hora.

La asistencia generada queda en `inputs/asistencias/ASISTENCIA_INVEX_AAAA-MM.xlsx`. Se parte del Excel de la carpeta configurada o de la asistencia generada, según cuál tenga la modificación más reciente. Así se conserva el acumulado y se pueden incorporar cambios de plantilla del Excel fuente. Los archivos originales permanecen intactos. No se necesita Excel instalado ni habilitar VBA; se conserva el XLSM original en `inputs/pandape/` como referencia local.

Si falla Pandape o la generación, el proceso se detiene y conserva el tablero anterior. La configuración `download_pandape` activa este paso. Las credenciales se obtienen de PANDAPE_USER/PANDAPE_PASSWORD o de `.private/pandape.json`, cifrado para la cuenta de Windows. El diagnóstico local está en `inputs/pandape/diagnostico.json` y su captura de pantalla en la misma carpeta; ambos se excluyen de publicación.

Prueba real del 13 de octubre de 2026: el acceso de Chrome automático recibió `403 Forbidden` antes del formulario de autenticación. El navegador integrado sí mostró el formulario. La descarga automática de Pandape todavía no está operativa; requiere resolver el acceso admitido por el servicio. No se modifica la seguridad ni se simula una descarga exitosa. Para procesar un reporte auténtico del día descargado desde el navegador se puede ejecutar `python python/procesar_cobertura.py --reporte-pandape "ruta/Reportede.xlsx"`. Esta opción también ejecuta MAAT y actualiza el tablero si todas las validaciones pasan. No usar reportes de días anteriores con esta opción.

## Funciones del motor original

Se conserva el motor recibido: presencia por entrada/salida, cobertura frente a plantilla autorizada, usuarios activos, semáforos, descansos oficiales, turnos aún no iniciados, huecos de cobertura, altas, bajas, rotación, reincidencias, Pandape/MAAT por día, cambio de tienda, cobertura externa, cierre manual, entrada tardía y salida anticipada. La interfaz consulta agregados por tienda; los registros nominales no se publican.
El detalle nominal completo del último cálculo queda en `inputs/analisis_actual.json`, disponible para revisión local y excluido de Git. Los intervalos se recortan al horario de apertura y cierre para evitar duraciones negativas fuera de ese rango.
Si MAAT contiene un día que aún no está capturado en el Excel, se muestran únicamente sus registros y el cruce de Pandape permanece sin evaluar. No se convierte ausencia de datos en falta de registro.
El motor original considera estatus ACTIVO para sus indicadores operativos; los KPI de plantilla existentes conservan su definición de promotores y sublíderes elegibles. El nombre completo de las ejecutivas se conserva para agrupar la gestión.

El adaptador identifica columnas por encabezados y luego entrega al motor su esquema original; una columna obligatoria ausente detiene la generación. Usa los días reales del mes y la zona America/Mexico_City. La regla de hora de corte se aplica únicamente cuando el día de asistencia corresponde a hoy. Un corte histórico no se recalcula como si su turno empezara en la hora actual. Los días sin captura global se excluyen de la tendencia y días rojos.

## Fuentes y credenciales

Las carpetas y el periodo están en `configuracion/config.local.json`, excluido de Git. Los Excel originales permanecen intactos. Los CSV de MAAT se guardan en `inputs/`, también excluido. Se aplican los mismos nueve mapeos de puntos de venta del descargador original. Las fechas se normalizan antes de sustituir registros, evitando duplicados por formatos DD/MM/AAAA y AAAA-MM-DD.

Las credenciales de MAAT se leen desde MAAT_USER y MAAT_PASSWORD, o desde `.private/maat.json`, cifrado por Windows para la cuenta local. No hay contraseñas ni tokens GitHub escritos en el código nuevo. La publicación utiliza Git autenticado, solo si `publish` está activado. Está activada en la configuración local y el remoto es `vicenteqm/invex-control-cobertura`. Un proceso válido envía los archivos agregados del tablero y GitHub Actions despliega Pages; si falla Pandape, se conserva la publicación anterior.

## Ejecución cada hora y fallos

La automatización de este chat ejecuta el procesador cada hora en este equipo. Requiere que Codex y el equipo estén disponibles. Evita procesos simultáneos mediante bloqueo del sistema operativo. El registro está en `logs/actualizacion.log` y el último resultado en `logs/ultimo-proceso.json`.

Si falla MAAT, se actualizan los cálculos válidos de los Excel y el panel indica que el cruce no está disponible; no presenta el concentrado antiguo como una descarga exitosa. Si falla una validación de los Excel o el motor, conserva los datos publicados anteriores. Un código de salida 2 indica fallo de descarga y 1 fallo del procesamiento.

El flujo completo es Pandape → asistencia mensual → MAAT → análisis → tablero → publicación, cuando esta última esté configurada. La base de tiendas sigue siendo un Excel local: el ZIP no contiene un descargador para ella. Los reportes de Pandape son diarios, igual que en el sistema anterior; una fecha sin ejecución no se recupera automáticamente. Cambiar el mes requiere revisar `period`, el Excel de plantilla y las carpetas en la configuración local.

## Descarga diaria MAAT

La descarga filtra start y end con la misma fecha del día de ejecución en America/Mexico_City. El CSV debe contener exclusivamente ese día. El concentrado mensual reemplaza solo los registros de esa fecha y conserva los demás días. El rango visible del histórico puede seguir incluyendo fechas anteriores; no representa el rango de la nueva descarga. El periodo configurado debe coincidir con el mes actual.

