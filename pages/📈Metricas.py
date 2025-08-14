import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pyairtable import Api
import numpy as np

# --- CONFIGURACIÓN DE LA PÁGINA Y TÍTULO ---
st.set_page_config(
    page_title="Dashboard de Métricas de RH",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard de Desempeño del Equipo de Reclutamiento")
st.markdown("Visualiza el rendimiento diario, semanal y mensual, y compara el desempeño histórico del equipo.")

# --- CONEXIÓN A AIRTABLE Y CACHÉ DE DATOS ---
@st.cache_data(ttl=43200)
def load_data_from_airtable():
    """
    Carga los datos desde Airtable usando las credenciales de st.secrets.
    Convierte los datos a un DataFrame de Pandas y realiza una limpieza básica.
    """
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
        return df
    except Exception as e:
        st.error(f"Error al cargar los datos desde Airtable: {e}")
        st.error("Por favor, verifica tus credenciales en .streamlit/secrets.toml y los nombres de tus columnas en Airtable.")
        return pd.DataFrame()

# --- FUNCIÓN PARA CREAR GRÁFICOS DE MEDIDOR (GAUGE) ---
def create_gauge_chart(value, goal, title):
    """
    Crea un gráfico de medidor (gauge) con Plotly.
    """
    if goal == 0: goal = 1
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'size': 20}},
        gauge={
            'axis': {'range': [0, goal], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "#007BFF"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#E0E0E0",
            'steps': [
                {'range': [0, goal * 0.5], 'color': '#FADBD8'},
                {'range': [goal * 0.5, goal * 0.8], 'color': '#FCF3CF'},
                {'range': [goal * 0.8, goal], 'color': '#D5F5E3'}
            ],
            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.9, 'value': goal}
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
    return fig

# --- CARGA DE DATOS ---
df = load_data_from_airtable()

# --- INTERFAZ DE USUARIO CON STREAMLIT ---
if not df.empty:
    st.sidebar.header("Filtros Principales")
    recruiters = sorted(df['Reclutador'].unique())
    selected_recruiter = st.sidebar.selectbox("Selecciona un Reclutador", ["Todos"] + recruiters)
    selected_date = st.sidebar.date_input("Selecciona una Fecha de Referencia", datetime.now())

    # --- FILTRADO DE DATOS ---
    if selected_recruiter != "Todos":
        df_filtered = df[df['Reclutador'] == selected_recruiter].copy()
    else:
        df_filtered = df.copy()

    daily_goals = {'Publicaciones': 30, 'Contactos': 25, 'Citas': 2, 'Entrevistas': 1, 'Aceptados': 1}

    # --- PESTAÑAS PARA VISTAS (DÍA, SEMANA, MES) ---
    tab_day, tab_week, tab_month = st.tabs(["Análisis del Día", "Análisis Semanal", "Análisis Mensual"])

    with tab_day:
        st.header(f"Desempeño para el día: {selected_date.strftime('%d de %B, %Y')}")
        daily_data = df_filtered[df_filtered['Fecha'].dt.date == selected_date]
        if daily_data.empty:
            st.warning("No hay datos para el reclutador y la fecha seleccionados.")
        else:
            daily_summary = daily_data.sum(numeric_only=True)
            cols = st.columns(len(daily_goals))
            for i, col in enumerate(cols):
                metric = list(daily_goals.keys())[i]
                value = daily_summary.get(metric, 0)
                goal = daily_goals[metric]
                with col:
                    st.plotly_chart(create_gauge_chart(value, goal, metric), use_container_width=True)

    with tab_week:
        st.header(f"Desempeño Semanal (Semana de {selected_date.strftime('%d/%m/%Y')})")
        start_of_week = selected_date - timedelta(days=selected_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        st.info(f"Mostrando datos desde el {start_of_week.strftime('%d/%m/%Y')} al {end_of_week.strftime('%d/%m/%Y')}")
        weekly_data = df_filtered[(df_filtered['Fecha'].dt.date >= start_of_week) & (df_filtered['Fecha'].dt.date <= end_of_week)]
        if weekly_data.empty:
            st.warning("No hay datos para la semana seleccionada.")
        else:
            weekly_summary = weekly_data.sum(numeric_only=True)
            st.sidebar.subheader("Metas Semanales (Ajustables)")
            weekly_goals = {
                'Publicaciones': st.sidebar.number_input("Meta Semanal de Publicaciones", value=25, min_value=1, key='w_pub'),
                'Contactos': st.sidebar.number_input("Meta Semanal de Contactos", value=100, min_value=1, key='w_con'),
                'Citas': st.sidebar.number_input("Meta Semanal de Citas", value=25, min_value=1, key='w_cit'),
                'Entrevistas': st.sidebar.number_input("Meta Semanal de Entrevistas", value=10, min_value=1, key='w_ent'),
                'Aceptados': st.sidebar.number_input("Meta Semanal de Aceptados", value=3, min_value=1, key='w_ace')
            }
            cols = st.columns(len(weekly_goals))
            for i, col in enumerate(cols):
                metric = list(weekly_goals.keys())[i]
                value = weekly_summary.get(metric, 0)
                goal = weekly_goals[metric]
                with col:
                    st.plotly_chart(create_gauge_chart(value, goal, metric), use_container_width=True)

    with tab_month:
        st.header(f"Desempeño Mensual ({selected_date.strftime('%B %Y')})")
        monthly_data = df_filtered[(df_filtered['Fecha'].dt.month == selected_date.month) & (df_filtered['Fecha'].dt.year == selected_date.year)]
        if monthly_data.empty:
            st.warning("No hay datos para el mes seleccionado.")
        else:
            monthly_summary = monthly_data.sum(numeric_only=True)
            st.sidebar.subheader("Metas Mensuales (Ajustables)")
            monthly_goals = {
                'Publicaciones': st.sidebar.number_input("Meta Mensual de Publicaciones", value=100, min_value=1, key='m_pub'),
                'Contactos': st.sidebar.number_input("Meta Mensual de Contactos", value=400, min_value=1, key='m_con'),
                'Citas': st.sidebar.number_input("Meta Mensual de Citas", value=100, min_value=1, key='m_cit'),
                'Entrevistas': st.sidebar.number_input("Meta Mensual de Entrevistas", value=40, min_value=1, key='m_ent'),
                'Aceptados': st.sidebar.number_input("Meta Mensual de Aceptados", value=10, min_value=1, key='m_ace')
            }
            cols = st.columns(len(monthly_goals))
            for i, col in enumerate(cols):
                metric = list(monthly_goals.keys())[i]
                value = monthly_summary.get(metric, 0)
                goal = monthly_goals[metric]
                with col:
                    st.plotly_chart(create_gauge_chart(value, goal, metric), use_container_width=True)

    st.divider()

    # --- SECCIÓN DE ANÁLISIS COMPARATIVO ---
    st.header("Análisis Comparativo por Métrica")
    
    # Filtro de periodo para la comparación
    time_range = st.selectbox(
        "Selecciona el periodo de comparación",
        ("Últimos 7 días", "Últimos 30 días", "Este Mes", "Todo el Histórico")
    )

    # Filtrar datos según el periodo seleccionado
    today = datetime.now().date()
    if time_range == "Últimos 7 días":
        start_date = today - timedelta(days=7)
        comparison_df = df[df['Fecha'].dt.date >= start_date]
    elif time_range == "Últimos 30 días":
        start_date = today - timedelta(days=30)
        comparison_df = df[df['Fecha'].dt.date >= start_date]
    elif time_range == "Este Mes":
        comparison_df = df[(df['Fecha'].dt.month == today.month) & (df['Fecha'].dt.year == today.year)]
    else: # Todo el Histórico
        comparison_df = df

    # Agrupar por reclutador y sumar métricas
    comparison_summary = comparison_df.groupby('Reclutador').sum(numeric_only=True)
    
    if comparison_summary.empty:
        st.warning(f"No hay datos para el periodo '{time_range}'.")
    else:
        # Crear el gráfico de barras agrupado
        fig_comp = go.Figure()
        metrics_to_compare = ['Publicaciones', 'Contactos', 'Citas', 'Entrevistas', 'Aceptados']
        
        for metric in metrics_to_compare:
            fig_comp.add_trace(go.Bar(
                name=metric,
                x=comparison_summary.index,
                y=comparison_summary[metric]
            ))

        fig_comp.update_layout(
            barmode='group',
            title=f"Comparativa de Reclutadores ({time_range})",
            xaxis_title="Reclutador",
            yaxis_title="Cantidad",
            legend_title="Métricas",
            height=500
        )
        st.plotly_chart(fig_comp, use_container_width=True)

    st.divider()

    # --- SECCIÓN DE ANÁLISIS DE EMBUDO (RADAR) ---
    st.header("Análisis Histórico del Embudo de Reclutamiento (Tasas de Conversión)")
    st.markdown("Estos gráficos muestran la eficiencia de cada reclutador en las distintas fases del proceso, basado en todos los datos históricos.")

    # Calcular totales históricos por reclutador
    historical_summary = df.groupby('Reclutador').sum(numeric_only=True)

    # Calcular tasas de conversión
    # Se usa np.divide para manejar divisiones por cero de forma segura, resultando en 0
    historical_summary['Pub_a_Contacto'] = np.divide(historical_summary['Contactos'], historical_summary['Publicaciones'], where=historical_summary['Publicaciones']!=0, out=np.zeros_like(historical_summary['Contactos'], dtype=float)) * 100
    historical_summary['Cont_a_Cita'] = np.divide(historical_summary['Citas'], historical_summary['Contactos'], where=historical_summary['Contactos']!=0, out=np.zeros_like(historical_summary['Citas'], dtype=float)) * 100
    historical_summary['Cita_a_Entrevista'] = np.divide(historical_summary['Entrevistas'], historical_summary['Citas'], where=historical_summary['Citas']!=0, out=np.zeros_like(historical_summary['Entrevistas'], dtype=float)) * 100
    historical_summary['Ent_a_Aceptado'] = np.divide(historical_summary['Aceptados'], historical_summary['Entrevistas'], where=historical_summary['Entrevistas']!=0, out=np.zeros_like(historical_summary['Aceptados'], dtype=float)) * 100

    conversion_metrics = ['Pub_a_Contacto', 'Cont_a_Cita', 'Cita_a_Entrevista', 'Ent_a_Aceptado']
    conversion_labels = ['Publicaciones a Contactos (%)', 'Contactos a Citas (%)', 'Citas a Entrevistas (%)', 'Entrevistas a Aceptados (%)']

    # Crear un gráfico de radar para cada reclutador
    if not historical_summary.empty:
        num_recruiters = len(historical_summary.index)
        cols = st.columns(min(num_recruiters, 3)) # Mostrar máximo 3 gráficos por fila
        
        for i, recruiter_name in enumerate(historical_summary.index):
            with cols[i % 3]:
                fig_radar = go.Figure()
                
                values = historical_summary.loc[recruiter_name, conversion_metrics].values
                
                fig_radar.add_trace(go.Scatterpolar(
                    r=values,
                    theta=conversion_labels,
                    fill='toself',
                    name=recruiter_name
                ))
                
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 100] # El rango es de 0 a 100%
                        )),
                    showlegend=False,
                    title=f"Embudo de {recruiter_name}",
                    height=400
                )
                st.plotly_chart(fig_radar, use_container_width=True)
    else:
        st.warning("No hay datos históricos suficientes para generar los gráficos de embudo.")

else:
    st.error("No se pudieron cargar los datos. Revisa la configuración y la conexión.")

