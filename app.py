import urllib.parse
import streamlit as st

# Reemplaza con la URL real de tu aplicación desplegada
URL_APP = "https://tu-app-de-rifa.streamlit.app"

# Mensaje que se compartirá
mensaje_compartir = (
    f"¡Hola! Te invito a participar en esta rifa 🎟️. Ingresa al enlace para elegir tu número: {URL_APP}"
)

# Codificar texto para la URL de WhatsApp
mensaje_encoded = urllib.parse.quote(mensaje_compartir)
link_whatsapp = f"https://api.whatsapp.com/send?text={mensaje_encoded}"

# Botón interactivo
st.markdown(
    f"""
    <a href="{link_whatsapp}" target="_blank" style="text-decoration: none;">
        <button style="
            background-color: #25D366;
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 8px;
            cursor: pointer;
            width: 100%;">
            📲 Compartir en WhatsApp
        </button>
    </a>
    """,
    unsafe_allow_html=True,
)
