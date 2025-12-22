# -*- coding: utf-8 -*-
"""
Created on Mon Dec 22 09:59:43 2025

@author: SE111882
"""

# app_dureza_coque.py
# --------------------------------------------------
# Streamlit – Análisis de dureza de coque
# Estructura base con 3 pestañas + estética Repsol
# --------------------------------------------------

import streamlit as st
import pandas as pd
import numpy as np
import zipfile
import io
from pathlib import Path
from PIL import Image, ImageFilter
import matplotlib.pyplot as plt
import re

# ==================================================
# CONFIGURACIÓN GENERAL
# ==================================================
st.set_page_config(
    page_title="Análisis dureza de coque",
    layout="wide"
)

# ==================================================
# ESTÉTICA (COPIADA DE TUS APPS)
# ==================================================
st.markdown("""
<style>

/* Fondo general */
html, body, .block-container, [class*="stApp"] {
    background-color: #FFFFFF !important;
    color: #333333 !important;
}

/* Títulos */
h1, h2, h3, h4, h5, h6 {
    color: #D98B3B !important;
    font-weight: 800 !important;
}

/* Título azul oscuro */
.darkblue-title {
    color: #0B1A33 !important;
    font-weight: 800 !important;
}

/* Widgets */
.stSelectbox label,
.stMultiSelect label,
.stNumberInput label,
.stSlider label,
.stTextInput label {
    color: #333333 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab"] p {
    color: #666666 !important;
    font-weight: 600 !important;
}

.stTabs [aria-selected="true"] p {
    color: red !important;
    font-weight: 700 !important;
}

/* Botones */
.stButton>button {
    background-color: #D98B3B !important;
    color: white !important;
    border-radius: 8px;
}
.stButton>button:hover {
    background-color: #b57830 !important;
}

</style>
""", unsafe_allow_html=True)

# ==================================================
# CABECERA + LOGO
# ==================================================
st.markdown("<h1 class='darkblue-title'>Análisis de dureza de coque</h1>", unsafe_allow_html=True)

logo_path = Path("logo_repsol.png")
if logo_path.exists():
    try:
        logo_original = Image.open(logo_path).convert("RGBA")
        blur_radius = 15
        padding = blur_radius * 4
        new_size = (logo_original.width + padding, logo_original.height + padding)
        final_logo = Image.new("RGBA", new_size, (255, 255, 255, 0))
        cx = (new_size[0] - logo_original.width) // 2
        cy = (new_size[1] - logo_original.height) // 2
        final_logo.paste(logo_original, (cx, cy), logo_original)
        mask = final_logo.split()[3]
        halo = Image.new("RGBA", final_logo.size, (255, 255, 255, 0))
        halo.putalpha(mask.filter(ImageFilter.GaussianBlur(blur_radius)))
        final_logo = Image.alpha_composite(halo, final_logo)
        st.image(final_logo, width=180)
    except Exception:
        st.warning("No se pudo cargar el logo.")
else:
    st.info("logo_repsol.png no encontrado.")

# ==================================================
# FUNCIONES DE LECTURA (DE interfazprograma.py)
# ==================================================
def leer_archivo(uploaded_file):
    hojas = {}

    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
        hojas["csv"] = df

    elif uploaded_file.name.endswith(".xlsx"):
        xls = pd.ExcelFile(uploaded_file)
        for sheet in xls.sheet_names:
            df = pd.read_excel(uploaded_file, sheet_name=sheet)
            hojas[sheet] = df

    elif uploaded_file.name.endswith(".zip"):
        with zipfile.ZipFile(uploaded_file) as z:
            for fname in z.namelist():
                if fname.lower().endswith(".csv"):
                    with z.open(fname) as f:
                        df = pd.read_csv(f)
                        hojas[fname.replace(".csv", "")] = df
    else:
        st.error("Formato no soportado")

    return hojas

# ==================================================
# SIDEBAR – ENTRADA DE DATOS
# ==================================================
st.sidebar.header("Carga de datos")

uploaded = st.sidebar.file_uploader(
    "Sube CSV o ZIP con CSVs",
    type=["csv", "xlsx", "zip"]
)

st.sidebar.markdown("---")
st.sidebar.info("""
Requisitos:
- Columna **Tiempo**
- Columna **Dureza** (dureza del coque)
- Variables de proceso numéricas
""")

# ==================================================
# PROCESADO DE DATOS
# ==================================================
df = None
if uploaded is not None:
    hojas = leer_archivo(uploaded)
    st.sidebar.success(f"Archivos cargados: {list(hojas.keys())}")

    # Heurística simple: unir todo por Tiempo
    dfs = []
    for name, dfi in hojas.items():
        dfi.columns = [str(c).strip() for c in dfi.columns]
        if "Tiempo" in dfi.columns:
            dfs.append(dfi)

    if len(dfs) >= 1:
        df = dfs[0]
        for dfi in dfs[1:]:
            df = df.merge(dfi, on="Tiempo", how="inner")

        # Convertir tiempo
        try:
            df["Tiempo"] = pd.to_datetime(df["Tiempo"])
        except Exception:
            pass

        # Convertir a numérico
        for c in df.columns:
            if c != "Tiempo":
                df[c] = pd.to_numeric(df[c], errors="coerce")

        st.success(f"Datos combinados: {df.shape[0]} filas, {df.shape[1]} columnas")
    else:
        st.error("No se encontró columna 'Tiempo'")

# ==================================================
# PESTAÑAS PRINCIPALES
# ==================================================
tab_comp, tab_modelo, tab_analisis = st.tabs(
    ["Comparación", "Modelo predictivo", "Análisis del modelo"]
)

# ==================================================
# PESTAÑA 1 – COMPARACIÓN
# ==================================================
with tab_comp:
    st.subheader("Comparación variables vs dureza")

    if df is None:
        st.info("Carga datos para comenzar")
    else:
        st.write("Aquí irán las gráficas:")
        st.write("- Variable de proceso vs dureza")
        st.write("- Variable vs tiempo")
        st.write("- Dureza vs tiempo de lavado")

        st.dataframe(df.head())

# ==================================================
# PESTAÑA 2 – MODELO
# ==================================================
with tab_modelo:
    st.subheader("Modelo predictivo de dureza")

    if df is None:
        st.info("Carga datos para entrenar el modelo")
    else:
        st.write("Aquí entrenaremos el modelo predictivo (RandomForest, etc.)")

# ==================================================
# PESTAÑA 3 – ANÁLISIS DEL MODELO
# ==================================================
with tab_analisis:
    st.subheader("Análisis e interpretación del modelo")

    st.write("Importancia de variables, SHAP, etc.")
