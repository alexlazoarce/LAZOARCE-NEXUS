@echo off
echo Limpiando datos antiguos...
rmdir /s /q backend\instance 2>nul

echo Deteniendo procesos anteriores...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5001') do taskkill /pid %%a /f 2>nul

echo Iniciando sistema de prestamos...
set FLASK_RUN_PORT=5001
python backend/app.py

pause
