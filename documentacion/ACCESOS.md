# Accesos sin cifrado

MAAT y Records leen el mismo archivo `configuracion/accesos.json`, con esta estructura:

```json
{
  "maat": {
    "usuario": "",
    "contrasena": ""
  }
}
```

Es texto legible. Puede editarse o copiarse a otro equipo; no usa DPAPI ni depende de la cuenta de Windows que lo creó. CONFIGURAR_EQUIPO.bat prepara un archivo vacío si no existe y conserva los accesos existentes. Las variables MAAT_USER y MAAT_PASSWORD, cuando existen, tienen prioridad.

Pandape conserva el ingreso manual de contraseña cuando vence su sesión. El perfil local de Edge está en `configuracion/sesiones/pandape_edge/`. Al actualizar esta instalación se traslada automáticamente desde la carpeta anterior. En otra computadora inicia sesión en Edge una vez; la sesión del navegador la administra el propio navegador.

El código y el tablero pueden publicarse en GitHub. La carpeta configuracion permanece excluida porque contiene la contraseña legible y la sesión del navegador. Para compartir accesos con otro equipo autorizado, copia accesos.json directamente a su carpeta configuracion; no es necesario publicarlo en el repositorio.
