# Imagen base
FROM python:3.9-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar todo el contenido del proyecto
COPY . .

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Instalar las dependencias de Python
RUN pip install --upgrade pip && pip install -r requirements.txt

# Dar permisos de ejecución al script de inicio
RUN chmod +x run_api.sh

# Exponer puertos para FastAPI y Streamlit
EXPOSE 8000 8501

# Usar el script como punto de entrada
ENTRYPOINT ["./run_api.sh"]
