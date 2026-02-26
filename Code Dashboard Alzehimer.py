import streamlit as st 
import pandas as pd
import plotly.express as px
import re
 
# Configuración técnica
st.set_page_config(
    page_title="Prevalencia de Dificultad Cognitiva Funcional en Adultos – EE.UU.",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo profesional
st.markdown("""
<style>
    .main { background-color: #F4F7FB; }

    .stMetric {
        background-color: #FFFFFF;
        padding: 18px;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
    }

    h1 { color: #1E3A8A; font-weight: 700; }
    h2, h3 { color: #1D4ED8; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# --- FUNCIONES ---

def extract_coords(point_str):
    try:
        if pd.isna(point_str) or str(point_str).strip() == "":
            return None, None
        coords = re.findall(r"[-+]?\d*\.\d+|\d+", str(point_str))
        if len(coords) >= 2:
            return float(coords[1]), float(coords[0]) 
    except:
        return None, None
    return None, None

@st.cache_data
def load_data():
    file_path = "Alzheimer's_Disease_and_Healthy_Aging_Data_2026.csv"
    df = pd.read_csv(file_path, sep=None, engine='python', on_bad_lines='skip')
    df['Data_Value'] = pd.to_numeric(df['Data_Value'], errors='coerce')

    if 'Geolocation' in df.columns:
        coords = df['Geolocation'].apply(extract_coords)
        df[['lat', 'lon']] = pd.DataFrame(coords.tolist(), index=df.index)

    return df

# --- APP ---

df = load_data()

st.title("Prevalencia de Dificultad Cognitiva Funcional en Adultos – EE.UU.")

st.info("""
Datos oficiales del CDC – Behavioral Risk Factor Surveillance System (BRFSS).

La prevalencia es el porcentaje de personas dentro de una población que presentan una condición específica en un período determinado.
Permite comparar la magnitud del fenómeno entre estados, grupos etarios y sexo.
""")

st.divider()

# --- FILTROS ---

st.sidebar.header("Filtros de Análisis")

years = sorted(df['YearStart'].dropna().unique())
year_sel = st.sidebar.selectbox("Seleccione el Año:", years)

df_age = df[df['StratificationCategory1'] == 'Age Group']
age_groups = sorted(df_age['Stratification1'].dropna().unique())
age_sel = st.sidebar.selectbox("Seleccione el Grupo Etario:", age_groups)

sex_options = ['Total', 'Female', 'Male']
sex_sel = st.sidebar.selectbox("Seleccione el Sexo:", sex_options)

df_filtered = df[
    (df['YearStart'] == year_sel) &
    (df['Stratification1'] == age_sel)
]

if sex_sel != "Total":
    df_filtered = df_filtered[df_filtered['Stratification2'] == sex_sel]

# --- MÉTRICAS ---

col1, col2, col3 = st.columns(3)

avg_val = df_filtered['Data_Value'].mean()
col1.metric("Prevalencia Promedio (%)", f"{avg_val:.2f}%" if not pd.isna(avg_val) else "N/A")
col2.metric("Estados Analizados", df_filtered['LocationAbbr'].nunique())
col3.metric("Observaciones", len(df_filtered))

st.divider()

# --- TABS ---

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Mapa de Prevalencia",
    "Comparativo Estatal",
    "Análisis Demográfico",
    "Evolución Temporal",
    "Base de Datos",
    "Metodología"
])

# TAB 1 — MAPA
with tab1:
    st.subheader("Prevalencia por Estado (%)")

    df_geo = df_filtered.groupby(['LocationAbbr','LocationDesc'])['Data_Value'].mean().reset_index()
    df_geo.rename(columns={
        'LocationDesc': 'Estado',
        'Data_Value': 'Prevalencia (%)'
    }, inplace=True)

    fig_map = px.choropleth(
        df_geo,
        locations='LocationAbbr',
        locationmode="USA-states",
        color='Prevalencia (%)',
        scope="usa",
        hover_name='Estado',
        color_continuous_scale=["#DBEAFE", "#3B82F6", "#1E3A8A"]
    )

    st.plotly_chart(fig_map, use_container_width=True)

# TAB 2 — COMPARATIVO
with tab2:
    st.subheader("Ranking Estatal de Prevalencia")

    df_rank = df_geo.sort_values("Prevalencia (%)", ascending=False)

    fig_rank = px.bar(
        df_rank,
        x="Prevalencia (%)",
        y="Estado",
        orientation="h"
    )

    fig_rank.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_rank, use_container_width=True)

# TAB 3 — DEMOGRÁFICO
with tab3:
    st.subheader("Prevalencia por Grupo Etario y Sexo")

    df_demo = df[
        (df['YearStart'] == year_sel) &
        (df['StratificationCategory1'] == 'Age Group') &
        (df['Stratification2'].isin(['Female','Male']))
    ]

    df_demo = df_demo.groupby(
        ['Stratification1','Stratification2']
    )['Data_Value'].mean().reset_index()

    df_demo.rename(columns={
        'Stratification1': 'Grupo Etario',
        'Stratification2': 'Sexo',
        'Data_Value': 'Prevalencia (%)'
    }, inplace=True)

    fig_demo = px.bar(
        df_demo,
        x="Grupo Etario",
        y="Prevalencia (%)",
        color="Sexo",
        barmode="group"
    )

    st.plotly_chart(fig_demo, use_container_width=True)

# TAB 4 — TEMPORAL
with tab4:
    st.subheader("Evolución Temporal de la Prevalencia")

    df_trend = df[df['Stratification1'] == age_sel]

    if sex_sel != "Total":
        df_trend = df_trend[df_trend['Stratification2'] == sex_sel]

    df_trend = df_trend.groupby('YearStart')['Data_Value'].mean().reset_index()
    df_trend.rename(columns={'Data_Value': 'Prevalencia (%)'}, inplace=True)

    fig_trend = px.line(
        df_trend,
        x="YearStart",
        y="Prevalencia (%)",
        markers=True
    )

    st.plotly_chart(fig_trend, use_container_width=True)

# TAB 5 — BASE DE DATOS
with tab5:
    st.subheader("Explorador de Datos Filtrados")
    st.dataframe(df_filtered, use_container_width=True)

# TAB 6 — METODOLOGÍA
with tab6:
    st.header("Metodología y Fuente de Datos")

    st.markdown("""
**Fuente Oficial:**  
Centers for Disease Control and Prevention (CDC)  
Sistema: Behavioral Risk Factor Surveillance System (BRFSS)

**Indicador Analizado:**  
Prevalencia autoreportada de dificultad cognitiva funcional en población adulta.

**Definición Operativa:**  
La prevalencia representa el porcentaje de individuos dentro de una población que reportan una condición específica en un período determinado.

**Enfoque Analítico:**  
- Análisis comparativo entre estados  
- Evaluación por grupo etario  
- Análisis por sexo  
- Tendencia temporal
""")

st.divider()

st.markdown("""
<div style="text-align: center; color: #6B7280; font-size: 0.8em;">
Informe Técnico - CDC BRFSS Data<br>
Elaborado por: Valentina Torres, Melanie Perez, Natalia Sojo, Dana Ramirez
</div>
""", unsafe_allow_html=True)
