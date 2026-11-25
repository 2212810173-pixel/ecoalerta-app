"""Servicios externos gratuitos y sin clave: clima (Open-Meteo) y dirección (Nominatim).
Todos fallan en silencio: la app nunca depende de ellos para guardar un registro."""
from __future__ import annotations

import requests
import streamlit as st

_CARD = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]


def cardinal(grados: float) -> str:
    return _CARD[int(((grados + 22.5) % 360) // 45)]


@st.cache_data(ttl=900, show_spinner=False)
def _clima(lat: float, lon: float):
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": lat, "longitude": lon, "wind_speed_unit": "kmh",
                    "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m",
                    "timezone": "America/Lima"},
            timeout=4,
        )
        r.raise_for_status()
        c = r.json()["current"]
        return {"viento": c["wind_speed_10m"], "dir": c["wind_direction_10m"],
                "temp": c["temperature_2m"], "hr": c["relative_humidity_2m"]}
    except Exception:
        return None


def clima_actual(lat: float, lon: float):
    return _clima(round(lat, 2), round(lon, 2))


def texto_clima(c: dict) -> str:
    return (f"Viento {c['viento']:.0f} km/h (desde {cardinal(c['dir'])}) · "
            f"{c['temp']:.0f} °C · HR {c['hr']:.0f} %")


def sugerencia_viento(c: dict) -> str:
    v = c["viento"]
    nivel = "calma o aire quieto" if v < 5 else "brisa ligera" if v < 20 else "viento moderado o fuerte"
    return f"🌤 Referencia automática: {texto_clima(c)} → sugiere *{nivel}*."


@st.cache_data(ttl=86400, show_spinner=False)
def _direccion(lat: float, lon: float):
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "jsonv2", "zoom": 18, "addressdetails": 1},
            headers={"User-Agent": "EcoAlerta-UNAH/9.0 (proyecto academico)"},
            timeout=4,
        )
        j = r.json()
        a = j.get("address", {})
        partes = [a.get("road"), a.get("neighbourhood") or a.get("suburb") or a.get("quarter")]
        txt = ", ".join(p for p in partes if p)
        return txt or j.get("display_name", "").split(",")[0] or None
    except Exception:
        return None


def referencia_sugerida(lat: float, lon: float):
    return _direccion(round(lat, 4), round(lon, 4))
