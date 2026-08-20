import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import urllib.parse
import streamlit.components.v1 as components

# ==========================================
# 1. CONFIGURACIÓN INICIAL DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Gestión de Rifas",
    page_icon="🎟️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. MANEJO DE LA BASE DE DATOS (SQLite)
# ==========================================
DB_NAME = "rifa_v3.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Tabla de Configuración de la Rifa
    c.execute('''
        CREATE TABLE IF NOT EXISTS configuracion (
            id INTEGER PRIMARY KEY DEFAULT 1,
            titulo TEXT,
            total_numeros INTEGER,
            precio_boleto REAL,
            fecha_sorteo TEXT,
            sinpe_numero TEXT,
            sinpe_nombre TEXT,
            premio_descripcion TEXT,
            reglamento TEXT,
            CONSTRAINT single_row CHECK (id = 1)
        )
    ''')
    # Tabla de Reservas/Compras
    c.execute('''
        CREATE TABLE IF NOT EXISTS reservas (
            numero INTEGER PRIMARY KEY,
            nombre_cliente TEXT,
            telefono_cliente TEXT,
            comprobante TEXT,
            estado TEXT DEFAULT 'Pendiente',
            fecha_reserva TEXT
        )
    ''')
    
    # Insertar configuración inicial por defecto si está vacía
    c.execute("SELECT COUNT(*) FROM configuracion")
    if c.fetchone()[0] == 0:
        c.execute('''
            INSERT INTO configuracion (id, titulo, total_numeros, precio_boleto, fecha_sorteo, sinpe_numero, sinpe_nombre, premio_descripcion, reglamento)
            VALUES (1, 'GRAN RIFA DE UN TELEVISOR 55"', 100, 2000, '2026-12-31', '88888888', 'Juan Pérez', 'Televisor Smart TV 55 Pulgadas 4K Ultra HD.', '1. Rifa válida para mayores de edad.\n2. Pagos por SINPE Móvil.')
        ''')
    conn.commit()
    conn.close()

init_db()

# --- Funciones de lectura/escritura DB ---
def cargar_configuracion():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM configuracion WHERE id = 1", conn)
    conn.close()
    return df.iloc[0].to_dict()

