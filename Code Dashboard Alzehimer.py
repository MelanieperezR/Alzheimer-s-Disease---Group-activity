import streamlit as st 
import pandas as pd
import plotly.express as px
import re
 
# Configuración técnica
st.set_page_config(
    page_title="Prevalencia de Deterioro Cognitivo Funcional en Población Adulta de Estados Unidos",
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

    df = df.rename(columns={
        "Stratification1": "Rango de edad",
        "Stratification2": "Sexo"
    })

    # Título principal
    st.title("Prevalencia de Deterioro Cognitivo Funcional en Población Adulta de Estados Unidos")

    # Bloque informativo institucional
    st.info("""
**Fuente de los datos:** Behavioral Risk Factor Surveillance System (BRFSS) – CDC.  
Los valores corresponden a prevalencia autoreportada de dificultad cognitiva funcional.

**¿Qué es la prevalencia?**  
La prevalencia es el porcentaje de personas dentro de una población que presentan una condición específica en un período determinado.  
Este indicador permite dimensionar la magnitud del fenómeno y compararlo entre estados, grupos etarios y géneros.
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
    edades = sorted(df_solo_edad['Rango de edad'].dropna().unique())
    if not edades:
        edades = sorted(df['Rango de edad'].dropna().unique())

    edad_sel = st.sidebar.selectbox("Seleccione el Rango de Edad:", edades)

    df_mapa = df[df['Rango de edad'] == edad_sel]

    # Métricas
    col1, col2, col3, col4 = st.columns(4)

    avg_val = df_mapa['Data_Value'].mean()
    col1.metric("Tasa de Prevalencia Promedio (%)", f"{avg_val:.2f}%" if not pd.isna(avg_val) else "N/A")
    col2.metric("Total de Registros Analizados", len(df_mapa))
    col3.metric("Cobertura Geográfica (Estados y Territorios)", df_mapa['LocationAbbr'].nunique())
    col4.metric("Última Actualización del Dashboard", "Feb 2026")

    st.divider()

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Mapa de Prevalencia",
        "Comparativo Estatal",
        "Análisis Demográfico",
        "Evolución Temporal",
        "Base de Datos",
        "Metodología"
    ])

    # TAB 1
    with tab1:
        st.subheader("Tasa de Prevalencia de Dificultad Cognitiva Funcional por Estado (%)")

        df_geo = df_mapa.groupby(['LocationAbbr', 'LocationDesc'])['Data_Value'].mean().reset_index()

        if not df_geo.empty:
            fig_map = px.choropleth(
                df_geo,
                locations='LocationAbbr',
                locationmode="USA-states",
                color='Data_Value',
                scope="usa",
                color_continuous_scale=["#DBEAFE", "#3B82F6", "#1E3A8A"],
                labels={'Data_Value': 'Tasa de Prevalencia (%)'},
                hover_name='LocationDesc'
            )

            fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig_map, use_container_width=True)

    # TAB 2 (NUEVO GRÁFICO AÑADIDO)
    with tab2:
        st.subheader("Comparativa de Extremos: Top 5 vs Bottom 5")

        df_ranking = (
            df_mapa.groupby('LocationDesc')['Data_Value']
            .mean()
            .sort_values(ascending=False)
            .reset_index()
        )

        if not df_ranking.empty:
            c_top, c_bot = st.columns(2)

            with c_top:
                st.markdown("**Estados con mayor prevalencia**")
                fig_top = px.bar(
                    df_ranking.head(5),
                    x='Data_Value',
                    y='LocationDesc',
                    orientation='h',
                    color='Data_Value',
                    color_continuous_scale='Reds'
                )
                fig_top.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_top, use_container_width=True)

            with c_bot:
                st.markdown("**Estados con menor prevalencia**")
                fig_bot = px.bar(
                    df_ranking.tail(5),
                    x='Tasa de Prevalencia (%)',
                    y='LocationDesc',
                    orientation='h',
                    color='Data_Value',
                    color_continuous_scale='Greens'
                )
                fig_bot.update_layout(showlegend=False, yaxis={'categoryorder':'total descending'})
                st.plotly_chart(fig_bot, use_container_width=True)

    # TAB 3
    with tab3:
        st.subheader("Tasa de Prevalencia por Rango de Edad y Sexo")

        gender_data = (
            df[df['Sexo'].isin(['Female', 'Male'])]
            .groupby(['Rango de edad', 'Sexo'])['Data_Value']
            .mean()
            .reset_index()
        )

        if not gender_data.empty:
            fig_gen = px.bar(
                gender_data,
                x='Rango de edad',
                y='Data_Value',
                color='Sexo',
                barmode='group',
                labels={'Data_Value': 'Tasa de Prevalencia Promedio (%)'}
            )

            st.plotly_chart(fig_gen, use_container_width=True)
            st.table(gender_data)

    # TAB 4
    with tab4:
        st.subheader("Evolución Temporal de la Tasa de Prevalencia (%)")
     
        df_trend = (
            df_mapa.groupby("YearStart")["Data_Value"]
            .mean()
            .reset_index()
            .sort_values("YearStart")
        )

        if not df_trend.empty:
            fig_trend = px.line(
                df_trend,
                x="YearStart",
                y="Data_Value",
                markers=True,
                labels={
                    "YearStart": "Año",
                    "Data_Value": "Tasa de Prevalencia Promedio (%)"
                }
            )

            fig_trend.update_traces(line=dict(color="#1E3A8A", width=3))
            fig_trend.update_layout(xaxis=dict(dtick=1))
            st.plotly_chart(fig_trend, use_container_width=True)

    # TAB 5
    with tab5:
        st.subheader("Explorador de Datos")
        st.dataframe(df_mapa, use_container_width=True)

    # TAB 6
    with tab6:
        st.header("Metodología")
        st.write("Datos oficiales del CDC obtenidos mediante el sistema BRFSS.")

else:
    st.error("Error al cargar el recurso de datos. Verifique la integridad del archivo CSV.")
