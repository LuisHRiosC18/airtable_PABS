import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pyairtable import Api

# --- CONFIGURACIÓN DE LA PÁGINA Y TÍTULO ---
st.set_page_config(
    page_title="Dashboard de Métricas de RH",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard de Desempeño del Equipo de Reclutamiento")
st.markdown("Visualiza el rendimiento diario, semanal y mensual del equipo.")

# --- CONEXIÓN A AIRTABLE Y CACHÉ DE DATOS ---
# Usamos st.cache_data para limitar las llamadas a la API.
# ttl (Time To Live) = 43200 segundos (12 horas). Los datos se refrescarán máximo 2 veces al día.
@st.cache_data(ttl=43200)
def load_data_from_airtable():
    """
    Carga los datos desde Airtable usando las credenciales de st.secrets.
    Convierte los datos a un DataFrame de Pandas y realiza una limpieza básica.
    """
    try:
        # Carga las credenciales desde el archivo secrets.toml
        api_key = st.secrets["airtable"]["api_key"]
        base_id = st.secrets["airtable"]["base_id"]
        table_name = st.secrets["airtable"]["table_name"]

        api = Api(api_key)
        table = api.table(base_id, table_name)
        
        # Obtenemos todos los registros de la tabla
        all_records = table.all()
        
        # Convertimos la lista de diccionarios a un DataFrame de Pandas
        df = pd.DataFrame([record['fields'] for record in all_records])

        # --- LIMPIEZA Y TRANSFORMACIÓN DE DATOS ---
        # Asegurarse de que la columna de fecha esté en el formato correcto
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')

        # Definir las columnas de métricas
        metric_columns = ['Publicaciones', 'Contactos', 'Citas', 'Entrevistas', 'Aceptados']
        
        # Convertir columnas de métricas a tipo numérico, manejando errores
        for col in metric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        return df
    except Exception as e:
        st.error(f"Error al cargar los datos desde Airtable: {e}")
        st.error("Por favor, verifica tus credenciales en el archivo .streamlit/secrets.toml y el nombre de tus columnas en Airtable.")
        return pd.DataFrame()

# --- FUNCIÓN ALTERNATIVA PARA CARGAR DATOS DESDE GITHUB (si se prefiere) ---
@st.cache_data
def load_data_from_github(url):
    """
    Carga los datos desde un archivo CSV alojado en GitHub.
    """
    try:
        df = pd.read_csv(url)
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        metric_columns = ['Publicaciones', 'Contactos', 'Citas', 'Entrevistas', 'Aceptados']
        for col in metric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Error al cargar el archivo CSV desde GitHub: {e}")
        return pd.DataFrame()

# --- FUNCIÓN PARA CREAR GRÁFICOS DE MEDIDOR (GAUGE) ---
def create_gauge_chart(value, goal, title):
    """
    Crea un gráfico de medidor (gauge) con Plotly.
    """
    if goal == 0: # Evitar división por cero
        goal = 1

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'size': 20}},
        gauge={
            'axis': {'range': [0, goal], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "#007BFF"}, # Color azul para la barra
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#E0E0E0",
            'steps': [
                {'range': [0, goal * 0.5], 'color': '#FADBD8'}, # Rojo claro
                {'range': [goal * 0.5, goal * 0.8], 'color': '#FCF3CF'}, # Amarillo claro
                {'range': [goal * 0.8, goal], 'color': '#D5F5E3'}  # Verde claro
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.9,
                'value': goal
            }
        }
    ))
    fig.update_layout(
        height=250, 
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

# --- CARGA DE DATOS ---
# Descomenta la línea de GitHub si prefieres usar esa opción
df = load_data_from_airtable()
# github_url = 'URL_RAW_DE_TU_CSV_EN_GITHUB'
# df = load_data_from_github(github_url)

# --- INTERFAZ DE USUARIO CON STREAMLIT ---
if not df.empty:
    st.sidebar.header("Filtros")

    # Filtro de Reclutador
    recruiters = sorted(df['Reclutador'].unique())
    selected_recruiter = st.sidebar.selectbox("Selecciona un Reclutador", ["Todos"] + recruiters)

    # Filtro de Fecha
    selected_date = st.sidebar.date_input("Selecciona una Fecha", datetime.now())

    # --- FILTRADO DE DATOS ---
    if selected_recruiter != "Todos":
        df_filtered = df[df['Reclutador'] == selected_recruiter].copy()
    else:
        df_filtered = df.copy()

    # --- DEFINICIÓN DE METAS ---
    # Metas diarias (fijas)
    daily_goals = {
        'Publicaciones': 5,
        'Contactos': 20,
        'Citas': 5,
        'Entrevistas': 2,
        'Aceptados': 1
    }

    # --- PESTAÑAS PARA VISTAS (DÍA, SEMANA, MES) ---
    tab_day, tab_week, tab_month = st.tabs(["Análisis del Día", "Análisis Semanal", "Análisis Mensual"])

    # --- VISTA DIARIA ---
    with tab_day:
        st.header(f"Desempeño para el día: {selected_date.strftime('%d de %B, %Y')}")
        
        daily_data = df_filtered[df_filtered['Fecha'].dt.date == selected_date]
        
        if daily_data.empty:
            st.warning("No hay datos para el reclutador y la fecha seleccionados.")
        else:
            # Agregamos los datos si hay múltiples entradas para el mismo día
            daily_summary = daily_data.sum(numeric_only=True)
            
            cols = st.columns(len(daily_goals))
            metric_keys = list(daily_goals.keys())
            
            for i, col in enumerate(cols):
                metric = metric_keys[i]
                value = daily_summary.get(metric, 0)
                goal = daily_goals[metric]
                with col:
                    st.plotly_chart(create_gauge_chart(value, goal, metric), use_container_width=True)

    # --- VISTA SEMANAL ---
    with tab_week:
        st.header(f"Desempeño Semanal (Semana de {selected_date.strftime('%d/%m/%Y')})")
        
        # Calcular inicio y fin de la semana (lunes a domingo)
        start_of_week = selected_date - timedelta(days=selected_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        st.info(f"Mostrando datos desde el {start_of_week.strftime('%d/%m/%Y')} al {end_of_week.strftime('%d/%m/%Y')}")

        weekly_data = df_filtered[
            (df_filtered['Fecha'].dt.date >= start_of_week) & 
            (df_filtered['Fecha'].dt.date <= end_of_week)
        ]
        
        if weekly_data.empty:
            st.warning("No hay datos para la semana seleccionada.")
        else:
            weekly_summary = weekly_data.sum(numeric_only=True)
            
            st.sidebar.subheader("Metas Semanales (Ajustables)")
            weekly_goals = {
                'Publicaciones': st.sidebar.number_input("Meta Semanal de Publicaciones", value=25, min_value=1),
                'Contactos': st.sidebar.number_input("Meta Semanal de Contactos", value=100, min_value=1),
                'Citas': st.sidebar.number_input("Meta Semanal de Citas", value=25, min_value=1),
                'Entrevistas': st.sidebar.number_input("Meta Semanal de Entrevistas", value=10, min_value=1),
                'Aceptados': st.sidebar.number_input("Meta Semanal de Aceptados", value=3, min_value=1)
            }
            
            cols = st.columns(len(weekly_goals))
            metric_keys = list(weekly_goals.keys())

            for i, col in enumerate(cols):
                metric = metric_keys[i]
                value = weekly_summary.get(metric, 0)
                goal = weekly_goals[metric]
                with col:
                    st.plotly_chart(create_gauge_chart(value, goal, metric), use_container_width=True)

    # --- VISTA MENSUAL ---
    with tab_month:
        st.header(f"Desempeño Mensual ({selected_date.strftime('%B %Y')})")
        
        monthly_data = df_filtered[
            (df_filtered['Fecha'].dt.month == selected_date.month) &
            (df_filtered['Fecha'].dt.year == selected_date.year)
        ]
        
        if monthly_data.empty:
            st.warning("No hay datos para el mes seleccionado.")
        else:
            monthly_summary = monthly_data.sum(numeric_only=True)

            st.sidebar.subheader("Metas Mensuales (Ajustables)")
            monthly_goals = {
                'Publicaciones': st.sidebar.number_input("Meta Mensual de Publicaciones", value=100, min_value=1),
                'Contactos': st.sidebar.number_input("Meta Mensual de Contactos", value=400, min_value=1),
                'Citas': st.sidebar.number_input("Meta Mensual de Citas", value=100, min_value=1),
                'Entrevistas': st.sidebar.number_input("Meta Mensual de Entrevistas", value=40, min_value=1),
                'Aceptados': st.sidebar.number_input("Meta Mensual de Aceptados", value=10, min_value=1)
            }

            cols = st.columns(len(monthly_goals))
            metric_keys = list(monthly_goals.keys())

            for i, col in enumerate(cols):
                metric = metric_keys[i]
                value = monthly_summary.get(metric, 0)
                goal = monthly_goals[metric]
                with col:
                    st.plotly_chart(create_gauge_chart(value, goal, metric), use_container_width=True)

else:
    st.error("No se pudieron cargar los datos. Revisa la configuración y la conexión.")
