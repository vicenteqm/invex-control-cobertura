@echo off
setlocal
chcp 65001 >nul
title INVEX - Actualizar cobertura
cd /d "%~dp0"
if errorlevel 1 goto carpeta_error
echo ============================================
echo INVEX - Actualizacion de cobertura
echo ============================================
echo.
if exist "%~dp0.venv\Scripts\python.exe" (
  "%~dp0.venv\Scripts\python.exe" -X utf8 "%~dp0python\ejecutar_actualizacion.py" %*
  goto resultado
)
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
  "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -X utf8 "%~dp0python\ejecutar_actualizacion.py" %*
  goto resultado
)
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -X utf8 "%~dp0python\ejecutar_actualizacion.py" %*
  goto resultado
)
where python >nul 2>nul
if not errorlevel 1 (
  python -X utf8 "%~dp0python\ejecutar_actualizacion.py" %*
  goto resultado
)
echo No se encontro Python. Instala Python 3.10 o posterior.
set "INVEX_EXIT=1"
goto fin
:carpeta_error
echo No se pudo abrir la carpeta del proyecto.
set "INVEX_EXIT=1"
goto fin
:resultado
set "INVEX_EXIT=%ERRORLEVEL%"
:fin
echo.
echo Puedes cerrar esta ventana despues de revisar el resultado.
pause
exit /b %INVEX_EXIT%
