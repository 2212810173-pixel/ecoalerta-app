from __future__ import annotations

import pandas as pd
import streamlit as st

from ecoalerta import servicios
from ecoalerta.auth import es_staff
from ecoalerta.catalogos import AIRE, RUIDO
from ecoalerta.config import ESTADOS_ATENCION, NIVELES
from ecoalerta.ui import components as ui

COLS = ["ID_Reporte", "Fecha_Hora", "Tipo_Registro", "Dominio_Ambiental", "Referencia_Lugar",
        "Nivel_Riesgo", "Indice_Riesgo_Pct", "Confirmaciones", "Estado_Atencion"]


def _s(v) -> str:
    return "—" if pd.isna(v) or v == "" else str(v)


def _detalle(f: pd.Series, staff: bool) -> None:
    st.markdown(f"#### Ticket `{f['ID_Reporte']}`")
    ui.md(f"""
    <div class="eco-result" style="--nivel:#0d9488">
      <div class="eco-meta" style="margin-top:0">
        <span><b>Fecha</b>{ui.esc(_s(f['Fecha_Hora']))}</span>
        <span><b>Tipo</b>{ui.esc(_s(f['Tipo_Registro']))}</span>
        <span><b>Dominio</b>{ui.esc(_s(f['Dominio_Ambiental']))}</span>
        <span><b>Riesgo</b>{ui.esc(_s(f['Nivel_Riesgo']))} · {ui.esc(_s(f['Indice_Riesgo_Pct']))}%</span>
      </div>
      <div class="eco-meta">
        <span><b>Lugar</b>{ui.esc(_s(f['Referencia_Lugar']))}</span>
        <span><b>Plazo</b>{ui.esc(_s(f['Plazo_Sugerido']))}</span>
        <span><b>Confirmaciones</b>{int(f['Confirmaciones'] or 0)}</span>
      </div>
    </div>""")

    st.markdown("##### 🧭 Trazabilidad")
    ui.timeline(f["Historial_Estados"] if isinstance(f["Historial_Estados"], str)
                else f"{f['Fecha_Hora']} · {f['Estado_Atencion']}")
    if isinstance(f["Nota_Institucional"], str) and f["Nota_Institucional"].strip():
        st.info(f"**Respuesta institucional:** {f['Nota_Institucional']}", icon="🏛️")

    with st.expander("Ver respuestas del formulario"):
        for c in AIRE + RUIDO:
            v = f.get(c.columna)
            if isinstance(v, str) and v and not v.startswith("No aplica"):
                st.markdown(f"**{c.codigo} · {c.etiqueta}**: {v}")
        st.caption(f"Momento: {_s(f['Momento_Observacion'])} · Meteo: {_s(f['Meteo_Auto'])} · "
                   f"Punto de control: {_s(f['Punto_Control'])}")
        st.caption(f"Datos técnicos: {_s(f['Datos_Tecnicos_Extra'])} · Evidencia: {_s(f['Evidencia_Foto'])}")
        if staff:
            st.caption(f"Observación: {_s(f['Observaciones'])} · Reportante: {_s(f['Usuario_Inspector'])}")

    if staff:
        if pd.notna(f["Latitud"]) and pd.notna(f["Longitud"]):
            st.link_button("🧭 Abrir ubicación exacta en Google Maps",
                           f"https://www.google.com/maps?q={f['Latitud']},{f['Longitud']}")
        st.markdown("##### Gestionar estado")
        actual = f["Estado_Atencion"]
        idx = ESTADOS_ATENCION.index(actual) if actual in ESTADOS_ATENCION else 0
        nuevo = st.selectbox("Nuevo estado", ESTADOS_ATENCION, index=idx, key=f"est_{f['ID_Reporte']}")
        nota = st.text_area("Nota para el ciudadano (opcional, será visible)", key=f"nota_{f['ID_Reporte']}",
                            max_chars=300, height=70,
                            placeholder="Ej. Se programó medición con sonómetro para el jueves.")
        if st.button("Actualizar estado", type="primary"):
            try:
                if servicios.cambiar_estado(f["ID_Reporte"], nuevo, nota):
                    st.success("Estado actualizado.")
                    st.rerun()
                else:
                    st.error("No se encontró el ticket.")
            except Exception as e:
                st.error(f"No se pudo actualizar: {e}")
    else:
        st.caption("🔒 La ubicación exacta y la gestión de estados son solo para personal autorizado.")


def render(df: pd.DataFrame) -> None:
    st.markdown("### 🎫 Seguimiento y trazabilidad")
    if df.empty:
        ui.vacio("🎫", "Aún no hay registros", "Cuando se guarde el primero aparecerá aquí.")
        return

    c1, c2 = st.columns([2, 1])
    q = c1.text_input("Buscar por ticket o referencia", value=st.session_state.ultimo_ticket or "",
                      placeholder="Ej. ECO-250101-101500-A3 o Mercado")
    niveles = c2.multiselect("Nivel de riesgo", NIVELES, default=list(NIVELES))

    f = df[df["Nivel_Riesgo"].isin(niveles) | df["Nivel_Riesgo"].isna()]
    if q.strip():
        t = q.strip().lower()
        f = f[f["ID_Reporte"].astype(str).str.lower().str.contains(t, regex=False, na=False)
              | f["Referencia_Lugar"].astype(str).str.lower().str.contains(t, regex=False, na=False)]
    f = f.sort_values("Fecha_Hora", ascending=False)

    if f.empty:
        st.warning("Ningún registro coincide con la búsqueda.")
        return

    vista = f[COLS].reset_index(drop=True)
    vista["Confirmaciones"] = vista["Confirmaciones"].fillna(0).astype(int)
    st.caption(f"{len(vista)} registro(s) · selecciona una fila para ver el detalle")
    ev = st.dataframe(
        vista, hide_index=True, use_container_width=True, key="tabla_seg",
        on_select="rerun", selection_mode="single-row",
        column_config={
            "ID_Reporte": "Ticket", "Fecha_Hora": "Fecha", "Tipo_Registro": "Finalidad",
            "Dominio_Ambiental": "Dominio", "Referencia_Lugar": "Lugar", "Nivel_Riesgo": "Nivel",
            "Confirmaciones": st.column_config.NumberColumn("👥", help="Confirmaciones comunitarias"),
            "Estado_Atencion": "Estado",
            "Indice_Riesgo_Pct": st.column_config.ProgressColumn("Riesgo", min_value=0, max_value=100, format="%.0f%%"),
        },
    )
    filas = ev.selection.rows
    if filas:
        id_sel = vista.iloc[filas[0]]["ID_Reporte"]
        _detalle(df[df["ID_Reporte"] == id_sel].iloc[0], es_staff())
    elif es_staff():
        st.info("Selecciona un ticket de la tabla para gestionar su estado.")
