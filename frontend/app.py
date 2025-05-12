import streamlit as st
import requests
import base64
API_URL = "http://localhost:8000/ask"
# --- FONDO PERSONALIZADO ---
def set_background(image_file):
    with open(image_file, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    st.markdown(
        f"""
<style>
        /* Fondo general */
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-position: center;
        }}
 
        /* Contenedor principal con desenfoque */
        .block-container {{
            margin-top: 12vh;
            backdrop-filter: blur(6px);
            background-color: rgba(255, 255, 255, 0.75);
            padding: 2rem;
            border-radius: 1rem;
        }}
 
        .block-container h1,
        .block-container p,
        .block-container label,
        .block-container .stMarkdown {{
            color: #222222 !important;
        }}
 
        /* Campo de texto */
        .stTextInput > div > input {{
            color: #ffffff !important;
            background-color: #333 !important;
        }}
        .stTextInput > div > input::placeholder {{
            color: #dddddd !important;
        }}
 
        /* Botón personalizado */
        button {{
            color: #ffffff !important;
            background-color: #28a745 !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.5em 1.2em !important;
            font-weight: bold !important;
            font-size: 1rem !important;
            transition: background-color 0.3s ease;
        }}
 
        button:hover {{
            background-color: #218838 !important;
            cursor: pointer;
        }}
 
        /* Texto blanco para sidebar */
        section[data-testid="stSidebar"] .css-1d391kg,
        section[data-testid="stSidebar"] .css-1cypcdb,
        .sidebar .element-container,
        .sidebar-content,
        .stSidebar p,
        .stSidebar h1, .stSidebar h2, .stSidebar h3 {{
            color: #fdfdfd !important;
        }}
</style>
        """,
        unsafe_allow_html=True
    )
# --- CONFIG ---
st.set_page_config(page_title="Asistente de Cocina Saludable", layout="centered")
set_background("frontend/background.jpg")
# --- SIDEBAR ---
st.sidebar.title("🍲 Tu Asistente de Cocina")
st.sidebar.markdown("""
Este asistente surge a partir del recetario **"100 recetas saludables para disfrutar en familia"**, elaborado por pediatras y nutricionistas comprometidos con una alimentación variada, accesible y divertida.
 
Vas a encontrar ideas aptas para toda la familia, incluyendo recetas sin gluten, vegetarianas, sin azúcar añadido y pensadas para cocinar con niños.
 
🍎 ¡Consultá, aprendé y cociná saludable!
""")
st.sidebar.markdown("---")
st.sidebar.info("Este es un proyecto demo. Si el backend no está activo, se muestra una respuesta simulada.")
# --- TÍTULO PRINCIPAL ---
st.title("Asistente de Cocina Saludable")
st.markdown("Preguntale al recetario por preparaciones, ingredientes o condiciones especiales de las recetas.")
# --- FORMULARIO ---
with st.form("pregunta_form"):
    pregunta = st.text_input("¿Qué querés saber?", placeholder="Ejemplo: ¿Qué recetas son aptas para celíacos y tienen lentejas?")
    enviar = st.form_submit_button("Consultar")
# --- CONSULTA AL BACKEND O SIMULACIÓN ---
if enviar and pregunta.strip():
    with st.spinner("Consultando..."):
        try:
            response = requests.post(API_URL, json={"question": pregunta}, timeout=30)
            if response.status_code == 200:
                respuesta = response.json().get("answer")
                st.success("Respuesta del recetario:")
                st.markdown(respuesta)
            else:
                st.warning("No se pudo contactar con el backend. Usando respuesta simulada.")
                st.info("Esto es una respuesta simulada: Podés usar lentejas en una ensalada sin TACC.")
        except Exception as e:
            st.warning("Backend no disponible. Usando respuesta simulada.")
            st.info("Esto es una respuesta simulada: Podés usar lentejas en una ensalada sin TACC.")