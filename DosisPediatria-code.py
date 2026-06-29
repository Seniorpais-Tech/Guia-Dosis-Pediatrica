import os
import sys

# Bloque de seguridad para librerías
try:
    import pandas as pd
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas"])
    import pandas as pd

import streamlit as st

# Configuración de la página del Dashboard
st.set_page_config(
    page_title="Dashboard de Dosificación Pediátrica y Neonatal",
    page_icon="🩺",
    layout="wide"
)

# Cargar los datos de manera ultra-flexible y automática
@st.cache_data
def cargar_datos_robusto():
    # 1. Buscar de forma automática cualquier archivo .csv en el repositorio
    archivo_csv = None
    for f in os.listdir("."):
        if f.lower().endswith(".csv"):
            archivo_csv = f
            break
            
    if not archivo_csv:
        raise FileNotFoundError("No se encontró ningún archivo .csv en el repositorio.")
        
    # 2. Intentar leer el CSV probando dinámicamente los separadores más comunes (; o ,)
    try:
        df = pd.read_csv(archivo_csv, sep=";", encoding="utf-8")
        if df.shape[1] <= 1: # Si leyó mal las columnas, cambia el separador
            df = pd.read_csv(archivo_csv, sep=",", encoding="utf-8")
    except Exception:
        # Respaldo por si hay problemas de codificación de Windows (Ansi/Excel)
        df = pd.read_csv(archivo_csv, sep=";", encoding="latin1")
        if df.shape[1] <= 1:
            df = pd.read_csv(archivo_csv, sep=",", encoding="latin1")
            
    # Limpiar espacios en blanco de los títulos de las columnas por seguridad
    df.columns = df.columns.str.strip()
    return df

try:
    df = cargar_datos_robusto()
except Exception as e:
    st.error(f"Error crítico al procesar la base de datos: {e}")
    st.stop()

# Título Principal
st.title("🩺 Dashboard Interactivo: Guía de Medicamentos Pediátricos y Neonatales")
st.markdown("Consulte dosis, ajustes biológicos, vías de administración y alertas de seguridad en tiempo real.")
st.write("---")

# ==========================================
# BARRA LATERAL: FILTROS DINÁMICOS
# ==========================================
st.sidebar.header("🔍 Filtros de Búsqueda")

if "Grupo" in df.columns and "Vía" in df.columns:
    grupos_disponibles = ["Todos"] + sorted(df["Grupo"].dropna().unique().tolist())
    grupo_seleccionado = st.sidebar.selectbox("Selecciona un Grupo Terapéutico:", grupos_disponibles)

    vias_disponibles = ["Todas"] + sorted(df["Vía"].dropna().unique().tolist())
    via_seleccionada = st.sidebar.selectbox("Selecciona la Vía de Administración:", vias_disponibles)

    df_filtrado = df.copy()
    if grupo_seleccionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Grupo"] == grupo_seleccionado]
    if via_seleccionada != "Todas":
        df_filtrado = df_filtrado[df_filtrado["Vía"] == via_seleccionada]
else:
    st.sidebar.warning("Columnas estructurales no encontradas.")
    df_filtrado = df.copy()

# ==========================================
# SECCIÓN 1: CONSULTAS CONCRETAS (ASISTENTE)
# ==========================================
st.header("⚡ Consultas Concretas e Instantáneas")
st.markdown("Selecciona o escribe un medicamento para ver su **Ficha Clínica Completa** de inmediato:")

if "Medicamento" in df.columns:
    medicamentos_lista = sorted(df["Medicamento"].dropna().unique().tolist())
    medicamento_consulta = st.selectbox("Buscar medicamento específico:", ["Selecciona uno..."] + medicamentos_lista)

    if medicamento_consulta != "Selecciona uno...":
        ficha = df[df["Medicamento"] == medicamento_consulta].iloc[0]
        
        st.subheader(f"💊 Ficha Técnica: {ficha['Medicamento']} ({ficha.get('Grupo', 'N/A')})")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Indicación Principal:**\n\n{ficha.get('Indicación principal', 'No especificado')}")
        with col2:
            st.success(f"**Dosis Pediátrica Usual:**\n\n{ficha.get('Dosis pediátrica usual', 'No especificado')}")
        with col3:
            st.warning(f"**Dosis Neonatal:**\n\n{ficha.get('Dosis neonatal', 'No especificado')}")
            
        st.write("")
        
        col4, col5 = st.columns(2)
        with col4:
            st.error(f"**Límite / Dosis Máxima:**\n\n{ficha.get('Dosis máxima / límite', 'No especificado')}")
            st.markdown(f"**Vía:** `{ficha.get('Vía', 'N/A')}`")
        with col5:
            st.markdown(f"⚠️ **Recomendaciones Clave:**\n{ficha.get('Recomendaciones', 'Ninguna')}")
            
        st.write("---")
        
        with st.expander("⚕️ Ajustes Renales / Hepáticos y Monitorización"):
            c1, c2 = st.columns(2)
            c1.markdown(f"**Ajuste Orgánico:** {ficha.get('Ajuste renal/hepático', 'No requiere')}")
            c2.markdown(f"**Parámetros a Monitorizar:** {ficha.get('Monitorización', 'Clínica usual')}")
            st.caption(f"**Fuente de Referencia Oficial:** {ficha.get('Fuente / URL', 'N/A')}")
else:
    st.warning("Columna 'Medicamento' no encontrada en el CSV.")

st.write("---")

# ==========================================
# SECCIÓN 2: TABLA DE DATOS EXPLORATORIA
# ==========================================
st.header("📊 Vista General y Explorador de Datos")
st.markdown(f"Mostrando **{len(df_filtrado)}** registros según los filtros de la barra lateral.")

st.dataframe(
    df_filtrado, 
    use_container_width=True,
    hide_index=True
)

csv_descarga = df_filtrado.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Descargar tabla actual en CSV",
    data=csv_descarga,
    file_name="guia_medicamentos_filtrada.csv",
    mime="text/csv",
)
