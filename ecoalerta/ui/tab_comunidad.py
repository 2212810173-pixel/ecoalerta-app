from __future__ import annotations

from datetime import timedelta

import streamlit as st

from ecoalerta import analitica
from ecoalerta.config import PUNTOS_CONTROL, ahora
from ecoalerta.ui import components as ui


def render(df) -> None:
    st.markdown("### 🏅 Comunidad y cobertura")
    st.caption("Los datos ciudadanos son creíbles cuando cubren todas las horas y todos los sectores. "
               "Estos retos ayudan a lograrlo.")
    if df.empty:
        ui.vacio("🏅", "Aún no hay actividad", "Sé la primera persona en registrar una observación.")
        return

    d = analitica.preparar(df)
    ult30 = d[d["Fecha"] >= ahora().replace(tzinfo=None) - timedelta(days=30)]

    c1, c2 = st.columns([0.9, 1.1], gap="large")
    with c1:
        st.markdown("##### 🎯 Retos de cobertura horaria (últimos 30 días)")
        total = max(len(ult30), 1)
        cnt = ult30["Franja"].value_counts()
        pobres = []
        for f in analitica.FRANJAS:
            n = int(cnt.get(f, 0))
            share = n / total
            st.progress(min(1.0, share / 0.25),
                        text=f"{analitica.ICONO_FRANJA[f]} {f} ({analitica.RANGO_FRANJA[f]}): {n} registro(s)")
            if share < 0.10:
                pobres.append(f)
        if pobres:
            st.warning("🚩 **Reto activo:** faltan datos en " + ", ".join(pobres) +
                       ". Un registro en esas franjas vale doble para la calidad del análisis.")
        else:
            st.success("Cobertura horaria equilibrada. ¡Sigan así!")
    with c2:
        st.markdown("##### 🚩 Puntos de control: cobertura de la semana")
        st.dataframe(analitica.cobertura_puntos(d, PUNTOS_CONTROL), hide_index=True, use_container_width=True)
        st.caption("✅ = hubo al menos un registro en esa franja durante los últimos 7 días.")

    st.markdown("##### 🌿 Red de monitores")
    st.caption("Solo aparecen quienes ingresaron un alias y no marcaron *anónimo*.")
    rk = analitica.monitores(d)
    if rk.empty:
        st.info("Aún no hay monitores con alias. Registra con tu nombre o alias para sumar insignias.")
    else:
        st.dataframe(rk[["Alias", "Registros", "Dias", "Sectores", "Insignias", "Ultimo"]],
                     hide_index=True, use_container_width=True, column_config={
            "Dias": "Días activos", "Ultimo": st.column_config.DatetimeColumn("Último", format="DD/MM HH:mm"),
        })
    with st.expander("¿Cómo se ganan las insignias?"):
        for nombre, desc in analitica.CATALOGO_INSIGNIAS.items():
            st.markdown(f"**{nombre}**: {desc}")
        st.caption("Las insignias premian justo lo que corrige los sesgos: variedad de horarios y de sectores.")
