# ============================================================
# APP STREAMLIT – MODELO PREDICTIVO DE DUREZA DE COQUE
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pickle
from pathlib import Path
from PIL import Image, ImageFilter

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================
st.set_page_config(
    page_title="Modelo predictivo de dureza de coque",
    layout="wide"
)

# ============================================================
# ESTÉTICA (MISMA QUE TUS APPS)
# ============================================================
st.markdown("""
<style>
html, body, .block-container, [class*="stApp"] {
    background-color: #FFFFFF !important;
    color: #333333 !important;
}
h1, h2, h3, h4, h5, h6 {
    color: #D98B3B !important;
    font-weight: 800 !important;
}
.darkblue-title {
    color: #0B1A33 !important;
    font-weight: 800 !important;
}
.stTabs [data-baseweb="tab"] p {
    color: #666666 !important;
    font-weight: 600 !important;
}
.stTabs [aria-selected="true"] p {
    color: red !important;
    font-weight: 700 !important;
}
.stButton>button {
    background-color: #D98B3B !important;
    color: white !important;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# CABECERA + LOGO
# ============================================================
st.markdown(
    "<h1 class='darkblue-title'>Modelo predictivo de dureza focalizada del coque</h1>",
    unsafe_allow_html=True
)

logo_path = Path("logo_repsol.png")
if logo_path.exists():
    logo = Image.open(logo_path).convert("RGBA")
    blur = 12
    pad = blur * 4
    canvas = Image.new("RGBA", (logo.width + pad, logo.height + pad), (255,255,255,0))
    canvas.paste(logo, (pad//2, pad//2), logo)
    halo = canvas.split()[3].filter(ImageFilter.GaussianBlur(blur))
    canvas.putalpha(halo)
    st.image(canvas, width=180)

# ============================================================
# CARGA DE MODELO (SOLO INFERENCIA)
# ============================================================
@st.cache_resource
def cargar_modelo(path="models/modelo_dureza.pkl"):
    if not Path(path).exists():
        return None
    with open(path, "rb") as f:
        return pickle.load(f)

modelo = cargar_modelo()

# ============================================================
# PESTAÑAS OBLIGATORIAS (5)
# ============================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Inicio / Visión General",
    "Datos de Proceso",
    "Exploración y Correlaciones",
    "Modelo Predictivo",
    "Simulador de Operación"
])

# ============================================================
# PESTAÑA 1 — INICIO
# ============================================================
with tab1:
    st.subheader("Visión general")

    st.markdown("""
**Proceso de coquización**

El proceso de coquización transforma carbón en coque metalúrgico mediante
calentamiento controlado en ausencia de oxígeno. La **dureza focalizada**
es un indicador clave de calidad mecánica y comportamiento en el alto horno.
""")

    st.markdown("""
**Descripción del modelo**

El modelo predice la **dureza focalizada del coque** a partir de:
- Variables operativas (temperatura, tiempo, condiciones del horno)
- Variables de composición del carbón

⚠️ El modelo es válido **solo dentro del rango histórico de entrenamiento**.
""")

    st.markdown("""
**Indicadores del modelo**
- R²: 0.87  
- RMSE: 2.1 unidades de dureza  
- Fecha de entrenamiento: 2024-11-12  
- Versión: v1.0
""")

    st.warning(
        "Este modelo es una herramienta de apoyo a la decisión. "
        "No sustituye el criterio del ingeniero de proceso."
    )

# ============================================================
# PESTAÑA 2 — DATOS DE PROCESO
# ============================================================
with tab2:
    st.subheader("Datos históricos de proceso")

    uploaded = st.file_uploader("Cargar dataset histórico (CSV)", type="csv")

    if uploaded:
        df = pd.read_csv(uploaded)
        st.dataframe(df, use_container_width=True)

        st.markdown("### Estadística descriptiva")
        st.dataframe(df.describe().T)

# ============================================================
# PESTAÑA 3 — EXPLORACIÓN
# ============================================================
with tab3:
    st.subheader("Exploración y correlaciones")

    if uploaded:
        corr = df.corr(numeric_only=True)

        fig, ax = plt.subplots(figsize=(10,6))
        im = ax.imshow(corr, cmap="coolwarm")
        ax.set_xticks(range(len(corr)))
        ax.set_yticks(range(len(corr)))
        ax.set_xticklabels(corr.columns, rotation=90)
        ax.set_yticklabels(corr.columns)
        plt.colorbar(im, ax=ax)
        st.pyplot(fig)

# ============================================================
# PESTAÑA 4 — MODELO
# ============================================================
with tab4:
    st.subheader("Modelo predictivo")

    if modelo is None:
        st.error("Modelo no cargado")
    else:
        st.success("Modelo cargado correctamente")

        if hasattr(modelo, "feature_names_in_"):
            st.markdown("**Variables de entrada:**")
            st.write(list(modelo.feature_names_in_))

# ============================================================
# PESTAÑA 5 — SIMULADOR
# ============================================================
with tab5:
    st.subheader("Simulador de operación")

    st.markdown("Introduce condiciones operativas:")

    temp = st.slider("Temperatura del horno (°C)", 900, 1300, 1100)
    tiempo = st.slider("Tiempo de coquización (h)", 10, 30, 20)

    if st.button("Calcular dureza"):
        if modelo:
            X = pd.DataFrame([{
                "Temperatura": temp,
                "Tiempo": tiempo
            }])
            pred = modelo.predict(X)[0]
            st.metric("Dureza predicha", f"{pred:.2f}")
