import sqlite3
import urllib.parse
from datetime import datetime, date
import pandas as pd
import streamlit as st
import re

# Configuración de la página
st.set_page_config(
    page_title="Gestor de Rifas CR 🇨🇷", layout="centered", page_icon="🎟️"
)

# Configura aquí tu dirección web desplegada
URL_APP = "https://tu-app-de-rifa.streamlit.app"

# Estilos CSS personalizados
st.markdown(
    """
    <style>
    .stButton>button {
        width: 100%;
        height: 3em;
        font-weight: bold;
        border-radius: 8px;
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
    </style>
""",
    unsafe_allow_html=True,
)


# --- CONEXIÓN Y FUNCIONES DE BASE DE DATOS ---
def conectar_db():
    conn = sqlite3.connect("rifa.db")
    c = conn.cursor()

    # Tabla de rifas
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

    # Tabla de reservas asociadas a una rifa específica
    c.execute("""
        CREATE TABLE IF NOT EXISTS numeros_comprados (
            rifa_id INTEGER,
            numero TEXT,
            comprador TEXT,
            telefono TEXT,
            estado_pago TEXT DEFAULT 'Pendiente',
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (rifa_id, numero),
            FOREIGN KEY (rifa_id) REFERENCES rifas (id)
        )
    """)

    conn.commit()

    # Si no existe ninguna rifa, creamos una inicial por defecto
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


def obtener_todas_las_rifas():
    conn = sqlite3.connect("rifa.db")
    c = conn.cursor()
    c.execute("SELECT id, titulo FROM rifas ORDER BY id DESC")
    filas = c.fetchall()
    conn.close()
    return filas


def obtener_configuracion_rifa(rifa_id):
    conn = sqlite3.connect("rifa.db")
    c = conn.cursor()
    c.execute(
        "SELECT id, titulo, precio, sinpe_numero, sinpe_nombre, fecha_sorteo,"
        " total_numeros FROM rifas WHERE id = ?",
        (rifa_id,),
    )
    fila = c.fetchone()
    conn.close()

    if fila:
        return {
            "id": fila[0],
            "rifa_titulo": fila[1],
            "rifa_precio": fila[2],
            "sinpe_numero": fila[3],
            "sinpe_nombre": fila[4],
            "rifa_fecha_sorteo": fila[5],
            "total_numeros": fila[6],
        }
    return None


def crear_nueva_rifa(
    titulo, precio, num_sinpe, nombre_sinpe, fecha_str, total_nums
):
    conn = sqlite3.connect("rifa.db")
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO rifas (titulo, precio, sinpe_numero, sinpe_nombre, fecha_sorteo, total_numeros)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            titulo,
            str(precio),
            num_sinpe,
            nombre_sinpe,
            fecha_str,
            str(total_nums),
        ),
    )
    nueva_id = c.lastrowid
    conn.commit()
    conn.close()
    return nueva_id


def actualizar_configuracion_rifa(
    rifa_id, titulo, precio, num_sinpe, nombre_sinpe, fecha_str, total_nums
):
    conn = sqlite3.connect("rifa.db")
    c = conn.cursor()
    c.execute(
        """
        UPDATE rifas 
        SET titulo = ?, precio = ?, sinpe_numero = ?, sinpe_nombre = ?, fecha_sorteo = ?, total_numeros = ?
        WHERE id = ?
    """,
        (
            titulo,
            str(precio),
            num_sinpe,
            nombre_sinpe,
            fecha_str,
            str(total_nums),
            rifa_id,
        ),
    )
    conn.commit()
    conn.close()


def obtener_mapa_numeros_ocupados(rifa_id):
    conn = sqlite3.connect("rifa.db")
    c = conn.cursor()
    c.execute(
        "SELECT numero, estado_pago FROM numeros_comprados WHERE rifa_id = ?",
        (rifa_id,),
    )
    filas = c.fetchall()
    conn.close()
    return {f[0]: f[1] for f in filas}


def guardar_reserva(rifa_id, numeros, nombre, telefono):
    conn = sqlite3.connect("rifa.db")
    c = conn.cursor()
    exitosos = []
    fallidos = []

    for num in numeros:
        try:
            c.execute(
                "INSERT INTO numeros_comprados (rifa_id, numero, comprador,"
                " telefono, estado_pago) VALUES (?, ?, ?, ?, 'Pendiente')",
                (rifa_id, num, nombre, telefono),
            )
            exitosos.append(num)
        except sqlite3.IntegrityError:
            fallidos.append(num)

    conn.commit()
    conn.close()
    return exitosos, fallidos


