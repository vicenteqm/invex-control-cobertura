# INVEX · Control de cobertura

Tablero publicado: https://vicenteqm.github.io/invex-control-cobertura/

Repositorio: https://github.com/vicenteqm/invex-control-cobertura

El módulo adicional de Seguimiento operativo y su actualización histórica se documentan en [INTEGRACION.md](docs/INTEGRACION.md).
El proceso manual abre MAAT en Edge visible, descarga su CSV y después continúa con Pandape, el cálculo y la publicación. Se documenta en [SISTEMA_HORARIO.md](docs/SISTEMA_HORARIO.md). La tarea automática por hora está pausada.

Panel estático de una sola página, en negro y blanco. Cobertura, Tiendas, Asistencia y Actualización. Sin proceso de compilación ni servicios externos para consultar los datos.

## Actualizar desde Excel

Instala Python 3.10 o posterior y las dependencias:

```powershell
python -m pip install -r requirements.txt
python python/actualizar.py --base "C:/ruta/BASE DE TIENDAS INVEX_OCTUBRE.xlsx" --asistencia "C:/ruta/ASISTENCIA_INVEX_OCTUBRE.xlsx" --periodo 2026-10
```

El periodo es explícito para evitar atribuir los días a un mes incorrecto. Los Excel no se copian al repositorio. Solo se genera `site/data.js` con información agregada por tienda y códigos de asistencia del periodo. El proceso reemplaza los datos únicamente al terminar correctamente; un error conserva la última versión. Revisa las advertencias que imprime.

Abre `site/index.html` directamente o ejecuta `python -m http.server 8000 --directory site` y consulta http://localhost:8000. Tras actualizar, recarga el navegador.

## Publicar en un repositorio nuevo

Nombre sugerido: `invex-control-cobertura`. Crea el repositorio en tu cuenta, sin README inicial, y conecta esta carpeta. Con Git instalado y autenticado:

```powershell
git add .
git commit -m "Crear panel de cobertura INVEX"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/invex-control-cobertura.git
git push -u origin main
```

En GitHub abre Settings → Pages → Source → GitHub Actions. El flujo `Publicar INVEX` despliega únicamente `site/`. El enlace real aparecerá en Actions y Pages al completar el despliegue.

Cada actualización posterior:

```powershell
python python/actualizar.py --base "C:/ruta/base.xlsx" --asistencia "C:/ruta/asistencia.xlsx" --periodo 2026-10
git add site/data.js
git commit -m "Actualizar cobertura INVEX"
git push
```

Puedes añadir `--publicar` al comando Python para hacer el commit y push de `site/data.js` automáticamente. Requiere Git en PATH, remoto, rama con seguimiento y autenticación configurados. Si falla la publicación, los datos locales se conservan y se muestra el error.

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
- `inputs/fuentes/asistencias/`: Excel de asistencia fuente. Reemplaza aquí el archivo al cambiar de mes.
- `inputs/fuentes/base_tiendas/`: Excel fuente de plantilla y tiendas.
- `inputs/asistencias/`: asistencia mensual generada por el proceso.
- `inputs/pandape/`: reportes descargados y reportes manuales.
- `inputs/maat_descargas/`: CSV descargados desde MAAT.
- `inputs/`: concentrado MAAT, análisis y Excel de detalle generados.
- `configuracion/config.local.json`: periodo, rutas y opciones locales.
- `site/`: página publicada, estilos, scripts y datos del tablero.
- `docs/`: manuales e integración.
- `tests/`: pruebas del sistema.
- `previews/`: capturas de diseño locales.
- `logs/`: registros de ejecución.
- `.private/`: credenciales cifradas; `.build-deps/`: dependencias locales.

Abre `ACTUALIZAR_INVEX.bat` o `ACTUALIZAR_CON_REPORTE.bat` en la raíz. Las rutas relativas de los Excel se resuelven desde la raíz del proyecto. Desde el 14 de octubre de 2026 el proceso utiliza las copias dentro de `inputs/fuentes/`; los originales externos se conservaron, pero ya no se leen automáticamente. Edita o sustituye las copias internas para futuras actualizaciones.

Para comprobar sin descargar ni publicar: `python python/ejecutar_actualizacion.py --comprobar`.
Las fuentes, configuración, capturas, registros y credenciales permanecen excluidas de GitHub.

## Usar en otra computadora

Abre CONFIGURAR_EQUIPO.bat para preparar un equipo Windows nuevo. MAAT inicia sesión automáticamente con los accesos del equipo; Pandape llena el correo y espera tu contraseña. En otro equipo configura sus propios accesos, sin copiar los archivos cifrados. Consulta [PORTABILIDAD.md](docs/PORTABILIDAD.md). La preparación nueva desactiva publicar hasta que configures tu repositorio y Git.

