# INVEX · Control de cobertura

Accesos actuales sin cifrado: MAAT y Records usan `configuracion/accesos.json`. Consulta [ACCESOS.md](documentacion/ACCESOS.md). Esta configuración se puede copiar entre equipos; Pandape mantiene el ingreso manual de contraseña cuando su sesión vence.

Tablero publicado: https://vicenteqm.github.io/invex-control-cobertura/

Repositorio: https://github.com/vicenteqm/invex-control-cobertura

El módulo adicional de Seguimiento operativo y su actualización histórica se documentan en [INTEGRACION.md](documentacion/INTEGRACION.md).
ACTUALIZAR_INVEX abre MAAT en Edge visible, descarga su asistencia diaria, continúa con Pandape y después descarga Records del primer al último día del mes de ejecución. Corrige las seis determinantes, cruza con la BPI más reciente, genera las horas productivas, recalcula y publica. La tarea automática por hora sigue pausada.

Panel estático de una sola página, en negro y blanco. Cobertura, Tiendas, Asistencia y Actualización. Sin proceso de compilación ni servicios externos para consultar los datos.

## Actualizar desde Excel

Instala Python 3.10 o posterior y las dependencias:

```powershell
python -m pip install -r requirements.txt
python python/actualizar.py --base "C:/ruta/BASE DE TIENDAS INVEX_OCTUBRE.xlsx" --asistencia "C:/ruta/ASISTENCIA_INVEX_OCTUBRE.xlsx" --periodo 2026-10
```

El periodo es explícito para evitar atribuir los días a un mes incorrecto. Los Excel no se copian al repositorio. Solo se genera `sitio/data.js` con información agregada por tienda y códigos de asistencia del periodo. El proceso reemplaza los datos únicamente al terminar correctamente; un error conserva la última versión. Revisa las advertencias que imprime.

Abre `sitio/index.html` directamente o ejecuta `python -m http.server 8000 --directory sitio` y consulta http://localhost:8000. Tras actualizar, recarga el navegador.

## Publicar en un repositorio nuevo

Nombre sugerido: `invex-control-cobertura`. Crea el repositorio en tu cuenta, sin README inicial, y conecta esta carpeta. Con Git instalado y autenticado:

```powershell
git add .
git commit -m "Crear panel de cobertura INVEX"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/invex-control-cobertura.git
git push -u origin main
```

En GitHub abre Settings → Pages → Source → GitHub Actions. El flujo `Publicar INVEX` despliega únicamente `sitio/`. El enlace real aparecerá en Actions y Pages al completar el despliegue.

Cada actualización posterior:

```powershell
python python/actualizar.py --base "C:/ruta/base.xlsx" --asistencia "C:/ruta/asistencia.xlsx" --periodo 2026-10
git add sitio/data.js
git commit -m "Actualizar cobertura INVEX"
git push
```

Puedes añadir `--publicar` al comando Python para hacer el commit y push de `sitio/data.js` automáticamente. Requiere Git en PATH, remoto, rama con seguimiento y autenticación configurados. Si falla la publicación, los datos locales se conservan y se muestra el error.

GitHub Actions utiliza el `GITHUB_TOKEN` automático para publicar Pages. No necesitas pegar un token en el HTML ni en Python para procesar los Excel. El envío desde tu equipo requiere autenticación Git (por ejemplo, Git Credential Manager). Si tu organización exige un token personal, configúralo en el administrador de credenciales, nunca en archivos del proyecto ni en la URL del remoto. No se programa una actualización sin una frecuencia acordada y acceso a los archivos del equipo.

Documentación: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages

## Definiciones

