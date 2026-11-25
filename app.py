import streamlit as st

st.set_page_config(
    page_title="EcoAlerta · Aire y Ruido · UNAH",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="auto",
)

from ecoalerta import estado, repository
from ecoalerta.auth import es_staff
from ecoalerta.ui import components, sidebar, styles
from ecoalerta.ui import (
    tab_comunidad, tab_dashboard, tab_metodologia, tab_registro, tab_seguimiento,
)

estado.inicializar()
styles.inyectar()

df = repository.cargar_reportes()

sidebar.render(df)
components.hero(df)

t1, t2, t3, t4, t5 = st.tabs([
    "📝 Registrar", "🎫 Seguimiento", "🗺️ Mapa y análisis", "🏅 Comunidad", "📘 Metodología",
])
with t1:
    tab_registro.render(df)
with t2:
    tab_seguimiento.render(df)
with t3:
    tab_dashboard.render(df, es_staff())
with t4:
    tab_comunidad.render(df)
with t5:
    tab_metodologia.render()
