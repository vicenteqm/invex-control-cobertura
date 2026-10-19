# Compartir el tablero sin esperar a GitHub Pages

Cada actualización publicada genera `INVEX_ACTUALIZADO.html` en la raíz y lo envía al mismo repositorio. Contiene estilos, datos, gráficas, filtros, exportaciones y Seguimiento operativo. Funciona al descargarlo y abrirlo en Edge o Chrome, sin cargar archivos adicionales.

El enlace de descarga de la versión más reciente es:

https://github.com/vicenteqm/invex-control-cobertura/raw/refs/heads/main/INVEX_ACTUALIZADO.zip

La descarga es un ZIP que contiene únicamente INVEX_ACTUALIZADO.html. Descomprime y abre ese HTML en el navegador. Se ofrece como ZIP porque GitHub sirve los HTML directamente como texto; el ZIP permite descargarlos y pesa menos. El HTML sin comprimir también queda en la raíz del repositorio.

La consola imprime además un enlace al corte concreto. Ambos enlaces quedan en `registros/enlace-html.txt`. Comparte el enlace o envía el archivo HTML como documento. La persona debe descargarlo y abrir el archivo en su navegador; los visores de documentos de correo o mensajería pueden no ejecutar las gráficas.

El archivo descargado conserva el corte con el que se generó. Para ver la siguiente actualización, descarga nuevamente desde el enlace más reciente o utiliza el nuevo enlace de corte. Esta descarga utiliza el repositorio y no requiere que se ejecute el despliegue de Pages. Sigue necesitando que GitHub permita enviar y descargar archivos.

La tarea horaria y los tres ejecutores manuales generan esta alternativa al publicar. Las credenciales y los Excel fuente quedan fuera; el HTML incluye los mismos datos ya autorizados para el tablero publicado, incluido el detalle por promotor.
