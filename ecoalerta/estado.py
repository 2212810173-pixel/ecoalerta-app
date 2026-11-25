import random
import streamlit as st

_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _nuevo_codigo() -> str:
    return "".join(random.choice(_CHARS) for _ in range(5))


def inicializar() -> None:
    por_defecto = {
        "lat": None, "lon": None, "centro": None,
        "gps_aplicado": None, "gps_precision": None,
        "captcha_codigo": _nuevo_codigo(),
        "ultimo_ticket": None, "ultimo_resultado": None,
        "form_n": 0,
        "map_n": 0,
        "ultimo_envio": 0.0, "staff": False, "confirmados": set(),
    }
    for k, v in por_defecto.items():
        st.session_state.setdefault(k, v)


def limpiar_punto() -> None:
    st.session_state.lat = None
    st.session_state.lon = None
    st.session_state.centro = None
    st.session_state.gps_precision = None
    st.session_state.map_n += 1


def fijar_punto(lat: float, lon: float, precision=None, zoom: int = 17) -> None:
    st.session_state.lat, st.session_state.lon = lat, lon
    st.session_state.gps_precision = precision
    st.session_state.centro = (lat, lon, zoom)
    st.session_state.map_n += 1


def nuevo_formulario() -> None:
    limpiar_punto()
    st.session_state.form_n += 1
    st.session_state.captcha_a = random.randint(2, 9)
    st.session_state.captcha_b = random.randint(1, 8)
    st.session_state.captcha_codigo = _nuevo_codigo()
