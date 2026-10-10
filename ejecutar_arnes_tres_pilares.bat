@echo off
REM Role: qa-engineer
REM Arnes de los tres pilares. El interprete y su validacion los resuelve scripts\entorno.bat.
setlocal
chcp 65001 > nul
cd /d "%~dp0"

call "%~dp0scripts\entorno.bat"
if errorlevel 1 exit /b 1

if exist "%CD%\.test-runtime" set "PYTHONPATH=%CD%\.test-runtime;%PYTHONPATH%"

echo [PILAR 1] Backend, arquitectura y controles de gobernanza...
"%PYTHON_BIN%" verificadores\arnes_cero_regresiones.py
if errorlevel 1 exit /b %errorlevel%

echo [PILAR 2] Tipado estricto del frontend...
pushd frontend
"%NODE_BIN%" node_modules\typescript\bin\tsc --noEmit
if errorlevel 1 (
    popd
    exit /b 1
)

echo [PILAR 3] Compilacion de produccion del frontend...
"%NODE_BIN%" node_modules\next\dist\bin\next build --turbopack
if errorlevel 1 (
    popd
    exit /b 1
)
popd

echo [ARNES] Los tres pilares pasaron exitosamente.
exit /b 0
