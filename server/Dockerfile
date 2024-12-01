# Dockerfile para el servidor
FROM base

# Crear directorio de trabajo
WORKDIR /app

# Copiar los archivos necesarios
COPY server/server.py ./server.py
COPY server/server.sh /usr/local/bin/server.sh

# Asegúrate de que el script sea ejecutable
RUN chmod +x /usr/local/bin/server.sh

# Ejecutar el script de configuración y luego iniciar el servidor
ENTRYPOINT ["/bin/bash", "-c", "/usr/local/bin/server.sh && python /app/server.py"]
