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
    st.header(" Análisis visual y modelado del proceso")

    # ==============================
    # COMPROBACIÓN DE DATOS
    # ==============================
    if df_proceso is None or df_proceso.empty:
        st.warning("No hay datos de proceso cargados")
        st.stop()

    df = df_proceso.copy()

    # ==============================
    # NORMALIZACIÓN FUERTE
    # ==============================
    for col in df.columns:
        if any(k in col.lower() for k in ["date", "inicio", "fin"]):
            df[col] = pd.to_datetime(df[col], errors="coerce")

    for col in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", ".", regex=False)
                .str.replace(" ", "", regex=False)
                .str.replace("nan", "", regex=False)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    columnas_num = df.select_dtypes(include="number").columns.tolist()

    if len(columnas_num) < 2:
        st.error("No hay suficientes variables numéricas")
        st.stop()

    # ==============================
    # SELECTORES
    # ==============================
    st.markdown("## 🔧 Selección de variables")

    c1, c2, c3 = st.columns(3)

    with c1:
        var_x = st.selectbox("Variable X", columnas_num, index=0)

    with c2:
        var_y = st.selectbox("Variable Y", columnas_num, index=1)

    with c3:
        var_color = st.selectbox("Color por", ["Ninguna"] + columnas_num)

    # ==============================
    # FILTROS
    # ==============================
    st.markdown("## 🎚️ Filtros de datos")

    fx_min, fx_max = float(df[var_x].min()), float(df[var_x].max())
    fy_min, fy_max = float(df[var_y].min()), float(df[var_y].max())

    f1, f2 = st.columns(2)

    with f1:
        rango_x = st.slider(f"Rango {var_x}", fx_min, fx_max, (fx_min, fx_max))

    with f2:
        rango_y = st.slider(f"Rango {var_y}", fy_min, fy_max, (fy_min, fy_max))

    df_f = df[
        (df[var_x] >= rango_x[0]) & (df[var_x] <= rango_x[1]) &
        (df[var_y] >= rango_y[0]) & (df[var_y] <= rango_y[1])
    ]

    # ==============================
    # OPCIONES DE MODELADO
    # ==============================
    st.markdown("## Modelado")

    c4, c5 = st.columns(2)

    with c4:
        usar_lineal = st.checkbox("Regresión lineal", value=True)
        usar_polinomica = st.checkbox("Regresión polinómica")

    with c5:
        grado = st.slider("Grado polinómico", 2, 5, 2)

    # ==============================
    # PREPARAR DATOS
    # ==============================
    df_modelo = df_f[[var_x, var_y]].dropna()

    if len(df_modelo) < 5:
        st.warning("No hay suficientes datos tras los filtros")
        st.stop()

    X = df_modelo[[var_x]].values
    y = df_modelo[var_y].values

    # ==============================
    # VISUALIZACIÓN
    # ==============================
    st.markdown("## Relación y tendencia")

    fig, ax = plt.subplots(figsize=(9, 6))

    if var_color == "Ninguna":
        ax.scatter(X, y, alpha=0.7, edgecolors="k")
    else:
        sc = ax.scatter(X, y, c=df_modelo[var_color], cmap="viridis", alpha=0.8)
        plt.colorbar(sc, ax=ax, label=var_color)

    resultados = []

    # ==============================
    # REGRESIÓN LINEAL
    # ==============================
    if usar_lineal:
        from sklearn.linear_model import LinearRegression
        from sklearn.metrics import r2_score, mean_squared_error
        import numpy as np

        lin = LinearRegression()
        lin.fit(X, y)

        x_line = np.linspace(X.min(), X.max(), 200).reshape(-1, 1)
        y_line = lin.predict(x_line)

        ax.plot(x_line, y_line, color="red", lw=2, label="Lineal")

        y_pred = lin.predict(X)
        resultados.append({
            "Modelo": "Lineal",
            "R2": r2_score(y, y_pred),
            "MSE": mean_squared_error(y, y_pred),
            "RMSE": mean_squared_error(y, y_pred, squared=False),
            "Ecuación": f"{var_y} = {lin.coef_[0]:.4f}·{var_x} + {lin.intercept_:.4f}"
        })

    # ==============================
    # REGRESIÓN POLINÓMICA
    # ==============================
    if usar_polinomica:
        from sklearn.preprocessing import PolynomialFeatures

        poly = PolynomialFeatures(degree=grado)
        Xp = poly.fit_transform(X)

        lin_p = LinearRegression()
        lin_p.fit(Xp, y)

        Xp_line = poly.transform(x_line)
        y_poly = lin_p.predict(Xp_line)

        ax.plot(x_line, y_poly, lw=2, linestyle="--", label=f"Polinómica (grado {grado})")

        y_pred_p = lin_p.predict(Xp)
        resultados.append({
            "Modelo": f"Polinómica g{grado}",
            "R2": r2_score(y, y_pred_p),
            "MSE": mean_squared_error(y, y_pred_p),
            "RMSE": mean_squared_error(y, y_pred_p, squared=False),
            "Ecuación": "Polinómica"
        })

    ax.set_xlabel(var_x)
    ax.set_ylabel(var_y)
    ax.grid(True)
    ax.legend()

    st.pyplot(fig)

    # ==============================
    # RESULTADOS NUMÉRICOS
    # ==============================
    st.markdown("##  Métricas del modelo")

    if resultados:
        df_res = pd.DataFrame(resultados)
        st.dataframe(df_res.style.format({
            "R2": "{:.4f}",
            "MSE": "{:.4f}",
            "RMSE": "{:.4f}"
        }))
