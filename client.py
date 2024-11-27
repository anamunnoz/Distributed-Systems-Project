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

def search_files(client_socket):
    """Busca archivos en el servidor y permite elegir para descargar."""
    search_term = input("Ingrese el término de búsqueda: ")
    file_type = input("Ingrese el tipo de archivo (* para todos): ")
    command = f"SEARCH|{search_term}|{file_type}"
    client_socket.send(command.encode())
    
    response = client_socket.recv(4096).decode()
    if response == "NO_RESULTS":
        print("[INFO] No se encontraron resultados.")
        return
    
    print("[INFO] Resultados de búsqueda:")
    results = response.split("\n")
    for line in results:
        if line == "END_RESULTS":
            break
        print(line)

    save_dir = input("Ingrese la ruta donde desea guardar los archivos o escriba \"EXIT\" para salir: ").strip()

    if save_dir != "EXIT":
            
        if not os.path.isdir(save_dir):
            print("[ERROR] La ruta proporcionada no es válida.")
            return

        # Permitir al usuario elegir archivos para descargar
        selected_files = input(
            "Ingrese los números de los archivos que desea descargar (separados por comas): "
        ).split(",")
        selected_files = [int(i.strip()) - 1 for i in selected_files if i.strip().isdigit()]

        for index in selected_files:
            if 0 <= index < len(results) - 1:
                file_info = results[index].split(",")[0].split(": ")[1]  # Obtener nombre
                download_file(client_socket, file_info,save_dir)

def download_file(client_socket, file_name, save_dir):
    """Descarga un archivo del servidor."""
    command = f"DOWNLOAD|{file_name}"
    client_socket.send(command.encode())

    # Recibir tipo de archivo
    response = client_socket.recv(1024).decode()
    if response.startswith("TYPE|"):
        _, file_type = response.split("|")
        client_socket.send(b"READY")

        save_path = os.path.join(save_dir,file_name)
        # Recibir contenido y guardar
        with open(save_path, 'wb') as f:
            while True:
                chunk = client_socket.recv(4096)
                if chunk == b"EOF":
                    break
                f.write(chunk)
                client_socket.send(b"next")  # Confirmación
        print(f"[INFO] Archivo descargado y guardado como {save_path}.{file_type}.")
    else:
        print("[ERROR] Archivo no encontrado.")

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
                search_files(client_socket)
            elif choice == "3":
                break
            else:
                print("[ERROR] Opción inválida.")
    finally:
        client_socket.close()
        print("[INFO] Conexión cerrada.")

if __name__ == "__main__":
    client_program()
