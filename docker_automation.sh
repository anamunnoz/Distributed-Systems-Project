#!/bin/bash

# Detener y eliminar contenedores si existen
docker stop server1 server2 server3 2>/dev/null
docker rm server1 server2 server3 2>/dev/null

# Eliminar imágenes si existen
docker rmi server client 2>/dev/null

# Construir la imagen del servidor
docker build -t server -f server/chord.Dockerfile .

# Crear una red Docker si no existe
docker network create servers 2>/dev/null

# Ejecutar los contenedores del servidor
docker run -it -v "$(pwd)/server/db:/app/db" --name server1 --cap-add NET_ADMIN --network servers -d server
docker run -it -v "$(pwd)/server/db:/app/db" --name server2 --cap-add NET_ADMIN --network servers -d server
docker run -it -v "$(pwd)/server/db:/app/db" --name server3 --cap-add NET_ADMIN --network servers -d server

# Construir la imagen del cliente
docker build -t client -f client/new_client.Dockerfile .

echo "Proceso completado. Contenedores e imágenes creados."