import os
import socket
import struct

MULTICAST_GROUP = '224.0.0.1'
MULTICAST_PORT = 10000


def upload_file(command):
    # Crear socket multicast
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)  # Esperar 5 segundos por una respuesta
    sock.bind(("",MULTICAST_PORT))

    # Unirse al grupo multicast
    group = socket.inet_aton(MULTICAST_GROUP)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    # Enviar solicitud de descubrimiento
    discover_message = b"DISCOVER_NODE"
    sock.sendto(discover_message, (MULTICAST_GROUP, MULTICAST_PORT))

    # Esperar respuesta de un nodo
    try:
        print("Esperando respuesta de un nodo...")
        while True:
            data, addr = sock.recvfrom(1024)
            if data == b"DISCOVER_NODE":
                continue
            node_ip = data.decode()  # La IP del nodo activo
            print(f"Nodo descubierto: {node_ip}")
            break

        # Ahora el cliente puede conectarse directamente al nodo
        # Ejemplo de conexión TCP:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.setblocking(True)
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client_socket.connect((node_ip, 8001))  # Conectar al puerto 5000 del nodo
        print(f"Conectado al nodo {node_ip}")
    except socket.timeout:
        print("No se recibió respuesta de ningún nodo.") 
    finally:
        sock.close()

    """Sube un archivo al servidor."""
    try:
        _, file_path = command.split(" ", 1)
        if not os.path.exists(file_path):
            print("[ERROR] Archivo no encontrado.")
            return
        
        file_name = os.path.basename(file_path)
        file_type = file_name.split(".")[-1]
        file_size = os.path.getsize(file_path)
        client_socket.send(f"{10},{file_name},{file_type},{file_size}".encode())
        ready = client_socket.recv(1024).decode()
        if ready == 'READY':
            with open(file_path, "rb") as f:
                while chunk := f.read(1024000):
                    client_socket.send(chunk)
            response = client_socket.recv(1024).decode()
            if response == '':
                print("Inserte nuevamente el comando")
                return
            print(f"[INFO] Respuesta del servidor: {response}")
            client_socket.close()
    except Exception as e:
        print("Inserte nuevamente el comando")
        client_socket.close()


def download_file(command):
    # Crear socket multicast
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)  # Esperar 5 segundos por una respuesta


    # Unirse al grupo multicast
    group = socket.inet_aton(MULTICAST_GROUP)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    sock.bind(("",MULTICAST_PORT))
    # Enviar solicitud de descubrimiento
    discover_message = b"DISCOVER_NODE"
    sock.sendto(discover_message, (MULTICAST_GROUP, MULTICAST_PORT))

    # Esperar respuesta de un nodo
    try:
        print("Esperando respuesta de un nodo...")
        while True:
            data, addr = sock.recvfrom(1024)
            if data == b"DISCOVER_NODE":
                continue
            node_ip = data.decode()  # La IP del nodo activo
            print(f"Nodo descubierto: {node_ip}")
            break

        # Ahora el cliente puede conectarse directamente al nodo
        # Ejemplo de conexión TCP:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.setblocking(True)
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client_socket.connect((node_ip, 8001))  # Conectar al puerto 5000 del nodo
        print(f"Conectado al nodo {node_ip}")
    except socket.timeout:
        print("No se recibió respuesta de ningún nodo.")
    finally:
        sock.close()
    
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
        hashes=[]
        files=[]
        nodes=[]
        for i in range(len(results)):
            if results[i]['hash'] not in hashes:
                hashes.append(results[i]['hash'])
                nodes.append([results[i]['ip']])
                files.append(results[i])
            else:
                nodes[hashes.index(results[i]['hash'])].append(results[i]['ip'])

        print("[INFO] Resultados de búsqueda:")

        for idx, result in enumerate(files, start =1):
            print(f"{idx}. {result['name']} ({result['type']})")

        selection = input("Ingrese el número del archivo a descargar: ")
        if selection.isdigit():
            index = int(selection) -1
            if 0 <= index < len(files):
                    i=0
                    for ip in nodes[index]:
                        i+=1
                        try:
                            host=ip
                            port=8001
                            client_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            client_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                            client_s.connect((host, port))
                            print(f"Conectado a {host}")
                            name=files[index]['name']
                            client_s.send(f"{12},{name}".encode())
                            size = int(client_s.recv(1024).decode())
                            remainder = size
                            client_s.send('ACK'.encode())
                            with open(name, 'wb') as f:
                                while remainder > 0:
                                    chunk = client_s.recv(min(remainder,1024000))
                                    f.write(chunk)
                                    remainder -= len(chunk)
                                    
                            print(f"[INFO] Archivo descargado y guardado como {name}")
                            client_s.close()
                            break
                        except:
                            pass
                    if i == len(nodes[index]): print("Ingrese el comando de descarga nuevamente")
                    
            else:
                print("[ERROR] Número de archivo inválido.")
        else:
            print("[ERROR] Entrada inválida. Debe ser un número.")
        client_socket.close()

    except Exception as e:
        print(f"[ERROR] Error al descargar el archivo: {e}")
        client_socket.close()


def client_program(host="10.0.11.3", port=8001):
    print("[INFO] Conectado al servidor.")
    
    try:
        while True:
            mes = ''' Ingrese el comando según la siguiente lista:
                - subir <ruta_archivo>
                - descargar <nombre_archivo> <tipo_archivo>(opcional)
                - salir
            '''
            command = input(mes)
            if command.startswith("subir"):
                upload_file(command)
            elif command.startswith("descargar"):
                download_file(command)
            elif command.startswith("salir"):
                break
            else:
                print("[ERROR] Comando inválido.")
    finally:
        print("[INFO] Conexión cerrada.")

if __name__ == "__main__":
    client_program()

