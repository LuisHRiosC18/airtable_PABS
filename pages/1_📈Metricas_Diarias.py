import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

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
st.set_page_config(page_title="Métricas de Reclutamiento", page_icon="📈", layout="wide")
st.title("📈 Métricas y Desempeño")
st.subheader("Visualiza el desempeño del departamento de reclutamiento por periodo.")

df = load_data_from_airtable()

if not df.empty:
    st.sidebar.header("Filtros Principales")
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

    # --- CREACIÓN DE PESTAÑAS ---
    tab_daily, tab_weekly, tab_monthly, tab_sunday = st.tabs(["Diario", "Semanal", "Mensual", "Análisis de Domingos"])

    # --- PESTAÑA DIARIA (ACTUALIZADA) ---
    with tab_daily:
        st.header("Métricas del Día")
        selected_date_daily = st.date_input("Selecciona un día", datetime.now().date(), key="daily_date_selector")
        
        # Calcular promedios históricos por día de la semana
        df['DiaSemana'] = df['Fecha'].dt.day_name()
        daily_avg = df.groupby('DiaSemana')[list(metric_labels.keys())].mean()
        
        daily_data = df_filtered[df_filtered['Fecha'].dt.date == selected_date_daily]
        
        if daily_data.empty:
            st.warning("No hay datos para el reclutador y el día seleccionados.")
        else:
            daily_summary = daily_data.sum(numeric_only=True)
            
            # --- 1. INDICADORES KPI CON COMPARATIVA ---
            st.subheader("Rendimiento vs Promedio Histórico")
            day_name = selected_date_daily.strftime('%A')
            # Mapeo de nombres de día de la semana de español a inglés para lookup
            day_map_es_en = {
                'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles', 
                'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
            }
            # strftime('%A') puede devolver nombres en el locale del sistema (español)
            # Hacemos una búsqueda para encontrar la clave en inglés
            day_name_en = next((en for en, es in day_map_es_en.items() if es.lower() == day_name.lower()), day_name)


            cols = st.columns(len(metric_labels))
            for i, (metric, label) in enumerate(metric_labels.items()):
                with cols[i]:
                    value = daily_summary.get(metric, 0)
                    avg_value = daily_avg.loc[day_name_en, metric] if day_name_en in daily_avg.index else 0
                    delta = f"{(value - avg_value):.1f}" if avg_value > 0 else None
                    st.metric(
                        label=label, 
                        value=f"{int(value)}",
                        delta=delta,
                        help=f"El promedio histórico para los {day_name} es {avg_value:.1f}"
                    )
            
            st.divider()

            # --- GRÁFICOS DE MEDIDOR (GAUGE) REINTEGRADOS ---
            st.subheader("Medidores de Volumen Diario")
            cols_gauge = st.columns(len(metric_labels))
            for i, (metric, label) in enumerate(metric_labels.items()):
                with cols_gauge[i]:
                    fig_gauge = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=daily_summary.get(metric, 0),
                        title={'text': label}
                    ))
                    fig_gauge.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
                    st.plotly_chart(fig_gauge, use_container_width=True, key=f"daily_gauge_reinstated_{metric}")

            st.divider()

            # --- 2. RANKING DE RECLUTADORES DEL DÍA ---
            st.subheader("Ranking de Reclutadores del Día")
            metric_to_rank = st.selectbox("Selecciona una métrica para el ranking:", options=list(metric_labels.keys()), format_func=lambda x: metric_labels[x], key="ranking_selector")
            
            ranking_data = daily_data.groupby('Reclutador')[metric_to_rank].sum().sort_values(ascending=False).reset_index()
            ranking_data = ranking_data[ranking_data[metric_to_rank] > 0]

            if ranking_data.empty:
                st.info(f"Nadie registró actividad para '{metric_labels[metric_to_rank]}' en este día.")
            else:
                fig_rank = go.Figure(go.Bar(
                    x=ranking_data['Reclutador'],
                    y=ranking_data[metric_to_rank],
                    text=ranking_data[metric_to_rank],
                    textposition='auto'
                ))
                fig_rank.update_layout(
                    title=f"Top Reclutadores por {metric_labels[metric_to_rank]}",
                    xaxis_title="Reclutador",
                    yaxis_title="Total"
                )
                st.plotly_chart(fig_rank, use_container_width=True)

            st.divider()

            # --- 3. TABLA DE RESUMEN DETALLADO ---
            st.subheader("Tabla de Resumen del Día")
            summary_table = daily_data.groupby('Reclutador')[list(metric_labels.keys())].sum()
            # Filtrar reclutadores sin actividad
            summary_table = summary_table[summary_table.sum(axis=1) > 0]
            if summary_table.empty:
                 st.info("No hay actividad registrada en la tabla de resumen.")
            else:
                st.dataframe(summary_table, use_container_width=True)


    # --- PESTAÑA SEMANAL ---
    with tab_weekly:
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
                with cols[i]:
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=weekly_summary.get(metric, 0),
                        title={'text': label}
                    ))
                    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
                    st.plotly_chart(fig, use_container_width=True, key=f"weekly_gauge_{metric}")

        st.divider()
        st.header("KPIs Acumulados por Semana")
        df_filtered['Week_Start'] = df_filtered['Fecha'].apply(get_thursday_week_range)
        weekly_kpis = df_filtered.groupby('Week_Start').sum(numeric_only=True).sort_index()
        
        if weekly_kpis.empty:
            st.warning("No hay suficientes datos históricos para mostrar KPIs acumulados.")
        else:
            cumulative_kpis = weekly_kpis.cumsum()
            kpi_cols = st.columns(len(metric_labels))
            for i, (metric, label) in enumerate(metric_labels.items()):
                with kpi_cols[i]:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=cumulative_kpis.index, y=cumulative_kpis[metric], fill='tozeroy', mode='lines', name=label))
                    fig.update_layout(title=f"Acumulado de {label}", height=300, margin=dict(l=20, r=20, t=40, b=20), xaxis_title=None, yaxis_title="Total")
                    st.plotly_chart(fig, use_container_width=True, key=f"weekly_kpi_{metric}")

    # --- PESTAÑA MENSUAL ---
    with tab_monthly:
        st.header("Análisis Mensual")
        df_filtered['MesAño'] = df_filtered['Fecha'].dt.strftime('%Y-%m')
        available_months = sorted(df_filtered['MesAño'].unique(), reverse=True)
        selected_month = st.selectbox("Selecciona un mes", options=available_months, key="monthly_selector")

        monthly_data = df_filtered[df_filtered['MesAño'] == selected_month]
        
        if monthly_data.empty:
            st.warning("No hay datos para el reclutador y el mes seleccionados.")
        else:
            monthly_summary = monthly_data.sum(numeric_only=True)
            cols = st.columns(len(metric_labels))
            for i, (metric, label) in enumerate(metric_labels.items()):
                with cols[i]:
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=monthly_summary.get(metric, 0),
                        title={'text': label}
                    ))
                    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
                    st.plotly_chart(fig, use_container_width=True, key=f"monthly_gauge_{metric}")

        st.divider()
        st.header("KPIs Acumulados por Mes")
        monthly_kpis = df_filtered.groupby('MesAño').sum(numeric_only=True).sort_index()
        
        if monthly_kpis.empty:
            st.warning("No hay suficientes datos históricos para mostrar KPIs acumulados.")
        else:
            cumulative_kpis_monthly = monthly_kpis.cumsum()
            kpi_cols = st.columns(len(metric_labels))
            for i, (metric, label) in enumerate(metric_labels.items()):
                with kpi_cols[i]:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=cumulative_kpis_monthly.index, y=cumulative_kpis_monthly[metric], fill='tozeroy', mode='lines', name=label))
                    fig.update_layout(title=f"Acumulado de {label}", height=300, margin=dict(l=20, r=20, t=40, b=20), xaxis_title=None, yaxis_title="Total")
                    st.plotly_chart(fig, use_container_width=True, key=f"monthly_kpi_{metric}")

    # --- PESTAÑA DE DOMINGOS ---
    with tab_sunday:
        st.header("Análisis de Publicaciones en Domingo")
        sunday_df = df[df['Fecha'].dt.weekday == 6].copy()
        
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
                total_pubs_sunday = sunday_df[sunday_df['Fecha'].dt.date == selected_sunday]['Publicaciones'].sum()
                st.metric(label=f"Total de Publicaciones del Domingo {selected_sunday.strftime('%d/%m/%Y')}", value=int(total_pubs_sunday))

            with col2:
                historical_sunday_pubs = sunday_df.groupby(sunday_df['Fecha'].dt.date)['Publicaciones'].sum().sort_index()
                fig_line = go.Figure()
                fig_line.add_trace(go.Scatter(x=historical_sunday_pubs.index, y=historical_sunday_pubs.values, mode='lines+markers', name='Publicaciones'))
                fig_line.update_layout(title="Tendencia de Publicaciones en Domingos", xaxis_title="Fecha", yaxis_title="Número de Publicaciones", height=350)
                st.plotly_chart(fig_line, use_container_width=True)
                
            st.divider()
            st.subheader(f"Desglose por Reclutador - {selected_sunday.strftime('%d/%m/%Y')}")
            sunday_detail_df = sunday_df[(sunday_df['Fecha'].dt.date == selected_sunday) & (sunday_df['Publicaciones'] > 0)][['Reclutador', 'Publicaciones']]

            if sunday_detail_df.empty:
                st.info("Ningún reclutador realizó publicaciones en el domingo seleccionado.")
            else:
                num_recruiters_posted = len(sunday_detail_df)
                cols = st.columns(min(num_recruiters_posted, 5)) 
                for i, row in enumerate(sunday_detail_df.itertuples()):
                    with cols[i % 5]:
                        st.metric(label=row.Reclutador, value=int(row.Publicaciones))
else:
    st.error("No se pudieron cargar los datos. Revisa la conexión y la configuración.")



