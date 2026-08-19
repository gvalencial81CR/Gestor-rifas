# --- CONEXIÓN Y FUNCIONES DE BASE DE DATOS ---
def conectar_db():
    conn = sqlite3.connect("rifa.db")
    c = conn.cursor()

    # 1. Tabla de rifas
    c.execute("""
        CREATE TABLE IF NOT EXISTS rifas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT,
            precio TEXT,
            sinpe_numero TEXT,
            sinpe_nombre TEXT,
            fecha_sorteo TEXT,
            total_numeros TEXT
        )
    """)

    # 2. Tabla de reservas
    c.execute("""
        CREATE TABLE IF NOT EXISTS numeros_comprados (
            rifa_id INTEGER DEFAULT 1,
            numero TEXT,
            comprador TEXT,
            telefono TEXT,
            estado_pago TEXT DEFAULT 'Pendiente',
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 🛠️ MIGRACIÓN AUTOMÁTICA: Si la tabla venía de la versión anterior, agregamos 'rifa_id'
    try:
        c.execute("ALTER TABLE numeros_comprados ADD COLUMN rifa_id INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass  # La columna ya existía

    conn.commit()

    # Si no existe ninguna rifa, creamos la inicial
    c.execute("SELECT COUNT(*) FROM rifas")
    if c.fetchone()[0] == 0:
        c.execute(
            """
            INSERT INTO rifas (titulo, precio, sinpe_numero, sinpe_nombre, fecha_sorteo, total_numeros)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                "🎟️ Gran Rifa Especial 🇨🇷",
                "1000",
                "88888888",
                "Juan Pérez",
                datetime.today().strftime("%Y-%m-%d"),
                "100",
            ),
        )
        conn.commit()

    conn.close()
