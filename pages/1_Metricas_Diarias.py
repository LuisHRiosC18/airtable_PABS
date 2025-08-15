
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

    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = df_filtered['Publicaciones'].sum(),
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Publicaciones"}))

    fig.show()

##Estoy muriendoooo