def guardar_configuracion(titulo, total_numeros, precio_boleto, fecha_sorteo, sinpe_numero, sinpe_nombre, premio, reglamento):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        UPDATE configuracion 
        SET titulo = ?, total_numeros = ?, precio_boleto = ?, fecha_sorteo = ?, sinpe_numero = ?, sinpe_nombre = ?, premio_descripcion = ?, reglamento = ?
        WHERE id = 1
    ''', (titulo, total_numeros, precio_boleto, str(fecha_sorteo), sinpe_numero, sinpe_nombre, premio, reglamento))
    conn.commit()
    conn.close()

def cargar_reservas():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM reservas", conn)
    conn.close()
    return df

def guardar_reserva(numero, nombre, telefono, comprobante):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        c.execute('''
            INSERT INTO reservas (numero, nombre_cliente, telefono_cliente, comprobante, estado, fecha_reserva)
            VALUES (?, ?, ?, ?, 'Pendiente', ?)
        ''', (numero, nombre, telefono, comprobante, fecha_hoy))
        conn.commit()
        exito = True
    except sqlite3.IntegrityError:
        exito = False
    conn.close()
    return exito

def actualizar_estado_reserva(numero, nuevo_estado):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE reservas SET estado = ? WHERE numero = ?", (nuevo_estado, numero))
    conn.commit()
    conn.close()

def eliminar_reserva(numero):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM reservas WHERE numero = ?", (numero,))
    conn.commit()
    conn.close()

# Cargar Configuración Actual
config = cargar_configuracion()

# ==========================================
# 3. COMPONENTE VISUAL: CONTADOR REGRESIVO
# ==========================================
def renderizar_contador_regresivo(fecha_sorteo_str):
    html_code = f"""
    <div style="
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        border-radius: 12px;
        padding: 15px;
        color: white;
        text-align: center;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        margin-bottom: 20px;
    ">
        <div style="font-size: 13px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; opacity: 0.9;">
            ⏳ Tiempo restante para el sorteo ⏳
        </div>
        <div id="countdown" style="display: flex; justify-content: center; gap: 10px; align-items: center;">
            <div style="background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(5px); border-radius: 8px; padding: 8px 12px; min-width: 60px;">
                <span id="days" style="font-size: 22px; font-weight: bold; display: block; line-height: 1;">00</span>
                <span style="font-size: 10px; opacity: 0.8; text-transform: uppercase;">Días</span>
            </div>
            <span style="font-size: 20px; font-weight: bold;">:</span>
            <div style="background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(5px); border-radius: 8px; padding: 8px 12px; min-width: 60px;">
                <span id="hours" style="font-size: 22px; font-weight: bold; display: block; line-height: 1;">00</span>
                <span style="font-size: 10px; opacity: 0.8; text-transform: uppercase;">Horas</span>
            </div>
            <span style="font-size: 20px; font-weight: bold;">:</span>
            <div style="background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(5px); border-radius: 8px; padding: 8px 12px; min-width: 60px;">
                <span id="minutes" style="font-size: 22px; font-weight: bold; display: block; line-height: 1;">00</span>
                <span style="font-size: 10px; opacity: 0.8; text-transform: uppercase;">Min</span>
            </div>
            <span style="font-size: 20px; font-weight: bold;">:</span>
            <div style="background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(5px); border-radius: 8px; padding: 8px 12px; min-width: 60px;">
                <span id="seconds" style="font-size: 22px; font-weight: bold; display: block; line-height: 1;">00</span>
                <span style="font-size: 10px; opacity: 0.8; text-transform: uppercase;">Seg</span>
            </div>
        </div>
        <div id="expired-msg" style="display: none; font-size: 16px; font-weight: bold; color: #ff6b6b; margin-top: 5px;">
            🎉 ¡El día del sorteo ha llegado! 🎉
        </div>
    </div>

    <script>
        const targetDate = new Date("{fecha_sorteo_str}T23:59:59").getTime();

        const timer = setInterval(function() {{
            const now = new Date().getTime();
            const difference = targetDate - now;

            if (difference < 0) {{
                clearInterval(timer);
                document.getElementById("countdown").style.display = "none";
                document.getElementById("expired-msg").style.display = "block";
                return;
            }}

            const days = Math.floor(difference / (1000 * 60 * 60 * 24));
            const hours = Math.floor((difference % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((difference % (1000 * 60)) / 1000);

            document.getElementById("days").innerText = days < 10 ? '0' + days : days;
            document.getElementById("hours").innerText = hours < 10 ? '0' + hours : hours;
            document.getElementById("minutes").innerText = minutes < 10 ? '0' + minutes : minutes;
            document.getElementById("seconds").innerText = seconds < 10 ? '0' + seconds : seconds;
        }}, 1000);
    </script>
    """
    components.html(html_code, height=125)

# ==========================================
# 4. BARRA LATERAL (PANEL ADMINISTRADOR)
# ==========================================
st.sidebar.title("🔐 Panel de Administración")
pwd = st.sidebar.text_input("Contraseña de Acceso:", type="password")

if pwd == "1234":
    st.sidebar.success("Acceso Concedido")
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Configuración General")
    
    with st.sidebar.form("form_config"):
        edit_titulo = st.text_input("Título de la Rifa:", config["titulo"])
        edit_total = st.number_input("Total de Números:", min_value=10, max_value=1000, value=int(config["total_numeros"]))
        edit_precio = st.number_input("Precio por Número (₡):", min_value=100, value=int(config["precio_boleto"]))
        
        # Fecha del sorteo con selector de calendario
        fecha_dt = datetime.strptime(config["fecha_sorteo"], "%Y-%m-%d").date()
        edit_fecha = st.date_input("Fecha del Sorteo:", value=fecha_dt)
        
        edit_sinpe_num = st.text_input("Número SINPE Móvil:", config["sinpe_numero"])
        edit_sinpe_nom = st.text_input("Nombre Titular SINPE:", config["sinpe_nombre"])
        edit_premio = st.text_area("Descripción del Premio:", config["premio_descripcion"])
        edit_reglamento = st.text_area("Reglamento:", config["reglamento"])
        
        if st.form_submit_button("💾 Guardar Configuración"):
            guardar_configuracion(edit_titulo, edit_total, edit_precio, edit_fecha, edit_sinpe_num, edit_sinpe_nom, edit_premio, edit_reglamento)
            st.success("¡Configuración guardada!")
            st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Estado de Reservas")
    df_admin = cargar_reservas()
    if not df_admin.empty:
        st.sidebar.dataframe(df_admin[["numero", "nombre_cliente", "estado"]])
    else:
        st.sidebar.info("Sin reservas aún.")

# ==========================================
# 5. VISTA PRINCIPAL (USUARIO COMPRADOR)
# ==========================================

st.title(f"🎟️ {config['titulo']}")
st.caption(f"📅 **Fecha del Sorteo:** {config['fecha_sorteo']} | 💵 **Precio por Número:** ₡{int(config['precio_boleto']):,}")

# --- CONTADOR REGRESIVO INTERACTIVO ---
renderizar_contador_regresivo(config["fecha_sorteo"])

tab_comprar, tab_premio, tab_reglamento = st.tabs(
    ["🎟️ Comprar Números", "🎁 Premio Único", "📜 Reglamento"]
)

# ------------------------------------------
# PESTAÑA 1: COMPRAR NÚMEROS
# ------------------------------------------
with tab_comprar:
    df_res = cargar_reservas()
    
    # Mapear estados de números
    numeros_ocupados = df_res[df_res['estado'] == 'Pagado']['numero'].tolist() if not df_res.empty else []
    numeros_pendientes = df_res[df_res['estado'] == 'Pendiente']['numero'].tolist() if not df_res.empty else []
    
    # Leyenda
    c1, c2, c3 = st.columns(3)
    c1.markdown("🟩 **Disponible**")
    c2.markdown("🟧 **Pendiente**")
    c3.markdown("🟥 **Pagado**")
    st.markdown("---")
    
    # Cuadrícula de Números (Lógica visual)
    st.subheader("Selecciona tus números:")
    total_nums = int(config["total_numeros"])
    cols = st.columns(5)
    
    for i in range(1, total_nums + 1):
        col_idx = (i - 1) % 5
        with cols[col_idx]:
            if i in numeros_ocupados:
                st.button(f"🔴 {i:02d}", key=f"btn_{i}", disabled=True)
            elif i in numeros_pendientes:
                st.button(f"🟠 {i:02d}", key=f"btn_{i}", disabled=True)
            else:
                st.button(f"🟢 {i:02d}", key=f"btn_{i}", disabled=False)

    st.markdown("---")
    st.subheader("📝 Formulario de Reserva")
    
    with st.form("form_reserva", clear_on_submit=True):
        num_elegido = st.number_input("Número a Reservar:", min_value=1, max_value=total_nums, step=1)
        nombre = st.text_input("Nombre Completo:")
        telefono = st.text_input("Teléfono / WhatsApp:")
        comprobante = st.text_input("Número de Comprobante SINPE:")
        
        st.info(f"📱 **Realizar SINPE Móvil al:** `{config['sinpe_numero']}` ({config['sinpe_nombre']})\nMonto: **₡{int(config['precio_boleto']):,}**")
        
        btn_reservar = st.form_submit_button("✅ Enviar Reserva por WhatsApp")
        
        if btn_reservar:
            if not nombre or not telefono or not comprobante:
                st.error("Por favor completa todos los campos del formulario.")
            elif num_elegido in numeros_ocupados or num_elegido in numeros_pendientes:
                st.error("El número seleccionado ya se encuentra ocupado o pendiente.")
            else:
                exito = guardar_reserva(num_elegido, nombre, telefono, comprobante)
                if exito:
                    st.success(f"¡Reserva del número {num_elegido} registrada con éxito!")
                    
                    # Generar enlace a WhatsApp
                    msg = (
                        f"Hola, acabo de realizar la reserva de la Rifa *{config['titulo']}*:\n\n"
                        f"🎟️ *Número:* {num_elegido}\n"
                        f"👤 *Nombre:* {nombre}\n"
                        f"📞 *Teléfono:* {telefono}\n"
                        f"🧾 *Comprobante SINPE:* {comprobante}\n\n"
                        f"Quedo a la espera de la confirmación."
                    )
                    url_wa = f"https://wa.me/506{config['sinpe_numero']}?text={urllib.parse.quote(msg)}"
                    st.markdown(f"[💬 **Haz clic aquí para enviar la confirmación por WhatsApp**]({url_wa})")
                    st.rerun()
                else:
                    st.error("Hubo un error al guardar la reserva. Inténtalo de nuevo.")

# ------------------------------------------
# PESTAÑA 2: PREMIO ÚNICO
# ------------------------------------------
with tab_premio:
    st.subheader("🎁 Detalles del Premio")
    st.write(config["premio_descripcion"])

# ------------------------------------------
# PESTAÑA 3: REGLAMENTO
# ------------------------------------------
with tab_reglamento:
    st.subheader("📜 Términos y Condiciones")
    st.write(config["reglamento"])
