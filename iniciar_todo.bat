@echo off
title JUBYS Plataforma LOPDP 360 - Lanzador Integral
echo ============================================================
echo   Iniciando JUBYS Plataforma LOPDP 360 (Backend + Frontend)
echo ============================================================
echo [1/2] Levantando Backend FastAPI en ventana separada...
start "LOPDP 360 Backend (:5000)" cmd /k iniciar_backend.bat

echo [2/2] Esperando 3 segundos para que el Backend inicialice...
timeout /t 3 /nobreak > nul

echo [3/3] Levantando Frontend Next.js (:3000) en ventana separada...
start "LOPDP 360 Frontend (:3000)" cmd /k iniciar_frontend.bat

echo ============================================================
echo   Plataforma iniciada con exito.
echo   - Backend API: http://localhost:5000/docs
echo   - Frontend IDE: http://localhost:3000
echo ============================================================
pause
