import sqlite3
import urllib.parse
from datetime import datetime
import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Gestor de Rifas CR 🇨🇷", layout="centered", page_icon="🎟️"
)

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
    </style>
""",
    unsafe_allow_html=True,
)


# --- CONEXIÓN Y FUNCIONES DE BASE DE DATOS ---
def conectar_db():
  conn = sqlite3.connect("rifa.db")
  c = conn.cursor()

  # Tabla de reservas (con estado_pago)
  c.execute("""
        CREATE TABLE IF NOT EXISTS numeros_comprados (
            numero TEXT PRIMARY KEY,
            comprador TEXT,
            telefono TEXT,
            estado_pago TEXT DEFAULT 'Pendiente',
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

  # Garantizar que existe la columna estado_pago si la tabla es antigua
  try:
    c.execute(
        "ALTER TABLE numeros_comprados ADD COLUMN estado_pago TEXT DEFAULT"
        " 'Pendiente'"
    )
  except sqlite3.OperationalError:
    pass

  # Tabla de configuración permanente
  c.execute("""
        CREATE TABLE IF NOT EXISTS configuracion (
            clave TEXT PRIMARY KEY,
            valor TEXT
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
  }

  for clave, valor in filas:
    config[clave] = valor

  return config


def guardar_configuracion(titulo, precio, num_sinpe, nombre_sinpe):
  conn = conectar_db()
  c = conn.cursor()
  datos = [
      ("rifa_titulo", titulo),
      ("rifa_precio", str(precio)),
      ("sinpe_numero", num_sinpe),
      ("sinpe_nombre", nombre_sinpe),
  ]
  c.executemany(
      "INSERT OR REPLACE INTO configuracion (clave, valor) VALUES (?, ?)", datos
  )
  conn.commit()
  conn.close()


def obtener_numeros_ocupados():
  conn = conectar_db()
  c = conn.cursor()
  c.execute("SELECT numero FROM numeros_comprados")
  filas = c.fetchall()
  conn.close()
  return [f[0] for f in filas]


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
      " FROM numeros_comprados ORDER BY numero ASC"
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


# --- CARGAR CONFIGURACIÓN PERMANENTE ---
config_actual = obtener_configuracion()

# --- INICIALIZACIÓN DE ESTADO DE SESIÓN ---
if "reserva_confirmada" not in st.session_state:
  st.session_state.reserva_confirmada = False
if "seleccionados_global" not in st.session_state:
  st.session_state.seleccionados_global = []

# --- PANEL LATERAL ---
with st.sidebar:
  st.title("⚙️ Panel de Control")

  # -------------------------------------------------------------
  # 🔑 SECCIÓN ADMIN Y ESTATUS DE PAGOS (AHORA VISIBLE DIRECTAMENTE)
  # -------------------------------------------------------------
  st.subheader("🔑 Modo Administrador")
  clave_admin = st.text_input(
      "Contraseña Admin:", type="password", key="pass_admin"
  )

  if clave_admin == "1234":
    st.success("✅ Acceso Concedido")

    df_reservas = obtener_todas_las_reservas()

    st.write("---")
    st.write("### 📊 ESTATUS DE PAGOS")

    if not df_reservas.empty:
      # Mostrar la lista completa con los estatus
      st.dataframe(df_reservas, use_container_width=True)

      st.write("#### ✏️ Cambiar Estatus de Pago")
      lista_numeros = df_reservas["Número"].tolist()

      num_a_pagar = st.selectbox(
          "Número:", lista_numeros, key="sel_num_estatus"
      )
      nuevo_est = st.selectbox(
          "Nuevo Estado:", ["✅ Pagado", "⏳ Pendiente"], key="sel_nuevo_estatus"
      )

      if st.button("💾 Guardar Estatus"):
        cambiar_estado_pago(num_a_pagar, nuevo_est)
        st.success(f"¡Número {num_a_pagar} actualizado a {nuevo_est}!")
        st.rerun()

      st.write("---")
      st.write("#### 🔓 Cancelar Reserva (Liberar)")
      num_a_liberar = st.selectbox("Número a liberar:", lista_numeros, key="sel_num_liberar")

      if st.button("🔓 Liberar Número"):
        liberar_numero(num_a_liberar)
        st.success(f"¡Número {num_a_liberar} liberado!")
        st.rerun()
    else:
      st.info("No hay reservas registradas por el momento.")

    st.write("---")

  elif clave_admin != "":
    st.error("Contraseña incorrecta")

  # -------------------------------------------------------------
  # CONFIGURACIÓN DE LA RIFA
  # -------------------------------------------------------------
  with st.expander("⚙️ Configuración de la Rifa (SINPE / Nombre)"):
    with st.form("form_configuracion"):
      nuevo_titulo = st.text_input(
          "Nombre de la Rifa:",
          value=config_actual["rifa_titulo"],
          key="input_titulo",
      )
      fecha_sorteo = st.date_input("Fecha del Sorteo:", value=datetime.today())
      nuevo_precio = st.number_input(
          "Precio por número (₡ CRC):",
          min_value=100,
          value=int(config_actual["rifa_precio"]),
          step=100,
          key="input_precio",
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
        sinpe_limpio = nuevo_sinpe.replace("-", "").replace(" ", "").strip()
        guardar_configuracion(
            nuevo_titulo, nuevo_precio, sinpe_limpio, nuevo_nombre_sinpe
        )
        st.success("¡Configuración guardada!")
        st.rerun()

  # Variables de fecha por si no abre el expander
  if "fecha_sorteo" not in locals():
    fecha_sorteo = datetime.today()

  st.write("---")
  st.write("### 📈 Ventas Totales")
  ocupados = obtener_numeros_ocupados()
  st.metric("Números Vendidos / Reservados", f"{len(ocupados)} / 100")

# Variables de configuración activas
fecha_formateada = fecha_sorteo.strftime("%d/%m/%Y")
titulo_rifa = config_actual["rifa_titulo"]
precio_numero = int(config_actual["rifa_precio"])
num_limpio = config_actual["sinpe_numero"]
nombre_sinpe = config_actual["sinpe_nombre"]

# --- VISTA PRINCIPAL ---
st.title(titulo_rifa)
st.caption(f"📅 **Fecha del Sorteo:** {fecha_formateada}")

# --- VISTA 1: SI YA SE CONFIRMÓ LA RESERVA ---
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
  st.info(
      f"👤 **Comprador:** {st.session_state.nombre_reserva} | 📅 **Fecha:**"
      f" {st.session_state.fecha_reserva} | 💰 **Total a pagar:**"
      f" ₡{st.session_state.total_reserva:,.0f} CRC"
  )

  st.write("---")
  st.subheader("📲 Elige tu método para pagar / enviar comprobante:")

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
  texto_sms_codificado = urllib.parse.quote(texto_sms)
  url_sms = f"sms:{numero_banco}?body={texto_sms_codificado}"

  mensaje_wa = (
      f"Hola! Acabo de reservar en la *{st.session_state.titulo_reserva}*:\n\n"
      f"👤 *Nombre:* {st.session_state.nombre_reserva}\n"
      f"📅 *Fecha del sorteo:* {st.session_state.fecha_reserva}\n"
      f"🎟️ *{txt_nums_wa}\n"
      f"💰 *Monto transferido:* ₡{st.session_state.total_reserva:,.0f} CRC\n\n"
      f"Adjunto el comprobante del SINPE Móvil enviado al {sinpe_final}."
  )
  mensaje_wa_codificado = urllib.parse.quote(mensaje_wa)
  url_whatsapp = f"https://wa.me/506{sinpe_final}?text={mensaje_wa_codificado}"

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

# --- VISTA 2: SELECCIÓN DE NÚMEROS (SI NO HA CONFIRMADO) ---
else:
  st.subheader("Elige tus números del 00 al 99")
  st.write("---")

  numeros_bloqueados = obtener_numeros_ocupados()

  st.write("### 🔢 Selecciona tus números por decenas:")
  st.caption("🔴 Indica número reservado/ocupado | ⚪ Número disponible")

  rangos = [
      "00 - 09",
      "10 - 19",
      "20 - 29",
      "30 - 39",
      "40 - 49",
      "50 - 59",
      "60 - 69",
      "70 - 79",
      "80 - 89",
      "90 - 99",
  ]

  tabs = st.tabs(rangos)

  for idx, tab in enumerate(tabs):
    with tab:
      inicio = idx * 10

      cols_fila1 = st.columns(5)
      for offset in range(5):
        i = inicio + offset
        num_str = f"{i:02d}"
        with cols_fila1[offset]:
          if num_str in numeros_bloqueados:
            st.button(f"❌ {num_str}", key=f"btn_{num_str}", disabled=True)
          else:
            if st.checkbox(num_str, key=f"num_{num_str}"):
              if num_str not in st.session_state.seleccionados_global:
                st.session_state.seleccionados_global.append(num_str)
            else:
              if num_str in st.session_state.seleccionados_global:
                st.session_state.seleccionados_global.remove(num_str)

      cols_fila2 = st.columns(5)
      for offset in range(5, 10):
        i = inicio + offset
        num_str = f"{i:02d}"
        with cols_fila2[offset - 5]:
          if num_str in numeros_bloqueados:
            st.button(f"❌ {num_str}", key=f"btn_{num_str}", disabled=True)
          else:
            if st.checkbox(num_str, key=f"num_{num_str}"):
              if num_str not in st.session_state.seleccionados_global:
                st.session_state.seleccionados_global.append(num_str)
            else:
              if num_str in st.session_state.seleccionados_global:
                st.session_state.seleccionados_global.remove(num_str)

  numeros_seleccionados = sorted(st.session_state.seleccionados_global)

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
        "Tu Número de Teléfono:", key="input_telefono"
    )

    if st.button("🔒 Confirmar Reserva"):
      if nombre_cliente.strip() != "" and telefono_cliente.strip() != "":
        exitosos, fallidos = guardar_reserva(
            numeros_seleccionados, nombre_cliente, telefono_cliente
        )

        if fallidos:
          msg_fallidos = (
              f"El número {fallidos[0]} ya había sido tomado."
              if len(fallidos) == 1
              else "Los siguientes números ya habían sido tomados:"
                   f" {', '.join(fallidos)}"
          )
          st.error(msg_fallidos)

        if exitosos:
          st.session_state.reserva_confirmada = True
          st.session_state.numeros_reserva = exitosos
          st.session_state.total_reserva = total
          st.session_state.nombre_reserva = nombre_cliente
          st.session_state.fecha_reserva = fecha_formateada
          st.session_state.titulo_reserva = titulo_rifa
          st.session_state.sinpe_reserva = num_limpio
          st.rerun()
      else:
        st.error(
            "Por favor completa tu nombre y número de teléfono antes de"
            " reservar."
        )
  else:
    st.warning("Selecciona al menos un número disponible para continuar.")
