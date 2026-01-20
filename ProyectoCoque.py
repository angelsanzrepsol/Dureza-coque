
import streamlit as st
import pandas as pd
import zipfile
from pathlib import Path
from PIL import Image, ImageFilter
import matplotlib.pyplot as plt
import plotly.express as px

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
    "<h1 class='darkblue-title'>Análisis dureza del coque</h1>",
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
        # CSV
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

        # Excel
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
    "Visión General",
    "Graficado",
    "Correlaciones",
    "Modelo Predictivo",
    "Simulador de Operación"
])

# ============================================================
# PESTAÑA 1 — VACÍA
# ============================================================
with tab1:
    pass

# ============================================================
# PESTAÑA 2 — GRAFICADO INTERACTIVO CON HISTÓRICO DE ELIMINADOS
# ============================================================
with tab2:

    st.subheader("Graficado interactivo de variables de proceso")

    if df_proceso is None or df_proceso.empty:
        st.warning("Cargue primero un archivo de datos de proceso en la barra lateral.")
    else:
        # --------------------------------------------------
        # Inicialización de estados
        # --------------------------------------------------
        if "df_activo_tab2" not in st.session_state:
            st.session_state.df_activo_tab2 = df_proceso.copy()

        if "df_eliminados_tab2" not in st.session_state:
            st.session_state.df_eliminados_tab2 = pd.DataFrame(columns=df_proceso.columns)

        df_activo = st.session_state.df_activo_tab2
        df_eliminados = st.session_state.df_eliminados_tab2

        # --------------------------------------------------
        # Selección de columnas numéricas
        # --------------------------------------------------
        columnas_numericas = df_activo.select_dtypes(include="number").columns.tolist()

        if len(columnas_numericas) < 2:
            st.error("Se necesitan al menos dos columnas numéricas para graficar.")
        else:
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

            with col1:
                x_var = st.selectbox(
                    "Variable eje X",
                    columnas_numericas,
                    key="tab2_x"
                )

            with col2:
                y_var = st.selectbox(
                    "Variable eje Y",
                    columnas_numericas,
                    index=1 if len(columnas_numericas) > 1 else 0,
                    key="tab2_y"
                )

            with col3:
                color_var = st.selectbox(
                    "Color (opcional)",
                    ["Ninguno"] + df_activo.columns.tolist(),
                    key="tab2_color"
                )

            with col4:
                if st.button("Restaurar todos los puntos"):
                    st.session_state.df_activo_tab2 = df_proceso.copy()
                    st.session_state.df_eliminados_tab2 = pd.DataFrame(columns=df_proceso.columns)
                    st.rerun()

            # --------------------------------------------------
            # Gráfico interactivo
            # --------------------------------------------------
            fig = px.scatter(
                df_activo,
                x=x_var,
                y=y_var,
                color=None if color_var == "Ninguno" else color_var,
                hover_data=df_activo.columns,
                title=f"{y_var} vs {x_var}"
            )

            fig.update_traces(marker=dict(size=10))
            fig.update_layout(height=520)

            event = st.plotly_chart(
                fig,
                use_container_width=True,
                on_select="rerun"
            )

            # --------------------------------------------------
            # Eliminación de puntos seleccionados
            # --------------------------------------------------
            st.markdown("Puntos seleccionados en el gráfico")

            if event and event.selection and event.selection.points:
                indices = [p["point_index"] for p in event.selection.points]

                st.write(f"Número de puntos seleccionados: {len(indices)}")

                if st.button("Eliminar puntos seleccionados"):
                    puntos_eliminados = df_activo.iloc[indices]

                    st.session_state.df_eliminados_tab2 = pd.concat(
                        [df_eliminados, puntos_eliminados],
                        ignore_index=True
                    )

                    st.session_state.df_activo_tab2 = (
                        df_activo.drop(df_activo.index[indices])
                        .reset_index(drop=True)
                    )

                    st.rerun()

                st.dataframe(
                    df_activo.iloc[indices],
                    use_container_width=True
                )
            else:
                st.info("Seleccione uno o varios puntos en el gráfico para eliminarlos.")

        # --------------------------------------------------
        # Tabla de puntos eliminados (debajo del gráfico)
        # --------------------------------------------------
        st.markdown("---")
        st.subheader("Puntos eliminados del análisis")

        if st.session_state.df_eliminados_tab2.empty:
            st.info("No se han eliminado puntos.")
        else:
            st.write(
                f"Total de puntos eliminados: {len(st.session_state.df_eliminados_tab2)}"
            )
            st.dataframe(
                st.session_state.df_eliminados_tab2,
                use_container_width=True
            )

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
