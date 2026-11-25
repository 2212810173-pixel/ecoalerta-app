from __future__ import annotations

import folium
import pandas as pd
from folium.plugins import Fullscreen, HeatMap, LocateControl

from ecoalerta.config import (
    COLOR_NIVEL, EMOJI_NIVEL, HUANTA_LAT, HUANTA_LON, LIMITES_MAPA, NIVELES, PUNTOS_CONTROL,
)
from ecoalerta.ui.components import esc

ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"


def dentro_de_limites(lat: float, lon: float) -> bool:
    lat_min, lon_min, lat_max, lon_max = LIMITES_MAPA
    return lat_min <= lat <= lat_max and lon_min <= lon <= lon_max


def _base(zoom: int, centro=(HUANTA_LAT, HUANTA_LON)) -> folium.Map:
    m = folium.Map(location=list(centro), zoom_start=zoom, tiles="CartoDB positron", control_scale=True)
    folium.TileLayer("OpenStreetMap", name="Calles (OSM)").add_to(m)
    folium.TileLayer(ESRI, attr="Esri World Imagery", name="Satélite").add_to(m)
    Fullscreen(position="topleft").add_to(m)
    return m


def _capa_puntos_control(m: folium.Map) -> None:
    capa = folium.FeatureGroup(name="🚩 Puntos de control")
    for p in PUNTOS_CONTROL:
        folium.Marker([p["lat"], p["lon"]], tooltip=f"{p['codigo']} · {p['nombre']}",
                      icon=folium.Icon(color="blue", icon="flag")).add_to(capa)
    capa.add_to(m)


def mapa_registro(lat, lon, recientes: pd.DataFrame, centro=None):
    lat0, lon0, zoom = centro or (HUANTA_LAT, HUANTA_LON, 15)
    m = _base(zoom, (lat0, lon0))
    LocateControl(auto_start=False, flyTo=True, strings={"title": "Mi ubicación"}).add_to(m)
    _capa_puntos_control(m)

    cap = folium.FeatureGroup(name="🟠 Reportes recientes (72 h)")
    for r in recientes.to_dict("records"):
        folium.CircleMarker(
            [r["Latitud"], r["Longitud"]], radius=6, color="#ea580c", weight=2, fill=True,
            fill_color="#fb923c", fill_opacity=0.7,
            tooltip=f"{r.get('Nivel_Riesgo', '')} · {esc(r.get('Referencia_Lugar', ''))}",
        ).add_to(cap)
    cap.add_to(m)
    folium.LayerControl(position="topright").add_to(m)

    grupo = folium.FeatureGroup(name="Punto seleccionado")
    if lat is not None and lon is not None:
        grupo.add_child(folium.Marker(
            [lat, lon], tooltip="Ubicación seleccionada", popup=f"{lat:.5f}, {lon:.5f}",
            icon=folium.Icon(color="red", icon="map-marker"),
        ))
    return m, grupo


_LEYENDA = """
<div style="position:fixed;bottom:24px;left:24px;z-index:9999;background:rgba(255,255,255,.95);
 padding:10px 14px;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,.2);font:600 12px Inter,sans-serif;color:#0f172a">
 <div style="margin-bottom:4px">Nivel de riesgo</div>{filas}
 <div style="margin-top:4px"><span style="display:inline-block;width:10px;height:10px;border:2px dashed #7c3aed;
 border-radius:50%;margin-right:6px"></span>Foco recurrente</div></div>
"""


def mapa_dashboard(df: pd.DataFrame, calor: bool = True, focos: pd.DataFrame | None = None) -> folium.Map:
    m = _base(zoom=14)
    pts = df.dropna(subset=["Latitud", "Longitud"])

    grupos = {n: folium.FeatureGroup(name=f"{EMOJI_NIVEL[n]} {n.title()}") for n in NIVELES}
    radios = {"BAJO": 7, "MODERADO": 10, "CRÍTICO": 13}
    calor_data = []

    for r in pts.to_dict("records"):
        nivel = r.get("Nivel_Riesgo") if r.get("Nivel_Riesgo") in NIVELES else "BAJO"
        color = COLOR_NIVEL[nivel]
        pct = r.get("Indice_Riesgo_Pct")
        peso = 0.5 if pd.isna(pct) else max(0.15, min(1.0, float(pct) / 100))
        calor_data.append([r["Latitud"], r["Longitud"], peso])
        conf = int(r.get("Confirmaciones") or 0)
        popup = (
            f"<b>{esc(r.get('ID_Reporte', '-'))}</b><br>{esc(r.get('Referencia_Lugar', ''))}<br>"
            f"<b>Tipo:</b> {esc(r.get('Tipo_Registro', ''))}<br>"
            f"<b>Dominio:</b> {esc(r.get('Dominio_Ambiental', ''))}<br>"
            f"<b>Riesgo:</b> {nivel} ({'' if pd.isna(pct) else f'{pct:.0f}'}%)<br>"
            f"<b>Confirmaciones:</b> {conf}"
        )
        folium.CircleMarker(
            [r["Latitud"], r["Longitud"]], radius=radios[nivel], color=color, weight=2,
            fill=True, fill_color=color, fill_opacity=0.75,
            popup=folium.Popup(popup, max_width=280),
            tooltip=f"{nivel} · {esc(r.get('Referencia_Lugar', ''))}",
        ).add_to(grupos[nivel])

    for g in grupos.values():
        g.add_to(m)
    if calor and calor_data:
        HeatMap(calor_data, name="🔥 Mapa de calor", radius=26, blur=18, min_opacity=0.3).add_to(m)

    if focos is not None and not focos.empty:
        cf = folium.FeatureGroup(name="🔁 Focos recurrentes")
        for f in focos.to_dict("records"):
            folium.Circle(
                [f["Lat"], f["Lon"]], radius=140, color="#7c3aed", weight=2, dash_array="6",
                fill=True, fill_opacity=0.06,
                tooltip=f"Foco: {esc(f['Referencia'])} · {f['Reportes']} reportes · riesgo {f['Riesgo_prom']:.0f}%",
            ).add_to(cf)
        cf.add_to(m)

    _capa_puntos_control(m)
    folium.LayerControl(position="topright").add_to(m)

    filas = "".join(
        f'<div><span style="display:inline-block;width:10px;height:10px;border-radius:50%;'
        f'background:{COLOR_NIVEL[n]};margin-right:6px"></span>{n.title()}</div>' for n in NIVELES)
    m.get_root().html.add_child(folium.Element(_LEYENDA.format(filas=filas)))

    if not pts.empty:
        m.fit_bounds([[pts["Latitud"].min(), pts["Longitud"].min()],
                      [pts["Latitud"].max(), pts["Longitud"].max()]], max_zoom=16, padding=(30, 30))
    return m
