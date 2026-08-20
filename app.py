import sqlite3
import urllib.parse
from datetime import datetime, date
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import re
import base64
import io
from PIL import Image, ImageDraw, ImageFont

# Configuración de la página
st.set_page_config(
    page_title="Gestor de Rifas CR 🇨🇷", layout="centered", page_icon="🎟️"
)

# Configura aquí tu dirección web desplegada
URL_APP = "https://gestor-rifas-ww94zdzkemq5cwjpqwc4ga.streamlit.app/"

# Estilos CSS personalizados
st.markdown(
    """
    <style>
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 4px !important;
    }

    div[data-testid="column"] {
        flex: 1 1 0 !important;
        min-width: 0 !important;
    }

    .stButton>button {
        width: 100% !important;
        height: 2.8em !important;
        font-weight: bold !important;
        border-radius: 6px !important;
        padding: 0px !important;
        font-size: 13px !important;
    }

    .stCheckbox {
        text-align: center;
        margin: 0px auto;
    }
    
    .stCheckbox > label {
        padding-left: 0px !important;
    }

    .block-container {
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        padding-top: 1.5rem !important;
    }

    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 12px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 10px;
    }
    .ticket-box {
        border: 2px dashed #0056b3;
        background-color: #eef6ff;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 15px;
    }
    .premio-box {
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 12px;
        background-color: #ffffff;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    </style>
""",
    unsafe_allow_html=True,
)


# --- FUNCIÓN COMPONENTE: CONTADOR REGRESIVO ---
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
    components.html(html_code, height=135)


