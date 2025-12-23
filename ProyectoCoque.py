# ============================================================
# APP STREAMLIT – MODELO PREDICTIVO DE DUREZA DE COQUE
# ESTRUCTURA BASE CON SIDEBAR DE DATOS Y PESTAÑAS VACÍAS
# ============================================================

import streamlit as st
import pandas as pd
import zipfile
from pathlib import Path
from PIL import Image, ImageFilter
import matplotlib.pyplot as plt

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================
st.set_page_config(
    page_title="Análisis dureza de coque",
    layout="wide"
)

# ============================================================
# ESTÉTICA (INDUSTRIAL – COPIADA DE TUS APPS)
# ============================================================
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
    try:
        logo = Image.open(logo_path).convert("RGBA")
        blur = 12
        pad = blur * 4

        canvas = Image.new(
            "RGBA",
            (logo.width + pad, logo.height + pad),
            (255, 255, 255, 0)
        )

        canvas.paste(logo, (pad // 2, pad // 2), logo)

        mask = canvas.split()[3]
        halo = mask.filter(ImageFilter.GaussianBlur(blur))
        canvas.putalpha(halo)

        st.image(canvas, width=180)
    except Exception:
        st.warning("No se pudo cargar el logo.")
else:
    st.info("Archivo logo_repsol.png no encontrado.")

# ============================================================
# FUNCIÓN DE LECTURA DE DATOS DE PROCESO
# ============================================================
def leer_datos_proceso(uploaded_file):
    """
    Lee datos de proceso desde:
    - CSV (coma o punto y coma)
    - Excel (.xlsx, .xls)

    Devuelve un DataFrame o None si hay error.
    """
    if uploaded_file is None:
        return None

    nombre = uploaded_file.name.lower()

    try:
        # --------------------------------------------------
        # CSV
        # --------------------------------------------------
        if nombre.endswith(".csv"):
            try:
                # Intento 1: separado por coma
                df = pd.read_csv(uploaded_file, sep=",")
                if df.shape[1] == 1:
                    raise ValueError("Solo una columna detectada")
            except Exception:
                # Intento 2: separado por punto y coma
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, sep=";")

            return df

        # --------------------------------------------------
        # Excel
        # --------------------------------------------------
        if nombre.endswith((".xlsx", ".xls")):
            return pd.read_excel(uploaded_file)

        st.sidebar.error("Formato de archivo no soportado")
        return None

    except Exception as e:
        st.sidebar.error(f"Error leyendo archivo: {e}")
        return None

# ============================================================
# SIDEBAR — CARGA DE DATOS DE PROCESO
# ============================================================
st.sidebar.header("Datos de proceso")

uploaded_proceso = st.sidebar.file_uploader(
    "Subir datos de proceso",
    type=["csv", "xlsx", "xls", "zip"],
    help="Archivo con variables de proceso (incluye columna temporal)"
)

df_proceso = None

if uploaded_proceso is not None:
    df_proceso = leer_datos_proceso(uploaded_proceso)

    if df_proceso is not None and not df_proceso.empty:
        st.sidebar.success(
            f"Datos cargados: {df_proceso.shape[0]} filas, {df_proceso.shape[1]} columnas"
        )
    else:
        st.sidebar.error("No se pudieron cargar los datos")
else:
    st.sidebar.info("No hay datos de proceso cargados")

# ============================================================
# PESTAÑAS OBLIGATORIAS (VACÍAS)
# ============================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Inicio / Visión General",
    "Datos de Proceso",
    "Exploración y Correlaciones",
    "Modelo Predictivo",
    "Simulador de Operación"
])

# ============================================================
# PESTAÑA 1 — VACÍA
# ============================================================
with tab1:
    pass

