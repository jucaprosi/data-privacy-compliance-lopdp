@echo off
title JUBYS Plataforma LOPDP 360 - Backend REST Gateway
echo ============================================================
echo   Iniciando Backend REST Gateway (FastAPI) en puerto 5000
echo   Documentacion Swagger: http://localhost:5000/docs
echo ============================================================
set "PYTHON_BIN=%~dp0.venv\Scripts\python.exe"
if not exist "%PYTHON_BIN%" set "PYTHON_BIN=python"
"%PYTHON_BIN%" main.py
pause
