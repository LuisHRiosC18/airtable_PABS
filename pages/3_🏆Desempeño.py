import streamlit as st
import pandas as pd
import numpy as np
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
        return df
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame()
# --- FIN: Función de carga ---

def get_thursday_week_range(date_obj):
    """Calcula el rango de semana de Jueves a Miércoles para una fecha dada."""
    days_since_thursday = (date_obj.weekday() - 3 + 7) % 7
    start_of_week = date_obj - timedelta(days=days_since_thursday)
    return start_of_week

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Análisis de Desempeño", page_icon="👍", layout="wide")
st.title("👍 Análisis de Desempeño vs. Promedio Histórico")

df = load_data_from_airtable()

if not df.empty:
    st.sidebar.header("Filtros de Desempeño")
    analysis_period = st.sidebar.selectbox("Analizar desempeño por:", ("Semana", "Mes"))

    # --- CÁLCULO DE PROMEDIOS HISTÓRICOS ---
    df['Week_Start'] = df['Fecha'].apply(get_thursday_week_range)
    df['Month_Start'] = df['Fecha'].dt.to_period('M').apply(lambda p: p.start_time).dt.date
    
    weekly_historical = df.groupby(['Reclutador', 'Week_Start']).sum(numeric_only=True)
    monthly_historical = df.groupby(['Reclutador', 'Month_Start']).sum(numeric_only=True)

    # Media y std del total por periodo para todo el equipo
    historical_mean_weekly = weekly_historical.mean()
    historical_std_weekly = weekly_historical.std()
    historical_mean_monthly = monthly_historical.mean()
    historical_std_monthly = monthly_historical.std()

    st.header(f"Análisis de Desempeño Total por {analysis_period}")

    grouped_data = pd.DataFrame()
    if analysis_period == "Semana":
        target_date = st.sidebar.date_input("Selecciona una fecha en la semana", datetime.now().date())
        start_of_week = get_thursday_week_range(target_date)
        end_of_week = start_of_week + timedelta(days=6)
        st.info(f"Analizando la semana del **Jueves, {start_of_week.strftime('%d/%m/%Y')}** al **Miércoles, {end_of_week.strftime('%d/%m/%Y')}**")
        period_df = df[(df['Fecha'].dt.date >= start_of_week) & (df['Fecha'].dt.date <= end_of_week)]
        grouped_data = period_df.groupby('Reclutador').sum(numeric_only=True)
        historical_mean, historical_std = historical_mean_weekly, historical_std_weekly
    else: # Mes
        target_date = st.sidebar.date_input("Selecciona una fecha en el mes", datetime.now().date())
        st.info(f"Analizando el mes de {target_date.strftime('%B %Y')}")
        period_df = df[(df['Fecha'].dt.month == target_date.month) & (df['Fecha'].dt.year == target_date.year)]
        grouped_data = period_df.groupby('Reclutador').sum(numeric_only=True)
        historical_mean, historical_std = historical_mean_monthly, historical_std_monthly

    def evaluate_performance(value, mean, std):
        if std == 0 or pd.isna(std): return "😐"
        z_score = (value - mean) / std
        if z_score > 0.75: return "🙂"
        elif z_score < -0.75: return "😠"
        else: return "😐"

    if grouped_data.empty:
        st.warning(f"No hay datos para el {analysis_period} seleccionado.")
    else:
        st.markdown(f"Se muestra el **total de métricas** para cada reclutador en el periodo seleccionado. La evaluación (emoji) compara este total con el rendimiento histórico.")
        metric_columns = ['Publicaciones', 'Contactos', 'Citas', 'Entrevistas', 'Aceptados']
        
        results_list = []
        for recruiter, data in grouped_data.iterrows():
            res = {"Reclutador": recruiter}
            for metric in metric_columns:
                value = data.get(metric, 0)
                mean = historical_mean.get(metric, 0)
                std = historical_std.get(metric, 0)
                emoji = evaluate_performance(value, mean, std)
                res[metric] = f"{int(value)} {emoji}"
            results_list.append(res)
        
        if results_list:
            results_df = pd.DataFrame(results_list).set_index("Reclutador")
            st.dataframe(results_df, use_container_width=True)

        # --- SECCIÓN DE GRÁFICOS DE RADAR (SOLO PARA VISTA SEMANAL) ---
        if analysis_period == "Semana":
            st.divider()
            st.header("Análisis del Embudo de Reclutamiento de la Semana")
            
            weekly_summary = period_df.groupby('Reclutador').sum(numeric_only=True)
            if not weekly_summary.empty:
                # Calcular tasas de conversión para la semana
                weekly_summary['Pub_a_Contacto'] = np.divide(weekly_summary['Contactos'], weekly_summary['Publicaciones'], where=weekly_summary['Publicaciones']!=0, out=np.zeros_like(weekly_summary['Contactos'], dtype=float)) * 100
                weekly_summary['Cont_a_Cita'] = np.divide(weekly_summary['Citas'], weekly_summary['Contactos'], where=weekly_summary['Contactos']!=0, out=np.zeros_like(weekly_summary['Citas'], dtype=float)) * 100
                weekly_summary['Cita_a_Entrevista'] = np.divide(weekly_summary['Entrevistas'], weekly_summary['Citas'], where=weekly_summary['Citas']!=0, out=np.zeros_like(weekly_summary['Entrevistas'], dtype=float)) * 100
                weekly_summary['Ent_a_Aceptado'] = np.divide(weekly_summary['Aceptados'], weekly_summary['Entrevistas'], where=weekly_summary['Entrevistas']!=0, out=np.zeros_like(weekly_summary['Aceptados'], dtype=float)) * 100

                conversion_metrics = ['Pub_a_Contacto', 'Cont_a_Cita', 'Cita_a_Entrevista', 'Ent_a_Aceptado']
                conversion_labels = ['Pub. a Contactos (%)', 'Cont. a Citas (%)', 'Citas a Entrev. (%)', 'Entrev. a Acept. (%)']
                
                num_recruiters = len(weekly_summary.index)
                cols = st.columns(min(num_recruiters, 3))
                
                for i, recruiter_name in enumerate(weekly_summary.index):
                    with cols[i % 3]:
                        values = weekly_summary.loc[recruiter_name, conversion_metrics].values
                        fig_radar = go.Figure(go.Scatterpolar(r=values, theta=conversion_labels, fill='toself', name=recruiter_name))
                        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, title=f"Embudo de {recruiter_name}", height=400)
                        st.plotly_chart(fig_radar, use_container_width=True)
            else:
                st.info("No hay suficientes datos en esta semana para generar los gráficos de embudo.")

else:
    st.error("No se pudieron cargar los datos.")

