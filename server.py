import os
import socket
import threading
import hashlib

# Directorio para almacenar archivos
STORAGE_DIR = "server_files"
os.makedirs(STORAGE_DIR, exist_ok=True)

# Diccionario para almacenar metadatos de archivos
file_registry = {}  # {hash: [file_path_1, file_path_2]}


def compute_hash(file_content):
    """Calcula el hash de un archivo."""
    return hashlib.sha256(file_content).hexdigest()

def handle_client(client_socket, client_address):
    print(f"[INFO] Conexión establecida con {client_address}")
    try:
        while True:
            # Recibir comando del cliente
            command = client_socket.recv(1024).decode()
            if not command:
                break
            print(f"[INFO] Comando recibido: {command}")
            
            if command.startswith("UPLOAD"):
                client_socket.send("mande".encode())
                _, file_name, file_type = command.split("|")
                file_content = client_socket.recv(1024 * 1024)  # Recibir el archivo

                file_hash = compute_hash(file_content)

                # Evitar duplicados
                if file_hash in file_registry:
                    file_registry[file_hash].append(file_name)
                    response = f"EXISTS|{file_registry[file_hash][0]}"
                else:
                    file_path = os.path.join(STORAGE_DIR, file_name)
                    with open(file_path, "wb") as f:
                        f.write(file_content)
                    file_registry[file_hash] = [file_name]
                    response = "UPLOADED"

                client_socket.send(response.encode())
            
            elif command.startswith("SEARCH"):
                _, search_term, file_type = command.split("|")
                results = []

                for file_hash, names in file_registry.items():
                    for name in names:
                        if (search_term in name) and (name.endswith(file_type) or file_type == "*"):
                            results.append(name)

                response = "\n".join(results) if results else "NO_RESULTS"
                client_socket.send(response.encode())
            else:
                client_socket.send("INVALID_COMMAND".encode())
    except Exception as e:
        print(f"[ERROR] Error manejando cliente {client_address}: {e}")
    finally:
        client_socket.close()
        print(f"[INFO] Conexión cerrada con {client_address}")

def start_server(host="0.0.0.0", port=5000):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"[INFO] Servidor escuchando en {host}:{port}")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_thread.start()
    except KeyboardInterrupt:
        print("[INFO] Apagando el servidor.")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()