"""Utilidades geográficas: distancias, privacidad de coordenadas y alertas cercanas."""
from __future__ import annotations

import hashlib
import math

import numpy as np
import pandas as pd
import streamlit as st

from ecoalerta.config import (
    CONFIRM_HORAS, CONFIRM_RADIO_M, DESPLAZAMIENTO_M, ESTADO_CERRADO, ahora,
)


def haversine_m(lat, lon, lats, lons) -> np.ndarray:
    r = 6_371_000.0
    p1, p2 = math.radians(lat), np.radians(lats)
    dphi = p2 - p1
    dl = np.radians(lons) - math.radians(lon)
    a = np.sin(dphi / 2) ** 2 + math.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def _sal() -> str:
    try:
        return str(st.secrets["privacidad"]["sal"])
    except Exception:
        return "ecoalerta-sal-por-defecto"


def desplazar(lat: float, lon: float, semilla: str, metros: float = DESPLAZAMIENTO_M):
    h = hashlib.sha256(f"{_sal()}|{semilla}".encode()).digest()
    ang = int.from_bytes(h[:4], "big") / 2**32 * 2 * math.pi
    rad = (0.4 + 0.6 * int.from_bytes(h[4:8], "big") / 2**32) * metros
    dlat = rad * math.cos(ang) / 111_320
    dlon = rad * math.sin(ang) / (111_320 * math.cos(math.radians(lat)))
    return round(lat + dlat, 6), round(lon + dlon, 6)


def publicar(df: pd.DataFrame, staff: bool) -> pd.DataFrame:
    if staff or df.empty:
        return df
    out = df.copy()
    ok = out[["Latitud", "Longitud"]].notna().all(axis=1)
    if ok.any():
        nuevos = [desplazar(r.Latitud, r.Longitud, r.ID_Reporte) for r in out.loc[ok].itertuples()]
        out.loc[ok, "Latitud"] = [n[0] for n in nuevos]
        out.loc[ok, "Longitud"] = [n[1] for n in nuevos]
    return out


def recientes(df: pd.DataFrame, horas: int = CONFIRM_HORAS) -> pd.DataFrame:
    if df.empty:
        return df
    fecha = pd.to_datetime(df["Fecha_Hora"], errors="coerce")
    horas_pasadas = (ahora().replace(tzinfo=None) - fecha).dt.total_seconds() / 3600
    return df[(horas_pasadas <= horas).to_numpy()].dropna(subset=["Latitud", "Longitud"])


def cercanos(df: pd.DataFrame, lat: float, lon: float,
             radio: float = CONFIRM_RADIO_M, horas: int = CONFIRM_HORAS) -> pd.DataFrame:
    x = recientes(df, horas)
    if x.empty:
        return x
    x = x[x["Tipo_Registro"].astype(str).str.startswith("Denuncia")
          & (x["Estado_Atencion"].astype(str) != ESTADO_CERRADO)]
    if x.empty:
        return x
    dist = haversine_m(lat, lon, x["Latitud"].to_numpy(float), x["Longitud"].to_numpy(float))
    x = x.assign(Distancia_m=dist, Fecha=pd.to_datetime(x["Fecha_Hora"], errors="coerce"))
    return x[dist <= radio].sort_values("Distancia_m")
