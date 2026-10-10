@echo off
title JUBYS Plataforma LOPDP 360 - Backend REST Gateway
echo ============================================================
echo   Iniciando Backend REST Gateway (FastAPI) en puerto 5000
echo   Documentacion Swagger: http://localhost:5000/docs
echo ============================================================
cd /d "%~dp0"
call "%~dp0scripts\entorno.bat" --sin-node
if errorlevel 1 (
    pause
    exit /b 1
)
"%PYTHON_BIN%" main.py
pause
