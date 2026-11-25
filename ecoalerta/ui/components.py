"""Componentes visuales reutilizables."""
from __future__ import annotations

import html as _html

import streamlit as st

from ecoalerta import analitica
from ecoalerta.config import APP_NOMBRE, APP_VERSION
from ecoalerta.scoring import Resultado


def esc(x) -> str:
    return _html.escape(str(x))


def md(html: str) -> None:
    limpio = " ".join(l.strip() for l in html.strip().splitlines() if l.strip())
    st.markdown(limpio, unsafe_allow_html=True)


def hero(df) -> None:
    n = len(df)
    crit = int((df["Nivel_Riesgo"] == "CRÍTICO").sum()) if n else 0
    gestion = analitica.tasa_gestion(analitica.preparar(df))[0] if n else None
    g_txt = "—" if gestion is None else f"{gestion:.0f}%"
    md(f"""
    <div class="eco-hero">
      <div>
        <div class="eco-title">🌿 {APP_NOMBRE} <span class="eco-ver">v{APP_VERSION}</span></div>
        <p>Vigilancia ambiental participativa de aire y ruido en Huanta. Tu observación de 2 minutos
        ayuda a decidir dónde medir primero.</p>
      </div>
      <div class="eco-hstats">
        <div class="eco-hs"><div class="eco-hs-v">{n}</div><div class="eco-hs-l">Registros</div></div>
        <div class="eco-hs"><div class="eco-hs-v">{crit}</div><div class="eco-hs-l">Críticos</div></div>
        <div class="eco-hs"><div class="eco-hs-v">{g_txt}</div><div class="eco-hs-l">Denuncias gestionadas</div></div>
      </div>
    </div>""")


def paso(numero, titulo: str, subtitulo: str = "") -> None:
    sub = f'<div class="eco-step-s">{esc(subtitulo)}</div>' if subtitulo else ""
    md(f"""
    <div class="eco-step">
      <div class="eco-step-n">{numero}</div>
      <div><div class="eco-step-t">{esc(titulo)}</div>{sub}</div>
    </div>""")


def como_funciona() -> None:
    md("""
    <div class="eco-how">
      <div><b>1 · Elige</b> si es una denuncia o un monitoreo, y qué evalúas.</div>
      <div><b>2 · Responde</b> lo que ves, hueles o escuchas. Sin trámites y puedes ser anónimo.</div>
      <div><b>3 · Marca</b> el lugar (o usa tu GPS) y recibe tu ticket de seguimiento.</div>
    </div>""")


def kpi(icono: str, valor, etiqueta: str) -> None:
    md(f"""
    <div class="eco-kpi">
      <div class="eco-kpi-ico">{icono}</div>
      <div><div class="eco-kpi-v">{esc(valor)}</div><div class="eco-kpi-l">{esc(etiqueta)}</div></div>
    </div>""")


def fila_kpis(items: list[tuple]) -> None:
    for col, (ico, val, lab) in zip(st.columns(len(items)), items):
        with col:
            kpi(ico, val, lab)


def medidor(res: Resultado) -> None:
    pct = max(0.0, min(100.0, res.pct))
    md(f"""
    <div class="eco-meter-box">
      <div class="eco-meter-head">
        <div>
          <div class="eco-meter-pct" style="color:{res.color}">{pct:.0f}%</div>
          <div class="eco-kpi-l">Índice de riesgo · {res.bruto}/{res.maximo} pts</div>
        </div>
        <span class="eco-badge {res.clase_badge}">{res.emoji} {res.nivel}</span>
      </div>
      <div class="eco-meter-track"><div class="eco-meter-marker" style="left:{pct}%"></div></div>
      <div class="eco-meter-scale"><span>Bajo</span><span>Moderado</span><span>Crítico</span></div>
      <div class="eco-meter-hint">⏱ {esc(res.plazo)}</div>
    </div>""")


def tarjeta_resultado(ticket: str, res: Resultado, tipo: str, dominio: str) -> None:
    md(f"""
    <div class="eco-result" style="--nivel:{res.color}">
      <div class="eco-result-top">
        <span class="eco-badge {res.clase_badge}">{res.emoji} {res.nivel} · {res.pct}% ({res.bruto}/{res.maximo} pts)</span>
        <span class="eco-ok">✅ Registro guardado</span>
      </div>
      <div class="eco-meta">
        <span><b>Ticket</b><code>{esc(ticket)}</code></span>
        <span><b>Tipo</b>{esc(tipo)}</span>
        <span><b>Dominio</b>{esc(dominio)}</span>
      </div>
      <div class="eco-meta">
        <span><b>Plazo sugerido</b>{esc(res.plazo)}</span>
        <span><b>Estado</b>{esc(res.estado_inicial)}</span>
      </div>
      <p class="eco-action">{esc(res.accion)}</p>
    </div>""")


def checklist(items: list[tuple[bool, str]]) -> None:
    li = "".join(f'<li class="{"ok" if ok else "no"}">{"✓" if ok else "○"} {esc(t)}</li>' for ok, t in items)
    md(f'<ul class="eco-check">{li}</ul>')


def precision_gps(metros) -> None:
    if metros is None:
        return
    if metros <= 20:
        c, t = "#16a34a", "Excelente"
    elif metros <= 50:
        c, t = "#d97706", "Aceptable"
    else:
        c, t = "#dc2626", "Baja · ajusta el punto en el mapa"
    md(f'<span class="eco-badge" style="background:{c}22;color:{c}">📡 Precisión GPS ±{metros:.0f} m · {t}</span>')


def timeline(historial) -> None:
    if not isinstance(historial, str):
        return
    pasos = [p.strip() for p in historial.split(" || ") if p.strip()]
    if not pasos:
        return
    items = "".join(f'<div class="eco-tl-i"><span class="eco-tl-d"></span><div>{esc(p)}</div></div>' for p in pasos)
    md(f'<div class="eco-tl">{items}</div>')


def vacio(icono: str, titulo: str, texto: str = "") -> None:
    md(f"""
    <div class="eco-empty">
      <div class="eco-empty-ico">{icono}</div>
      <div class="eco-empty-t">{esc(titulo)}</div>
      <div class="eco-empty-s">{esc(texto)}</div>
    </div>""")
