#!/bin/bash
echo "Limpiando datos antiguos..."
rm -rf backend/instance

echo "Deteniendo procesos anteriores..."
lsof -ti :5001 | xargs -r kill -9 2>/dev/null

echo "Iniciando sistema de prestamos..."
FLASK_RUN_PORT=5001 python backend/app.py
