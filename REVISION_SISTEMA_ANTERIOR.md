# Revisión de cob.zip

Archivo revisado: `C:/Users/plantilla.r3/Downloads/cob.zip`.

El ZIP contiene varias versiones históricas del tablero, Excel y concentrados MAAT, además de dos entornos virtuales con dependencias. No es necesario copiar esos entornos al proyecto.

El `engine.py` de la raíz coincide con el motor integrado; la única diferencia funcional es nuestra corrección que recorta los intervalos al horario de apertura y cierre.

## Componente adicional encontrado

La carpeta `MACRO ASISTENCIA` contiene un flujo previo al cálculo de cobertura:

1. `descarga.py` inicia sesión en Pandape y solicita la exportación de fichajes.
2. `run_macro.py` abre `ASISTENCIA_INVEX.xlsm` mediante Excel de Windows, ejecuta una macro y exporta la asistencia mensual.
3. `descarga.bat` coordina el flujo anterior.

Este componente no venía en los tres scripts recibidos inicialmente. Su descarga se replicó en `descarga_pandape.py` y la lógica de la macro se trasladó a `generar_asistencia.py`, con sus reglas de consolidación, cruce y clasificación. La automatización invoca ambos antes de MAAT. La ejecución real depende de que el acceso a Pandape y su exportación funcionen; consultar el diagnóstico y el último resultado antes de considerar el flujo operativo.

La carpeta incluye archivos históricos de agosto y septiembre, así como un CSV de MAAT de octubre. No se sustituyeron las fuentes actuales con esos archivos para evitar cambiar el corte o mezclar versiones.

Se revisó el contenido sin ejecutar los scripts ni la macro del ZIP. Las instrucciones de los README antiguos no modifican la configuración de publicación ni autorizan usar su repositorio o sus tokens. Las credenciales deben permanecer fuera del código y de los archivos públicos.
