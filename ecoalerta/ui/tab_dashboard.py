from __future__ import annotations

import json
from datetime import timedelta

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_folium import st_folium

from ecoalerta import analitica, geo
from ecoalerta.config import COLOR_NIVEL, COLUMNAS_PRIVADAS, DOMINIOS, NIVELES, TIPOS_REGISTRO, ahora
from ecoalerta.ui import components as ui
from ecoalerta.ui.maps import mapa_dashboard

COLOR_FRANJA = {"Madrugada": "#6366f1", "Mañana": "#f59e0b", "Tarde": "#0f766e", "Noche": "#1e293b"}
COLOR_CICLO = {"Sin gestión": "#94a3b8", "En gestión": "#f59e0b", "Cerrado": "#16a34a"}


def _estilo(fig, alto: int):
    fig.update_layout(
        height=alto, margin=dict(t=40, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter"), title_font=dict(size=14), legend=dict(orientation="h", y=-0.18),
    )
    return fig


def _geojson(d: pd.DataFrame) -> str:
    feats = []
    for r in d.dropna(subset=["Latitud", "Longitud"]).to_dict("records"):
        pct = r.get("Indice_Riesgo_Pct")
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(r["Longitud"]), float(r["Latitud"])]},
            "properties": {
                "id": str(r.get("ID_Reporte", "")), "tipo": str(r.get("Tipo_Registro", "")),
                "dominio": str(r.get("Dominio_Ambiental", "")), "nivel": str(r.get("Nivel_Riesgo", "")),
                "pct": None if pd.isna(pct) else float(pct), "franja": str(r.get("Franja", "")),
                "confirmaciones": int(r.get("Confirmaciones", 0)),
                "lugar": str(r.get("Referencia_Lugar", "")), "fecha": str(r.get("Fecha_Hora", "")),
            },
        })
    return json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False, indent=2)


