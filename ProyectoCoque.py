
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
import json
from io import BytesIO

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
# ===============================
# ESTADOS PARA FILTROS GUARDADOS
# ===============================
if "filtros_guardados" not in st.session_state:
    st.session_state.filtros_guardados = {}

if "filtro_activo" not in st.session_state:
    st.session_state.filtro_activo = None

# ===============================
# ESTADO PARA DESCARGA TAB 2
# ===============================
if "datos_descarga_tab2" not in st.session_state:
    st.session_state.datos_descarga_tab2 = {}

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
                f"La cámara {camara} ya está cargada"
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
tab1, tab_filtros, tab2, tab3, tab4, tab5 = st.tabs([
    "Visión General",
    "Filtros guardados",
    "Graficado",
    "Correlaciones",
    "Modelo Predictivo",
    "Simulador de Operación"
])

# ============================================================
# PESTAÑA 1 — VACÍA
# ============================================================
with tab1:
    st.subheader("Visión General — creación de filtros")

    if not st.session_state.df_camaras_original:
        st.info("Cargue datos primero")
        st.stop()

    camara = st.selectbox(
        "Cámara",
        st.session_state.df_camaras_original.keys()
    )

    df = st.session_state.df_camaras_original[camara]
    cols = df.select_dtypes(include="number").columns.tolist()

    x_var = st.selectbox("Variable base (X)", cols)

    filtros_temp = {}

    st.markdown("### Ajuste de rangos por variable")

    for y in cols:
        if y == x_var:
            continue

        ymin, ymax = float(df[y].min()), float(df[y].max())
        rmin, rmax = st.slider(
            f"{y}",
            ymin, ymax,
            (ymin, ymax),
            key=f"vg_{camara}_{y}"
        )

        filtros_temp[y] = (rmin, rmax)

        df_plot = df[(df[y] >= rmin) & (df[y] <= rmax)]
        fig = px.scatter(df_plot, x=x_var, y=y)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    nombre_filtro = st.text_input("Nombre del filtro")

    if st.button("Guardar filtro"):
        if nombre_filtro:
            st.session_state.filtros_guardados[nombre_filtro] = {
                "camara": camara,
                "x_var": x_var,
                "rangos": filtros_temp
            }
            st.success(f"Filtro '{nombre_filtro}' guardado")
# ============================================================
# PESTAÑA 2 — Filtros
# ============================================================
with tab_filtros:
    st.subheader("Filtros guardados")
# --------------------------------------------------
# DESCARGAR FILTROS
# --------------------------------------------------
if st.session_state.filtros_guardados:
    filtros_json = json.dumps(
        st.session_state.filtros_guardados,
        indent=4
    )

    st.download_button(
        "📥 Descargar filtros",
        data=filtros_json,
        file_name="filtros_coque.json",
        mime="application/json"
    )
# --------------------------------------------------
# IMPORTAR FILTROS
# --------------------------------------------------
st.markdown("---")
st.markdown("### Importar filtros")

filtro_file = st.file_uploader(
    "Subir archivo de filtros (.json)",
    type=["json"]
)

if filtro_file is not None:
    try:
        filtros_importados = json.load(filtro_file)

        if isinstance(filtros_importados, dict):
            # Mezclar con los existentes
            for k, v in filtros_importados.items():
                if k not in st.session_state.filtros_guardados:
                    st.session_state.filtros_guardados[k] = v
            st.success("Filtros importados correctamente")
        else:
            st.error("Formato de filtros no válido")

    except Exception as e:
        st.error(f"Error leyendo el archivo: {e}")

    if not st.session_state.filtros_guardados:
        st.info("No hay filtros guardados")
    else:
        for nombre, f in st.session_state.filtros_guardados.items():
            with st.expander(nombre):
                st.write(f"Cámara: {f['camara']}")
                st.write(f"Variable X: {f['x_var']}")
                st.json(f["rangos"])

                col1, col2 = st.columns(2)

                if col1.button("Aplicar", key=f"ap_{nombre}"):
                    st.session_state.filtro_activo = nombre
                    st.success("Filtro aplicado")

                if col2.button("Eliminar", key=f"del_{nombre}"):
                    del st.session_state.filtros_guardados[nombre]
                    st.rerun()

