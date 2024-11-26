import socket
import os

def upload_file(client_socket, file_path, file_type):
    """Sube un archivo al servidor."""
    if not os.path.exists(file_path):
        print("[ERROR] Archivo no encontrado.")
        return
    
    file_name = os.path.basename(file_path)

    command = f"UPLOAD|{file_name}|{file_type}"
    client_socket.send(command.encode())
    w = client_socket.recv(1024).decode()
    if w=="mande":
        with open(file_path, "rb") as f:
            while chunk := f.read(4096):  # Leer en fragmentos de 4 KB
                client_socket.send(chunk)
                ne=client_socket.recv(1024).decode()
                if ne=="next":
                    pass
        
        client_socket.send(b"EOF")  # Señal de fin de archivo

    
    response = client_socket.recv(1024).decode()
    print(f"[INFO] Respuesta del servidor: {response}")

def search_files(client_socket, search_term, file_type):
    """Busca archivos en el servidor."""
    command = f"SEARCH|{search_term}|{file_type}"
    client_socket.send(command.encode())
    
    response = client_socket.recv(1024).decode()
    print(f"[INFO] Resultados de búsqueda:\n{response}")

def client_program(host="127.0.0.1", port=5000):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    print("[INFO] Conectado al servidor.")
    
    try:
        while True:
            print("\n1. Subir archivo")
            print("2. Buscar archivo")
            print("3. Salir")
            choice = input("Seleccione una opción: ")
            
            if choice == "1":
                file_path = input("Ingrese la ruta del archivo: ")
                file_type = input("Ingrese el tipo de archivo (txt, jpg, mp3, etc.): ")
                upload_file(client_socket, file_path, file_type)
            elif choice == "2":
                search_term = input("Ingrese el término de búsqueda: ")
                file_type = input("Ingrese el tipo de archivo (* para todos): ")
                search_files(client_socket, search_term, file_type)
            elif choice == "3":
                break
            else:
                print("[ERROR] Opción inválida.")
    finally:
        client_socket.close()
        print("[INFO] Conexión cerrada.")

if __name__ == "__main__":
    client_program()
