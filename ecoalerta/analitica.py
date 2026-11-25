"""Analítica de calidad de muestra: sesgos horario/espacial, focos, cobertura e insignias."""
from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd

from ecoalerta.config import (
    CELDA_GRADOS, ESTADO_CERRADO, ESTADOS_EN_GESTION, MIN_FOCO, MIN_MUESTRA, ahora,
)
from ecoalerta.geo import haversine_m

FRANJAS = ("Madrugada", "Mañana", "Tarde", "Noche")
ICONO_FRANJA = {"Madrugada": "🌌", "Mañana": "🌅", "Tarde": "☀️", "Noche": "🌙"}
RANGO_FRANJA = {"Madrugada": "0–5 h", "Mañana": "6–11 h", "Tarde": "12–17 h", "Noche": "18–23 h"}


def franja_de(h) -> str | None:
    if pd.isna(h):
        return None
    h = int(h)
    return "Madrugada" if h < 6 else "Mañana" if h < 12 else "Tarde" if h < 18 else "Noche"


def categoria_estado(e) -> str:
    e = str(e)
    if e == ESTADO_CERRADO:
        return "Cerrado"
    return "En gestión" if e in ESTADOS_EN_GESTION else "Sin gestión"


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["Fecha"] = pd.to_datetime(d["Fecha_Hora"], errors="coerce")
    d["Hora"] = d["Fecha"].dt.hour
    d["Franja"] = d["Hora"].map(franja_de)
    d["Confirmaciones"] = d["Confirmaciones"].fillna(0).astype(int)
    lat_c = (d["Latitud"] / CELDA_GRADOS).round()
    lon_c = (d["Longitud"] / CELDA_GRADOS).round()
    d["Celda"] = np.where(
        lat_c.notna() & lon_c.notna(),
        lat_c.fillna(0).astype(int).astype(str) + "_" + lon_c.fillna(0).astype(int).astype(str),
        None,
    )
    d["Ciclo"] = d["Estado_Atencion"].map(categoria_estado)
    d["Prioridad"] = (d["Indice_Riesgo_Pct"].fillna(0)
                      + 5 * d["Confirmaciones"].clip(upper=6)).clip(upper=100).round(1)
    return d


def tasa_gestion(d: pd.DataFrame):
    den = d[d["Tipo_Registro"].astype(str).str.startswith("Denuncia")]
    if den.empty:
        return None, None, 0
    gestion = (den["Ciclo"] != "Sin gestión").mean() * 100
    cierre = (den["Ciclo"] == "Cerrado").mean() * 100
    return gestion, cierre, len(den)


def focos(d: pd.DataFrame, minimo: int = MIN_FOCO) -> pd.DataFrame:
    x = d.dropna(subset=["Celda"])
    if x.empty:
        return pd.DataFrame()
    g = x.groupby("Celda").agg(
        Reportes=("ID_Reporte", "count"),
        Riesgo_prom=("Indice_Riesgo_Pct", "mean"),
        Confirmaciones=("Confirmaciones", "sum"),
        Lat=("Latitud", "mean"), Lon=("Longitud", "mean"),
        Ultimo=("Fecha", "max"),
        Referencia=("Referencia_Lugar", lambda s: s.mode().iat[0] if not s.mode().empty else ""),
    )
    g = g[g["Reportes"] >= minimo].sort_values(["Riesgo_prom", "Reportes"], ascending=False)
    return g.reset_index()


