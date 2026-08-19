import sqlite3
import urllib.parse
from datetime import datetime, date
import pandas as pd
import streamlit as st
import re
import base64

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Gestor de Rifas CR 🇨🇷", 
    layout="centered", 
    page_icon="🎟️"
)

# Configura aquí tu URL desplegada
URL_APP = "https://tu-app-de-rifa.streamlit.app"

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown(
    """
    <style>
    .stButton>button {
        width: 100%;
        height: 3em;
        font-weight: bold;
        border-radius: 8px;
    }
    .premio-card {
        border: 2px solid #e0e0e0;
        padding: 20px;
        border-radius: 15px;
        background-color: #ffffff;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .ticket-box {
        border: 2px dashed #0056b3;
        background-color: #eef6ff;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 8px 8px 0px 0px;
        padding-top: 10px;
        padding-bottom: 10px;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0056b3 !important;
        color: white !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# --- CONEXIÓN Y BASE DE DATOS ---
def conectar_db():
    conn = sqlite3.connect("rifa_v3.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS numeros_comprados (
            numero TEXT PRIMARY KEY,
            comprador TEXT,
            telefono TEXT,
            estado_pago TEXT DEFAULT 'Pendiente',
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS configuracion (
            clave TEXT PRIMARY KEY,
            valor TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS premios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lugar TEXT,
            nombre TEXT,
            descripcion TEXT,
            imagen_data TEXT
        )
    """)

    conn.commit()
    return conn


def obtener_configuracion():
    conn = conectar_db()
    c = conn.cursor()
    c.execute("SELECT clave, valor FROM configuracion")
    filas = c.fetchall()
    conn.close()

    config = {
        "rifa_titulo": "🎟️ Gran Rifa Especial 🇨🇷",
        "rifa_precio": "1000",
        "sinpe_numero": "88888888",
        "sinpe_nombre": "Juan Pérez",
        "rifa_fecha_sorteo": datetime.today().strftime("%Y-%m-%d"),
        "total_numeros": "100",
    }

    for clave, valor in filas:
        config[clave] = valor

    return config


def guardar_configuracion(titulo, precio, num_sinpe, nombre_sinpe, fecha_str, total_nums):
    conn = conectar_db()
    c = conn.cursor()
    datos = [
        ("rifa_titulo", titulo),
        ("rifa_precio", str(precio)),
        ("sinpe_numero", num_sinpe),
        ("sinpe_nombre", nombre_sinpe),
        ("rifa_fecha_sorteo", fecha_str),
        ("total_numeros", str(total_nums)),
    ]
    c.executemany(
        "INSERT OR REPLACE INTO configuracion (clave, valor) VALUES (?, ?)", datos
    )
    conn.commit()
    conn.close()


