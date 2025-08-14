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
    
    metric_to_compare = st.sidebar.selectbox(
        "Selecciona una métrica para comparar:",
        ['Publicaciones', 'Contactos', 'Citas', 'Entrevistas', 'Aceptados']
    )
    time_range = st.sidebar.selectbox(
        "Selecciona el periodo de tiempo:",
        ("Últimos 7 días", "Últimos 30 días", "Esta Semana (Jue-Mie)", "Semana Pasada (Jue-Mie)", "Este Mes", "Mes Pasado", "Todo el Histórico")
    )

    # --- LÓGICA DE FILTRADO DE TIEMPO ---
    today = datetime.now().date()
    comparison_df = pd.DataFrame()

    def get_thursday_week_range(date_obj):
        days_since_thursday = (date_obj.weekday() - 3 + 7) % 7
        start = date_obj - timedelta(days=days_since_thursday)
        end = start + timedelta(days=6)
        return start, end

    if time_range == "Últimos 7 días":
        start_date = today - timedelta(days=6)
        comparison_df = df[df['Fecha'].dt.date >= start_date]
    elif time_range == "Últimos 30 días":
        start_date = today - timedelta(days=29)
        comparison_df = df[df['Fecha'].dt.date >= start_date]
    elif time_range == "Esta Semana (Jue-Mie)":
        start_date, end_date = get_thursday_week_range(today)
        comparison_df = df[(df['Fecha'].dt.date >= start_date) & (df['Fecha'].dt.date <= end_date)]
    elif time_range == "Semana Pasada (Jue-Mie)":
        start_of_this_week, _ = get_thursday_week_range(today)
        end_of_last_week = start_of_this_week - timedelta(days=1)
        start_of_last_week, _ = get_thursday_week_range(end_of_last_week)
        comparison_df = df[(df['Fecha'].dt.date >= start_of_last_week) & (df['Fecha'].dt.date <= end_of_last_week)]
    elif time_range == "Este Mes":
        comparison_df = df[(df['Fecha'].dt.month == today.month) & (df['Fecha'].dt.year == today.year)]
    elif time_range == "Mes Pasado":
        first_day_of_current_month = today.replace(day=1)
        last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
        first_day_of_last_month = last_day_of_last_month.replace(day=1)
        comparison_df = df[(df['Fecha'].dt.date >= first_day_of_last_month) & (df['Fecha'].dt.date <= last_day_of_last_month)]
    else: # Todo el Histórico
        comparison_df = df

    if comparison_df.empty:
        st.warning(f"No se encontraron datos para el periodo '{time_range}'.")
    else:
        st.header(f"Comparativa General de '{metric_to_compare}' por Equipo ({time_range})")
        team_results = [{"Equipo": f"{name}", "Total": comparison_df[comparison_df['Reclutador'].isin(data['members'])][metric_to_compare].sum()} for name, data in TEAMS_CONFIG.items()]
        results_df = pd.DataFrame(team_results)

        fig = go.Figure(go.Bar(x=results_df['Equipo'], y=results_df['Total'], text=results_df['Total'], textposition='auto', marker_color='royalblue'))
        fig.update_layout(title=f"Total de {metric_to_compare} por Equipo", xaxis_title="Equipos y Gerentes", yaxis_title=f"Total de {metric_to_compare}", height=500)
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        
        # --- NUEVA SECCIÓN: DESGLOSE POR EQUIPO ---
        st.header("Desglose de Rendimiento por Miembro del Equipo")
        
        num_teams = len(TEAMS_CONFIG)
        cols = st.columns(num_teams)
        
        for i, (team_name, team_data) in enumerate(TEAMS_CONFIG.items()):
            with cols[i]:
                st.subheader(f"Equipo {team_name}")
                team_df = comparison_df[comparison_df['Reclutador'].isin(team_data['members'])]
                member_summary = team_df.groupby('Reclutador')[metric_to_compare].sum().reset_index()
                
                if member_summary.empty or member_summary[metric_to_compare].sum() == 0:
                    st.info("Sin actividad en este periodo.")
                    continue

                fig_member = go.Figure(go.Bar(
                    x=member_summary['Reclutador'],
                    y=member_summary[metric_to_compare],
                    text=member_summary[metric_to_compare],
                    textposition='auto'
                ))
                fig_member.update_layout(
                    title=f"{metric_to_compare}",
                    xaxis_title="Reclutador",
                    yaxis_title="Total",
                    height=400,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig_member, use_container_width=True)

else:
    st.error("No se pudieron cargar los datos.")