def advertencias(d: pd.DataFrame) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    n = len(d)
    if n < MIN_MUESTRA:
        out.append(("info", f"Muestra pequeña ({n} de {MIN_MUESTRA} registros recomendados): "
                            "interpreta los resultados como indicativos."))
    if n < 10:
        return out
    fr = d["Franja"].value_counts(normalize=True)
    if not fr.empty and fr.iloc[0] > 0.6:
        out.append(("warning", f"**Sesgo horario:** el {fr.iloc[0]*100:.0f} % de los registros ocurre en la franja "
                               f"*{fr.index[0]}*. Puede sobrerrepresentar episodios de mala dispersión atmosférica."))
    faltan = [f for f in FRANJAS if fr.get(f, 0) < 0.10]
    if faltan:
        out.append(("info", "**Poca cobertura horaria:** " + ", ".join(f"{f} ({RANGO_FRANJA[f]})" for f in faltan)
                            + ". Programa rondas de monitoreo en esos horarios."))
    ce = d["Celda"].value_counts(normalize=True)
    if not ce.empty and ce.iloc[0] > 0.5 and d["Celda"].nunique() > 1:
        out.append(("warning", f"**Sesgo espacial:** el {ce.iloc[0]*100:.0f} % de los registros proviene de una sola "
                               "celda de ~275 m. La densidad puede reflejar participación y no severidad."))
    if d["Celda"].nunique() < 3:
        out.append(("info", "Menos de 3 sectores con datos: la cobertura territorial es limitada."))
    if not d["Tipo_Registro"].astype(str).str.startswith("Monitoreo").any():
        out.append(("info", "No hay registros de **Monitoreo / Línea Base**: sin ellos no hay punto de comparación."))
    return out


def cobertura_puntos(d: pd.DataFrame, puntos, dias: int = 7, radio: float = 150) -> pd.DataFrame:
    corte = ahora().replace(tzinfo=None) - timedelta(days=dias)
    rec = d[d["Fecha"] >= corte]
    filas = []
    for p in puntos:
        if rec.empty:
            sub = rec
        else:
            con_geo = rec.dropna(subset=["Latitud", "Longitud"])
            dist = haversine_m(p["lat"], p["lon"], con_geo["Latitud"].to_numpy(float),
                               con_geo["Longitud"].to_numpy(float))
            sub = con_geo[(dist <= radio) | (con_geo["Punto_Control"] == p["codigo"])]
        fila = {"Punto": f"{p['codigo']} · {p['nombre']}", f"Registros ({dias} d)": len(sub)}
        for f in FRANJAS:
            fila[f"{ICONO_FRANJA[f]} {f}"] = "✅" if (sub["Franja"] == f).any() else "—"
        fila["Última"] = sub["Fecha"].max().strftime("%d/%m %H:%M") if len(sub) else "Sin datos"
        filas.append(fila)
    return pd.DataFrame(filas)


def monitores(d: pd.DataFrame) -> pd.DataFrame:
    x = d[(d["Anonimo"] == "No") & d["Usuario_Inspector"].notna()
          & ~d["Usuario_Inspector"].isin(["No especificado", "Anónimo"])].copy()
    if x.empty:
        return pd.DataFrame()
    x["Alias"] = x["Usuario_Inspector"].astype(str).str.strip()
    x["clave"] = x["Alias"].str.lower()
    g = x.groupby("clave").agg(
        Alias=("Alias", "first"), Registros=("ID_Reporte", "count"),
        Dias=("Fecha", lambda s: s.dt.date.nunique()), Sectores=("Celda", "nunique"),
        Nocturnos=("Franja", lambda s: s.isin(["Noche", "Madrugada"]).sum()),
        Ultimo=("Fecha", "max"),
    ).reset_index(drop=True)
    g["Insignias"] = g.apply(_insignias, axis=1)
    return g.sort_values(["Registros", "Dias"], ascending=False).reset_index(drop=True)


CATALOGO_INSIGNIAS = {
    "🌱 Primer aporte": "Registraste tu primera observación.",
    "📡 Monitor constante": "5 o más registros en al menos 3 días distintos.",
    "🧭 Explorador": "Registros en 3 o más sectores distintos (reduce el sesgo espacial).",
    "🌙 Guardián nocturno": "Registraste de noche o madrugada (las franjas con menos datos).",
    "🏅 Vigía ambiental": "15 o más registros.",
}


def _insignias(r) -> str:
    b = []
    if r.Registros >= 1:
        b.append("🌱")
    if r.Registros >= 5 and r.Dias >= 3:
        b.append("📡")
    if r.Sectores >= 3:
        b.append("🧭")
    if r.Nocturnos >= 1:
        b.append("🌙")
    if r.Registros >= 15:
        b.append("🏅")
    return " ".join(b)
