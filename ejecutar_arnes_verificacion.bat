@echo off
chcp 65001 > nul
set PYTHON_BIN="C:\Users\Juan Carlos\AppData\Local\Python\bin\python.exe"

echo [ARNES] Ejecutando arnes_cero_regresiones...
if exist %PYTHON_BIN% (
    %PYTHON_BIN% verificadores\arnes_cero_regresiones.py
) else (
    python verificadores\arnes_cero_regresiones.py
)
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

echo [ARNES] Ejecutando pruebas unitarias backend con pytest...
if exist %PYTHON_BIN% (
    %PYTHON_BIN% -m pytest tests/
) else (
    python -m pytest tests/
)
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

echo [ARNES] Verificando compilacion del frontend...
cd frontend
call npm run build
if %ERRORLEVEL% NEQ 0 (
    cd ..
    exit /b %ERRORLEVEL%
)
cd ..

echo [ARNES] Todas las verificaciones pasaron exitosamente.
exit /b 0
