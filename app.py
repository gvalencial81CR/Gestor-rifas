import sqlite3
import urllib.parse
from datetime import datetime, date
import pandas as pd
import streamlit as st
import re
import base64

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="Gestor de Rifas CR 🇨🇷", 
    layout="centered", 
    page_icon="🎟️"
)

# Configura aquí tu URL desplegada
URL_APP = "https://tu-app-de-rifa.streamlit.app"

# ==========================================
# 2. ESTILOS CSS PERSONALIZADOS DETALLADOS
# ==========================================
st.markdown(
    """
    <style>
    /* Botones generales */
    .stButton>button {
        width: 100%;
        height: 3.2em;
        font-weight: bold;
        border-radius: 10px;
        transition: all 0.2s ease-in-out;
    }
    
    /* Tarjeta de Premio */
    .premio-card {
        border: 2px solid #e0e0e0;
        padding: 24px;
        border-radius: 18px;
        background: linear-gradient(135deg, #ffffff 0%, #f9fbfd 100%);
        margin-bottom: 25px;
        box-shadow: 0 6px 12px rgba(0,0,0,0.08);
    }
    
    /* Caja Comprobante de Reserva */
    .ticket-box {
        border: 2px dashed #0056b3;
        background-color: #f0f7ff;
        padding: 24px;
        border-radius: 14px;
        text-align: center;
        margin-top: 15px;
        margin-bottom: 25px;
    }
    .ticket-box h3 {
        color: #0056b3;
        margin-bottom: 12px;
    }
    
    /* Estilos para las Pestañas (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre-wrap;
        background-color: #f1f3f5;
        border-radius: 10px 10px 0px 0px;
        padding-top: 8px;
        padding-bottom: 8px;
        font-weight: bold;
        color: #495057;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0056b3 !important;
        color: white !important;
    }
    
    /* Botón flotante o destacado de WhatsApp */
    .btn-whatsapp {
        background-color: #25D366;
        color: white;
        text-align: center;
        padding: 12px;
        font-weight: bold;
        border-radius: 10px;
        text-decoration: none;
        display: block;
        margin-top: 10px;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# 3. BASE DE DATOS Y FUNCIONES DE SOPORTE
# ==========================================
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


# ==========================================
# 4. CARGA DE CONFIGURACIÓN E INICIALIZACIÓN
# ==========================================
config_actual = obtener_configuracion()
try:
    total_numeros_config = int(config_actual.get("total_numeros", 100))
except ValueError:
    total_numeros_config = 100

precio_numero = int(config_actual["rifa_precio"])
num_limpio = config_actual["sinpe_numero"]
nombre_sinpe = config_actual["sinpe_nombre"]
titulo_rifa = config_actual["rifa_titulo"]

try:
    fecha_sorteo_db = datetime.strptime(config_actual["rifa_fecha_sorteo"], "%Y-%m-%d").date()
except (KeyError, ValueError):
    fecha_sorteo_db = date.today()

fecha_formateada = fecha_sorteo_db.strftime("%d/%m/%Y")

# Estados de sesión
if "reserva_confirmada" not in st.session_state:
    st.session_state.reserva_confirmada = False
if "seleccionados_global" not in st.session_state:
    st.session_state.seleccionados_global = []


# ==========================================
# 5. CABECERA PRINCIPAL
# ==========================================
st.title(titulo_rifa)
st.markdown(f"🗓️ **Fecha de la Rifa:** {fecha_formateada} | 💰 **Precio por número:** ₡{precio_numero:,.0f} CRC")
st.write("---")


# ==========================================
# 6. PESTAÑAS DE NAVEGACIÓN
# ==========================================
tab_comprar, tab_estado, tab_admin = st.tabs([
    "🎟️ Comprar Números", 
    "📊 Estado de Números", 
    "🔐 Administración"
])

# -------------------------------------------------------------
# PESTAÑA 1: COMPRAR NÚMEROS
# -------------------------------------------------------------
with tab_comprar:
    # Mostrar tarjeta del Premio Único
    premios = obtener_premios()
    if premios:
        _, _, p_nombre, p_desc, p_img = premios[0]
        st.markdown('<div class="premio-card">', unsafe_allow_html=True)
        
        if p_img:
            col_img, col_txt = st.columns([1, 2])
            with col_img:
                try:
                    st.image(base64.b64decode(p_img), use_container_width=True)
                except Exception:
                    st.write("🖼️ [Imagen del Premio]")
            with col_txt:
                st.subheader("🏆 Premio Único")
                st.markdown(f"## {p_nombre}")
                if p_desc:
                    st.write(p_desc)
        else:
            st.subheader("🏆 Premio Único")
            st.markdown(f"## {p_nombre}")
            if p_desc:
                st.write(p_desc)
                
        st.markdown('</div>', unsafe_allow_html=True)

    # Evaluación si la reserva acaba de realizarse
    if st.session_state.reserva_confirmada:
        st.balloons()
        st.success("🎉 ¡Tu reserva se ha registrado exitosamente!")
        
        st.markdown(
            f"""
            <div class="ticket-box">
                <h3>🎟️ COMPROBANTE DE RESERVA</h3>
                <p style="font-size: 1.1em;"><b>Comprador:</b> {st.session_state.nombre_reserva}</p>
                <p style="font-size: 1.2em; color: #0056b3;"><b>Número(s) Seleccionado(s):</b> {', '.join(st.session_state.numeros_reserva)}</p>
                <p style="font-size: 1.3em; font-weight: bold;"><b>Total a Pagar:</b> ₡{st.session_state.total_reserva:,.0f} CRC</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader("📲 Paso Final: Realiza el Pago por SINPE Móvil")
        st.write(f"1. Transfiere **₡{st.session_state.total_reserva:,.0f} CRC** al teléfono: **{num_limpio}** ({nombre_sinpe}).")
        st.write("2. Presiona el botón verde de abajo para enviar la confirmación por WhatsApp:")
        
        mensaje_wa = f"Hola! Acabo de hacer una reserva en la *{titulo_rifa}*:\n\n👤 *Nombre:* {st.session_state.nombre_reserva}\n🎟️ *Número(s):* {', '.join(st.session_state.numeros_reserva)}\n💰 *Monto a pagar:* ₡{st.session_state.total_reserva:,.0f} CRC\n\nAdjunto la foto/comprobante del SINPE."
        url_wa = f"https://wa.me/506{num_limpio}?text={urllib.parse.quote(mensaje_wa)}"
        
        st.markdown(f'<a href="{url_wa}" target="_blank" style="text-decoration:none;"><div class="btn-whatsapp">🟢 Enviar Comprobante por WhatsApp</div></a>', unsafe_allow_html=True)
        st.write("")
        
        if st.button("🔄 Elegir más números"):
            st.session_state.reserva_confirmada = False
            st.session_state.seleccionados_global = []
            st.rerun()

    else:
        st.write("### 📌 Selecciona tus números")
        mapa_ocupados = obtener_mapa_numeros_ocupados()
        disponibles = total_numeros_config - len(mapa_ocupados)
        
        # Panel informativo
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Total Números", total_numeros_config)
        col_m2.metric("⚪ Disponibles", disponibles)
        col_m3.metric("❌ Reservados/Pagados", len(mapa_ocupados))

        st.write("---")
        st.write("Utiliza las pestañas de abajo para explorar cada decena de números:")

        # Pestañas por decenas (00-09, 10-19, ..., 90-99)
        rangos = []
        bloques = []
        for i in range(0, total_numeros_config, 10):
            fin_b = min(i + 9, total_numeros_config - 1)
            rangos.append(f"{i:02d}-{fin_b:02d}")
            bloques.append((i, fin_b))

        sub_tabs = st.tabs(rangos)
        for idx, sub_tab in enumerate(sub_tabs):
            with sub_tab:
                inicio, fin = bloques[idx]
                nums_bloque = list(range(inicio, fin + 1))
                
                # Fila 1: Primeros 5 números
                fila1 = nums_bloque[:5]
                cols1 = st.columns(len(fila1))
                for c_idx, num_val in enumerate(fila1):
                    num_str = f"{num_val:02d}"
                    with cols1[c_idx]:
                        if num_str in mapa_ocupados:
                            st.button(f"❌ {num_str}", key=f"b_{num_str}", disabled=True)
                        else:
                            marcado = num_str in st.session_state.seleccionados_global
                            if st.checkbox(num_str, value=marcado, key=f"c_{num_str}"):
                                if num_str not in st.session_state.seleccionados_global:
                                    st.session_state.seleccionados_global.append(num_str)
                                    st.rerun()
                            else:
                                if num_str in st.session_state.seleccionados_global:
                                    st.session_state.seleccionados_global.remove(num_str)
                                    st.rerun()

                # Fila 2: Siguientes 5 números
                fila2 = nums_bloque[5:]
                if fila2:
                    cols2 = st.columns(len(fila2))
                    for c_idx, num_val in enumerate(fila2):
                        num_str = f"{num_val:02d}"
                        with cols2[c_idx]:
                            if num_str in mapa_ocupados:
                                st.button(f"❌ {num_str}", key=f"b_{num_str}", disabled=True)
                            else:
                                marcado = num_str in st.session_state.seleccionados_global
                                if st.checkbox(num_str, value=marcado, key=f"c_{num_str}"):
                                    if num_str not in st.session_state.seleccionados_global:
                                        st.session_state.seleccionados_global.append(num_str)
                                        st.rerun()
                                else:
                                    if num_str in st.session_state.seleccionados_global:
                                        st.session_state.seleccionados_global.remove(num_str)
                                        st.rerun()

        # Resumen de lo seleccionado
        seleccionados = sorted(st.session_state.seleccionados_global, key=lambda x: int(x))
        st.write("---")
        
        if seleccionados:
            total_pagar = len(seleccionados) * precio_numero
            st.info(f"🎟️ **Números seleccionados:** {', '.join(seleccionados)}  \n💰 **Monto Total:** ₡{total_pagar:,.0f} CRC")
            
            st.write("### 📋 Formulario de Reserva")
            st.write("Por favor ingresa tus datos para apartar tus números:")
            
            col_in1, col_in2 = st.columns(2)
            with col_in1:
                nom_cli = st.text_input("Nombre Completo:", placeholder="Ej: Maria Rodríguez")
            with col_in2:
                tel_cli = st.text_input("Número de Teléfono (8 dígitos):", placeholder="Ej: 88888888", max_chars=8)

            if st.button("🔒 Reservar Mis Números Ahora"):
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
                        st.error("⚠️ Uno o más de los números seleccionados ya fueron apartados por otra persona. Revisa la lista.")
                else:
                    st.error("⚠️ Revisa los datos: Ingresa un nombre válido y un número de teléfono de 8 dígitos sin espacios ni guiones.")

# -------------------------------------------------------------
# PESTAÑA 2: ESTADO DE NÚMEROS (PÚBLICO)
# -------------------------------------------------------------
with tab_estado:
    st.subheader("📊 Estado Transparente de la Rifa")
    st.write("Aquí puedes verificar de forma transparente la lista pública de los números reservados y sus estados.")
    
    df_publico = obtener_todas_las_reservas()
    
    if not df_publico.empty:
        # Copia sin teléfono por motivos de privacidad
        df_ver = df_publico[["Número", "Comprador", "Estatus Pago"]].copy()
        
        busqueda = st.text_input("🔍 Buscar por número o nombre del comprador:", placeholder="Ej: 07 o Carlos")
        if busqueda:
            df_ver = df_ver[
                df_ver["Número"].str.contains(busqueda) | 
                df_ver["Comprador"].str.lower().str.contains(busqueda.lower())
            ]
            
        st.dataframe(df_ver, use_container_width=True)
    else:
        st.info("Aún no hay números reservados. ¡Sé el primero en seleccionar uno en la pestaña de compra!")

# -------------------------------------------------------------
# PESTAÑA 3: ADMINISTRACIÓN (PRIVADA)
# -------------------------------------------------------------
with tab_admin:
    st.subheader("🔐 Panel de Control de Administración")
    clave_admin = st.text_input("Ingresa la Contraseña de Administrador:", type="password")
    
    if clave_admin == "1234":
        st.success("Acceso concedido al Administrador.")
        
        # Dashboard de métricas
        st.write("---")
        st.markdown("### 📈 Métricas de la Rifa")
        mapa = obtener_mapa_numeros_ocupados()
        tot_res = len(mapa)
        tot_pag = sum(1 for e in mapa.values() if "Pagado" in str(e))
        tot_pen = tot_res - tot_pag
        recaudado = tot_pag * precio_numero

        col_adm_m1, col_adm_m2, col_adm_m3, col_adm_m4 = st.columns(4)
        col_adm_m1.metric("Reservados", f"{tot_res}/{total_numeros_config}")
        col_adm_m2.metric("✅ Pagados", f"{tot_pag}")
        col_adm_m3.metric("⏳ Pendientes", f"{tot_pen}")
        col_adm_m4.metric("💰 Recaudado", f"₡{recaudado:,.0f}")
        
        progreso = min(tot_res / total_numeros_config, 1.0)
        st.progress(progreso)

        st.write("---")
        # Gestión detallada de reservas
        st.markdown("### 📋 Registro General de Ventas")
        df_admin = obtener_todas_las_reservas()
        
        if not df_admin.empty:
            st.dataframe(df_admin, use_container_width=True)
            
            c_adm1, c_adm2 = st.columns(2)
            with c_adm1:
                st.markdown("#### ✏️ Actualizar Estado de Pago")
                num_est = st.selectbox("Seleccionar Número:", df_admin["Número"].tolist(), key="sel_a1")
                nuevo_e = st.selectbox("Nuevo Estado:", ["✅ Pagado", "⏳ Pendiente"], key="sel_a2")
                if st.button("💾 Guardar Nuevo Estado"):
                    cambiar_estado_pago(num_est, nuevo_e)
                    st.success(f"Estado del número {num_est} actualizado a {nuevo_e}")
                    st.rerun()

            with c_adm2:
                st.markdown("#### 🔓 Liberar un Número")
                num_lib = st.selectbox("Seleccionar Número a Liberar:", df_admin["Número"].tolist(), key="sel_a3")
                if st.button("🔓 Cancelar Reserva y Liberar"):
                    liberar_numero(num_lib)
                    st.success(f"El número {num_lib} ha sido liberado nuevamente.")
                    st.rerun()
        else:
            st.info("Aún no hay compras o reservas en el sistema.")

        st.write("---")
        # Gestión de Premio Único
        st.markdown("### 🎁 Configurar el Premio Único")
        with st.form("form_premio_admin"):
            p_nom = st.text_input("Nombre del Premio:", placeholder="Ej: Motocicleta Formula 150cc")
            p_desc = st.text_area("Descripción detallada:", placeholder="Modelo 2024, cero kilómetros, incluye casco.")
            p_file = st.file_uploader("Fotografía del premio:", type=["png", "jpg", "jpeg", "webp"])
            
            if st.form_submit_button("💾 Guardar / Actualizar Premio Único"):
                if p_nom:
                    img_b64 = procesar_imagen_a_base64(p_file)
                    agregar_premio("Premio Único", p_nom, p_desc, img_b64)
                    st.success("Premio Único actualizado exitosamente.")
                    st.rerun()
                else:
                    st.error("Ingresa al menos el nombre del premio.")

        st.write("---")
        # Ajustes de configuración
        st.markdown("### ⚙️ Configuración de la Rifa y Cuenta SINPE")
        with st.form("form_config_admin"):
            cfg_tit = st.text_input("Título de la Rifa:", value=titulo_rifa)
            cfg_pre = st.number_input("Precio de cada número (₡):", value=precio_numero, step=500)
            cfg_tot = st.number_input("Total de números habilitados:", value=total_numeros_config, step=10)
            cfg_fec = st.date_input("Fecha del Sorteo:", value=fecha_sorteo_db)
            cfg_sin = st.text_input("Número SINPE Móvil:", value=num_limpio)
            cfg_nom = st.text_input("Nombre del Titular del SINPE:", value=nombre_sinpe)
            
            if st.form_submit_button("💾 Guardar Configuración General"):
                guardar_configuracion(cfg_tit, cfg_pre, cfg_sin, cfg_nom, cfg_fec.strftime("%Y-%m-%d"), cfg_tot)
                st.success("Configuración del sistema actualizada correctamente.")
                st.rerun()

        # Zona de reinicio completo
        st.write("---")
        st.markdown("### ⚠️ Zona Peligrosa")
        if st.checkbox("Confirmo que deseo borrar de forma permanente todas las reservas actuales"):
            if st.button("🗑️ Reiniciar Rifa Completa (Borrar Todas las Reservas)"):
                reiniciar_rifa()
                st.success("Se han eliminado todas las reservas. La rifa está lista desde cero.")
                st.rerun()

    elif clave_admin != "":
        st.error("❌ Contraseña incorrecta. Inténtalo de nuevo.")
