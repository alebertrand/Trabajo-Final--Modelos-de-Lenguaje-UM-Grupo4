#!/bin/bash

# Asegurar que estés en la raíz del proyecto
cd "$(dirname "$0")"

# Desactivar conda si está activa
#conda deactivate 2>/dev/null

# Activar tu entorno virtual (si estás usando venv)
source venv/bin/activate

# Levantar FastAPI (API backend) en background
echo "Iniciando backend FastAPI en http://127.0.0.1:8000 ..."
uvicorn backend.main:app --reload &

# Levantar Streamlit (frontend)
echo "Iniciando interfaz Streamlit en http://localhost:8501 ..."
streamlit run frontend/app.py

# NOTA: Cuando se cierra streamlit, matamos el backend también
trap "pkill -f 'uvicorn backend.main:app'" EXIT