# ============================================================
# PESTAÑA 2 — VACÍA
# ============================================================
with tab2:
    st.subheader("Datos de proceso – Visualización")

    if df_proceso is None:
        st.info("Carga datos de proceso en la barra lateral para comenzar.")
    else:
        df = df_proceso.copy()

        # --------------------------------------------------
        # Limpieza básica
        # --------------------------------------------------
        for c in df.columns:
            if c != "Tiempo":
                df[c] = pd.to_numeric(df[c], errors="coerce")

        # Detectar columna Tiempo
        tiene_tiempo = False
        if "Tiempo" in df.columns:
            try:
                df["Tiempo"] = pd.to_datetime(df["Tiempo"], errors="coerce")
                tiene_tiempo = True
            except Exception:
                tiene_tiempo = False

        # --------------------------------------------------
        # Columnas numéricas
        # --------------------------------------------------
        cols_numericas = [c for c in df.columns if c != "Tiempo"]

        if len(cols_numericas) == 0:
            st.warning("No hay variables numéricas para visualizar.")
        else:
            # Inicialización segura
            y_var = cols_numericas[0]
            x_var = "Tiempo" if tiene_tiempo else cols_numericas[0]

            # --------------------------------------------------
            # Selectores
            # --------------------------------------------------
            col1, col2 = st.columns(2)

            with col1:
                y_var = st.selectbox(
                    "Variable a analizar (Y)",
                    options=cols_numericas,
                    index=0
                )

            with col2:
                x_mode = st.radio(
                    "Eje X",
                    options=["Tiempo", "Otra variable"],
                    index=0 if tiene_tiempo else 1
                )

                if x_mode == "Otra variable":
                    opciones_x = [c for c in cols_numericas if c != y_var]
                    if len(opciones_x) > 0:
                        x_var = st.selectbox(
                            "Variable X",
                            options=opciones_x
                        )
                    else:
                        x_var = None
                else:
                    x_var = "Tiempo" if tiene_tiempo else None

            # --------------------------------------------------
            # Filtros
            # --------------------------------------------------
            st.markdown("### Filtros")

            colf1, colf2 = st.columns(2)

            with colf1:
                max_puntos = st.slider(
                    "Máximo número de puntos a mostrar",
                    min_value=100,
                    max_value=len(df),
                    value=min(len(df), 2000),
                    step=100
                )

            with colf2:
                quitar_nulos = st.checkbox("Eliminar valores nulos", value=True)

            # --------------------------------------------------
            # Preparar datos
            # --------------------------------------------------
            plot_df = df.copy()

            if quitar_nulos:
                subset = [y_var]
                if x_var not in (None, "Tiempo"):
                    subset.append(x_var)
                plot_df = plot_df.dropna(subset=subset)

            plot_df = plot_df.iloc[:max_puntos]

            # --------------------------------------------------
            # Gráfica
            # --------------------------------------------------
            st.markdown("### Visualización")

            if plot_df.empty or x_var is None:
                st.warning("No hay datos suficientes para graficar.")
            else:
                fig, ax = plt.subplots(figsize=(10, 6))

                if x_var == "Tiempo" and tiene_tiempo:
                    ax.scatter(
                        plot_df["Tiempo"],
                        plot_df[y_var],
                        s=15,
                        alpha=0.7
                    )
                    ax.set_xlabel("Tiempo")
                else:
                    ax.scatter(
                        plot_df[x_var],
                        plot_df[y_var],
                        s=15,
                        alpha=0.7
                    )
                    ax.set_xlabel(x_var)

                ax.set_ylabel(y_var)
                ax.set_title(f"{y_var} vs {x_var}")
                ax.grid(True)

                st.pyplot(fig)

            # --------------------------------------------------
            # Vista previa
            # --------------------------------------------------
            with st.expander("Ver datos utilizados en la gráfica"):
                st.dataframe(plot_df.head(500))


# ============================================================
# PESTAÑA 3 — VACÍA
# ============================================================
with tab3:
    pass

# ============================================================
# PESTAÑA 4 — VACÍA
# ============================================================
with tab4:
    pass

# ============================================================
# PESTAÑA 5 — VACÍA
# ============================================================
with tab5:
    pass
