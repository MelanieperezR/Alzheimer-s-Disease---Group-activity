import streamlit as st
import pandas as pd
import plotly.express as px
import re

# Configuración técnica
st.set_page_config(
    page_title=" Prevalencia de Deterioro Cognitivo Funcional en Población Adulta de Estados Unidos (BRFSS)",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo profesional
st.markdown("""
<style>
.main {
    background-color: #F4F7FB;
}
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

        # Renombrar columnas
        df.rename(columns={
            'Data_Value': 'Prevalence_Value',
            'LocationDesc': 'State_Name'
        }, inplace=True)

        cols_to_fix = ['Prevalence_Value', 'Low_Confidence_Limit', 'High_Confidence_Limit']
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

    st.title("Prevalencia de Deterioro Cognitivo Funcional en Población Adulta de Estados Unidos (BRFSS)")

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

    # 🔹 NUEVOS FILTROS

    # Año
    years = sorted(df['YearStart'].dropna().unique())
    selected_year = st.sidebar.selectbox("Seleccione el Año:", years)

    # Grupo Etario
    df_age = df[df['StratificationCategory1'] == 'Age Group']
    age_groups = sorted(df_age['Stratification1'].dropna().unique())
    selected_age = st.sidebar.selectbox("Seleccione el Grupo Etario:", age_groups)

    # Sexo
    sexes = sorted(df['Stratification2'].dropna().unique())
    selected_sex = st.sidebar.selectbox("Seleccione el Sexo:", sexes)

    # Base filtrada
    df_filtered = df[
        (df['YearStart'] == selected_year) &
        (df['Stratification1'] == selected_age) &
        (df['Stratification2'] == selected_sex)
    ]

    # Métricas
    col1, col2, col3, col4 = st.columns(4)

    avg_val = df_filtered['Prevalence_Value'].mean()

    col1.metric("Prevalencia Promedio (%)", f"{avg_val:.2f}%" if not pd.isna(avg_val) else "N/A")
    col2.metric("Total de Observaciones", len(df_filtered))
    col3.metric("Estados y Territorios Analizados", df_filtered['LocationAbbr'].nunique())
    col4.metric("Última Actualización del Dashboard", "Feb 2026")

    st.divider()

    # Tabs
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
        st.subheader("Prevalencia por Estado (%)")

        df_geo = df_filtered.groupby(['LocationAbbr', 'State_Name'])['Prevalence_Value'].mean().reset_index()

        if not df_geo.empty:
            fig_map = px.choropleth(
                df_geo,
                locations='LocationAbbr',
                locationmode="USA-states",
                color='Prevalence_Value',
                scope="usa",
                hover_name='State_Name'
            )
            st.plotly_chart(fig_map, use_container_width=True)

    # TAB 2
    with tab2:
        st.subheader("Ranking Estatal")

        df_ranking = (
            df_filtered.groupby('State_Name')['Prevalence_Value']
            .mean()
            .sort_values(ascending=False)
            .reset_index()
        )

        if not df_ranking.empty:
            fig_rank = px.bar(
                df_ranking,
                x='Prevalence_Value',
                y='State_Name',
                orientation='h'
            )
            st.plotly_chart(fig_rank, use_container_width=True)

    # TAB 3
    with tab3:
        st.subheader("Comparación por Grupo Etario y Sexo")

        demo_data = (
            df[df['YearStart'] == selected_year]
            .groupby(['Stratification1', 'Stratification2'])['Prevalence_Value']
            .mean()
            .reset_index()
        )

        fig_demo = px.bar(
            demo_data,
            x='Stratification1',
            y='Prevalence_Value',
            color='Stratification2',
            barmode='group'
        )

        st.plotly_chart(fig_demo, use_container_width=True)

    # TAB 4
    with tab4:
        st.subheader("Evolución Temporal")

        trend_data = (
            df[
                (df['Stratification1'] == selected_age) &
                (df['Stratification2'] == selected_sex)
            ]
            .groupby('YearStart')['Prevalence_Value']
            .mean()
            .reset_index()
        )

        fig_trend = px.line(trend_data, x="YearStart", y="Prevalence_Value", markers=True)
        st.plotly_chart(fig_trend, use_container_width=True)

    # TAB 5
    with tab5:
        st.subheader("Explorador de Datos")
        st.dataframe(df_filtered, use_container_width=True)

    # TAB 6
    with tab6:
        st.header("Metodología")
        st.write("Datos provenientes del CDC - Alzheimer's Disease and Healthy Aging Data.")

else:
    st.error("Error al cargar el recurso de datos.")
