
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

@st.cache_data(ttl=43200)
def load_data_from_airtable():
    from pyairtable import Api
    try:
        api_key = st.secrets["airtable"]["api_key"]
        base_id = st.secrets["airtable"]["base_id"]
        table_name = st.secrets["airtable"]["table_name"]
        api = Api(api_key)
        table = api.table(base_id, table_name)
        all_records = table.all()
        df = pd.DataFrame([record['fields'] for record in all_records])
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        metric_columns = ['Publicaciones', 'Contactos', 'Citas', 'Entrevistas', 'Aceptados']
        for col in metric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        if 'Reclutador' in df.columns:
            df['Reclutador'] = df['Reclutador'].str.strip()
        # Eliminar filas donde la fecha no se pudo convertir
        df.dropna(subset=['Fecha'], inplace=True)
        return df
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame()

def get_thursday_week_range(date_obj):
    """Calcula el inicio de la semana (Jueves) para una fecha dada."""
    days_since_thursday = (date_obj.weekday() - 3 + 7) % 7
    start_of_week = date_obj - timedelta(days=days_since_thursday)
    return start_of_week

st.set_page_config(page_title="Métricas Diarias", page_icon="📈", layout="wide")
st.title("📈 Métricas y desempeño diario")
st.subheader(f"Visualiza el desempeño diario del departamento de reclutamiento.")


df = load_data_from_airtable()

if not df.empty:
    st.sidebar.header("Filtrar por")
    recruiters = sorted(df['Reclutador'].unique())
    selected_recruiter = st.sidebar.selectbox("Selecciona un Reclutador", ["Todos"] + recruiters)
    
    df_filtered = df if selected_recruiter == "Todos" else df[df['Reclutador'] == selected_recruiter].copy()

    metric_labels = {
        'Publicaciones': 'Publicaciones', 
        'Contactos': 'Contactados', 
        'Citas': 'Citados', 
        'Entrevistas': 'Entrevistados', 
        'Aceptados': 'Aceptados'
    }

    tabs1, tabs2, tabs3 = st.tabs(["☝️🤓 Diario", "☝️🤓 Semanal", "☝️🤓 Mensual"])

    with tab1:
        st.header("Tetas de hamster")
    with tab2:
        st.header("Prueba")
    with tab3:
        st.header("Artimaña")

        
        col1, col2, col3= st.columns([1, 1, 1])
        col4, col5 = st.columns([2,2])

        #Primer columna para el gauge jeje equis de
    with col1:
        fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = df_filtered['Publicaciones'].sum(),
        title = {'text': "Publicaciones"}))
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = df_filtered['Contactos'].sum(),
        title = {'text': "Contactados"}))
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = df_filtered['Citas'].sum(),
        title = {'text': "Citados"}))
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        fig4 = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = df_filtered['Entrevistas'].sum(),
        title = {'text': "Acudieron a la cita"}))
        st.plotly_chart(fig4, use_container_width=True)

    with col5:
        fig5 = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = df_filtered['Aceptados'].sum(),
        title = {'text': "Aceptados"}))
        st.plotly_chart(fig5, use_container_width=True)

    

    
    st.divider()
    

##Estoy muriendoooo









