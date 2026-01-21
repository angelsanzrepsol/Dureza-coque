
import streamlit as st
import pandas as pd
import zipfile
from pathlib import Path
from PIL import Image, ImageFilter
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re

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

def leer_datos_csv(uploaded_file):
    try:
        try:
            df = pd.read_csv(uploaded_file, sep=",")
            if df.shape[1] == 1:
                raise ValueError
        except Exception:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, sep=";")
        return df
    except Exception:
        return None


def extraer_codigo_camara(nombre_archivo):
    """
    Extrae códigos tipo C0004A, C0005B, etc. del nombre del archivo.
    """
    match = re.search(r"C\d{4}[A-Z]", nombre_archivo.upper())
    return match.group(0) if match else None

# ============================================================
# SIDEBAR — CARGA DE DATOS DE PROCESO (VARIOS EXCEL = VARIAS CÁMARAS)
# ============================================================
st.sidebar.header("Datos de proceso")

uploaded_files = st.sidebar.file_uploader(
    "Subir archivos Excel de proceso",
    type=["xlsx", "xls"],
    accept_multiple_files=True,
    help="Cada archivo debe contener un código C000xA/B en el nombre"
)

# Inicializar estados UNA SOLA VEZ
if "df_camaras_original" not in st.session_state:
    st.session_state.df_camaras_original = {}

if "df_camaras_activo" not in st.session_state:
    st.session_state.df_camaras_activo = {}

if "df_camaras_eliminados" not in st.session_state:
    st.session_state.df_camaras_eliminados = {}

if uploaded_files:
    for uploaded_file in uploaded_files:
        nombre = uploaded_file.name

        camara = extraer_codigo_camara(nombre)

        if camara is None:
            st.sidebar.warning(
                f"No se detectó cámara en {nombre} (se ignora)"
            )
            continue

        # Evitar cargar dos veces la misma cámara
        if camara in st.session_state.df_camaras_original:
            st.sidebar.info(
                f"La cámara {camara} ya está cargada (se omite)"
            )
            continue

        try:
            df = pd.read_excel(uploaded_file)

            if df is None or df.empty:
                st.sidebar.warning(
                    f"{nombre} está vacío (se ignora)"
                )
                continue

            # Guardar estados
            st.session_state.df_camaras_original[camara] = df.copy()
            st.session_state.df_camaras_activo[camara] = df.copy()
            st.session_state.df_camaras_eliminados[camara] = pd.DataFrame(
                columns=df.columns
            )

            st.sidebar.success(
                f"Cargado {nombre}\nCámara detectada: {camara}"
            )

        except Exception as e:
            st.sidebar.error(
                f"Error leyendo {nombre}: {e}"
            )

if not st.session_state.df_camaras_original:
    st.sidebar.info("No hay cámaras cargadas todavía")
