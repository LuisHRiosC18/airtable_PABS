import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pyairtable import Api
import numpy as np

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from pyairtable import Api
from scipy import stats

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Análisis de Desempeño", page_icon="🏆", layout="wide")
st.title("🏆 Análisis de Desempeño vs. Promedio Histórico")
st.markdown("Evalúa el rendimiento de cada reclutador comparado con la media histórica del equipo.")

# --- CONEXIÓN Y CARGA DE DATOS (Función reutilizada) ---
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
        if 'Reclutador' in df.columns:
            df['Reclutador'] = df['Reclutador'].str.strip()
        return df
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame()

df = load_data_from_airtable()

if not df.empty:
    st.sidebar.header("Filtros de Desempeño")
    
    # Filtro para el periodo de análisis
    analysis_period = st.sidebar.selectbox(
        "Analizar desempeño por:",
        ("Día", "Semana", "Mes")
    )

    # --- CÁLCULO DE PROMEDIOS HISTÓRICOS ---
    # Agrupamos por reclutador y fecha para obtener el total diario de cada uno
    daily_totals = df.groupby(['Reclutador', df['Fecha'].dt.date]).sum(numeric_only=True)
    
    # Calculamos la media y desviación estándar del rendimiento DIARIO por reclutador
    historical_mean = daily_totals.mean()
    historical_std = daily_totals.std()

    st.header(f"Análisis de Desempeño por {analysis_period}")
    
    # --- LÓGICA DE ANÁLISIS ---
    if analysis_period == "Día":
        target_date = st.sidebar.date_input("Selecciona el día", datetime.now().date())
        period_df = df[df['Fecha'].dt.date == target_date]
        grouped_data = period_df.groupby('Reclutador').sum(numeric_only=True)

    elif analysis_period == "Semana":
        target_date = st.sidebar.date_input("Selecciona una fecha en la semana", datetime.now().date())
        start_of_week = target_date - timedelta(days=target_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        st.info(f"Analizando la semana del {start_of_week.strftime('%d/%m/%Y')} al {end_of_week.strftime('%d/%m/%Y')}")
        period_df = df[(df['Fecha'].dt.date >= start_of_week) & (df['Fecha'].dt.date <= end_of_week)]
        # Calculamos el promedio diario para la semana
        grouped_data = period_df.groupby('Reclutador').mean(numeric_only=True)

    else: # Mes
        target_date = st.sidebar.date_input("Selecciona una fecha en el mes", datetime.now().date())
        st.info(f"Analizando el mes de {target_date.strftime('%B %Y')}")
        period_df = df[(df['Fecha'].dt.month == target_date.month) & (df['Fecha'].dt.year == target_date.year)]
        # Calculamos el promedio diario para el mes
        grouped_data = period_df.groupby('Reclutador').mean(numeric_only=True)

    # --- FUNCIÓN DE EVALUACIÓN ---
    def evaluate_performance(value, mean, std):
        if std == 0: # Si no hay variación, cualquier valor igual a la media es normal
            return "😐" if value == mean else "🙂"
        
        # Calculamos el Z-score: (valor - media) / desviación estándar
        z_score = (value - mean) / std
        
        if z_score > 0.5: # Más de media desviación estándar por encima de la media
            return "🙂"
        elif z_score < -0.5: # Más de media desviación estándar por debajo de la media
            return "😠"
        else: # Dentro del rango normal
            return "😐"

    # --- MOSTRAR RESULTADOS ---
    if grouped_data.empty:
        st.warning(f"No hay datos para el {analysis_period} seleccionado.")
    else:
        st.markdown(f"""
        A continuación se muestra el rendimiento promedio diario para cada reclutador en el periodo seleccionado.
        La evaluación se basa en la comparación con el rendimiento histórico promedio de **todo el equipo**.
        - 🙂: Rendimiento significativamente **superior** al promedio.
        - 😐: Rendimiento **dentro del rango** esperado.
        - 😠: Rendimiento significativamente **inferior** al promedio.
        """)
        
        metric_columns = ['Publicaciones', 'Contactos', 'Citas', 'Entrevistas', 'Aceptados']
        
        # Creamos una tabla para mostrar los resultados
        results_list = []
        for recruiter, data in grouped_data.iterrows():
            res = {"Reclutador": recruiter}
            for metric in metric_columns:
                value = data.get(metric, 0)
                mean = historical_mean.get(metric, 0)
                std = historical_std.get(metric, 0)
                emoji = evaluate_performance(value, mean, std)
                res[f"{metric} {emoji}"] = f"{value:.2f}"
            results_list.append(res)
        
        if results_list:
            results_df = pd.DataFrame(results_list).set_index("Reclutador")
            st.dataframe(results_df, use_container_width=True)

else:
    st.error("No se pudieron cargar los datos. Revisa la conexión y la configuración.")



