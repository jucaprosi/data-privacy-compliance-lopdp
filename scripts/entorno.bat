@echo off
REM Resuelve y valida el entorno de ejecucion del proyecto. Es la UNICA pieza que decide el
REM interprete: ningun otro .bat lleva rutas de una maquina concreta.
REM
REM Uso:    call "%~dp0scripts\entorno.bat" [--sin-node]
REM Salida: define PYTHON_BIN (y NODE_BIN, salvo con --sin-node) en el entorno de quien llama
REM         y termina con codigo 0; con cualquier otro codigo, el entorno no sirve.
REM         No usa setlocal: las variables deben quedar para quien llama.
REM
REM Precedencia de cada interprete:
REM   1. La variable ya definida por quien llama (PYTHON_BIN, NODE_BIN): permite forzar otro.
REM   2. Python: el entorno virtual del proyecto (.venv).
REM   3. El que este en el PATH.
REM Despues de resolver Python se comprueba que tenga todos los requisitos de requirements.txt.

for %%I in ("%~dp0..") do set "ENTORNO_RAIZ=%%~fI"

if not defined PYTHON_BIN if exist "%ENTORNO_RAIZ%\.venv\Scripts\python.exe" set "PYTHON_BIN=%ENTORNO_RAIZ%\.venv\Scripts\python.exe"
if not defined PYTHON_BIN set "PYTHON_BIN=python"

"%PYTHON_BIN%" --version >nul 2>&1
if errorlevel 1 goto sin_python

"%PYTHON_BIN%" "%ENTORNO_RAIZ%\scripts\verificar_entorno.py"
if errorlevel 1 exit /b 1

if /i "%~1"=="--sin-node" exit /b 0

if not defined NODE_BIN set "NODE_BIN=node"
"%NODE_BIN%" --version >nul 2>&1
if errorlevel 1 goto sin_node
exit /b 0

:sin_python
echo [ENTORNO] No se puede ejecutar el interprete de Python: %PYTHON_BIN%
echo           Cree el entorno virtual del proyecto o defina PYTHON_BIN con una ruta valida.
exit /b 1

:sin_node
echo [ENTORNO] No se puede ejecutar Node.js: %NODE_BIN%
echo           Instale Node.js o defina NODE_BIN con una ruta valida.
exit /b 1