else:
    st.sidebar.markdown("### Cámaras cargadas")
    for cam in st.session_state.df_camaras_original:
        st.sidebar.write(f"- {cam}")


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
# PESTAÑA 2 — GRAFICADO AVANZADO MULTICÁMARA (COMPLETO)
# ============================================================
with tab2:

    st.subheader("Graficado interactivo avanzado de variables de proceso")

    # --------------------------------------------------
    # COMPROBACIÓN DE DATOS
    # --------------------------------------------------
    if "df_camaras_activo" not in st.session_state:
        st.warning("Cargue primero un Excel con cámaras.")
        st.stop()

    df_camaras_activo = st.session_state.df_camaras_activo
    df_camaras_eliminados = st.session_state.df_camaras_eliminados
    df_camaras_original = st.session_state.df_camaras_original

    camaras_disponibles = sorted(df_camaras_activo.keys())

    # --------------------------------------------------
    # SELECCIÓN DE CÁMARAS
    # --------------------------------------------------
    camaras_sel = st.multiselect(
        "Cámaras a representar",
        camaras_disponibles,
        default=camaras_disponibles[:1]
    )

    if not camaras_sel:
        st.warning("Seleccione al menos una cámara.")
        st.stop()

    # --------------------------------------------------
    # VARIABLES NUMÉRICAS (referencia primera cámara)
    # --------------------------------------------------
    df_ref = df_camaras_activo[camaras_sel[0]]
    cols_num = df_ref.select_dtypes(include="number").columns.tolist()

    if len(cols_num) < 2:
        st.error("Se necesitan al menos dos columnas numéricas.")
        st.stop()

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
            st.session_state.df_camaras_activo = {
                k: v.copy() for k, v in df_camaras_original.items()
            }
            st.session_state.df_camaras_eliminados = {
                k: pd.DataFrame(columns=v.columns)
                for k, v in df_camaras_original.items()
            }
            st.session_state.axis_frozen_tab2 = False
            st.session_state.axis_limits_tab2 = {}
            st.rerun()

    if not y_vars:
        st.warning("Seleccione al menos una variable Y.")
        st.stop()

    # --------------------------------------------------
    # FILTRO POR X (COMÚN)
    # --------------------------------------------------
    xmin = min(df_camaras_activo[c][x_var].min() for c in camaras_sel)
    xmax = max(df_camaras_activo[c][x_var].max() for c in camaras_sel)

    rx_min, rx_max = st.slider(
        f"Rango para {x_var}",
        float(xmin), float(xmax),
        (float(xmin), float(xmax))
    )

    # --------------------------------------------------
    # ESTADO DE EJES
    # --------------------------------------------------
    if "axis_frozen_tab2" not in st.session_state:
        st.session_state.axis_frozen_tab2 = False

    if "axis_limits_tab2" not in st.session_state:
        st.session_state.axis_limits_tab2 = {}

    # --------------------------------------------------
    # GRÁFICO
    # --------------------------------------------------
    fig = go.Figure()

    puntos_seleccionables = {}

    for camara in camaras_sel:
        df_cam = df_camaras_activo[camara]
        df_cam = df_cam[
            (df_cam[x_var] >= rx_min) &
            (df_cam[x_var] <= rx_max)
        ]

        for y in y_vars:
            ymin, ymax = float(df_cam[y].min()), float(df_cam[y].max())

            ry_min, ry_max = st.slider(
                f"{camara} – rango {y}",
                ymin, ymax, (ymin, ymax),
                key=f"{camara}_{y}"
            )

            df_y = df_cam[
                (df_cam[y] >= ry_min) &
                (df_cam[y] <= ry_max)
            ]

            fig.add_trace(
                go.Scatter(
                    x=df_y[x_var],
                    y=df_y[y],
                    mode="markers",
                    name=f"{camara} – {y}",
                    customdata=[(camara, i) for i in df_y.index]
                )
            )

            # Regresión independiente
            if len(df_y) >= 2:
                x = df_y[x_var].values
                yy = df_y[y].values

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
                        name=f"{camara} – {y} (R²={r2:.3f})"
                    )
                )

    fig.update_layout(
        height=600,
        xaxis_title=x_var,
        yaxis_title="Variables",
        legend_title="Cámara / Variable"
    )

    # --------------------------------------------------
    # CONGELAR EJES TRAS PRIMER AUTOAJUSTE
    # --------------------------------------------------
    if st.session_state.axis_frozen_tab2:
        fig.update_layout(
            xaxis=dict(
                range=st.session_state.axis_limits_tab2["x"],
                autorange=False
            ),
            yaxis=dict(
                range=st.session_state.axis_limits_tab2["y"],
                autorange=False
            )
        )

    event = st.plotly_chart(fig, use_container_width=True, on_select="rerun")

    if not st.session_state.axis_frozen_tab2:
        st.session_state.axis_limits_tab2 = {
            "x": fig.layout.xaxis.range,
            "y": fig.layout.yaxis.range
        }
        st.session_state.axis_frozen_tab2 = True

    # --------------------------------------------------
    # EXCLUSIÓN DESDE GRÁFICO
    # --------------------------------------------------
    if event and event.selection and event.selection.points:
        seleccion = event.selection.points

        if st.button("Excluir puntos seleccionados del gráfico"):
            for p in seleccion:
                camara, idx = p["customdata"]
                df_cam = df_camaras_activo[camara]

                if idx in df_cam.index:
                    fila = df_cam.loc[[idx]]

                    df_camaras_eliminados[camara] = pd.concat(
                        [df_camaras_eliminados[camara], fila],
                        ignore_index=True
                    )

                    df_camaras_activo[camara] = df_cam.drop(idx)

            st.rerun()

    # --------------------------------------------------
    # EXCLUSIÓN MANUAL POR TABLA (POR CÁMARA)
    # --------------------------------------------------
    st.markdown("---")
    st.subheader("Excluir puntos manualmente por cámara")

    for camara in camaras_sel:
        st.markdown(f"**Cámara {camara}**")

        df_tabla = df_camaras_activo[camara].copy()
        df_tabla["Excluir"] = False

        with st.form(f"form_exclusion_{camara}"):
            df_editado = st.data_editor(
                df_tabla,
                num_rows="fixed",
                use_container_width=True
            )
            submit = st.form_submit_button("Excluir filas marcadas")

        if submit:
            filas = df_editado[df_editado["Excluir"]].index.tolist()

            if filas:
                puntos = df_camaras_activo[camara].loc[filas]

                df_camaras_eliminados[camara] = pd.concat(
                    [df_camaras_eliminados[camara], puntos],
                    ignore_index=True
                )

                df_camaras_activo[camara] = (
                    df_camaras_activo[camara].drop(filas)
                )
                st.rerun()

    # --------------------------------------------------
    # TABLA DE EXCLUIDOS
    # --------------------------------------------------
    st.markdown("---")
    st.subheader("Puntos excluidos del análisis")

    df_excluidos_total = pd.concat(
        [
            df.assign(Camara=cam)
            for cam, df in df_camaras_eliminados.items()
            if not df.empty
        ],
        ignore_index=True
    ) if any(not df.empty for df in df_camaras_eliminados.values()) else pd.DataFrame()

    if df_excluidos_total.empty:
        st.info("No hay puntos excluidos.")
    else:
        st.dataframe(df_excluidos_total, use_container_width=True)

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