def render(df: pd.DataFrame, staff: bool) -> None:
    if df.empty:
        ui.vacio("🗺️", "Aún no hay datos para el dashboard", "Registra el primer reporte para ver el mapa y las métricas.")
        return

    base = analitica.preparar(df)

    with st.container(border=True):
        c1, c2, c3, c4, c5 = st.columns([1, 1, 1.2, 1, 0.6])
        f_tipo = c1.selectbox("Finalidad", ("Todos", *TIPOS_REGISTRO), key="d_tipo")
        f_dom = c2.selectbox("Dominio", ("Todos", *DOMINIOS), key="d_dom")
        f_niv = c3.multiselect("Nivel de riesgo", NIVELES, default=list(NIVELES), key="d_niv")
        f_per = c4.selectbox("Período", ("Todo", "Últimos 7 días", "Últimos 30 días"), key="d_per")
        calor = c5.toggle("Calor", value=True, key="d_calor")

    mask = base["Nivel_Riesgo"].isin(f_niv)
    if f_tipo != "Todos":
        mask &= base["Tipo_Registro"] == f_tipo
    if f_dom != "Todos":
        mask &= base["Dominio_Ambiental"] == f_dom
    dias = {"Últimos 7 días": 7, "Últimos 30 días": 30}.get(f_per)
    if dias:
        mask &= base["Fecha"] >= ahora().replace(tzinfo=None) - timedelta(days=dias)
    d = base[mask]
    if d.empty:
        st.warning("No hay registros con esos filtros.")
        return

    dp = geo.publicar(d, staff)
    fc = analitica.focos(d)
    gestion, cierre, n_den = analitica.tasa_gestion(d)

    es_den = d["Tipo_Registro"].astype(str).str.startswith("Denuncia")
    prom = d["Indice_Riesgo_Pct"].mean()
    prom_txt = f"{prom:.1f}%" if pd.notna(prom) else "0.0%"
    ui.fila_kpis([
        ("📋", len(d), "Registros"),
        ("🚨", int(es_den.sum()), "Denuncias"),
        ("📡", int((~es_den).sum()), "Monitoreos"),
        ("🔴", int((d["Nivel_Riesgo"] == "CRÍTICO").sum()), "Críticos"),
        ("📈", prom_txt, "Riesgo promedio"),
        ("🏛️", "—" if gestion is None else f"{gestion:.0f}%", "Denuncias gestionadas"),
    ])
    st.write("")

    avisos = analitica.advertencias(d)
    if avisos:
        with st.expander(f"🧪 Calidad de la muestra · {len(avisos)} aviso(s)",
                         expanded=any(t == "warning" for t, _ in avisos)):
            for t, msg in avisos:
                (st.warning if t == "warning" else st.info)(msg)
    else:
        st.caption("🧪 Muestra equilibrada en horarios y sectores.")

    col_mapa, col_graf = st.columns([1.25, 0.75], gap="large")
    with col_mapa:
        st_folium(mapa_dashboard(dp, calor, fc), height=470, use_container_width=True,
                  key="mapa_dash", returned_objects=[])
        if not staff:
            st.caption("🔒 Por privacidad, las ubicaciones públicas se desplazan unos metros respecto al punto real.")
    with col_graf:
        niv = d["Nivel_Riesgo"].value_counts().rename_axis("Nivel").reset_index(name="Cantidad")
        fig = px.pie(niv, values="Cantidad", names="Nivel", hole=0.6, color="Nivel",
                     color_discrete_map=COLOR_NIVEL, title="Niveles de riesgo")
        st.plotly_chart(_estilo(fig, 225), use_container_width=True, config={"displayModeBar": False})

        dom = d["Dominio_Ambiental"].value_counts().rename_axis("Dominio").reset_index(name="Cantidad")
        fig = px.bar(dom, x="Cantidad", y="Dominio", orientation="h", title="Registros por dominio",
                     color_discrete_sequence=["#0f766e"])
        fig.update_layout(yaxis_title="", xaxis_title="")
        st.plotly_chart(_estilo(fig, 225), use_container_width=True, config={"displayModeBar": False})

    g1, g2 = st.columns(2, gap="large")
    with g1:
        h = d.groupby("Hora").size().reindex(range(24), fill_value=0).rename_axis("Hora").reset_index(name="Registros")
        h["Franja"] = h["Hora"].map(analitica.franja_de)
        fig = px.bar(h, x="Hora", y="Registros", color="Franja", color_discrete_map=COLOR_FRANJA,
                     title="¿A qué hora se reporta? (detecta sesgo horario)")
        fig.update_layout(xaxis=dict(dtick=2), xaxis_title="Hora del día", legend_title="")
        st.plotly_chart(_estilo(fig, 290), use_container_width=True, config={"displayModeBar": False})
    with g2:
        if n_den:
            den = d[es_den]["Ciclo"].value_counts().reindex(["Sin gestión", "En gestión", "Cerrado"], fill_value=0)
            ciclo = den.rename_axis("Estado").reset_index(name="Denuncias")
            fig = px.bar(ciclo, x="Denuncias", y="Estado", orientation="h", color="Estado",
                         color_discrete_map=COLOR_CICLO, title=f"Ciclo de respuesta · {cierre:.0f}% cerradas")
            fig.update_layout(showlegend=False, yaxis_title="")
            st.plotly_chart(_estilo(fig, 290), use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Aún no hay denuncias en el filtro actual.")

    g3, g4 = st.columns(2, gap="large")
    with g3:
        serie = d.dropna(subset=["Fecha"]).assign(Día=lambda x: x["Fecha"].dt.date)
        if not serie.empty:
            s = serie.groupby(["Día", "Tipo_Registro"]).size().reset_index(name="Registros")
            fig = px.bar(s, x="Día", y="Registros", color="Tipo_Registro", title="Registros por día",
                         color_discrete_sequence=["#0f766e", "#f59e0b"])
            fig.update_layout(xaxis_title="", legend_title="")
            st.plotly_chart(_estilo(fig, 300), use_container_width=True, config={"displayModeBar": False})
    with g4:
        st.markdown("##### 🎯 Top 5 prioridades")
        st.caption("Prioridad = riesgo + respaldo comunitario (5 pts por confirmación, máx. 6).")
        top = d.sort_values("Prioridad", ascending=False).head(5)[
            ["ID_Reporte", "Referencia_Lugar", "Indice_Riesgo_Pct", "Confirmaciones", "Prioridad", "Estado_Atencion"]]
        st.dataframe(top, hide_index=True, use_container_width=True, column_config={
            "ID_Reporte": "Ticket", "Referencia_Lugar": "Lugar", "Estado_Atencion": "Estado",
            "Confirmaciones": st.column_config.NumberColumn("👥"),
            "Indice_Riesgo_Pct": st.column_config.ProgressColumn("Riesgo", min_value=0, max_value=100, format="%.0f%%"),
            "Prioridad": st.column_config.NumberColumn(format="%.0f"),
        })

    st.markdown("##### 🔁 Focos recurrentes (≥3 reportes en una celda de ~275 m)")
    if fc.empty:
        st.caption("Todavía no hay celdas con reportes repetidos. Cuando se acumulen, aparecerán aquí "
                   "como candidatas a medición instrumental.")
    else:
        st.dataframe(fc[["Referencia", "Reportes", "Riesgo_prom", "Confirmaciones", "Ultimo"]],
                     hide_index=True, use_container_width=True, column_config={
            "Riesgo_prom": st.column_config.ProgressColumn("Riesgo prom.", min_value=0, max_value=100, format="%.0f%%"),
            "Ultimo": st.column_config.DatetimeColumn("Último reporte", format="DD/MM HH:mm"),
        })

    with st.expander("📄 Ver tabla completa y exportar"):
        exp = dp.drop(columns=[c for c in ("Fecha", "Celda", "Ciclo") if c in dp.columns])
        if not staff:
            exp = exp.drop(columns=COLUMNAS_PRIVADAS, errors="ignore")
            st.caption("Los datos públicos excluyen alias y usan coordenadas desplazadas (~80 m).")
        st.dataframe(exp, hide_index=True, use_container_width=True)
        sello = ahora().strftime("%Y%m%d")
        e1, e2 = st.columns(2)
        e1.download_button("⬇️ Descargar CSV", exp.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"ecoalerta_{sello}.csv", mime="text/csv", use_container_width=True)
        e2.download_button("⬇️ Descargar GeoJSON", _geojson(dp), file_name=f"ecoalerta_{sello}.geojson",
                           mime="application/geo+json", use_container_width=True)
