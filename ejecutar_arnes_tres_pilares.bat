@echo off
REM Role: qa-engineer
setlocal
chcp 65001 > nul
cd /d "%~dp0"

if not defined PYTHON_BIN set "PYTHON_BIN=%LocalAppData%\Python\bin\python.exe"
if not exist "%PYTHON_BIN%" set "PYTHON_BIN=C:\Users\Juan Carlos\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%PYTHON_BIN%" set "PYTHON_BIN=python"
set "NODE_BIN=C:\Users\Juan Carlos\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
if not exist "%NODE_BIN%" set "NODE_BIN=node"

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