- Tiendas operando: estatus OPERANDO en la hoja BASE DE TIENDAS INVEX.
- Plantilla requerida: PROMOTORES REQUERIDOS + primera columna SUBLIDER (numérica). La segunda SUBLIDER contiene nombres y no se usa como plantilla.
- Personal activo: ACTIVO y perfil PROMOTOR DE CREDITO o SUBLIDER, en Hoja1 de asistencia, unido por socio + determinante a tiendas operando. Se cuentan personas, sin ponderación por jornada. Se excluye ACTIVO TEAM.
- Vacantes: suma de `max(requeridos - activos, 0)` por tienda y perfil. Los excedentes no compensan otros faltantes.
- Cobertura: suma de plazas cubiertas por tienda y perfil / plantilla requerida. No hay cobertura calculable cuando la plantilla es cero.
- Identificador de personal: nómina + nombre normalizado, o solo nombre cuando la nómina está ausente o es PENDIENTE. Una nómina asociada a nombres distintos genera advertencia y se conserva cada persona. Duplicados idénticos se omiten con advertencia; duplicados de la misma identidad con datos contradictorios detienen el proceso. Los identificadores no se publican.
- Asistencia: códigos diarios del mismo universo elegible. Catálogo confirmado: A = Asistencia, F = Falta, R = Retardo, V = Vacaciones, I = Incapacidad. Los demás códigos se conservan sin atribuirles un significado.
- Cada encabezado numérico de día está seguido de Entr y Sal. Se leen horas Excel, fracciones de día y textos HH:MM[:SS]. Celdas vacías y 00:00:00 se tratan como sin registro, siguiendo el marcador usado en esta fuente. Se publican únicamente resúmenes diarios de horas.
- Se muestran entradas, salidas, pares completos, intervalos de horas y duración promedio ponderada por pares válidos. El intervalo entre checadas no equivale a horas trabajadas ni descuenta descansos. Salidas anteriores a entradas se reportan y excluyen del promedio; no se supone un turno nocturno. Los retardos se cuentan por R, sin deducirlos del horario.
- El detalle incluye todos los días del mes del periodo explícito, con Sin captura para días sin códigos ni horas; no se consideran faltas automáticamente. El corte indica el último día con algún código, sin garantizar captura completa.
- Última actualización: momento de procesamiento, mostrado en America/Mexico_City. Se muestra también la modificación de cada fuente.

El sitio compartido expone los agregados publicados a sus visitantes. El detalle por promotor publica nombres, jornadas, checadas y estatus según la autorización del usuario. Nóminas, teléfonos, usuarios de acceso, sueldos y credenciales no se publican. Las fuentes originales permanecen intactas.


## Organización de carpetas

- `python/`: todos los módulos y ejecutores Python.
- `datos/fuentes/asistencias/`: Excel de asistencia fuente. Reemplaza aquí el archivo al cambiar de mes.
- `datos/fuentes/base_tiendas/`: Excel fuente de plantilla y tiendas.
- `datos/fuentes/bpi/`: BPI con hoja PROIND; se elige el `.xlsx` modificado más recientemente, sin abrir selector.
- `datos/descargas/records/`: cada descarga original y su copia corregida, identificadas por ejecución.
- `resultados/horas_productivas/AAAA/`: Excel mensual generado; por ejemplo `2026/Horas Productivas Octubre.xlsx`.
- `datos/asistencias/`: asistencia mensual generada por el proceso.
- `datos/pandape/`: reportes descargados y reportes manuales.
- `datos/maat_descargas/`: CSV descargados desde MAAT.
- `datos/`: concentrado MAAT, análisis y Excel de detalle generados.
- `configuracion/config.local.json`: periodo, rutas y opciones locales.
- `sitio/`: página publicada, estilos, scripts y datos del tablero.
- `documentacion/`: manuales e integración.
- `pruebas/`: pruebas del sistema.
- `vistas_previas/`: capturas de diseño locales.
- `registros/`: registros de ejecución.
- `.private/`: credenciales cifradas; `.build-deps/`: dependencias locales.