def obtener_todas_las_reservas(rifa_id):
    conn = sqlite3.connect("rifa.db")
    query = f"""
        SELECT numero AS 'Número', comprador AS 'Comprador', telefono AS 'Teléfono', estado_pago AS 'Estatus Pago', fecha AS 'Fecha Reserva'
        FROM numeros_comprados 
        WHERE rifa_id = {rifa_id}
        ORDER BY CAST(numero AS INTEGER) ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def cambiar_estado_pago(rifa_id, numero, nuevo_estado):
    conn = sqlite3.connect("rifa.db")
    c = conn.cursor()
    c.execute(
        "UPDATE numeros_comprados SET estado_pago = ? WHERE rifa_id = ? AND"
        " numero = ?",
        (nuevo_estado, rifa_id, numero),
    )
    conn.commit()
    conn.close()


def liberar_numero(rifa_id, numero):
    conn = sqlite3.connect("rifa.db")
    c = conn.cursor()
    c.execute(
        "DELETE FROM numeros_comprados WHERE rifa_id = ? AND numero = ?",
        (rifa_id, numero),
    )
    conn.commit()
    conn.close()


# Inicializar DB
conectar_db()
lista_rifas = obtener_todas_las_rifas()

# Rifa activa en la sesión por defecto (la más reciente)
if "rifa_activa_id" not in st.session_state:
    st.session_state.rifa_activa_id = lista_rifas[0][0]

config_actual = obtener_configuracion_rifa(st.session_state.rifa_activa_id)
total_numeros_config = int(config_actual["total_numeros"])

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

# --- PANEL LATERAL ---
with st.sidebar:
    st.title("⚙️ Panel de Control")

    # Selector de Rifa Activa
    opciones_rifas = {r[1]: r[0] for r in lista_rifas}
    rifa_seleccionada_nombre = st.selectbox(
        "🎯 Seleccionar Rifa Activa:",
        options=list(opciones_rifas.keys()),
        index=0,
    )
    rifa_id_seleccionada = opciones_rifas[rifa_seleccionada_nombre]

    if rifa_id_seleccionada != st.session_state.rifa_activa_id:
        st.session_state.rifa_activa_id = rifa_id_seleccionada
        st.session_state.reserva_confirmada = False
        st.session_state.seleccionados_global = []
        st.rerun()

    st.write("---")

    # -------------------------------------------------------------
    # ➕ CREAR UNA NUEVA RIFA
    # -------------------------------------------------------------
    with st.expander("➕ Crear Nueva Rifa"):
        with st.form("form_nueva_rifa"):
            nuevo_titulo_crear = st.text_input(
                "Nombre de la nueva rifa:",
                placeholder="Ej. Rifa Navideña 2026",
            )
            fecha_sorteo_crear = st.date_input("Fecha del Sorteo:", value=date.today())
            nuevo_precio_crear = st.number_input(
                "Precio por número (₡ CRC):",
                min_value=100,
                value=1000,
                step=100,
            )
            nuevo_total_numeros_crear = st.number_input(
                "Cantidad total de números:",
                min_value=10,
                max_value=1000,
                value=100,
                step=10,
            )
            nuevo_sinpe_crear = st.text_input(
                "Número SINPE:", value=config_actual["sinpe_numero"]
            )
            nuevo_nombre_sinpe_crear = st.text_input(
                "Titular SINPE:", value=config_actual["sinpe_nombre"]
            )

            btn_crear_rifa = st.form_submit_button("🚀 Crear Rifa")

            if btn_crear_rifa:
                if nuevo_titulo_crear.strip() == "":
                    st.error("Ingresa un nombre para la nueva rifa.")
                else:
                    sinpe_limpio = (
                        nuevo_sinpe_crear.replace("-", "").replace(" ", "").strip()
                    )
                    fecha_str = fecha_sorteo_crear.strftime("%Y-%m-%d")
                    nueva_id = crear_nueva_rifa(
                        nuevo_titulo_crear,
                        nuevo_precio_crear,
                        sinpe_limpio,
                        nuevo_nombre_sinpe_crear,
                        fecha_str,
                        nuevo_total_numeros_crear,
                    )
                    st.session_state.rifa_activa_id = nueva_id
                    st.session_state.reserva_confirmada = False
                    st.session_state.seleccionados_global = []
                    st.success(f"¡Rifa '{nuevo_titulo_crear}' creada!")
                    st.rerun()

    # -------------------------------------------------------------
    # 🔑 MODO ADMINISTRADOR
    # -------------------------------------------------------------
    st.subheader("🔑 Modo Administrador")
    clave_admin = st.text_input(
        "Contraseña Admin:", type="password", key="pass_admin"
    )

    if clave_admin == "1234":
        st.success("✅ Acceso Concedido")

        mapa_ocupados = obtener_mapa_numeros_ocupados(
            st.session_state.rifa_activa_id
        )
        total_reservados = len(mapa_ocupados)
        total_pagados = sum(
            1 for est in mapa_ocupados.values() if "Pagado" in str(est)
        )
        total_pendientes = total_reservados - total_pagados

        pct_ocupados = (total_reservados / total_numeros_config) * 100
        pct_pagados = (
            (total_pagados / total_reservados * 100) if total_reservados > 0 else 0
        )
        pct_pendientes = (
            (total_pendientes / total_reservados * 100)
            if total_reservados > 0
            else 0
        )

        precio_num = int(config_actual["rifa_precio"])
        recaudado = total_pagados * precio_num

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
                "✅ Pagados", f"{total_pagados}", delta=f"{pct_pagados:.0f}% del total"
            )
        with col_m2:
            st.metric(
                "⏳ Pendientes",
                f"{total_pendientes}",
                delta=f"{pct_pendientes:.0f}% del total",
            )
            st.metric("💰 Recaudado", f"₡{recaudado:,.0f}")

        st.progress(min(total_reservados / total_numeros_config, 1.0))

        df_reservas = obtener_todas_las_reservas(
            st.session_state.rifa_activa_id
        )

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
                    "Buscar (Nombre/Tel):", key="search_admin", placeholder="Ej: Juan"
                )

            df_filtrado = df_reservas.copy()
            if filtro_estado != "Todos":
                df_filtrado = df_filtrado[df_filtrado["Estatus Pago"] == filtro_estado]

            if busqueda_txt.strip():
                txt_b = busqueda_txt.strip().lower()
                df_filtrado = df_filtrado[
                    df_filtrado["Comprador"].str.lower().str.contains(txt_b)
                    | df_filtrado["Teléfono"].str.contains(txt_b)
                ]

            st.dataframe(df_filtrado, use_container_width=True)

            csv_data = df_reservas.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Descargar Lista Completa (CSV)",
                data=csv_data,
                file_name=f"Reservas_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )

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
                cambiar_estado_pago(
                    st.session_state.rifa_activa_id, num_a_pagar, nuevo_est
                )
                st.success(f"¡Número {num_a_pagar} actualizado!")
                st.rerun()

            st.write("---")
            st.write("#### 🔓 Cancelar Reserva (Liberar)")
            num_a_liberar = st.selectbox(
                "Número a liberar:", lista_numeros, key="sel_num_liberar"
            )

            if st.button("🔓 Liberar Número"):
                liberar_numero(st.session_state.rifa_activa_id, num_a_liberar)
                st.success(f"¡Número {num_a_liberar} liberado!")
                st.rerun()
        else:
            st.info("No hay reservas en esta rifa.")

        st.write("---")

    elif clave_admin != "":
        st.error("Contraseña incorrecta")

    # -------------------------------------------------------------
    # EDICIÓN DE LA RIFA ACTUAL
    # -------------------------------------------------------------
    with st.expander("⚙️ Editar Rifa Actual"):
        with st.form("form_configuracion"):
            nuevo_titulo = st.text_input(
                "Nombre de la Rifa:",
                value=config_actual["rifa_titulo"],
                key="input_titulo",
            )
            fecha_sorteo = st.date_input("Fecha del Sorteo:", value=fecha_sorteo_db)
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

            btn_guardar = st.form_submit_button("💾 Guardar Cambios")

            if btn_guardar:
                sinpe_limpio = (
                    nuevo_sinpe.replace("-", "").replace(" ", "").strip()
                )
                fecha_str = fecha_sorteo.strftime("%Y-%m-%d")
                actualizar_configuracion_rifa(
                    st.session_state.rifa_activa_id,
                    nuevo_titulo,
                    nuevo_precio,
                    sinpe_limpio,
                    nuevo_nombre_sinpe,
                    fecha_str,
                    nuevo_total_numeros,
                )
                st.success("¡Rifa actualizada!")
                st.rerun()

# Variables de configuración activas
fecha_formateada = fecha_sorteo_db.strftime("%d/%m/%Y")
titulo_rifa = config_actual["rifa_titulo"]
precio_numero = int(config_actual["rifa_precio"])
num_limpio = config_actual["sinpe_numero"]
nombre_sinpe = config_actual["sinpe_nombre"]

# --- VISTA PRINCIPAL ---
st.title(titulo_rifa)
st.caption(f"📅 **Fecha del Sorteo:** {fecha_formateada}")

# INDICADOR DE DISPONIBILIDAD
mapa_numeros_actual = obtener_mapa_numeros_ocupados(
    st.session_state.rifa_activa_id
)
disponibles_count = total_numeros_config - len(mapa_numeros_actual)

if disponibles_count <= (total_numeros_config * 0.2) and disponibles_count > 0:
    st.warning(f"🔥 **¡Atención! Solo quedan {disponibles_count} números disponibles.**")
else:
    st.info(f"🎟️ **Números disponibles:** {disponibles_count} de {total_numeros_config}")

# REGLAMENTO
with st.expander("📜 Reglamento y Términos de la Rifa"):
    st.markdown(f"""
    * **Valor del boleto:** ₡{precio_numero:,.0f} CRC cada número.
    * **Pago vía SINPE Móvil:** Transferir el monto exacto al **{num_limpio}** a nombre de **{nombre_sinpe}**.
    * **Confirmación:** Envía el comprobante vía WhatsApp para confirmar tu número.
    """)

# --- VISTA 1: RESERVA CONFIRMADA ---
if st.session_state.reserva_confirmada:
    st.balloons()

    cant_reserva = len(st.session_state.numeros_reserva)
    if cant_reserva == 1:
        msg_exito = (
            "🎉 ¡Número"
            f" **{st.session_state.numeros_reserva[0]}** reservado exitosamente!"
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
        <h3>🎟️ BOLETO DIGITAL DE RESERVA</h3>
        <p><b>Rifa:</b> {st.session_state.titulo_reserva}</p>
        <p><b>Comprador:</b> {st.session_state.nombre_reserva}</p>
        <p><b>Número(s):</b> {', '.join(st.session_state.numeros_reserva)}</p>
        <p><b>Total a Pagar:</b> ₡{st.session_state.total_reserva:,.0f} CRC</p>
        <p><b>Fecha de Sorteo:</b> {st.session_state.fecha_reserva}</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.write("---")
    st.subheader("📲 Método de Pago / Comprobante:")

    bancos_sms = {
        "Banco Nacional (BNCR)": "2627",
        "Banco de Costa Rica (BCR)": "4066",
        "BAC Credomatic": "70701222",
        "Banco Promerica": "62232450",
    }

    banco_seleccionado = st.selectbox(
        "Si pagas por SMS, selecciona tu banco:", list(bancos_sms.keys())
    )
    numero_banco = bancos_sms[banco_seleccionado]
    sinpe_final = st.session_state.sinpe_reserva

    texto_sms = f"PASE {int(st.session_state.total_reserva)} {sinpe_final} Rifa"
    url_sms = f"sms:{numero_banco}?body={urllib.parse.quote(texto_sms)}"

    mensaje_wa = (
        f"Hola! Acabo de reservar en la *{st.session_state.titulo_reserva}*:\n\n"
        f"👤 *Nombre:* {st.session_state.nombre_reserva}\n"
        f"📅 *Fecha del sorteo:* {st.session_state.fecha_reserva}\n"
        f"🎟️ *{txt_nums_wa}\n"
        f"💰 *Monto transferido:* ₡{st.session_state.total_reserva:,.0f} CRC\n\n"
        f"Adjunto comprobante enviado al {sinpe_final}."
    )
    url_whatsapp = f"https://wa.me/506{sinpe_final}?text={urllib.parse.quote(mensaje_wa)}"

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        st.markdown(
            f'<a href="{url_sms}"><button style="background-color: #0056b3;'
            " color: white; border: none; padding: 14px 15px; font-size: 15px;"
            " font-weight: bold; border-radius: 8px; cursor: pointer; width:"
            ' 100%;">💬 Pagar por SMS</button></a>',
            unsafe_allow_html=True,
        )
    with col_btn2:
        st.markdown(
            f'<a href="{url_whatsapp}" target="_blank"><button'
            ' style="background-color: #25D366; color: white; border: none;'
            " padding: 14px 15px; font-size: 15px; font-weight: bold;"
            ' border-radius: 8px; cursor: pointer; width: 100%;">🟢 Confirmar'
            " por WhatsApp</button></a>",
            unsafe_allow_html=True,
        )

    st.write("---")
    if st.button("🔄 Hacer otra reserva"):
        st.session_state.reserva_confirmada = False
        st.session_state.seleccionados_global = []
        st.rerun()

# --- VISTA 2: SELECCIÓN DE NÚMEROS ---
else:
    st.subheader(f"Elige tus números (del 00 al {total_numeros_config - 1:02d})")
    st.write("---")

    mapa_numeros = obtener_mapa_numeros_ocupados(
        st.session_state.rifa_activa_id
    )

    st.write("### 🔢 Selecciona tus números por decenas:")
    st.caption("✅ **Confirmado** | ❌ **Reservado** | ⚪ **Disponible**")

    rangos = []
    bloques = []
    for i in range(0, total_numeros_config, 10):
        fin_bloque = min(i + 9, total_numeros_config - 1)
        rangos.append(f"{i:02d} - {fin_bloque:02d}")
        bloques.append((i, fin_bloque))

    tabs = st.tabs(rangos)

    for idx, tab in enumerate(tabs):
        with tab:
            inicio, fin = bloques[idx]
            numeros_bloque = list(range(inicio, fin + 1))

            for row_start in range(0, len(numeros_bloque), 5):
                fila_nums = numeros_bloque[row_start : row_start + 5]
                cols = st.columns(len(fila_nums))

                for c_idx, num_val in enumerate(fila_nums):
                    num_str = f"{num_val:02d}"
                    with cols[c_idx]:
                        if num_str in mapa_numeros:
                            estatus = mapa_numeros[num_str]
                            etiqueta_btn = (
                                f"✅ {num_str}"
                                if "Pagado" in str(estatus)
                                else f"❌ {num_str}"
                            )
                            st.button(etiqueta_btn, key=f"btn_{num_str}", disabled=True)
                        else:
                            if st.checkbox(num_str, key=f"num_{num_str}"):
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
            "Número elegido" if cant_seleccionados == 1 else "Números elegidos"
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
        nombre_cliente = st.text_input("Tu Nombre Completo:", key="input_nombre")
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
            es_telefono_valido = bool(re.match(r"^\d{8}$", telefono_limpio))

            if not es_nombre_valido:
                st.error("⚠️ Ingresa un nombre válido (solo letras y espacios).")
            elif not es_telefono_valido:
                st.error("⚠️ El teléfono debe tener exactamente 8 dígitos.")
            else:
                exitosos, fallidos = guardar_reserva(
                    st.session_state.rifa_activa_id,
                    numeros_seleccionados,
                    nombre_limpio,
                    telefono_limpio,
                )

                if fallidos:
                    st.error(
                        "Algunos números ya fueron tomados:"
                        f" {', '.join(fallidos)}"
                    )

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
        st.warning("Selecciona al menos un número disponible para continuar.")

# -------------------------------------------------------------
# 🔗 OPCIÓN DISCRETA AL FINAL DE PÁGINA
# -------------------------------------------------------------
st.markdown("---")
st.caption("🔗 **Compartir esta rifa:**")

msg_invitacion = f"¡Hola! Te invito a participar en la rifa 🎟️ '{titulo_rifa}': {URL_APP}"
link_wa_invitacion = (
    f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg_invitacion)}"
)

col_share1, col_share2 = st.columns([1, 2])

with col_share1:
    st.link_button("📲 WhatsApp", link_wa_invitacion, use_container_width=True)

with col_share2:
    st.code(URL_APP, language="text")
