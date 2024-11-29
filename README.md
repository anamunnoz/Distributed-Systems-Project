# Proyecto de Sistemas Distribuidos
## Tema: Buscador
## Integrantes del equipo:
- Ana Paula González Muñoz (C412)
- Dennis Daniel González Durán (C412)

## Comandos para configurar el entorno:
En esta seccion se muestran los comandos necesarios para configurar el entorno de docker y permitir la comunicación entre los clientes y el servidor

### Crear las redes:
- docker network create clients --subnet 10.0.10.0/24
- docker network create servers --subnet 10.0.11.0/24

### Crear y configurar el router:
- docker build -t router -f router/router.Dockerfile .
- docker run -itd --rm --name router router
- docker network connect --ip 10.0.10.254 clients router
- docker network connect --ip 10.0.11.254 servers router

### Crear y configurar cliente y servidor:
- docker build -t client -f client/Dockerfile .
- docker build -t server -f server/Dockerfile .

### Correr el servidor:
- docker run -it -v "$(pwd)/server/db:/app/db" --name server1 --cap-add NET_ADMIN --network servers server

### Correr el cliente:
- docker run -it --name client1 --cap-add NET_ADMIN --network clients client




