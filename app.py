import streamlit as st
import sqlite3
import urllib.parse
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Gestor de Rifas CR 🇨🇷", layout="centered", page_icon="🎟️")

# --- CONEXIÓN Y FUNCIONES DE BASE DE DATOS ---
def conectar_db():
    conn = sqlite3.connect("rifa.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS numeros_comprados (
            numero TEXT PRIMARY KEY,
            comprador TEXT,
            telefono TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

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
            c.execute("INSERT INTO numeros_comprados (numero, comprador, telefono) VALUES (?, ?, ?)", (num, nombre, telefono))
            exitosos.append(num)
        except sqlite3.IntegrityError:
            fallidos.append(num)
            
    conn.commit()
    conn.close()
    return exitosos, fallidos

def obtener_todas_las_reservas():
    conn = conectar_db()
    query = "SELECT numero AS 'Número', comprador AS 'Comprador', telefono AS 'Teléfono', fecha AS 'Fecha Reserva' FROM numeros_comprados ORDER BY numero ASC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def liberar_numero(numero):
    conn = conectar_db()
    c = conn.cursor()
    c.execute("DELETE FROM numeros_comprados WHERE numero = ?", (numero,))
    conn.commit()
    conn.close()

# --- PANEL LATERAL ---
with st.sidebar:
    st.header("⚙️ Configuración de la Rifa")
    titulo_rifa = st.text_input("Nombre de la Rifa:", "🎟️ Gran Rifa Especial 🇨🇷")
    precio_numero = st.number_input("Precio por número (₡ CRC):", min_value=100, value=1000, step=100)
    
    st.write("---")
    st.header("📱 Datos de SINPE Móvil")
    num_sinpe = st.text_input("Tu Número de SINPE Móvil:", "88888888")
    nombre_sinpe = st.text_input("Nombre Titular del SINPE:", "Juan Pérez")
    
    st.write("---")
    st.write("### 📊 Estado de Ventas")
    ocupados = obtener_numeros_ocupados()
    st.metric("Números Vendidos / Reservados", f"{len(ocupados)} / 100")

    st.write("---")
    # --- PESTAÑA DE ADMINISTRACIÓN EN LA BARRA LATERAL ---
    with st.expander("🔑 Admin: Gestionar y Liberar Números"):
        clave_admin = st.text_input("Contraseña Admin:", type="password")
        
        if clave_admin == "1234":  # Cambia esta clave si lo deseas
            st.success("Acceso concedido")
            
            df_reservas = obtener_todas_las_reservas()
            
            if not df_reservas.empty:
                st.write("### 📋 Reservas Actuales")
                st.dataframe(df_reservas, use_container_width=True)
                
                lista_numeros_reservados = df_reservas['Número'].tolist()
                num_a_liberar = st.selectbox("Selecciona un número a LIBERAR:", lista_numeros_reservados)
                
                if st.button("🔓 Liberar Número"):
                    liberar_numero(num_a_liberar)
                    st.success(f"¡El número {num_a_liberar} ha sido liberado!")
                    st.rerun()
            else:
                st.info("No hay números reservados por el momento.")
        elif clave_admin != "":
            st.error("Contraseña incorrecta")

# --- VISTA PRINCIPAL ---
st.title(titulo_rifa)
st.subheader("Selecciona tus números del 00 al 99")

st.write("---")

numeros_bloqueados = obtener_numeros_ocupados()

st.write("### Tablero de Números:")
st.caption("🔴 Rojo = Reservado/Ocupado | ⚪ Blanco = Disponible")

# Matriz del 00 al 99 en 10 columnas
cols = st.columns(10)
numeros_seleccionados = []

for i in range(100):
    num_str = f"{i:02d}"
    col_idx = i % 10
    
    with cols[col_idx]:
        if num_str in numeros_bloqueados:
            st.button(f"❌ {num_str}", key=f"btn_{num_str}", disabled=True)
        else:
            if st.checkbox(num_str, key=f"num_{num_str}"):
                numeros_seleccionados.append(num_str)

st.write("---")

# --- RESUMEN DE PAGO Y RESERVA ---
if numeros_seleccionados:
    total = len(numeros_seleccionados) * precio_numero
    num_limpio = num_sinpe.replace("-", "").replace(" ", "")
    
    st.success(f"**Números elegidos:** {', '.join(numeros_seleccionados)}")
    st.info(f"**Total a pagar:** ₡{total:,.0f} CRC")
    
    st.write("### 💳 Datos para pagar por SINPE Móvil")
    st.write(f"**Titular:** {nombre_sinpe}")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.code(num_limpio, language="text")
        st.caption("👆 Copiar número SINPE")
    with col_b:
        st.code(f"{int(total)}", language="text")
        st.caption("👆 Copiar monto exacto")

    st.write("---")
    st.write("### 📋 Datos para la Reserva")
    nombre_cliente = st.text_input("Tu Nombre Completo:")
    telefono_cliente = st.text_input("Tu Número de Teléfono:")
    
    if st.button("🔒 Confirmar Reserva"):
        if nombre_cliente.strip() != "" and telefono_cliente.strip() != "":
            exitosos, fallidos = guardar_reserva(numeros_seleccionados, nombre_cliente, telefono_cliente)
            
            if fallidos:
                st.error(f"Los siguientes números ya habían sido tomados: {', '.join(fallidos)}")
            
            if exitosos:
                st.balloons()
                st.success(f"🎉 ¡Números {', '.join(exitosos)} reservados exitosamente!")
                
                st.write("---")
                st.subheader("📲 Elige cómo pagar / enviar comprobante:")

                # Lista de bancos de Costa Rica para SMS
                bancos_sms = {
                    "Banco Nacional (BNCR)": "2627",
                    "Banco de Costa Rica (BCR)": "4066",
                    "BAC Credomatic": "70701222",
                    "Banco Promerica": "62232450"
                }

                banco_seleccionado = st.selectbox("Si pagas por SMS (mensajería de texto), selecciona tu banco:", list(bancos_sms.keys()))
                numero_banco = bancos_sms[banco_seleccionado]
                
                # Texto para SMS
                texto_sms = f"PASE {int(total)} {num_limpio} Rifa"
                texto_sms_codificado = urllib.parse.quote(texto_sms)
                url_sms = f"sms:{numero_banco}?body={texto_sms_codificado}"

                # Texto para WhatsApp
                nums_texto = ", ".join(exitosos)
                mensaje_wa = (
                    f"Hola! Acabo de reservar en la *{titulo_rifa}*:\n\n"
                    f"👤 *Nombre:* {nombre_cliente}\n"
                    f"🎟️ *Números:* {nums_texto}\n"
                    f"💰 *Monto transferido:* ₡{total:,.0f} CRC\n\n"
                    f"Adjunto el comprobante del SINPE Móvil enviado al {num_sinpe}."
                )
                mensaje_wa_codificado = urllib.parse.quote(mensaje_wa)
                url_whatsapp = f"https://wa.me/506{num_limpio}?text={mensaje_wa_codificado}"
                
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    st.markdown(f"""
                        <a href="{url_sms}">
                            <button style="background-color: #0056b3; color: white; border: none; padding: 14px 15px; font-size: 15px; font-weight: bold; border-radius: 8px; cursor: pointer; width: 100%; margin-bottom: 10px;">
                                💬 Pagar vía SMS ({numero_banco})
                            </button>
                        </a>
                    """, unsafe_allow_html=True)

                with col_btn2:
                    st.markdown(f"""
                        <a href="{url_whatsapp}" target="_blank">
                            <button style="background-color: #25D366; color: white; border: none; padding: 14px 15px; font-size: 15px; font-weight: bold; border-radius: 8px; cursor: pointer; width: 100%;">
                                🟢 Confirmar por WhatsApp
                            </button>
                        </a>
                    """, unsafe_allow_html=True)
        else:
            st.error("Por favor completa tu nombre y número de teléfono antes de reservar.")
else:
    st.warning("Selecciona al menos un número disponible para continuar.")
