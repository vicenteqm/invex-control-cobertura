@echo off
call "%~dp0ACTUALIZAR_INVEX.bat" --seleccionar-reporte %*
exit /b %ERRORLEVEL%
