import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Se asume una función de carga en utils.py
# from utils import load_data_from_airtable 

# --- INICIO: Función de carga (copiar a utils.py o mantener aquí) ---
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
# --- FIN: Función de carga ---

def get_thursday_week_range(date_obj):
    """Calcula el inicio de la semana (Jueves) para una fecha dada."""
    days_since_thursday = (date_obj.weekday() - 3 + 7) % 7
    start_of_week = date_obj - timedelta(days=days_since_thursday)
    return start_of_week

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Métricas Individuales", page_icon="📈", layout="wide")
st.title("📈 Métricas y Desempeño Individual")

df = load_data_from_airtable()

if not df.empty:
    st.sidebar.header("Filtros Principales")
    recruiters = sorted(df['Reclutador'].unique())
    selected_recruiter = st.sidebar.selectbox("Selecciona un Reclutador", ["Todos"] + recruiters)
    
    df_filtered = df if selected_recruiter == "Todos" else df[df['Reclutador'] == selected_recruiter].copy()

    # --- CORRECCIÓN: Definir metric_labels en un alcance superior ---
    metric_labels = {
        'Publicaciones': 'Publicaciones', 
        'Contactos': 'Contactados', 
        'Citas': 'Citados', 
        'Entrevistas': 'Entrevistados', 
        'Aceptados': 'Aceptados'
    }

    st.header("Análisis Semanal (Jueves a Miércoles)")
    selected_date_week = st.date_input("Selecciona una fecha para ver su semana", datetime.now().date(), key="weekly_date_selector")
    
    start_of_week, end_of_week = get_thursday_week_range(selected_date_week), get_thursday_week_range(selected_date_week) + timedelta(days=6)
    st.info(f"Mostrando datos del **Jueves, {start_of_week.strftime('%d/%m/%Y')}** al **Miércoles, {end_of_week.strftime('%d/%m/%Y')}**")

    weekly_data = df_filtered[(df_filtered['Fecha'].dt.date >= start_of_week) & (df_filtered['Fecha'].dt.date <= end_of_week)]
    
    if weekly_data.empty:
        st.warning("No hay datos para el reclutador y la semana seleccionados.")
    else:
        weekly_summary = weekly_data.sum(numeric_only=True)
        cols = st.columns(len(metric_labels))
        for i, (metric, label) in enumerate(metric_labels.items()):
            cols[i].metric(label=label, value=f"{int(weekly_summary.get(metric, 0))}")

    st.divider()

    # --- NUEVA SECCIÓN: GRÁFICOS DE ACUMULADO KPI ---
    st.header("KPIs Acumulados por Semana")
    df_filtered['Week_Start'] = df_filtered['Fecha'].apply(get_thursday_week_range)
    weekly_kpis = df_filtered.groupby('Week_Start').sum(numeric_only=True).sort_index()
    
    if weekly_kpis.empty:
        st.warning("No hay suficientes datos históricos para mostrar KPIs acumulados.")
    else:
        cumulative_kpis = weekly_kpis.cumsum()
        
        # Ahora esta línea funcionará siempre
        kpi_cols = st.columns(len(metric_labels))
        for i, (metric, label) in enumerate(metric_labels.items()):
            with kpi_cols[i]:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=cumulative_kpis.index, 
                    y=cumulative_kpis[metric], 
                    fill='tozeroy', 
                    mode='lines',
                    name=label
                ))
                fig.update_layout(
                    title=f"Acumulado de {label}",
                    height=300,
                    margin=dict(l=20, r=20, t=40, b=20),
                    xaxis_title=None,
                    yaxis_title="Total"
                )
                st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --- SECCIÓN ACTUALIZADA: PUBLICACIONES DEL DOMINGO ---
    st.header("Análisis de Publicaciones en Domingo")
    
    sunday_df = df[df['Fecha'].dt.weekday == 6].copy() # 6 es Domingo
    
    if sunday_df.empty:
        st.warning("No se han registrado publicaciones en ningún domingo.")
    else:
        sunday_df.sort_values('Fecha', ascending=False, inplace=True)
        available_sundays = sunday_df['Fecha'].dt.date.unique()
        
        selected_sunday = st.selectbox(
            "Selecciona un domingo para ver el detalle:",
            options=available_sundays,
            format_func=lambda date: date.strftime('%d de %B, %Y')
        )
        
        col1, col2 = st.columns([1, 2])

        with col1:
            # INDICADOR GRANDE
            total_pubs_sunday = sunday_df[sunday_df['Fecha'].dt.date == selected_sunday]['Publicaciones'].sum()
            st.metric(
                label=f"Total de Publicaciones del Domingo {selected_sunday.strftime('%d/%m/%Y')}",
                value=int(total_pubs_sunday)
            )

        with col2:
            # GRÁFICO DE LÍNEAS HISTÓRICO
            historical_sunday_pubs = sunday_df.groupby(sunday_df['Fecha'].dt.date)['Publicaciones'].sum().sort_index()
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(
                x=historical_sunday_pubs.index,
                y=historical_sunday_pubs.values,
                mode='lines+markers',
                name='Publicaciones'
            ))
            fig_line.update_layout(
                title="Tendencia de Publicaciones en Domingos",
                xaxis_title="Fecha",
                yaxis_title="Número de Publicaciones",
                height=350
            )
            st.plotly_chart(fig_line, use_container_width=True)

else:
    st.error("No se pudieron cargar los datos. Revisa la conexión y la configuración.")
