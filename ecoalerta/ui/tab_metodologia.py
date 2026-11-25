import pandas as pd
import streamlit as st

from ecoalerta.catalogos import AIRE, RUIDO, rango
from ecoalerta.config import INTEGRAL_MODO, UMBRAL_CRITICO, UMBRAL_MODERADO
from ecoalerta.ui import components as ui


def _tabla_criterios(criterios) -> None:
    mn, mx = rango(criterios)
    st.caption(f"{len(criterios)} criterios · puntaje posible: {mn} a {mx} pts")
    for c in criterios:
        with st.expander(f"{c.codigo} · {c.etiqueta}"):
            st.dataframe(pd.DataFrame({"Opción": list(c.opciones), "Puntos": list(c.opciones.values())}),
                         hide_index=True, use_container_width=True)


LECCIONES = [
    ("Sin opción «sin olor» (OdourCollect)", "No había línea base limpia.",
     "Interruptor «Todo normal» en Monitoreo: registra 0 % y cuenta como dato."),
    ("Reportes retrospectivos (Smell Pittsburgh)", "Hora y lugar mal recordados.",
     "Campo «¿Cuándo lo observaste?», hora Lima automática y meteorología solo si es «Ahora mismo»."),
    ("Sesgo horario (Pittsburgh, Los Álamos)", "Reportes concentrados en la mañana.",
     "Gráfico por hora, avisos automáticos y retos de cobertura por franja."),
    ("Sesgo espacial (Pittsburgh, Los Álamos)", "La densidad refleja activismo, no severidad.",
     "Celdas de ~275 m, aviso de concentración, focos recurrentes y puntos de control."),
    ("Participación espontánea baja (Los Álamos)", "Solo 20 usuarios; se pasó a monitores con ruta.",
     "Puntos de control, modo «Monitor con experiencia» y tabla de cobertura semanal."),
    ("Percepción subjetiva (Chile, Applied Sciences 2025)", "Residentes más sensibles que inspectores.",
     "Criterios observables, viento automático y lectura sonora referencial."),
    ("Exposición de domicilios (Pittsburgh)", "Riesgo de identificar al denunciante.",
     "Coordenadas públicas desplazadas con sal secreta; alias fuera del CSV público."),
    ("Ciclo sin cierre (Reporta Residuos)", "Respuesta municipal heterogénea.",
     "Historial del ticket, nota institucional y KPI de denuncias gestionadas/cerradas."),
    ("Fatiga de participación (Smoke Sense)", "Cae el compromiso tras el entusiasmo inicial.",
     "Insignias ligadas a corregir sesgos y retos visibles."),
    ("Límite de peticiones HTTP 429", "Caída por lecturas excesivas.",
     "Caché de 45 s y respaldo con los últimos datos conocidos."),
]


def render() -> None:
    st.markdown("### 📘 Metodología y marco normativo")
    ui.md("""
    <div class="eco-result" style="--nivel:#0d9488">
      <p style="margin:0">EcoAlerta es una herramienta de <b>tamizaje participativo</b>: prioriza zonas y orienta
      la vigilancia, pero <b>no reemplaza</b> mediciones instrumentales acreditadas ni la fiscalización oficial.
      Separa <b>Denuncia / Alerta</b> de <b>Monitoreo / Línea Base</b> y adapta el cuestionario a
      <b>Calidad del Aire</b> y <b>Ruido Ambiental</b>.</p>
    </div>""")
    st.write("")

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("##### Índice de riesgo normalizado")
        st.latex(r"\text{Índice}(\%)=\frac{P-P_{min}}{P_{max}-P_{min}}\times 100")
        st.caption(f"P = suma de puntos de los criterios activos. Modo Integral: **{INTEGRAL_MODO}** "
                   "(suma = compatible con registros históricos; promedio/máximo = más equilibrado entre dominios).")
        st.latex(r"\text{Prioridad}=\min\big(100,\ \text{Índice}+5\cdot\min(\text{Confirmaciones},6)\big)")
    with c2:
        st.markdown("##### Niveles de riesgo")
        st.dataframe(pd.DataFrame([
            {"Nivel": "🟢 BAJO", "Rango": f"< {UMBRAL_MODERADO:.0f}%", "Lectura": "Línea base / seguimiento"},
            {"Nivel": "🟡 MODERADO", "Rango": f"{UMBRAL_MODERADO:.0f}% – {UMBRAL_CRITICO:.0f}%", "Lectura": "Inspección o medición puntual"},
            {"Nivel": "🔴 CRÍTICO", "Rango": f"≥ {UMBRAL_CRITICO:.0f}%", "Lectura": "Atención prioritaria"},
        ]), hide_index=True, use_container_width=True)

    st.markdown("##### Lecciones de proyectos similares incorporadas")
    st.dataframe(pd.DataFrame(LECCIONES, columns=["Antecedente", "Problema documentado", "Solución en EcoAlerta"]),
                 hide_index=True, use_container_width=True)

    st.markdown("##### Criterios y puntajes")
    t_aire, t_ruido = st.tabs(["💨 Aire", "🔊 Ruido"])
    with t_aire:
        _tabla_criterios(AIRE)
    with t_ruido:
        _tabla_criterios(RUIDO)

    st.markdown("##### Limitaciones")
    st.markdown(
        "- El micrófono del celular entrega **dB referenciales sin ponderación A**; no son dBA certificados.\n"
        "- La meteorología (Open-Meteo) es un modelo de la zona, no una medición en el punto exacto.\n"
        "- La evidencia fotográfica se comprime y sella, pero **su archivo no se almacena en el servidor**; "
        "solo se guarda su descripción y huella SHA-256.\n"
        "- Los reportes voluntarios son anecdóticos y sesgables: usa siempre el panel *Calidad de la muestra*."
    )

    st.markdown("##### Marco normativo")
    st.dataframe(pd.DataFrame([
        {"Eje": "Calidad del Aire", "Base técnica / normativa": "D.S. N° 003-2017-MINAM, R.M. N° 182-2016-MINAM, escala Ringelmann, Beaufort, FIDOL, OMS"},
        {"Eje": "Ruido Ambiental", "Base técnica / normativa": "D.S. N° 085-2003-PCM (ECA Ruido) y evaluación sensorial / instrumental de molestia sonora"},
        {"Eje": "Gobernanza y participación", "Base técnica / normativa": "Constitución (Art. 2.17), Ley N° 28611, Ley N° 28245 / SINIA, ciencia ciudadana"},
    ]), hide_index=True, use_container_width=True)