def procesar_imagen_a_base64(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        return base64.b64encode(bytes_data).decode("utf-8")
    return ""


def agregar_premio(lugar, nombre, descripcion, imagen_data):
    conn = conectar_db()
    c = conn.cursor()
    c.execute("DELETE FROM premios")
    c.execute(
        "INSERT INTO premios (lugar, nombre, descripcion, imagen_data) VALUES (?, ?, ?, ?)",
        (lugar, nombre, descripcion, imagen_data),
    )
    conn.commit()
    conn.close()


def obtener_premios():
    conn = conectar_db()
    c = conn.cursor()
    c.execute("SELECT id, lugar, nombre, descripcion, imagen_data FROM premios ORDER BY id DESC LIMIT 1")
    filas = c.fetchall()
    conn.close()
    return filas


def eliminar_premio(premio_id):
    conn = conectar_db()
    c = conn.cursor()
    c.execute("DELETE FROM premios WHERE id = ?", (premio_id,))
    conn.commit()
    conn.close()


def obtener_mapa_numeros_ocupados():
    conn = conectar_db()
    c = conn.cursor()
    c.execute("SELECT numero, estado_pago FROM numeros_comprados")
    filas = c.fetchall()
    conn.close()
    return {f[0]: f[1] for f in filas}


def guardar_reserva(numeros, nombre, telefono):
    conn = conectar_db()
    c = conn.cursor()
    exitosos = []
    fallidos = []

    for num in numeros:
        try:
            c.execute(
                "INSERT INTO numeros_comprados (numero, comprador, telefono, estado_pago) VALUES (?, ?, ?, 'Pendiente')",
                (num, nombre, telefono),
            )
            exitosos.append(num)
        except sqlite3.IntegrityError:
            fallidos.append(num)

    conn.commit()
    conn.close()
    return exitosos, fallidos


def obtener_todas_las_reservas():
    conn = conectar_db()
    query = (
        "SELECT numero AS 'Número', comprador AS 'Comprador', telefono AS 'Teléfono', "
        "estado_pago AS 'Estatus Pago', fecha AS 'Fecha Reserva' "
        "FROM numeros_comprados ORDER BY CAST(numero AS INTEGER) ASC"
    )
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def cambiar_estado_pago(numero, nuevo_estado):
    conn = conectar_db()
    c = conn.cursor()
    c.execute("UPDATE numeros_comprados SET estado_pago = ? WHERE numero = ?", (nuevo_estado, numero))
    conn.commit()
    conn.close()


def liberar_numero(numero):
    conn = conectar_db()
    c = conn.cursor()
    c.execute("DELETE FROM numeros_comprados WHERE numero = ?", (numero,))
    conn.commit()
    conn.close()


def reiniciar_rifa():
    conn = conectar_db()
    c = conn.cursor()
    c.execute("DELETE FROM numeros_comprados")
    conn.commit()
    conn.close()


# --- CARGAR CONFIGURACIÓN PERMANENTE ---
config_actual = obtener_configuracion()
total_numeros_config = int(config_actual.get("total_numeros", 100))
precio_numero = int(config_actual["rifa_precio"])
num_limpio = config_actual["sinpe_numero"]
nombre_sinpe = config_actual["sinpe_nombre"]
titulo_rifa = config_actual["rifa_titulo"]

try:
    fecha_sorteo_db = datetime.strptime(config_actual["rifa_fecha_sorteo"], "%Y-%m-%d").date()
except (KeyError, ValueError):
    fecha_sorteo_db = date.today()

fecha_formateada = fecha_sorteo_db.strftime("%d/%m/%Y")

# --- INICIALIZACIÓN DE ESTADO ---
if "reserva_confirmada" not in st.session_state:
    st.session_state.reserva_confirmada = False
if "seleccionados_global" not in st.session_state:
    st.session_state.seleccionados_global = []

# --- ENCABEZADO PRINCIPAL ---
st.title(titulo_rifa)
st.caption(f"📅 **Fecha del Sorteo:** {fecha_formateada} | 🎟️ **Valor del número:** ₡{precio_numero:,.0f} CRC")

# --- PESTAÑAS PRINCIPALES ---
tab_comprar, tab_estado, tab_admin = st.tabs([
    "🎟️ Comprar Boletos", 
    "📊 Estado de Números", 
    "🔐 Administración"
])

# =============================================================
# 🎟️ PESTAÑA 1: COMPRAR BOLETOS
# =============================================================
with tab_comprar:
    # Premio Único
    premios = obtener_premios()
    if premios:
        _, _, p_nombre, p_desc, p_img = premios[0]
        st.markdown('<div class="premio-card">', unsafe_allow_html=True)
        col_p1, col_p2 = st.columns([1, 2]) if p_img else (None, st)
        
        if p_img and col_p1:
            with col_p1:
                try:
                    st.image(base64.b64decode(p_img), use_container_width=True)
                except Exception:
                    pass
            with col_p2:
                st.subheader("🏆 Premio Único")
                st.markdown(f"## {p_nombre}")
                if p_desc: st.write(p_desc)
        else:
            st.subheader("🏆 Premio Único")
            st.markdown(f"## {p_nombre}")
            if p_desc: st.write(p_desc)
            
        st.markdown('</div>', unsafe_allow_html=True)

    # Proceso de reserva
    if st.session_state.reserva_confirmada:
        st.balloons()
        st.success("🎉 ¡Reserva realizada con éxito!")
        st.markdown(
            f"""
            <div class="ticket-box">
                <h3>🎟️ BOLETO DIGITAL DE RESERVA</h3>
                <p><b>Comprador:</b> {st.session_state.nombre_reserva}</p>
                <p><b>Número(s):</b> {', '.join(st.session_state.numeros_reserva)}</p>
                <p><b>Total a Pagar:</b> ₡{st.session_state.total_reserva:,.0f} CRC</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader("📲 Paso Final: Realiza el Pago y Envía el Comprobante")
        
        mensaje_wa = f"Hola! Reservé en la *{titulo_rifa}*:\n👤 Nombre: {st.session_state.nombre_reserva}\n🎟️ Números: {', '.join(st.session_state.numeros_reserva)}\n💰 Monto: ₡{st.session_state.total_reserva:,.0f} CRC\n\nAdjunto el comprobante del SINPE enviando al {num_limpio}."
        url_wa = f"https://wa.me/506{num_limpio}?text={urllib.parse.quote(mensaje_wa)}"
        
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            st.markdown(f'<a href="{url_wa}" target="_blank"><button style="background-color:#25D366; color:white;">🟢 Confirmar por WhatsApp</button></a>', unsafe_allow_html=True)
        with col_w2:
            if st.button("🔄 Comprar más números"):
                st.session_state.reserva_confirmada = False
                st.session_state.seleccionados_global = []
                st.rerun()

    else:
        st.subheader("Selecciona tus números:")
        mapa_ocupados = obtener_mapa_numeros_ocupados()
        disponibles = total_numeros_config - len(mapa_ocupados)
        st.caption(f"⚪ Disponibles: **{disponibles}** | ❌ Reservados / Pagados: **{len(mapa_ocupados)}**")

        # Generador de pestañas por decenas
        rangos, bloques = [], []
        for i in range(0, total_numeros_config, 10):
            fin_b = min(i + 9, total_numeros_config - 1)
            rangos.append(f"{i:02d}-{fin_b:02d}")
            bloques.append((i, fin_b))

        sub_tabs = st.tabs(rangos)
        for idx, sub_tab in enumerate(sub_tabs):
            with sub_tab:
                inicio, fin = bloques[idx]
                nums_bloque = list(range(inicio, fin + 1))
                for r_start in range(0, len(nums_bloque), 5):
                    fila = nums_bloque[r_start : r_start + 5]
                    cols = st.columns(len(fila))
                    for c_idx, num_val in enumerate(fila):
                        num_str = f"{num_val:02d}"
                        with cols[c_idx]:
                            if num_str in mapa_ocupados:
                                st.button(f"❌ {num_str}", key=f"b_{num_str}", disabled=True)
                            else:
                                if st.checkbox(num_str, key=f"c_{num_str}"):
                                    if num_str not in st.session_state.seleccionados_global:
                                        st.session_state.seleccionados_global.append(num_str)
                                else:
                                    if num_str in st.session_state.seleccionados_global:
                                        st.session_state.seleccionados_global.remove(num_str)

        seleccionados = sorted(st.session_state.seleccionados_global, key=lambda x: int(x))
        if seleccionados:
            total_pagar = len(seleccionados) * precio_numero
            st.info(f"🎟️ **Seleccionados:** {', '.join(seleccionados)} | 💰 **Total:** ₡{total_pagar:,.0f} CRC")
            
            st.write("---")
            st.write("### 📋 Completa tu Reserva")
            col_in1, col_in2 = st.columns(2)
            with col_in1:
                nom_cli = st.text_input("Nombre Completo:")
            with col_in2:
                tel_cli = st.text_input("Teléfono (8 dígitos):", max_chars=8)

            if st.button("🔒 Reservar Números"):
                nom_l = nom_cli.strip()
                tel_l = tel_cli.strip().replace(" ", "").replace("-", "")
                
                if re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$", nom_l) and re.match(r"^\d{8}$", tel_l):
                    ex, fa = guardar_reserva(seleccionados, nom_l, tel_l)
                    if exitosos := ex:
                        st.session_state.reserva_confirmada = True
                        st.session_state.numeros_reserva = exitosos
                        st.session_state.total_reserva = total_pagar
                        st.session_state.nombre_reserva = nom_l
                        st.rerun()
                    else:
                        st.error("Esos números ya fueron reservados.")
                else:
                    st.error("Verifica que el nombre y el número de teléfono sean válidos.")

# =============================================================
# 📊 PESTAÑA 2: ESTADO DE NÚMEROS (PÚBLICA)
# =============================================================
with tab_estado:
    st.subheader("📊 Estado Transparente de la Rifa")
    df_publico = obtener_todas_las_reservas()
    
    if not df_publico.empty:
        # Ocultar teléfono por privacidad
        df_ver = df_publico[["Número", "Comprador", "Estatus Pago"]].copy()
        
        busqueda = st.text_input("🔍 Buscar por número o nombre:", placeholder="Ej: 05 o Juan")
        if busqueda:
            df_ver = df_ver[
                df_ver["Número"].str.contains(busqueda) | 
                df_ver["Comprador"].str.lower().str.contains(busqueda.lower())
            ]
            
        st.dataframe(df_ver, use_container_width=True)
    else:
        st.info("Aún no hay números reservados. ¡Sé el primero en comprar!")

# =============================================================
# 🔐 PESTAÑA 3: ADMINISTRACIÓN (PRIVADA)
# =============================================================
with tab_admin:
    clave_admin = st.text_input("🔑 Contraseña de Administrador:", type="password")
    
    if clave_admin == "1234":
        st.success("Acceso Administrador Autorizado")
        
        # --- RESUMEN DE METRICAS ---
        mapa = obtener_mapa_numeros_ocupados()
        tot_res = len(mapa)
        tot_pag = sum(1 for e in mapa.values() if "Pagado" in str(e))
        tot_pen = tot_res - tot_pag
        recaudado = tot_pag * precio_numero

        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("Total Reservados", f"{tot_res}/{total_numeros_config}")
        c_m2.metric("✅ Pagados", f"{tot_pag}")
        c_m3.metric("💰 Recaudado", f"₡{recaudado:,.0f}")
        
        st.progress(min(tot_res / total_numeros_config, 1.0))

        st.write("---")
        # --- GESTIÓN DE RESERVAS ---
        st.subheader("📋 Administración de Ventas")
        df_admin = obtener_todas_las_reservas()
        
        if not df_admin.empty:
            st.dataframe(df_admin, use_container_width=True)
            
            c_adm1, c_adm2 = st.columns(2)
            with c_adm1:
                st.markdown("#### ✏️ Cambiar Estado")
                num_est = st.selectbox("Número:", df_admin["Número"].tolist(), key="sel_a1")
                nuevo_e = st.selectbox("Estado:", ["✅ Pagado", "⏳ Pendiente"], key="sel_a2")
                if st.button("💾 Actualizar Estado"):
                    cambiar_estado_pago(num_est, nuevo_e)
                    st.success("Estado actualizado")
                    st.rerun()

            with c_adm2:
                st.markdown("#### 🔓 Liberar Número")
                num_lib = st.selectbox("Número:", df_admin["Número"].tolist(), key="sel_a3")
                if st.button("🔓 Liberar y Borrar Reserva"):
                    liberar_numero(num_lib)
                    st.success("Número liberado")
                    st.rerun()

        st.write("---")
        # --- CONFIGURAR PREMIO ÚNICO ---
        st.subheader("🎁 Configurar Premio Único")
        with st.form("form_p"):
            p_nom = st.text_input("Nombre del Premio:")
            p_desc = st.text_area("Descripción:")
            p_file = st.file_uploader("Foto del premio:", type=["png", "jpg", "jpeg", "webp"])
            if st.form_submit_button("💾 Guardar Premio Único"):
                if p_nom:
                    img_b64 = procesar_imagen_a_base64(p_file)
                    agregar_premio("Premio Único", p_nom, p_desc, img_b64)
                    st.success("Premio actualizado")
                    st.rerun()

        st.write("---")
        # --- CONFIGURACIÓN GENERAL ---
        st.subheader("⚙️ Configuración General de la Rifa")
        with st.form("form_cfg"):
            cfg_tit = st.text_input("Título de la Rifa:", value=titulo_rifa)
            cfg_pre = st.number_input("Precio por número:", value=precio_numero, step=500)
            cfg_tot = st.number_input("Total de números:", value=total_numeros_config, step=10)
            cfg_fec = st.date_input("Fecha Sorteo:", value=fecha_sorteo_db)
            cfg_sin = st.text_input("Número SINPE:", value=num_limpio)
            cfg_nom = st.text_input("Nombre SINPE:", value=nombre_sinpe)
            
            if st.form_submit_button("💾 Guardar Configuración"):
                guardar_configuracion(cfg_tit, cfg_pre, cfg_sin, cfg_nom, cfg_fec.strftime("%Y-%m-%d"), cfg_tot)
                st.success("Configuración guardada")
                st.rerun()

        # --- ZONA DE BORRADO ---
        st.write("---")
        if st.checkbox("⚠️ Confirmar borrado completo de la rifa"):
            if st.button("🗑️ Borrar Todas las Reservas"):
                reiniciar_rifa()
                st.success("Rifa reiniciada")
                st.rerun()

    elif clave_admin != "":
        st.error("Contraseña incorrecta")
