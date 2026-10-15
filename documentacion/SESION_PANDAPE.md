# Sesión reutilizable de Pandape / HolmesHR

El ejecutor usa un perfil propio de Edge o Chrome dentro de `.private/pandape_perfil_edge` (o `_chrome`). Guarda las cookies de la sesión para reutilizar el acceso sin escribir la contraseña en cada actualización. El perfil está excluido de GitHub; no debe copiarse a otro equipo ni compartirse.

Para prepararlo sin descargar MAAT, calcular ni publicar, ejecuta:

```
ACTUALIZAR_INVEX.bat --guardar-sesion-pandape
```

Escribe tus credenciales en la ventana del ejecutor y marca **Permanecer conectado** si HolmesHR ofrece esa opción. El navegador se cerrará al confirmar el ingreso. Después, ACTUALIZAR_INVEX.bat intentará reutilizar esa sesión. La sesión del navegador integrado de este chat o del Edge habitual no se transfiere al perfil del ejecutor.

No se escribe ni se guarda la contraseña desde Python. El gestor de contraseñas del perfil está desactivado; las cookies siguen siendo datos privados. No es necesario mantener abierta la ventana del navegador: se conserva el perfil al cerrarla normalmente. No abras dos procesos con ese perfil simultáneamente.

HolmesHR controla la caducidad de la sesión. Si vence o requiere una verificación, el proceso visible espera hasta cinco minutos para que completes el acceso; no elude CAPTCHA ni rechazos del servidor. Cada computadora requiere su propia sesión inicial.

La detección reconoce los dominios del acceso antiguo y de HolmesHR. Llegar al servidor de login nuevo no se considera autenticación completada. Se verificaron el reingreso con sesión guardada, los filtros COMPAÑÍA / DEPARTAMENTO / INVEX y la exportación diaria con descarga y validación del Excel en HolmesHR.
