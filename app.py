import urllib.parse
import streamlit as st

# 1. Configuración general
URL_APP = "https://tu-app-de-rifa.streamlit.app"  # Modifica con tu enlace real

st.title("🎟️ Sistema de Rifas")
st.write("Selecciona tus números y realiza tu reserva.")

# --- AQUÍ VA TU LÓGICA DE SELECCIÓN DE NÚMEROS Y BASE DE DATOS ---
# (Mantén aquí el código donde cargas números de 00 al 99, formulario de reserva, etc.)

st.info("Selecciona tus números disponibles y completa los datos de pago.")

# -----------------------------------------------------------------

# Divider o espacio para separar el flujo principal
st.markdown("---")

# --- SECCIÓN OPCIONAL AL FINAL DE LA PÁGINA ---
st.caption("¿Quieres invitar a alguien más a participar?")

# Botón discreto para compartir por WhatsApp
mensaje = f"¡Hola! Te invito a participar en la rifa 🎟️. Elige tu número aquí: {URL_APP}"
link_wa = f"https://api.whatsapp.com/send?text={urllib.parse.quote(mensaje)}"

col1, col2 = st.columns([1, 2])

with col1:
    # Botón nativo de Streamlit estilo enlace
    st.link_button("📲 Compartir por WhatsApp", link_wa, use_container_width=True)

with col2:
    # Opción alternativa para copiar enlace si no usan WhatsApp
    if st.button("📋 Copiar enlace", use_container_width=True):
        st.toast(f"Enlace para copiar: {URL_APP}", icon="ℹ️")
