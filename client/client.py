import asyncio
import zmq.asyncio
import os

async def upload_file(client_socket, command):
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
        message = {'action': 'subir', 'file_name': file_name, 'file_type': file_type, 'file_content': content}
        await client_socket.send_pyobj(message)
        answer = await client_socket.recv_string()
        print(f"[INFO] Respuesta del servidor: {answer}")
    except Exception as e:
        print(f"No se pudo procesar el comando: {e}")

async def download_file(client_socket, command):
    """Descarga un archivo del servidor."""

    try: 
        parts = command.split(" ")
        if len(parts) < 2:
            print("[ERROR] Comando inválido. Use descargar nombre [tipo]")
            return
        
        file_name = parts[1]
        file_type = parts[2] if len(parts) > 2 else "*"
        message = {'action': 'buscar', 'file_name': file_name, 'file_type': file_type}
        await client_socket.send_pyobj(message)
        results = await client_socket.recv_pyobj()

        if not results:
            print("[ERROR] No se encontraron resultados.")
            return
        
        print("[INFO] Resultados de búsqueda:")

        for idx, result in enumerate(results, satrt =1):
            print(f"{idx}. {result['name']} ({result['type']})")

        selection = input("Ingrese el número del archivo a descargar: ")
        if selection.isdigit():
            index = int(selection) -1
            if 0 <= index < len(results):
                await client_socket.send_pyobj({'action': 'descargar', 'file_name': results[index]['name']})
                file = await client_socket.recv_pyobj()
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


async def client_program(host="10.0.11.2", port=5000):
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(f"tcp://{host}:{port}")
    print("[INFO] Conectado al servidor.")
    
    try:
        while True:
            command = input("Ingrese el comando: ")
            if command.startswith("subir"):
                await upload_file(socket, command)
            elif command.startswith("descargar"):
                await download_file(socket, command)
            elif command.startswith("salir"):
                break
            else:
                print("[ERROR] Comando inválido.")
    finally:
        socket.close()
        print("[INFO] Conexión cerrada.")

if __name__ == "__main__":
    asyncio.run(client_program())
