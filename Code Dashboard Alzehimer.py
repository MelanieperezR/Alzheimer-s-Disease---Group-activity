import streamlit as st 
import pandas as pd
import plotly.express as px
import re
 
# Configuración técnica
st.set_page_config(
    page_title="Prevalencia de Deterioro Cognitivo Funcional en Población Adulta de Estados Unidos (BRFSS)",
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

    h1 {
        color: #1E3A8A;
        font-weight: 700;
    }

    h2, h3 {
        color: #1D4ED8;
        font-weight: 600;
    }

    .stTabs [data-baseweb="tab"] {
        font-weight: 500;
    }
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
    try:
        df = pd.read_csv(file_path, sep=None, engine='python', on_bad_lines='skip')

        cols_to_fix = ['Data_Value', 'Low_Confidence_Limit', 'High_Confidence_Limit']
        for col in cols_to_fix:
            if col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce')

        if 'Geolocation' in df.columns:
            coords = df['Geolocation'].apply(extract_coords)
            df[['lat', 'lon']] = pd.DataFrame(coords.tolist(), index=df.index)

        return df
    except Exception as e:
        st.error(f"Error en la carga de datos: {e}")
        return None

# --- APP ---

df = load_data()

if df is not None:

    # Renombrar columnas visibles al usuario
    df = df.rename(columns={
        "Stratification1": "Rango de Edad",
        "Stratification2": "Sexo",
        "LocationDesc": "Estado",
        "LocationAbbr": "Código Estado",
        "Data_Value": "Tasa de Prevalencia (%)",
        "YearStart": "Año"
    })

    st.title("Prevalencia de Deterioro Cognitivo Funcional en Población Adulta de Estados Unidos")

    st.info("""
**Fuente de los datos:** Sistema de Vigilancia de Factores de Riesgo Conductuales (BRFSS) – CDC.  
Los valores corresponden a prevalencia autoreportada de dificultad cognitiva funcional.

**¿Qué es la prevalencia?**  
La prevalencia es el porcentaje de personas dentro de una población que presentan una condición específica en un período determinado.  
Este indicador permite dimensionar la magnitud del fenómeno y compararlo entre estados, grupos etarios y sexo.
""")

    st.divider()

    # Sidebar
    st.sidebar.markdown("### Integrantes del Proyecto")
    st.sidebar.markdown("""
    * Valentina Torres Lujo
    * Melanie Perez Rojano
    * Natalia Sojo Jimenez
    * Dana Ramirez Suarez
    """)
    st.sidebar.divider()

    st.sidebar.header("Parámetros de Análisis")

    df_solo_edad = df[df['StratificationCategory1'] == 'Age Group']
    edades = sorted(df_solo_edad['Rango de Edad'].dropna().unique())
    if not edades:
        edades = sorted(df['Rango de Edad'].dropna().unique())

    edad_sel = st.sidebar.selectbox("Seleccione el Rango de Edad:", edades)

    df_filtrado = df[df['Rango de Edad'] == edad_sel]

    # Métricas
    col1, col2, col3, col4 = st.columns(4)

    promedio = df_filtrado['Tasa de Prevalencia (%)'].mean()

    col1.metric("Tasa de Prevalencia Promedio (%)", f"{promedio:.2f}%" if not pd.isna(promedio) else "N/D")
    col2.metric("Total de Registros Analizados", len(df_filtrado))
    col3.metric("Cobertura Geográfica (Estados y Territorios)", df_filtrado['Código Estado'].nunique())
    col4.metric("Última Actualización del Panel", "Febrero 2026")

    st.divider()

    pestañas = st.tabs([
        "Mapa de Prevalencia",
        "Comparativo Estatal",
        "Análisis Demográfico",
        "Evolución Temporal",
        "Base de Datos",
        "Metodología"
    ])

    # --- MAPA ---
    with pestañas[0]:
        st.subheader("Tasa de Prevalencia por Estado (%)")

        df_geo = df_filtrado.groupby(['Código Estado', 'Estado'])['Tasa de Prevalencia (%)'].mean().reset_index()

        if not df_geo.empty:
            fig_mapa = px.choropleth(
                df_geo,
                locations='Código Estado',
                locationmode="USA-states",
                color='Tasa de Prevalencia (%)',
                scope="usa",
                color_continuous_scale=["#DBEAFE", "#3B82F6", "#1E3A8A"],
                labels={'Tasa de Prevalencia (%)': 'Tasa de Prevalencia (%)'},
                hover_name='Estado'
            )

            fig_mapa.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig_mapa, use_container_width=True)

    # --- COMPARATIVO ---
    with pestañas[1]:
       
        st.subheader("Análisis Comparativo de los Extremos: Top 5 ")
        df_ranking = df_mapa.groupby('LocationDesc')['Data_Value'].mean().sort_values(ascending=False).reset_index()
 
        if not df_ranking.empty:
            c_top, c_bot = st.columns(2)
            with c_top:
                st.markdown("**Estados con mayor prevalencia**")
                fig_top = px.bar(df_ranking.head(5), x='Tasa de Prevalencia (%)', y='Estado' , orientation='h',
                                 color='Data_Value', color_continuous_scale='Reds')
                fig_top.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_top, use_container_width=True)
 
            with c_bot:
                st.markdown("**Estados con menor prevalencia**")
                fig_bot = px.bar(df_ranking.tail(5),  x='Tasa de Prevalencia (%)', y='Estado' , orientation='h',
                                 color='Data_Value', color_continuous_scale='Greens')
                fig_bot.update_layout(showlegend=False, yaxis={'categoryorder':'total descending'})
                st.plotly_chart(fig_bot, use_container_width=True)

    # --- DEMOGRÁFICO ---
    with pestañas[2]:
        st.subheader("Tasa de Prevalencia por Rango de Edad y Sexo")

        demografico = (
            df[df['Sexo'].isin(['Female', 'Male'])]
            .groupby(['Rango de Edad', 'Sexo'])['Tasa de Prevalencia (%)']
            .mean()
            .reset_index()
        )

        if not demografico.empty:
            fig_demo = px.bar(
                demografico,
                x='Rango de Edad',
                y='Tasa de Prevalencia (%)',
                color='Sexo',
                barmode='group'
            )
            st.plotly_chart(fig_demo, use_container_width=True)
            st.dataframe(demografico, use_container_width=True)

    # --- TEMPORAL ---
    with pestañas[3]:
        st.subheader("Evolución Temporal de la Tasa de Prevalencia (%)")

        tendencia = (
            df_filtrado.groupby("Año")["Tasa de Prevalencia (%)"]
            .mean()
            .reset_index()
            .sort_values("Año")
        )

        if not tendencia.empty:
            fig_linea = px.line(
                tendencia,
                x="Año",
                y="Tasa de Prevalencia (%)",
                markers=True
            )
            st.plotly_chart(fig_linea, use_container_width=True)

    # --- BASE DE DATOS ---
    with pestañas[4]:
        st.subheader("Explorador de Datos")
        st.dataframe(df_filtrado, use_container_width=True)

    # --- METODOLOGÍA ---
    with pestañas[5]:
        st.header("Metodología")
        st.write("Datos oficiales obtenidos mediante el sistema BRFSS del CDC.")

    st.divider()
    st.markdown("""
<div style="text-align: center; color: #6B7280; font-size: 0.8em;">
Informe Técnico - Enfermedad de Alzheimer y Envejecimiento Saludable<br>
Elaborado por: Valentina Torres, Melanie Perez, Natalia Sojo, Dana Ramirez
</div>
""", unsafe_allow_html=True)

else:
    st.error("Error al cargar el archivo de datos. Verifique la integridad del CSV.")
