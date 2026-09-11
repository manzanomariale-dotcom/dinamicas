import sqlite3
from config import Config

def get_db_connection():
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tabla de Administradores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')

    # Tabla de Dinámicas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dynamycs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            draw_datetime TEXT NOT NULL,
            status TEXT DEFAULT 'ACTIVA' -- ACTIVA, CERRADA
        )
    ''')

    # Tabla de Tickets
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dynamic_id INTEGER NOT NULL,
            client_name TEXT NOT NULL,
            client_phone TEXT NOT NULL,
            raw_text TEXT NOT NULL,
            extracted_agency TEXT,
            extracted_serial TEXT NOT NULL,
            extracted_amount REAL NOT NULL,
            participation_number TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'PENDIENTE', -- PENDIENTE, VALIDADO, RECHAZADO
            reject_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dynamic_id) REFERENCES dynamycs (id)
        )
    ''')

    # Tabla de Ganadores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS winners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dynamic_id INTEGER UNIQUE NOT NULL,
            ticket_id INTEGER NOT NULL,
            client_name TEXT NOT NULL,
            masked_phone TEXT NOT NULL,
            participation_number TEXT NOT NULL,
            serial TEXT NOT NULL,
            drawn_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dynamic_id) REFERENCES dynamycs (id),
            FOREIGN KEY (ticket_id) REFERENCES tickets (id)
        )
    ''')

    # Crear admin por defecto si no existe (admin / admin123)
    from werkzeug.security import generate_password_hash
    cursor.execute("SELECT * FROM admins WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO admins (username, password_hash) VALUES (?, ?)",
                       ('admin', generate_password_hash('admin123')))

    # Crear dinámica #001 por defecto si no existe ninguna activa
    cursor.execute("SELECT * FROM dynamycs WHERE status = 'ACTIVA'")
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO dynamycs (name, start_date, end_date, draw_datetime, status)
            VALUES (?, ?, ?, ?, ?)
        ''', ('DINÁMICA #001', '2026-09-07', '2026-09-13', '2026-09-13T20:00', 'ACTIVA'))

    conn.commit()
    conn.close()