# ============================================================
# PESTAÑA 3 — GRAFICADO
# ============================================================
with tab2:

    st.subheader("Graficado interactivo avanzado de variables de proceso")

    # --------------------------------------------------
    # COMPROBACIÓN DE DATOS
    # --------------------------------------------------
    if "df_camaras_activo" not in st.session_state:
        st.warning("Cargue primero datos de cámaras.")
        st.stop()

    df_camaras_activo = st.session_state.df_camaras_activo
    df_camaras_eliminados = st.session_state.df_camaras_eliminados
    df_camaras_original = st.session_state.df_camaras_original

    camaras_disponibles = sorted(df_camaras_activo.keys())

    # --------------------------------------------------
    # SELECCIÓN DE CÁMARAS A REPRESENTAR
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
    # SELECCIÓN DE CÁMARA FUENTE DE X
    # --------------------------------------------------
    camara_x = st.selectbox(
        "Cámara de referencia para el eje X",
        camaras_sel
    )

    df_x_ref = df_camaras_activo[camara_x]
    cols_num_x = df_x_ref.select_dtypes(include="number").columns.tolist()

    if len(cols_num_x) < 1:
        st.error("La cámara de referencia no tiene columnas numéricas.")
        st.stop()

    x_var = st.selectbox(
        "Variable eje X (común)",
        cols_num_x
    )
    # --------------------------------------------------
    # FILTRO PREFIJADO
    # --------------------------------------------------
    filtro_sel = st.selectbox(
        "Filtro prefijado",
        ["(ninguno)"] + list(st.session_state.filtros_guardados.keys())
    )
    
    if filtro_sel != "(ninguno)":
        st.session_state.filtro_activo = filtro_sel
    else:
        st.session_state.filtro_activo = None


    # --------------------------------------------------
    # SELECCIÓN DE Y POR CÁMARA
    # --------------------------------------------------
    st.markdown("### Selección de variables Y por cámara")

    y_vars_por_camara = {}

    for camara in camaras_sel:
        df_cam = df_camaras_activo[camara]
        cols_cam = df_cam.select_dtypes(include="number").columns.tolist()

        y_sel = st.multiselect(
            f"Variables Y para cámara {camara}",
            [c for c in cols_cam if c != x_var],
            default=[c for c in cols_cam if c != x_var][:1],
            key=f"y_sel_{camara}"
        )

        if y_sel:
            y_vars_por_camara[camara] = y_sel

    if not y_vars_por_camara:
        st.warning("Seleccione al menos una variable Y.")
        st.stop()

    # --------------------------------------------------
    # BOTÓN RESTAURAR
    # --------------------------------------------------
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

    # --------------------------------------------------
    # FILTRO POR X (USANDO CÁMARA DE REFERENCIA)
    # --------------------------------------------------
    xmin = float(df_x_ref[x_var].min())
    xmax = float(df_x_ref[x_var].max())

    rx_min, rx_max = st.slider(
        f"Rango para {x_var} (cámara {camara_x})",
        xmin, xmax,
        (xmin, xmax)
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
    # --------------------------------------------------
    # APLICAR FILTRO GUARDADO
    # --------------------------------------------------
    if st.session_state.filtro_activo:
        f = st.session_state.filtros_guardados[st.session_state.filtro_activo]
    
        if f["camara"] == camara_x and f["x_var"] == x_var:
            for cam in camaras_sel:
                df = df_camaras_activo[cam]
                for var, (vmin, vmax) in f["rangos"].items():
                    if var in df.columns:
                        df = df[(df[var] >= vmin) & (df[var] <= vmax)]
                df_camaras_activo[cam] = df

    fig = go.Figure()
    st.session_state.datos_descarga_tab2 = {}

    for camara, y_vars in y_vars_por_camara.items():
        df_cam = df_camaras_activo[camara]
        st.session_state.datos_descarga_tab2[camara] = []

        # Filtrado por X usando valores de ESA cámara
        if x_var in df_cam.columns:
            df_cam = df_cam[
                (df_cam[x_var] >= rx_min) &
                (df_cam[x_var] <= rx_max)
            ]

        for y in y_vars:
            ymin, ymax = float(df_cam[y].min()), float(df_cam[y].max())

            ry_min, ry_max = st.slider(
                f"{camara} – rango {y}",
                ymin, ymax, (ymin, ymax),
                key=f"slider_{camara}_{y}"
            )

            df_y = df_cam[
                (df_cam[y] >= ry_min) &
                (df_cam[y] <= ry_max)
            ]
            # Guardar datos representados para descarga
            df_export = df_y.copy()
            df_export["Variable_X"] = x_var
            df_export["Variable_Y"] = y
            
            st.session_state.datos_descarga_tab2[camara].append(df_export)

            fig.add_trace(
                go.Scatter(
                    x=df_y[x_var] if x_var in df_y.columns else df_y.index,
                    y=df_y[y],
                    mode="markers",
                    name=f"{camara} – {y}",
                    customdata=[(camara, i) for i in df_y.index]
                )
            )

            # Regresión lineal independiente
            if x_var in df_y.columns and len(df_y) >= 2:
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
        xaxis_title=f"{x_var} (ref: {camara_x})",
        yaxis_title="Variables",
        legend_title="Cámara / Variable"
    )

    # --------------------------------------------------
    # CONGELAR EJES
    # --------------------------------------------------
    if st.session_state.axis_frozen_tab2:
        fig.update_layout(
            xaxis=dict(range=st.session_state.axis_limits_tab2["x"], autorange=False),
            yaxis=dict(range=st.session_state.axis_limits_tab2["y"], autorange=False)
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
        if st.button("Excluir puntos seleccionados del gráfico"):
            for p in event.selection.points:
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
    # EXCLUSIÓN MANUAL POR TABLA
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

                df_camaras_activo[camara] = df_camaras_activo[camara].drop(filas)
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
    from io import BytesIO
    
    st.markdown("---")
    st.subheader("Descargar datos representados")
    
    if any(st.session_state.datos_descarga_tab2.values()):
        output = BytesIO()
    
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            for cam, lista in st.session_state.datos_descarga_tab2.items():
                if lista:
                    pd.concat(lista, ignore_index=True).to_excel(
                        writer,
                        sheet_name=cam[:31],
                        index=False
                    )
    
        output.seek(0)
        nombre = st.session_state.filtro_activo or "sin_filtro"
    
        st.download_button(
            "📥 Descargar Excel (una hoja por cámara)",
            data=output,
            file_name=f"datos_grafico_{nombre}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("No hay datos para descargar")

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
