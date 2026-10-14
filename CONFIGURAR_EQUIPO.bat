@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
if errorlevel 1 exit /b 1
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -X utf8 "%~dp0python\configurar_equipo.py" --instalar
  goto resultado
)
where python >nul 2>nul
if not errorlevel 1 (
  python -X utf8 "%~dp0python\configurar_equipo.py" --instalar
  goto resultado
)
echo Instala Python 3.10 o posterior y vuelve a ejecutar este archivo.
pause
exit /b 1
:resultado
set "INVEX_SETUP_EXIT=%ERRORLEVEL%"
if not "%INVEX_SETUP_EXIT%"=="0" echo No se completo la preparacion. Revisa el mensaje anterior.
pause
exit /b %INVEX_SETUP_EXIT%
