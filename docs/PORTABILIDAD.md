# Usar el proyecto en otro equipo o repositorio

## Equipo Windows nuevo

1. Instala Python 3.10 o posterior y Microsoft Edge. Para publicar instala también Git.
2. Clona el repositorio o copia el código. No copies `.private`, `.venv`, `.build-deps` ni cachés de otro equipo.
3. Abre `CONFIGURAR_EQUIPO.bat`. Crea el entorno `.venv`, instala `requirements.txt` y prepara las carpetas y la configuración cuando no existen. Requiere conexión para instalar las dependencias.
4. Coloca el Excel de asistencia en `inputs/fuentes/asistencias/` y la base de tiendas en `inputs/fuentes/base_tiendas/`.
5. Revisa el periodo en `configuracion/config.local.json`.
6. Abre `ACTUALIZAR_INVEX.bat`. MAAT inicia sesión automáticamente; configura MAAT_USER y MAAT_PASSWORD en el entorno del equipo. Para Pandape configura pandape_user en el JSON local o PANDAPE_USER en el entorno: el correo se llena automáticamente y tú escribes la contraseña. Después continúa con la descarga y los cálculos. Dispones de cinco minutos para el ingreso en Pandape.

Los sitios siguen necesitando cuentas válidas. No se elimina ni se evita su autenticación o CAPTCHA. La contraseña de Pandape se escribe personalmente en el navegador. MAAT puede usar MAAT_USER y MAAT_PASSWORD del entorno para evitar depender de archivos cifrados. En el equipo original, si no están esas variables, se utiliza opcionalmente .private/maat.json. No copies ese archivo a otro equipo; configura allí sus propios accesos.

El sitio de consulta puede abrirse desde otras plataformas; el ejecutor actual está preparado para Windows (BAT, Edge y bloqueo msvcrt).

## Publicación en tu repositorio

La preparación nueva establece `publish: false`: permite descargar y generar el tablero local sin una cuenta GitHub. Para consultarlo ejecuta `python -m http.server 8000 --directory site` desde la raíz y abre `http://localhost:8000`.

Para publicar, crea o utiliza un repositorio propio, configura el remoto `origin` con su dirección, autentica Git con una cuenta que tenga permisos y configura el nombre/correo de autor de Git. Utiliza la rama `main` y activa GitHub Pages mediante GitHub Actions. Después activa `publish: true` en la configuración local.

Ejemplo de cambio de destino, desde la raíz del proyecto, sustituyendo USUARIO y REPOSITORIO por el destino correcto:

```powershell
git remote set-url origin https://github.com/USUARIO/REPOSITORIO.git
python python/publicar_github.py
```

`publicar_github.py` toma el propietario y nombre desde `origin`; no está vinculado a una cuenta específica ni crea repositorios automáticamente. Necesita una sesión GitHub disponible en Git Credential Manager para las operaciones de la API. GitHub puede exigir configurar Pages en los ajustes del repositorio según sus permisos y disponibilidad.

Los Excel, credenciales, configuración y logs continúan excluidos del repositorio. El directorio `site` contiene los datos del tablero: su visibilidad depende del repositorio y alojamiento elegidos.

## Opciones existentes

MAAT automático y Pandape manual son los valores predeterminados (maat_manual_login=false y pandape_manual_login=true). El modo automático opcional solo usa variables de entorno MAAT_USER/MAAT_PASSWORD o PANDAPE_USER/PANDAPE_PASSWORD, con compatibilidad opcional de credenciales cifradas para MAAT en el equipo original. Pandape puede rechazar ese modo con CAPTCHA; no se garantiza acceso sin intervención.
