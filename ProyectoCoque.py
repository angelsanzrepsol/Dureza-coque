
import streamlit as st
import pandas as pd
import zipfile
from pathlib import Path
from PIL import Image, ImageFilter
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

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
# PESTAÑA 2 — GRAFICADO AVANZADO CON FILTRADO REAL
# ============================================================
with tab2:

    st.subheader("Graficado interactivo avanzado de variables de proceso")

    if df_proceso is None or df_proceso.empty:
        st.warning("Cargue primero un archivo de datos de proceso.")
    else:
        # --------------------------------------------------
        # ESTADOS
        # --------------------------------------------------
        if "df_activo_tab2" not in st.session_state:
            st.session_state.df_activo_tab2 = df_proceso.copy()

        if "df_eliminados_tab2" not in st.session_state:
            st.session_state.df_eliminados_tab2 = pd.DataFrame(columns=df_proceso.columns)

        df_activo = st.session_state.df_activo_tab2
        df_eliminados = st.session_state.df_eliminados_tab2

        # --------------------------------------------------
        # VARIABLES NUMÉRICAS
        # --------------------------------------------------
        cols_num = df_activo.select_dtypes(include="number").columns.tolist()

        if len(cols_num) < 2:
            st.error("Se necesitan al menos dos variables numéricas.")
        else:
            colx, coly, colr = st.columns([1, 2, 1])

            with colx:
                x_var = st.selectbox("Variable eje X", cols_num)

            with coly:
                y_vars = st.multiselect(
                    "Variables eje Y",
                    [c for c in cols_num if c != x_var],
                    default=[c for c in cols_num if c != x_var][:1]
                )

            with colr:
                if st.button("Restaurar todo"):
                    st.session_state.df_activo_tab2 = df_proceso.copy()
                    st.session_state.df_eliminados_tab2 = pd.DataFrame(columns=df_proceso.columns)
                    st.rerun()

            if not y_vars:
                st.warning("Seleccione al menos una variable en Y.")
            else:
                # --------------------------------------------------
                # FILTRADO REAL POR SLIDERS (ELIMINA FILAS)
                # --------------------------------------------------
                st.markdown("Filtros por rango (eliminan filas fuera del rango)")

                df_filtrado = df_activo.copy()

                for col in [x_var] + y_vars:
                    vmin = float(df_activo[col].min())
                    vmax = float(df_activo[col].max())

                    rmin, rmax = st.slider(
                        col,
                        min_value=vmin,
                        max_value=vmax,
                        value=(vmin, vmax),
                        key=f"slider_{col}"
                    )

                    # FILTRADO REAL
                    df_filtrado = df_filtrado[
                        (df_filtrado[col] >= rmin) &
                        (df_filtrado[col] <= rmax)
                    ]

                # --------------------------------------------------
                # GRÁFICO + REGRESIONES (SOLO DATOS FILTRADOS)
                # --------------------------------------------------
                fig = go.Figure()

                for y in y_vars:
                    fig.add_trace(
                        go.Scatter(
                            x=df_filtrado[x_var],
                            y=df_filtrado[y],
                            mode="markers",
                            name=y,
                            customdata=df_filtrado.index
                        )
                    )

                    df_reg = df_filtrado[[x_var, y]].dropna()

                    if len(df_reg) >= 2:
                        x = df_reg[x_var].values
                        yy = df_reg[y].values

                        m, b = np.polyfit(x, yy, 1)
                        x_line = np.linspace(x.min(), x.max(), 100)
                        y_line = m * x_line + b

                        ss_res = ((yy - (m * x + b)) ** 2).sum()
                        ss_tot = ((yy - yy.mean()) ** 2).sum()
                        r2 = 1 - ss_res / ss_tot if ss_tot != 0 else np.nan

                        fig.add_trace(
                            go.Scatter(
                                x=x_line,
                                y=y_line,
                                mode="lines",
                                name=f"{y} (R²={r2:.3f})"
                            )
                        )

                fig.update_layout(
                    height=550,
                    xaxis_title=x_var,
                    yaxis_title="Variables",
                    xaxis=dict(autorange=True),
                    yaxis=dict(autorange=True)
                )

                event = st.plotly_chart(
                    fig,
                    use_container_width=True,
                    on_select="rerun"
                )

                # --------------------------------------------------
                # EXCLUSIÓN DESDE GRÁFICO
                # --------------------------------------------------
                if event and event.selection and event.selection.points:
                    indices = list(set(p["customdata"] for p in event.selection.points))

                    if st.button("Excluir puntos seleccionados del gráfico"):
                        puntos = df_activo.loc[indices]

                        st.session_state.df_eliminados_tab2 = pd.concat(
                            [df_eliminados, puntos],
                            ignore_index=True
                        )

                        st.session_state.df_activo_tab2 = (
                            df_activo.drop(indices)
                            .reset_index(drop=True)
                        )
                        st.rerun()

        # --------------------------------------------------
        # EXCLUSIÓN MANUAL POR TABLA
        # --------------------------------------------------
        st.markdown("---")
        st.subheader("Excluir puntos manualmente")

        df_tabla = df_activo.copy()
        df_tabla["Excluir"] = False

        with st.form("form_exclusion_tab2"):
            df_editado = st.data_editor(df_tabla, num_rows="fixed", use_container_width=True)
            submit = st.form_submit_button("Excluir filas marcadas")

        if submit:
            filas = df_editado[df_editado["Excluir"]].index.tolist()

            if filas:
                puntos = df_activo.loc[filas]

                st.session_state.df_eliminados_tab2 = pd.concat(
                    [df_eliminados, puntos],
                    ignore_index=True
                )

                st.session_state.df_activo_tab2 = (
                    df_activo.drop(filas)
                    .reset_index(drop=True)
                )
                st.rerun()

        # --------------------------------------------------
        # TABLA DE EXCLUIDOS
        # --------------------------------------------------
        st.markdown("---")
        st.subheader("Puntos excluidos del análisis")

        if st.session_state.df_eliminados_tab2.empty:
            st.info("No hay puntos excluidos.")
        else:
            st.dataframe(st.session_state.df_eliminados_tab2, use_container_width=True)


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
