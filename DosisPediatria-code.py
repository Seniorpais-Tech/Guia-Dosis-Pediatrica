import os
import sys

# Bloque de seguridad: Forzar la instalación de pandas si Streamlit Cloud la ignora
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

# Cargar los datos buscando el archivo en el directorio actual
@st.cache_data
def cargar_datos():
    # Buscamos el archivo ignorando problemas de mayúsculas/minúsculas o espacios
    nombre_archivo = "Guia medicamentos_pediatricos Sebas01.csv"
    if not os.path.exists(nombre_archivo):
        # Intenta buscarlo si hay pequeñas variaciones en el nombre
        for f in os.listdir("."):
            if f.lower().startswith("guia medicamentos"):
                nombre_archivo = f
                break
                
    df = pd.read_csv(nombre_archivo, sep=";")
    return df

try:
    df = cargar_datos()
except Exception as e:
    st.error(f"Error al cargar la base de datos CSV. Detalle: {e}")
    st.stop()

# Título Principal
st.title("🩺 Dashboard Interactivo: Guía de Medicamentos Pediátricos y Neonatales")
st.markdown("Consulte dosis, ajustes biológicos, vías de administración y alertas de seguridad en tiempo real.")
st.write("---")

# ==========================================
# BARRA LATERAL: FILTROS DINÁMICOS
# ==========================================
st.sidebar.header("🔍 Filtros de Búsqueda")

grupos_disponibles = ["Todos"] + sorted(df["Grupo"].dropna().unique().tolist())
grupo_seleccionado = st.sidebar.selectbox("Selecciona un Grupo Terapéutico:", grupos_disponibles)

vias_disponibles = ["Todas"] + sorted(df["Vía"].dropna().unique().tolist())
via_seleccionada = st.sidebar.selectbox("Selecciona la Vía de Administración:", vias_disponibles)

df_filtrado = df.copy()
if grupo_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Grupo"] == grupo_seleccionado]
if via_seleccionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Vía"] == via_seleccionada]

# ==========================================
# SECCIÓN 1: CONSULTAS CONCRETAS (ASISTENTE)
# ==========================================
st.header("⚡ Consultas Concretas e Instantáneas")
st.markdown("Selecciona o escribe un medicamento para ver su **Ficha Clínica Completa** de inmediato:")

medicamentos_lista = sorted(df["Medicamento"].dropna().unique().tolist())
medicamento_consulta = st.selectbox("Buscar medicamento específico:", ["Selecciona uno..."] + medicamentos_lista)

if medicamento_consulta != "Selecciona uno...":
    ficha = df[df["Medicamento"] == medicamento_consulta].iloc[0]
    
    st.subheader(f"💊 Ficha Técnica: {ficha['Medicamento']} ({ficha['Grupo']})")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**Indicación Principal:**\n\n{ficha['Indicación principal']}")
    with col2:
        st.success(f"**Dosis Pediátrica Usual:**\n\n{ficha['Dosis pediátrica usual']}")
    with col3:
        st.warning(f"**Dosis Neonatal:**\n\n{ficha['Dosis neonatal']}")
        
    st.write("")
    
    col4, col5 = st.columns(2)
    with col4:
        st.error(f"**Límite / Dosis Máxima:**\n\n{ficha['Dosis máxima / límite']}")
        st.markdown(f"**Vía:** `{ficha['Vía']}`")
    with col5:
        st.markdown(f"⚠️ **Recomendaciones Clave:**\n{ficha['Recomendaciones']}")
        
    st.write("---")
    
    with st.expander("⚕️ Ajustes Renales / Hepáticos y Monitorización"):
        c1, c2 = st.columns(2)
        c1.markdown(f"**Ajuste Orgánico:** {ficha['Ajuste renal/hepático']}")
        c2.markdown(f"**Parámetros a Monitorizar:** {ficha['Monitorización']}")
        st.caption(f"**Fuente de Referencia Oficial:** {ficha['Fuente / URL']}")
        
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
