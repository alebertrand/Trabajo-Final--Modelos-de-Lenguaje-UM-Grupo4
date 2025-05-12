#!/bin/bash
IMAGE_NAME=recetario
CONTAINER_NAME=recetario_container

# Eliminar contenedor anterior si existe
docker rm -f $CONTAINER_NAME 2>/dev/null

# Construir imagen
echo "Construyendo la imagen Docker '$IMAGE_NAME'..."
docker build -t $IMAGE_NAME .

# Ejecutar contenedor
echo "Ejecutando el contenedor..."
docker run --name $CONTAINER_NAME -p 8000:8000 -p 8501:8501 $IMAGE_NAME