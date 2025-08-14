## Esta pagina es dedicada a la comparativa entre el desempeño de los distintos equipos.
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pyairtable import Api
import numpy as np

st.set_page_config(
    page_title="Comparativa entre equipos ",
    page_icon="⚔️",
    layout="wide"
)

st.title("⚔️ Comparativa entre equipos de  ")
st.markdown("Visualiza el desempeño de cada reclutador con respecto a la semana, mes e historicamente.")

