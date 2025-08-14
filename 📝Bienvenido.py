import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pyairtable import Api
import numpy as np

# Función para cargar datos
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
        # Asegurarse de que la columna Aceptados sea numérica
        if 'Aceptados' in df.columns:
            df['Aceptados'] = pd.to_numeric(df['Aceptados'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame()


st.set_page_config(
    page_title="Reclutamiento",
    page_icon="👋",
)

st.write("# Bienvenido a la pagina dedicada a Reclutamiento! 🙂‍↔️🙂‍↔️🙂‍↔️🙂‍↔️🙂‍↔️")

st.sidebar.success("Escoge la información que quieras ver.")

st.markdown(
    """
    En esta aplicación encontrarás información relacionada a reclutamiento de nuestra empresa.
    ### ¿Qué incluye? 🔥🔥🔥🔥🔥🔥🔥
    - Métricas del trabajo realizado por los reclutadores. 🦾🦾🦾
    - Comparativas entre los distintos equipos de reclutadores. 🫂🫂🫂
    - Pruebas de Hipotesis que comparan el desempeño a comparación del desempeño historico. ⚖️⚖️⚖️
    """
)

st.divider()

# KPI ACEPTADOS a chuparla guaarrrrrra 

st.header("KPI Histórico: Total de Aceptados por Mes")

df = load_data_from_airtable()

if not df.empty and 'Aceptados' in df.columns:
    # Asegurarse de que no haya fechas nulas
    df.dropna(subset=['Fecha'], inplace=True)
    
    # Crear una columna con el formato 'Año-Mes' para agrupar
    df['Mes'] = df['Fecha'].dt.to_period('M').astype(str)
    
    #Agrupamos por número de aceptados y sumamos perrrrrro
    monthly_accepted = df.groupby('Mes')['Aceptados'].sum().reset_index()
    
    if monthly_accepted.empty:
        st.warning("No hay datos de 'Aceptados' para mostrar.")
    else:
        fig = go.Figure(go.Lines(
            x=monthly_accepted['Mes'],
            y=monthly_accepted['Aceptados'],
            text=monthly_accepted['Aceptados'],
            textposition='auto',
            marker_color='indigo'
        ))
        
        fig.update_layout(
            title="Total de Candidatos Aceptados Mensualmente",
            xaxis_title="Mes",
            yaxis_title="Número de Aceptados",
            xaxis={'type': 'category'},
            height=450
        )
        st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No se pudieron cargar los datos o falta la columna 'Aceptados' para mostrar el KPI mensual.")