Abre `ACTUALIZAR_INVEX.bat` o `ACTUALIZAR_CON_REPORTE.bat` en la raíz. Las rutas relativas de los Excel se resuelven desde la raíz del proyecto. La base de tiendas vinculada se sincroniza desde la ruta guardada; las demás fuentes usan las carpetas configuradas. La BPI se toma de `datos/fuentes/bpi/`.

Para comprobar sin descargar ni publicar: `python python/ejecutar_actualizacion.py --comprobar`.
Las fuentes, configuración, capturas, registros y credenciales permanecen excluidas de GitHub.

## Usar en otra computadora

Abre CONFIGURAR_EQUIPO.bat para preparar un equipo Windows nuevo. MAAT inicia sesión automáticamente con los accesos del equipo; Pandape llena el correo y espera tu contraseña. En otro equipo configura sus propios accesos, sin copiar los archivos cifrados. Consulta [PORTABILIDAD.md](documentacion/PORTABILIDAD.md). La preparación nueva desactiva publicar hasta que configures tu repositorio y Git.


## Horas productivas Walmart y Sam's

Coloca la BPI nueva en `datos/fuentes/bpi/` y abre ACTUALIZAR_INVEX.bat. No se solicitan fechas ni archivos: Records abarca el mes completo de Ciudad de México y se usa la BPI más reciente. Los días futuros no generan ingresos ficticios. El reporte mensual se valida contra DETALLE antes de reemplazar el anterior; un fallo detiene la publicación del tablero. Consulta [AUTOMATIZACION_HORAS.md](documentacion/AUTOMATIZACION_HORAS.md).


## Actualizar la base de tiendas con un selector
Abre ACTUALIZAR_BASE_TIENDAS.bat, elige el Excel actualizado y guarda los cambios antes de ejecutar. También puedes arrastrar una base sobre ACTUALIZAR_INVEX.bat: el ejecutor distingue sus columnas del reporte Pandape. Se valida y copia a datos/fuentes/base_tiendas/BASE_TIENDAS_ACTUAL.xlsx. La ruta seleccionada queda vinculada en la configuración local y sus futuras ediciones se sincronizan al ejecutar el proceso. Si mueves el archivo, vuelve a seleccionarlo. Si no has vinculado una fuente, se conserva la selección de la carpeta interna existente. La base debe estar disponible y guardada para copiarla; no se sustituye por una copia vieja si falta la fuente vinculada.

## Filtros de Cobertura
Región y Tienda filtran las KPI, cobertura general, perfiles, vacantes por región, estatus y ambas tablas de horarios. Ver general restablece la vista nacional. Las KPI conservan el universo OPERANDO; el gráfico de estatus muestra todos los estatus de la selección. Los filtros de Tiendas y Horas productivas son independientes.

# Actualizar un solo Excel y publicar

Guía con los tres accesos y qué archivo seleccionar: [ACTUALIZACION_MANUAL.md](documentacion/ACTUALIZACION_MANUAL.md).

Abre con doble clic el ejecutor correspondiente y selecciona el archivo `.xlsx`:

- `ACTUALIZAR_ASISTENCIAS.bat`: asistencia mensual actualizada (no el reporte diario de fichajes).
- `ACTUALIZAR_BASE_TIENDAS.bat`: base de tiendas actualizada.
- `ACTUALIZAR_HORAS_PRODUCTIVAS.bat`: libro de horas productivas con sus hojas.

Estos tres ejecutores validan el archivo para el periodo configurado, recalculan con las demás fuentes locales y hacen commit y push de los datos agregados a GitHub. No descargan MAAT ni Pandape. Requieren conexión a internet y Git autenticado; Pages puede tardar unos minutos. Si cancelas la selección no se cambia nada. Si la publicación falla, vuelve a ejecutar el mismo acceso para reintentar. Los Excel originales permanecen locales.

`ACTUALIZAR_INVEX.bat` realiza el flujo completo de MAAT, Pandape, Records y generación automática de horas productivas. Los tres selectores manuales siguen disponibles para actualizar una sola fuente.

