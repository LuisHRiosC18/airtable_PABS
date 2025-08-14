import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pyairtable import Api
import numpy as np

st.set_page_config(
    page_title="Desempeño Relcutadores ",
    page_icon="🏆",
    layout="wide"
)

st.title("📊 Visualiza el desempeño ")
st.markdown("Visualiza el desempeño de cada reclutador con respecto a la semana, mes e historicamente.")

