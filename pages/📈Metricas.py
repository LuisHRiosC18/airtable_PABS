import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pyairtable import Api
import numpy as np

# --- CONFIGURACIÓN DE LA PÁGINA Y TÍTULO ---
st.set_page_config(
    page_title="Métricas totales e individuales",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard de Métricas de Reclutamiento")
st.markdown("Visualiza el rendimiento diario, semanal y mensual, y compara el desempeño histórico del equipo.")

# --- CONEXIÓN A AIRTABLE Y CACHÉ DE DATOS ---
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
        return df
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame()
# --- FIN: Función de carga ---

def get_thursday_week_range(date_obj):
    """Calcula el rango de semana de Jueves a Miércoles para una fecha dada."""
    days_since_thursday = (date_obj.weekday() - 3 + 7) % 7
    start_of_week = date_obj - timedelta(days=days_since_thursday)
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week, end_of_week

df = load_data_from_airtable()

if not df.empty:
    st.sidebar.header("Filtros Principales")
    recruiters = sorted(df['Reclutador'].unique())
    selected_recruiter = st.sidebar.selectbox("Selecciona un Reclutador", ["Todos"] + recruiters)
    
    # --- FILTRADO DE DATOS ---
    if selected_recruiter != "Todos":
        df_filtered = df[df['Reclutador'] == selected_recruiter].copy()
    else:
        df_filtered = df.copy()

    # --- PESTAÑAS PARA VISTAS (SEMANA) ---
    st.header("Análisis Semanal (Jueves a Miércoles)")
    
    selected_date_week = st.date_input(
        "Selecciona una fecha para ver su semana correspondiente", 
        datetime.now().date(),
        key="weekly_date_selector"
    )
    
    start_of_week, end_of_week = get_thursday_week_range(selected_date_week)
    
    st.info(f"Mostrando datos para la semana del **Jueves, {start_of_week.strftime('%d/%m/%Y')}** al **Miércoles, {end_of_week.strftime('%d/%m/%Y')}**")

    weekly_data = df_filtered[
        (df_filtered['Fecha'].dt.date >= start_of_week) & 
        (df_filtered['Fecha'].dt.date <= end_of_week)
    ]
    
    if weekly_data.empty:
        st.warning("No hay datos para el reclutador y la semana seleccionados.")
    else:
        weekly_summary = weekly_data.sum(numeric_only=True)
        
        # --- NUEVOS INDICADORES ---
        st.subheader("Totales de la Semana")
        
        # Renombramos las métricas para la visualización
        metric_labels = {
            'Publicaciones': 'Publicaciones de la semana',
            'Contactos': 'Contactados',
            'Citas': 'Citados',
            'Entrevistas': 'Entrevistados',
            'Aceptados': 'Aceptados'
        }

        cols = st.columns(len(metric_labels))
        
        for i, (metric, label) in enumerate(metric_labels.items()):
            value = weekly_summary.get(metric, 0)
            cols[i].metric(label=label, value=f"{int(value)}")

    st.divider()

    # --- NUEVA SECCIÓN: PUBLICACIONES DEL DOMINGO ---
    st.header("Publicaciones del Último Domingo")
    
    today = datetime.now().date()
    # Encontrar el domingo más reciente
    last_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
    
    st.markdown(f"Mostrando las publicaciones realizadas el **Domingo, {last_sunday.strftime('%d de %B, %Y')}**")
    
    sunday_df = df[df['Fecha'].dt.date == last_sunday]
    
    if sunday_df.empty:
        st.warning("No se encontraron publicaciones para el último domingo.")
    else:
        sunday_publications = sunday_df[sunday_df['Publicaciones'] > 0][['Reclutador', 'Publicaciones']]
        if sunday_publications.empty:
            st.info("Ningún reclutador realizó publicaciones el último domingo.")
        else:
            st.dataframe(sunday_publications.set_index('Reclutador'), use_container_width=True)

else:
    st.error("No se pudieron cargar los datos. Revisa la conexión y la configuración.")
