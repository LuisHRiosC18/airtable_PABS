## Esta pagina es dedicada a la comparativa entre el desempeño de los distintos equipos.
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pyairtable import Api
import numpy as np

TEAMS_CONFIG = {
    "Equipo Jeanneth": {
        "manager": "Jeanneth",
        "members": ["ISABEL", "ORLANDO"]
    },
    "Equipo José Luis": {
        "manager": "José Luis",
        "members": ["ENOC"]
    },
    "Equipo Joel": {
        "manager": "Joel",
        "members": ["KAREN"]
    },
    "Equipo de Laura": {
        "manager": "Laura",
        "members": ["DAVID"]
    }
}

# Cargar lo del airtable
@st.cache_data(ttl=43200)
def load_data_from_airtable():
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
        # Asegurarse de que los nombres de los reclutadores no tengan espacios extra
        if 'Reclutador' in df.columns:
            df['Reclutador'] = df['Reclutador'].str.strip()
        return df
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame()

df = load_data_from_airtable()

if not df.empty:
    st.sidebar.header("Filtros de Comparación")
    
    # Filtro para seleccionar la métrica a comparar
    metric_to_compare = st.sidebar.selectbox(
        "Selecciona una métrica para comparar:",
        ['Publicaciones', 'Contactos', 'Citas', 'Entrevistas', 'Aceptados']
    )

    # Filtro para el rango de tiempo
    time_range = st.sidebar.selectbox(
        "Selecciona el periodo de tiempo:",
        ("Últimos 7 días", "Últimos 30 días", "Este Mes", "Mes Pasado", "Todo el Histórico")
    )

    # --- LÓGICA DE FILTRADO DE TIEMPO ---
    today = datetime.now().date()
    comparison_df = pd.DataFrame()

    if time_range == "Últimos 7 días":
        start_date = today - timedelta(days=7)
        comparison_df = df[df['Fecha'].dt.date >= start_date]
    elif time_range == "Últimos 30 días":
        start_date = today - timedelta(days=30)
        comparison_df = df[df['Fecha'].dt.date >= start_date]
    elif time_range == "Este Mes":
        comparison_df = df[(df['Fecha'].dt.month == today.month) & (df['Fecha'].dt.year == today.year)]
    elif time_range == "Mes Pasado":
        first_day_of_current_month = today.replace(day=1)
        last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
        first_day_of_last_month = last_day_of_last_month.replace(day=1)
        comparison_df = df[(df['Fecha'].dt.date >= first_day_of_last_month) & (df['Fecha'].dt.date <= last_day_of_last_month)]
    else: # Todo el Histórico
        comparison_df = df

    # --- CÁLCULO Y VISUALIZACIÓN ---
    if comparison_df.empty:
        st.warning(f"No se encontraron datos para el periodo '{time_range}'.")
    else:
        st.header(f"Comparativa de '{metric_to_compare}' por equipo ({time_range})")

        team_results = []
        for team_name, team_data in TEAMS_CONFIG.items():
            # Filtrar el dataframe para incluir solo a los miembros del equipo
            team_df = comparison_df[comparison_df['Reclutador'].isin(team_data['members'])]
            total_metric = team_df[metric_to_compare].sum()
            team_results.append({
                "Equipo": f"{team_name} (Gerente: {team_data['manager']})",
                "Total": total_metric
            })

        results_df = pd.DataFrame(team_results)

        # Crear gráfico de barras
        fig = go.Figure(go.Bar(
            x=results_df['Equipo'],
            y=results_df['Total'],
            text=results_df['Total'],
            textposition='auto',
            marker_color='royalblue'
        ))

        fig.update_layout(
            title=f"Total de {metric_to_compare} por Equipo",
            xaxis_title="Equipos y Gerentes",
            yaxis_title=f"Total de {metric_to_compare}",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

else:
    st.error("No se pudieron cargar los datos. Revisa la conexión y la configuración.")


