# Actualizar Excel manualmente

Los tres accesos están en la raíz del proyecto. Guarda los cambios del Excel antes de seleccionarlo. Requieren internet y Git autenticado para publicar.

| Archivo que recibiste | Acceso que debes abrir | Qué seleccionar |
| --- | --- | --- |
| Base de tiendas | ACTUALIZAR_BASE_TIENDAS.bat | Excel `.xlsx` completo de tiendas y plantilla |
| Asistencias | ACTUALIZAR_ASISTENCIAS.bat | Asistencia mensual `.xlsx`, con sus días y horas; no el reporte diario de fichajes Pandape |
| Horas productivas | ACTUALIZAR_HORAS_PRODUCTIVAS.bat | Excel mensual `.xlsx` de horas productivas, con todas sus hojas; no la BPI ni el CSV Records |

1. Haz doble clic en el acceso correspondiente.
2. Selecciona el Excel actualizado del mismo mes configurado en cobertura.
3. Espera el mensaje **ACTUALIZACIÓN PUBLICADA**. El proceso valida, copia el archivo, recalcula y envía los datos a GitHub. No vuelve a abrir MAAT ni Pandape.
4. Espera el despliegue de GitHub Pages y recarga la página con **Ctrl + F5**. Revisa la fecha de actualización; en Horas productivas también se muestra la fecha de modificación de su fuente.

Si recibiste los tres archivos, usa los tres accesos, uno por uno, esperando a que termine cada proceso. No es necesario ejecutar después ACTUALIZAR_INVEX.bat: ese acceso inicia el flujo automático y puede reemplazar la productividad manual con un nuevo cruce BPI/Records.

La nueva base queda vinculada a su ruta de origen para las futuras ejecuciones completas. Si la mueves o renombras, selecciónala de nuevo. La asistencia y la productividad seleccionadas se copian a las carpetas locales y quedan configuradas como fuentes para el recálculo.

Si aparece un error, no cierres la ventana hasta leerlo. Revisa `registros/actualizacion.log`. Si falló solo el envío a GitHub, vuelve a abrir el mismo acceso y selecciona el mismo archivo. Una selección cancelada no publica cambios. Si Excel bloquea la copia de un archivo de trabajo, ciérralo y reintenta.

Para actualizar la BPI del flujo automático, colócala en `datos/fuentes/bpi/` y abre ACTUALIZAR_INVEX.bat. La tarea horaria sigue pausada: colocar un archivo por sí solo no inicia un proceso.
