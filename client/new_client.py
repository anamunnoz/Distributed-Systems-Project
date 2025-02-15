import asyncio
import zmq.asyncio
import os
import socket

def upload_file(client_socket: socket.socket, command):
    """Sube un archivo al servidor."""
    try:
        _, file_path = command.split(" ", 1)
        if not os.path.exists(file_path):
            print("[ERROR] Archivo no encontrado.")
            return
        
        file_name = os.path.basename(file_path)
        file_type = file_name.split(".")[-1]

        with open(file_path, "rb") as f:
            content = f.read()
        message = f"{10},{file_name},{file_type},{content}".encode()
        client_socket.sendall(message)
        answer = client_socket.recv(1024)
        print(f"[INFO] Respuesta del servidor: {answer.decode()}")
    except Exception as e:
        print(f"No se pudo procesar el comando: {e}")

def download_file(client_socket, command):
    """Descarga un archivo del servidor."""

    try: 
        parts = command.split(" ")
        if len(parts) < 2:
            print("[ERROR] Comando inválido. Use descargar nombre [tipo]")
            return
        
        file_name = parts[1]
        file_type = parts[2] if len(parts) > 2 else "*"
        message = f"{11},{file_name},{file_type}".encode()
        client_socket.sendall(message)
        print("antes del eval")
        results = eval(client_socket.recv(1024).decode())

        if not results:
            print("[ERROR] No se encontraron resultados.")
            return
        
        print("[INFO] Resultados de búsqueda:")

        for idx, result in enumerate(results, start =1):
            print(f"{idx}. {result['name']} ({result['type']})")

        selection = input("Ingrese el número del archivo a descargar: ")
        if selection.isdigit():
            index = int(selection) -1
            if 0 <= index < len(results):
                client_socket.sendall(f"{12},{results[index]['name']}".encode())
                file = eval(client_socket.recv(1024).decode())
                if 'error' in file:
                    print(f"[ERROR] {file['error']}")
                else:
                    with open(file['name'], 'wb') as f:
                        f.write(file['content'])
                    print(f"[INFO] Archivo descargado y guardado como {file['name']}")
            else:
                print("[ERROR] Número de archivo inválido.")
        else:
            print("[ERROR] Entrada inválida. Debe ser un número.")
    except Exception as e:
        print(f"[ERROR] Error al descargar el archivo: {e}")


def client_program(host="10.0.11.3", port=8001):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client_socket.connect((host, port))
    print("[INFO] Conectado al servidor.")
    
    try:
        while True:
            command = input("Ingrese el comando: ")
            if command.startswith("subir"):
                upload_file(client_socket, command)
            elif command.startswith("descargar"):
                download_file(client_socket, command)
            elif command.startswith("salir"):
                break
            else:
                print("[ERROR] Comando inválido.")
    finally:
        socket.close()
        print("[INFO] Conexión cerrada.")

if __name__ == "__main__":
    client_program()