# --- FUNCIÓN PARA GENERAR LA IMAGEN TIPO COMPROBANTE ---
def generar_imagen_comprobante_admin(
    titulo, comprador, numeros, total, fecha, estado_pago
):
    ancho, alto = 650, 360
    # Fondo azul claro pastel
    img = Image.new("RGB", (ancho, alto), color="#edf5ff")
    draw = ImageDraw.Draw(img)

    # Borde marco azul
    draw.rectangle([12, 12, ancho - 12, alto - 12], outline="#0056b3", width=2)

    # Textos principales centrados
    draw.text(
        (ancho // 2, 35),
        "🎟️ NÚMERO(S) DIGITAL DE RESERVA",
        fill="#1a2530",
        anchor="mm",
    )
    draw.text((ancho // 2, 75), f"Rifa: {titulo}", fill="#333333", anchor="mm")
    draw.text(
        (ancho // 2, 110), f"Comprador: {comprador}", fill="#333333", anchor="mm"
    )
    draw.text(
        (ancho // 2, 145), f"Número(s): {numeros}", fill="#333333", anchor="mm"
    )
    draw.text(
        (ancho // 2, 180),
        f"Total: ₡{total:,.0f} CRC",
        fill="#333333",
        anchor="mm",
    )
    draw.text(
        (ancho // 2, 215),
        f"Estado de Pago: {estado_pago}",
        fill="#0056b3",
        anchor="mm",
    )
    draw.text(
        (ancho // 2, 250),
        f"Fecha de Sorteo: {fecha}",
        fill="#333333",
        anchor="mm",
    )

    # Pie de página / Mensaje final
    draw.text(
        (ancho // 2, 305), "🍀 ¡Buena Suerte! 🍀", fill="#0056b3", anchor="mm"
    )

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# --- CONEXIÓN Y FUNCIONES DE BASE DE DATOS (rifa_v3.db) ---
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


def guardar_configuracion(
    titulo, precio, num_sinpe, nombre_sinpe, fecha_str, total_nums
):
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
        base64_encoded = base64.b64encode(bytes_data).decode("utf-8")
        return base64_encoded
    return ""


def agregar_premio(lugar, nombre, descripcion, imagen_data):
    conn = conectar_db()
    c = conn.cursor()
    c.execute("DELETE FROM premios")
    c.execute(
        "INSERT INTO premios (lugar, nombre, descripcion, imagen_data) VALUES"
        " (?, ?, ?, ?)",
        (lugar, nombre, descripcion, imagen_data),
    )
    conn.commit()
    conn.close()


def obtener_premios():
    conn = conectar_db()
    c = conn.cursor()
    c.execute(
        "SELECT id, lugar, nombre, descripcion, imagen_data FROM premios"
        " ORDER BY id DESC LIMIT 1"
    )
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
                "INSERT INTO numeros_comprados (numero, comprador, telefono,"
                " estado_pago) VALUES (?, ?, ?, 'Pendiente')",
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
        "SELECT numero AS 'Número', comprador AS 'Comprador', telefono AS"
        " 'Teléfono', estado_pago AS 'Estatus Pago', fecha AS 'Fecha Reserva'"
        " FROM numeros_comprados ORDER BY CAST(numero AS INTEGER) ASC"
    )
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def cambiar_estado_pago(numero, nuevo_estado):
    conn = conectar_db()
    c = conn.cursor()
    c.execute(
        "UPDATE numeros_comprados SET estado_pago = ? WHERE numero = ?",
        (nuevo_estado, numero),
    )
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

# --- INICIALIZACIÓN DE ESTADO DE SESIÓN ---
if "reserva_confirmada" not in st.session_state:
    st.session_state.reserva_confirmada = False
if "seleccionados_global" not in st.session_state:
    st.session_state.seleccionados_global = []

try:
    fecha_sorteo_db = datetime.strptime(
        config_actual["rifa_fecha_sorteo"], "%Y-%m-%d"
    ).date()
except (KeyError, ValueError):
    fecha_sorteo_db = date.today()

fecha_formateada = fecha_sorteo_db.strftime("%d/%m/%Y")
titulo_rifa = config_actual["rifa_titulo"]
precio_numero = int(config_actual["rifa_precio"])
num_limpio = config_actual["sinpe_numero"]
nombre_sinpe = config_actual["sinpe_nombre"]

# --- PANEL LATERAL ---
with st.sidebar:
    st.title("⚙️ Panel de Control")

    st.subheader("🔑 Modo Administrador")
    clave_admin = st.text_input(
        "Contraseña Admin:", type="password", key="pass_admin"
    )

    if clave_admin == "1234":
        st.success("✅ Acceso Concedido")

        mapa_ocupados = obtener_mapa_numeros_ocupados()
        total_reservados = len(mapa_ocupados)
        total_pagados = sum(
            1 for est in mapa_ocupados.values() if "Pagado" in str(est)
        )
        total_pendientes = total_reservados - total_pagados

        pct_ocupados = (total_reservados / total_numeros_config) * 100
        pct_pagados = (
            (total_pagados / total_reservados * 100)
            if total_reservados > 0
            else 0
        )
        pct_pendientes = (
            (total_pendientes / total_reservados * 100)
            if total_reservados > 0
            else 0
        )

        recaudado = total_pagados * precio_numero

        st.write("---")
        st.markdown("### 📊 Resumen de Ventas (Privado)")

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric(
                "Total Ocupados",
                f"{total_reservados}/{total_numeros_config}",
                delta=f"{pct_ocupados:.0f}% meta",
            )
            st.metric(
                "✅ Pagados",
                f"{total_pagados}",
                delta=f"{pct_pagados:.0f}% del total",
            )
        with col_m2:
            st.metric(
                "⏳ Pendientes",
                f"{total_pendientes}",
                delta=f"{pct_pendientes:.0f}% del total",
            )
            st.metric("💰 Recaudado", f"₡{recaudado:,.0f}")

        st.progress(min(total_reservados / total_numeros_config, 1.0))

        df_reservas = obtener_todas_las_reservas()

        st.write("---")
        st.write("### 📋 Tabla General de Reservas")

        if not df_reservas.empty:
            col_f1, col_f2 = st.columns([1, 1])
            with col_f1:
                filtro_estado = st.selectbox(
                    "Filtrar Estado:",
                    ["Todos", "✅ Pagado", "⏳ Pendiente"],
                    key="filtro_est",
                )
            with col_f2:
                busqueda_txt = st.text_input(
                    "Buscar (Nombre/Tel):",
                    key="search_admin",
                    placeholder="Ej: Juan",
                )

            df_filtrado = df_reservas.copy()
            if filtro_estado != "Todos":
                df_filtrado = df_filtrado[
                    df_filtrado["Estatus Pago"] == filtro_estado
                ]

            if busqueda_txt.strip():
                txt_b = busqueda_txt.strip().lower()
                df_filtrado = df_filtrado[
                    df_filtrado["Comprador"].str.lower().str.contains(txt_b)
                    | df_filtrado["Teléfono"].str.contains(txt_b)
                ]

            st.dataframe(df_filtrado, use_container_width=True)

            st.write("---")
            st.write("#### ✏️ Cambiar Estatus de Pago")
            lista_numeros = df_reservas["Número"].tolist()

            num_a_pagar = st.selectbox(
                "Número:", lista_numeros, key="sel_num_estatus"
            )
            nuevo_est = st.selectbox(
                "Nuevo Estado:",
                ["✅ Pagado", "⏳ Pendiente"],
                key="sel_nuevo_estatus",
            )

            if st.button("💾 Guardar Estatus"):
                cambiar_estado_pago(num_a_pagar, nuevo_est)
                st.success(f"¡Número {num_a_pagar} actualizado a {nuevo_est}!")
                st.rerun()

            # SECCIÓN PARA GENERAR IMAGEN ENVIABLE POR WHATSAPP COMO ADMIN
            st.write("---")
            st.write("#### 🖼️ Generar Comprobante en Imagen")
            num_para_foto = st.selectbox(
                "Selecciona el número a exportar:",
                lista_numeros,
                key="sel_num_foto",
            )

            if num_para_foto:
                fila_reserva = df_reservas[
                    df_reservas["Número"] == num_para_foto
                ].iloc[0]
                nom_c = fila_reserva["Comprador"]
                tel_c = fila_reserva["Teléfono"]
                est_c = fila_reserva["Estatus Pago"]

                # Agrupar todos los números que pertenecen al mismo comprador
                todos_nums_comprador = df_reservas[
                    df_reservas["Comprador"] == nom_c
                ]["Número"].tolist()
                nums_str = ", ".join(todos_nums_comprador)
                monto_total_compra = (
                    len(todos_nums_comprador) * precio_numero
                )

                bytes_comprobante = generar_imagen_comprobante_admin(
                    titulo=titulo_rifa,
                    comprador=nom_c,
                    numeros=nums_str,
                    total=monto_total_compra,
                    fecha=fecha_formateada,
                    estado_pago=est_c,
                )

                st.image(
                    bytes_comprobante,
                    caption="Vista previa del comprobante",
                    use_container_width=True,
                )

                st.download_button(
                    label=f"📥 Descargar Comprobante ({nom_c})",
                    data=bytes_comprobante,
                    file_name=f"Boleto_{nom_c}_{num_para_foto}.png",
                    mime="image/png",
                    use_container_width=True,
                )

                # Link para abrir chat directamente con el cliente
                msg_admin = (
                    f"Hola {nom_c}, te adjunto la confirmación de tus número(s)"
                    f" {nums_str} para la {titulo_rifa}. Estado: {est_c}."
                )
                url_wa_admin = (
                    f"https://wa.me/506{tel_c}?text={urllib.parse.quote(msg_admin)}"
                )

                st.markdown(
                    f"""
                    <a href="{url_wa_admin}" target="_blank">
                        <button style="background-color: #25D366; color: white; border: none; padding: 10px; font-weight: bold; border-radius: 6px; width: 100%; cursor: pointer;">
                            💬 Abrir Chat de WhatsApp con {nom_c}
                        </button>
                    </a>
                    """,
                    unsafe_allow_html=True,
                )

            st.write("---")
            st.write("#### 🔓 Cancelar Reserva Individual")
            num_a_liberar = st.selectbox(
                "Número a liberar:", lista_numeros, key="sel_num_liberar"
            )

            if st.button("🔓 Liberar Número"):
                liberar_numero(num_a_liberar)
                st.success(f"¡Número {num_a_liberar} liberado!")
                st.rerun()
        else:
            st.info("No hay reservas registradas por el momento.")

        # GESTIÓN DE PREMIO ÚNICO
        st.write("---")
        st.write("### 🎁 Configurar Premio Único")
        with st.form("form_nuevo_premio", clear_on_submit=True):
            premio_nombre = st.text_input(
                "Nombre del Premio:", placeholder="Ej: Pantalla Smart TV 55''"
            )
            premio_desc = st.text_area(
                "Descripción del Premio:",
                placeholder="Marca LG 4K Ultra HD...",
            )

            archivo_imagen = st.file_uploader(
                "📷 Seleccionar foto del premio:",
                type=["png", "jpg", "jpeg", "webp"],
            )

            btn_guardar_premio = st.form_submit_button(
                "💾 Guardar Premio Único"
            )

            if btn_guardar_premio:
                if premio_nombre.strip():
                    img_base64 = procesar_imagen_a_base64(archivo_imagen)
                    agregar_premio(
                        "🏆 Premio Único",
                        premio_nombre,
                        premio_desc,
                        img_base64,
                    )
                    st.success(
                        f"¡Premio '{premio_nombre}' guardado exitosamente!"
                    )
                    st.rerun()
                else:
                    st.error("Por favor ingresa al menos el nombre del premio.")

        premios_registrados = obtener_premios()
        if premios_registrados:
            st.write("#### Premio Actual:")
            for p in premios_registrados:
                p_id, p_lugar, p_nombre, p_desc, p_img = p
                c_p1, c_p2 = st.columns([3, 1])
                with c_p1:
                    st.write(f"**{p_nombre}**")
                with c_p2:
                    if st.button("🗑️ Borrar", key=f"del_p_{p_id}"):
                        eliminar_premio(p_id)
                        st.rerun()

        # REINICIAR RIFA
        st.write("---")
        st.write("#### ⚠️ Reiniciar / Borrar Rifa")
        confirmar_borrado = st.checkbox(
            "Confirmo borrar TODAS las reservas", key="check_borrar"
        )

        if st.button("🗑️ Borrar Rifa Actual"):
            if confirmar_borrado:
                reiniciar_rifa()
                st.success("¡Se han borrado todas las reservas!")
                st.session_state.reserva_confirmada = False
                st.session_state.seleccionados_global = []
                st.rerun()
            else:
                st.warning("Debes marcar la casilla de confirmación.")

    elif clave_admin != "":
        st.error("Contraseña incorrecta")

    # CONFIGURACIÓN GENERAL
    with st.expander("⚙️ Configuración de la Rifa (SINPE / Nombre)"):
        with st.form("form_configuracion"):
            nuevo_titulo = st.text_input(
                "Nombre de la Rifa:",
                value=config_actual["rifa_titulo"],
                key="input_titulo",
            )
            fecha_sorteo = st.date_input(
                "Fecha del Sorteo:", value=fecha_sorteo_db
            )
            nuevo_precio = st.number_input(
                "Precio por número (₡ CRC):",
                min_value=100,
                value=int(config_actual["rifa_precio"]),
                step=100,
                key="input_precio",
            )
            nuevo_total_numeros = st.number_input(
                "Cantidad total de números:",
                min_value=10,
                max_value=1000,
                value=total_numeros_config,
                step=10,
                key="input_total_nums",
            )

            st.write("---")
            nuevo_sinpe = st.text_input(
                "Tu Número SINPE:",
                value=config_actual["sinpe_numero"],
                key="input_sinpe_num",
            )
            nuevo_nombre_sinpe = st.text_input(
                "Titular del SINPE:",
                value=config_actual["sinpe_nombre"],
                key="input_sinpe_nom",
            )

            btn_guardar = st.form_submit_button("💾 Guardar Configuración")

            if btn_guardar:
                sinpe_limpio = (
                    nuevo_sinpe.replace("-", "").replace(" ", "").strip()
                )
                fecha_str = fecha_sorteo.strftime("%Y-%m-%d")
                guardar_configuracion(
                    nuevo_titulo,
                    nuevo_precio,
                    sinpe_limpio,
                    nuevo_nombre_sinpe,
                    fecha_str,
                    nuevo_total_numeros,
                )
                st.success("¡Configuración guardada!")
                st.rerun()

# --- VISTA PRINCIPAL ---
st.title(titulo_rifa)
st.caption(f"📅 **Fecha del Sorteo:** {fecha_formateada}")

# --- COMPONENTE VISUAL: CONTADOR REGRESIVO ---
renderizar_contador_regresivo(config_actual["rifa_fecha_sorteo"])

tab_comprar, tab_premio, tab_reglamento = st.tabs(
    ["🎟️ Comprar Números", "🎁 Premio Único", "📜 Reglamento"]
)

with tab_comprar:
    mapa_numeros_actual = obtener_mapa_numeros_ocupados()
    disponibles_count = total_numeros_config - len(mapa_numeros_actual)

    if (
        disponibles_count <= (total_numeros_config * 0.2)
        and disponibles_count > 0
    ):
        st.warning(
            "🔥 **¡Atención! Solo quedan"
            f" {disponibles_count} números disponibles.**"
        )
    else:
        st.info(
            "🎟️ **Números disponibles:**"
            f" {disponibles_count} de {total_numeros_config}"
        )

    if st.session_state.reserva_confirmada:
        st.balloons()

        cant_reserva = len(st.session_state.numeros_reserva)
        if cant_reserva == 1:
            msg_exito = (
                "🎉 ¡Número"
                f" **{st.session_state.numeros_reserva[0]}** reservado"
                " exitosamente!"
            )
            txt_nums_wa = f"Número:* {st.session_state.numeros_reserva[0]}"
        else:
            nums_texto = ", ".join(st.session_state.numeros_reserva)
            msg_exito = f"🎉 ¡Números **{nums_texto}** reservados exitosamente!"
            txt_nums_wa = f"Números:* {nums_texto}"

        st.success(msg_exito)

        st.markdown(
            f"""
        <div class="ticket-box">
            <h3>🎟️ NÚMERO(S) DIGITAL DE RESERVA</h3>
            <p><b>Rifa:</b> {st.session_state.titulo_reserva}</p>
            <p><b>Comprador:</b> {st.session_state.nombre_reserva}</p>
            <p><b>Número(s):</b> {', '.join(st.session_state.numeros_reserva)}</p>
            <p><b>Total a Pagar:</b> ₡{st.session_state.total_reserva:,.0f} CRC</p>
            <p><b>Fecha de Sorteo:</b> {st.session_state.fecha_reserva}</p>
            <h4 style="margin-top: 15px; color: #0056b3;">🍀 ¡Buena Suerte! 🍀</h4>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.write("---")
        st.subheader("📲 Elige tu método para pagar / enviar comprobante:")

        bancos_sms = {
            "Banco Nacional (BNCR) - 2627": "2627",
            "BAC Credomatic - 70701222": "70701222",
            "Banco de Costa Rica (BCR) - 4066": "4066",
            "Banco Promerica - 62232450": "62232450",
            "Banco Davivienda - 70707474": "70707474",
            "Banco LAFISE - 9091": "9091",
        }

        banco_seleccionado = st.selectbox(
            "Si pagas por SMS, selecciona tu banco:", list(bancos_sms.keys())
        )
        numero_banco = bancos_sms[banco_seleccionado]

        sinpe_final = st.session_state.sinpe_reserva

        texto_sms = (
            f"PASE {int(st.session_state.total_reserva)} {sinpe_final} Rifa"
        )
        texto_sms_codificado = urllib.parse.quote(texto_sms)
        url_sms = f"sms:{numero_banco}?body={texto_sms_codificado}"

        mensaje_wa = (
            "Hola! Acabo de reservar en la"
            f" *{st.session_state.titulo_reserva}*:\n\n👤 *Nombre:*"
            f" {st.session_state.nombre_reserva}\n📅 *Fecha del sorteo:*"
            f" {st.session_state.fecha_reserva}\n🎟️ *{txt_nums_wa}\n💰 *Monto"
            f" transferido:* ₡{st.session_state.total_reserva:,.0f} CRC\n\nAdjunto"
            " el comprobante del SINPE Móvil enviado al"
            f" {sinpe_final}."
        )
        mensaje_wa_codificado = urllib.parse.quote(mensaje_wa)
        url_whatsapp = (
            f"https://wa.me/506{sinpe_final}?text={mensaje_wa_codificado}"
        )

        col_btn1, col_btn2 = st.columns(2)

        with col_btn1:
            st.markdown(
                f"""
                <a href="{url_sms}">
                    <button style="background-color: #0056b3; color: white; border: none; padding: 14px 15px; font-size: 15px; font-weight: bold; border-radius: 8px; cursor: pointer; width: 100%; margin-bottom: 10px;">
                        💬 Pagar vía SMS ({numero_banco})
                    </button>
                </a>
                """,
                unsafe_allow_html=True,
            )

        with col_btn2:
            st.markdown(
                f"""
                <a href="{url_whatsapp}" target="_blank">
                    <button style="background-color: #25D366; color: white; border: none; padding: 14px 15px; font-size: 15px; font-weight: bold; border-radius: 8px; cursor: pointer; width: 100%;">
                        🟢 Confirmar por WhatsApp
                    </button>
                </a>
                """,
                unsafe_allow_html=True,
            )

        st.write("---")
        if st.button("🔄 Hacer otra reserva"):
            st.session_state.reserva_confirmada = False
            st.session_state.seleccionados_global = []
            st.rerun()

    else:
        st.subheader("Selecciona tus números")
        st.caption("✅ **Pagado** | ❌ **Reservado** | ⚪ **Disponible**")
        st.write("---")

        mapa_numeros = obtener_mapa_numeros_ocupados()

        columnas_por_fila = 5
        total_nums = list(range(0, total_numeros_config))

        for row_start in range(0, len(total_nums), columnas_por_fila):
            fila_nums = total_nums[row_start : row_start + columnas_por_fila]
            cols = st.columns(columnas_por_fila)

            for c_idx, num_val in enumerate(fila_nums):
                num_str = f"{num_val:02d}"
                with cols[c_idx]:
                    if num_str in mapa_numeros:
                        estatus = mapa_numeros[num_str]
                        etiqueta_btn = (
                            f"✅{num_str}"
                            if "Pagado" in str(estatus)
                            else f"❌{num_str}"
                        )
                        st.button(
                            etiqueta_btn, key=f"btn_{num_str}", disabled=True
                        )
                    else:
                        esta_seleccionado = (
                            num_str in st.session_state.seleccionados_global
                        )
                        if st.checkbox(
                            num_str,
                            value=esta_seleccionado,
                            key=f"num_{num_str}",
                        ):
                            if (
                                num_str
                                not in st.session_state.seleccionados_global
                            ):
                                st.session_state.seleccionados_global.append(
                                    num_str
                                )
                        else:
                            if (
                                num_str
                                in st.session_state.seleccionados_global
                            ):
                                st.session_state.seleccionados_global.remove(
                                    num_str
                                )

        numeros_seleccionados = sorted(
            st.session_state.seleccionados_global, key=lambda x: int(x)
        )

        st.write("---")

        if numeros_seleccionados:
            total = len(numeros_seleccionados) * precio_numero
            cant_seleccionados = len(numeros_seleccionados)

            etiqueta_elegidos = (
                "Número elegido"
                if cant_seleccionados == 1
                else "Números elegidos"
            )

            st.success(
                f"**{etiqueta_elegidos} ({cant_seleccionados}):**"
                f" {', '.join(numeros_seleccionados)}"
            )
            st.info(f"**Total a pagar:** ₡{total:,.0f} CRC")

            st.write("### 💳 Datos para pagar por SINPE Móvil")
            st.write(f"**Titular:** {nombre_sinpe}")

            col_a, col_b = st.columns(2)
            with col_a:
                st.code(num_limpio, language="text")
                st.caption("Copiar número SINPE")
            with col_b:
                st.code(f"{int(total)}", language="text")
                st.caption("Copiar monto exacto")

            st.write("---")
            st.write("### 📋 Datos para la Reserva")
            nombre_cliente = st.text_input(
                "Tu Nombre Completo:", key="input_nombre"
            )
            telefono_cliente = st.text_input(
                "Tu Número de Teléfono (8 dígitos):",
                key="input_telefono",
                max_chars=8,
                placeholder="88888888",
            )

            if st.button("🔒 Confirmar Reserva"):
                nombre_limpio = nombre_cliente.strip()
                telefono_limpio = (
                    telefono_cliente.strip().replace(" ", "").replace("-", "")
                )

                es_nombre_valido = bool(
                    re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$", nombre_limpio)
                )
                es_telefono_valido = bool(
                    re.match(r"^\d{8}$", telefono_limpio)
                )

                if not es_nombre_valido:
                    st.error("⚠️ Por favor ingresa un nombre válido.")
                elif not es_telefono_valido:
                    st.error("⚠️ El teléfono debe tener 8 dígitos.")
                else:
                    exitosos, fallidos = guardar_reserva(
                        numeros_seleccionados, nombre_limpio, telefono_limpio
                    )

                    if fallidos:
                        st.error(f"Números ocupados: {', '.join(fallidos)}")

                    if exitosos:
                        st.session_state.reserva_confirmada = True
                        st.session_state.numeros_reserva = exitosos
                        st.session_state.total_reserva = total
                        st.session_state.nombre_reserva = nombre_limpio
                        st.session_state.fecha_reserva = fecha_formateada
                        st.session_state.titulo_reserva = titulo_rifa
                        st.session_state.sinpe_reserva = num_limpio
                        st.rerun()
        else:
            st.warning(
                "Selecciona al menos un número disponible para continuar."
            )

with tab_premio:
    lista_premios = obtener_premios()
    if lista_premios:
        p = lista_premios[0]
        _, p_lugar, p_nombre, p_desc, p_img = p

        with st.container():
            st.markdown('<div class="premio-box">', unsafe_allow_html=True)
            if p_img:
                col_img, col_txt = st.columns([1, 2])
                with col_img:
                    try:
                        img_bytes = base64.b64decode(p_img)
                        st.image(img_bytes, use_container_width=True)
                    except Exception:
                        st.caption("📷 [Imagen no disponible]")
                with col_txt:
                    st.markdown("### 🎁 Premio Único")
                    st.markdown(f"## {p_nombre}")
                    if p_desc and p_desc.strip():
                        st.write(p_desc)
            else:
                st.markdown("### 🎁 Premio Único")
                st.markdown(f"## {p_nombre}")
                if p_desc and p_desc.strip():
                    st.write(p_desc)
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Aún no se ha detallado el premio para esta rifa.")

with tab_reglamento:
    st.markdown(f"""
    * **Valor del boleto:** ₡{precio_numero:,.0f} CRC cada número.
    * **Pago vía SINPE Móvil:** Al realizar la reserva, debes transferir el monto exacto al **{num_limpio}** a nombre de **{nombre_sinpe}**.
    * **Confirmación:** Envía el comprobante de pago vía WhatsApp para confirmar tu número.
    * **Plazo máximo:** Las reservas no pagadas en un plazo razonable podrán ser liberadas.
    """)

# --- PIE DE PÁGINA ---
st.markdown("---")
st.caption("🔗 **Compartir esta rifa:**")

msg_invitacion = (
    f"¡Hola! Te invito a participar en la rifa 🎟️ '{titulo_rifa}': {URL_APP}"
)
link_wa_invitacion = (
    f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg_invitacion)}"
)

col_share1, col_share2 = st.columns([1, 2])

with col_share1:
    st.link_button("📲 WhatsApp", link_wa_invitacion, use_container_width=True)

with col_share2:
    st.code(URL_APP, language="text")
