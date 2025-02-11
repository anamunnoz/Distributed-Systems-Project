import asyncio
import zmq.asyncio
import os
import hashlib
import sqlite3


# Configuración de SQLite
DB_FILE = "db/server_files.db"
db_lock = asyncio.Lock() #Para manejar la concurrencia en SQLite

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
        type TEXT NOT NULL
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


async def save_file(file_name, file_type, file_content):
    """Guarda un archivo en la base de datos."""
    async with db_lock:
        file_hash = compute_hash(file_content)
        cursor.execute('SELECT id FROM files WHERE hash = ?', (file_hash,))
        file_record = cursor.fetchone()

        if file_record:
            file_id = file_record[0]
            cursor.execute('SELECT name FROM file_names WHERE file_id = ? AND name = ?', (file_id, file_name))
            name_record = cursor.fetchone()

            if not name_record:
                cursor.execute('INSERT INTO file_names (file_id, name) VALUES (?, ?)', (file_id, file_name))
                conn.commit()
                return "Nombre agregado al archivo existente"
            return "El archivo ya existe con ese nombre"
        else:
            cursor.execute('INSERT INTO files (hash, content, type) VALUES (?, ?, ?)', (file_hash, file_content, file_type))
            file_id = cursor.lastrowid
            cursor.execute('INSERT INTO file_names (file_id, name) VALUES (?, ?)', (file_id, file_name))
            conn.commit()
            return "Archivo subido correctamente"

async def search_file(file_name, file_type):
    """Busca un archivo en la base de datos."""
    query = '''SELECT DISTINCT fn.name, f.type
    FROM files f JOIN file_names fn ON 
    f.id = fn.file_id WHERE fn.name LIKE ?'''
    params = (f"%{file_name}%",)
    if file_type != "*":
        query += ' AND f.type = ?'
        params += (file_type,)
    cursor.execute(query, params)
    return [{"name": row[0], "type": row[1]} for row in cursor.fetchall()]

async def download_file(file_name):
    """Descarga un archivo de la base de datos."""
    cursor.execute('''SELECT f.content, fn.name FROM files f
    JOIN file_names fn ON f.id = fn.file_id WHERE fn.name = ?''', (file_name,))
    result = cursor.fetchone()
    return {'name': result[1], 'content': result[0]} if result else None

async def handle_client(client_socket):
    try:
        while True:
            # Recibir comando del cliente
            command = await client_socket.recv_pyobj()
            if command['action'] == 'subir':
                answer = await save_file( command['file_name'], command['file_type'], command['file_content'])
                await client_socket.send_string(answer)
            elif command['action'] == 'buscar':
                answer = await search_file(command['file_name'], command['file_type'])
                await client_socket.send_pyobj(answer)
            elif command['action'] == 'descargar':
                answer = await download_file(command['file_name'])
                await client_socket.send_pyobj(answer if answer else {'error': 'Archivo no encontrado'}) 
            elif command['action'] == 'salir':
                break
    except Exception as e:
        print(f"[ERROR] Error manejando cliente. Error: {e}")
    finally:
        client_socket.close()
        print(f"[INFO] Conexión cerrada")

async def start_server(host="0.0.0.0", port=5000):
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://{host}:{port}")
    print(f"[INFO] Servidor escuchando en {host}:{port}")

    try:
        while True:
            await handle_client(socket)
    except KeyboardInterrupt:
        print("[INFO] Apagando el servidor.")
    finally:
        socket.close()

if __name__ == "__main__":
    asyncio.run(start_server())