@echo off
REM Arnes de verificacion. El interprete y su validacion los resuelve scripts\entorno.bat.
setlocal
chcp 65001 > nul
cd /d "%~dp0"

call "%~dp0scripts\entorno.bat"
if errorlevel 1 exit /b 1

echo [ARNES] Ejecutando arnes_cero_regresiones...
"%PYTHON_BIN%" verificadores\arnes_cero_regresiones.py
if errorlevel 1 exit /b %errorlevel%

echo [ARNES] Ejecutando pruebas unitarias backend con pytest...
"%PYTHON_BIN%" -m pytest tests/
if errorlevel 1 exit /b %errorlevel%

echo [ARNES] Verificando compilacion del frontend...
pushd frontend
call npm run build
if errorlevel 1 (
    popd
    exit /b 1
)
popd

echo [ARNES] Todas las verificaciones pasaron exitosamente.
exit /b 0
