import os
import socket
import threading
import hashlib
import sqlite3
from datetime import datetime

# Configuración de SQLite
DB_FILE = "db/server_files.db"
db_lock = threading.Lock() #Para manejar la concurrencia en SQLite

# Crear directorio de base de datos si no existe
os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

# Crear tablas si no existen
with db_lock:
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hash TEXT UNIQUE NOT NULL,
        content BLOB NOT NULL,
        type TEXT NOT NULL,
        timestamp TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS file_names (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        FOREIGN KEY (file_id) REFERENCES files (id)
    )
    ''')
    conn.commit()

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
                
                # Recibir contenido del archivo
                file_content = b""
                while True:
                    chunk = client_socket.recv(1024000)
                    if chunk == b"EOF":
                        break
                    file_content += chunk
                    client_socket.send("next".encode())

                file_hash = compute_hash(file_content)
                
                with db_lock:
                    # Verificar si el archivo ya existe
                    cursor.execute('SELECT id FROM files WHERE hash = ?', (file_hash,))
                    file_record = cursor.fetchone()
                    
                    if file_record:
                        file_id = file_record[0]
                        # Verificar si el nombre ya está asociado
                        cursor.execute('SELECT name FROM file_names WHERE file_id = ? AND name = ?', (file_id, file_name))
                        name_record = cursor.fetchone()

                        if not name_record: 
                            # Registrar el nuevo nombre
                            cursor.execute('INSERT INTO file_names (file_id, name) VALUES (?, ?)', (file_id, file_name))
                            conn.commit()
                            response = f"ALIAS_ADDED|{file_name}"
                        else:
                            response = f"EXISTS|{file_name}"

                        
                    else:
                        # Registrar el nuevo archivo con su contenido binario
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        cursor.execute('INSERT INTO files (hash, content, type, timestamp) VALUES (?, ?, ?, ?)',
                                    (file_hash, file_content, file_type, timestamp))
                        file_id = cursor.lastrowid

                        # Registrar el nombre inicial
                        cursor.execute('INSERT INTO file_names (file_id, name) VALUES (?, ?)', (file_id, file_name))
                        conn.commit()
                        response = "UPLOADED"

                client_socket.send(response.encode())
            
            elif command.startswith("SEARCH"):
                _, search_term, file_type = command.split("|")
                query = '''
                SELECT DISTINCT fn.name, f.type, f.timestamp
                FROM files f
                JOIN file_names fn ON f.id = fn.file_id
                WHERE fn.name LIKE ? 
                '''
                params = (f"%{search_term}%",)
                if file_type != "*":
                    query += ' AND f.type = ?'
                    params += (file_type,)

                with db_lock:
                    cursor.execute(query, params)
                    results = cursor.fetchall() 

                if results:
                    response = "\n".join(
                        [f"{i+1}. Name: {r[0]}, Type: {r[1]}, Uploaded: {r[2]}" for i,r in enumerate(results)]
                    )
                    response += "\nEND_RESULTS"
                else: 
                    response = "NO_RESULTS"

                client_socket.send(response.encode())

            elif command.startswith("DOWNLOAD"):
                _, file_name = command.split("|")
                query = '''
                SELECT f.content, f.type FROM files f
                JOIN file_names fn ON f.id = fn.file_id
                WHERE fn.name = ?
                '''

                with db_lock:
                    cursor.execute(query, (file_name,))
                    result = cursor.fetchone()

                if result:
                    file_content, file_type = result
                    client_socket.send(f"TYPE|{file_type}".encode())  # Enviar tipo de archivo
                    client_socket.recv(1024)  # Confirmación

                    # Enviar contenido
                    for i in range(0, len(file_content), 1024000):
                        chunk = file_content[i:i+1024000]
                        client_socket.send(chunk)
                        client_socket.recv(1024)  # Confirmación
                    client_socket.send(b"EOF")
                else:
                    client_socket.send(b"FILE NOT FOUND")
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