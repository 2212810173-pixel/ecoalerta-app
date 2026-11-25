"""Motor de riesgo: lógica pura, sin Streamlit."""
from __future__ import annotations

from dataclasses import dataclass

from ecoalerta.catalogos import AIRE, RUIDO, criterios_activos, rango, usa_aire, usa_ruido
from ecoalerta.config import (
    COLOR_NIVEL, DOM_INTEGRAL, EMOJI_NIVEL, INTEGRAL_MODO, UMBRAL_CRITICO, UMBRAL_MODERADO,
)

POLITICA = {
    "BAJO": {
        True: ("Verificación programada (7-15 días)",
               "Alerta de baja severidad aparente; se recomienda registro de seguimiento y verificación."),
        False: ("Seguimiento periódico (30-90 días)",
                "Registro útil para línea base ambiental o vigilancia participativa sin alerta inmediata."),
    },
    "MODERADO": {
        True: ("Atención preventiva (5-15 días)",
               "Condición intermedia que amerita inspección preventiva, medición puntual o seguimiento vecinal."),
        False: ("Monitoreo focalizado (15-30 días)",
                "Condición intermedia que amerita inspección preventiva, medición puntual o seguimiento vecinal."),
    },
    "CRÍTICO": {
        True: ("Atención prioritaria (24-72 horas)",
               "Alerta alta: priorizar fiscalización municipal/OEFA y evaluación en campo."),
        False: ("Prioridad alta de monitoreo instrumental",
                "Zona de alta presión ambiental: priorizar despliegue de sensor/sonómetro o vigilancia continua."),
    },
}
ACCION_LIMPIA = ("Línea base limpia registrada. Este dato es tan valioso como una alerta: "
                 "permite distinguir los focos reales del ruido de fondo.")
CLASE_BADGE = {"BAJO": "b-bajo", "MODERADO": "b-moderado", "CRÍTICO": "b-critico"}


@dataclass(frozen=True)
class Resultado:
    bruto: int
    minimo: int
    maximo: int
    pct: float
    nivel: str
    plazo: str
    accion: str
    estado_inicial: str
    pts_aire: int | None
    pts_ruido: int | None
    sin_emision: bool = False

    @property
    def emoji(self) -> str:
        return EMOJI_NIVEL[self.nivel]

    @property
    def color(self) -> str:
        return COLOR_NIVEL[self.nivel]

    @property
    def clase_badge(self) -> str:
        return CLASE_BADGE[self.nivel]


def puntaje(criterios, respuestas: dict) -> int:
    return sum(c.opciones[respuestas[c.codigo]] for c in criterios)


def respuestas_minimas(criterios) -> dict:
    return {c.codigo: min(c.opciones, key=c.opciones.get) for c in criterios}


def clasificar(pct: float) -> str:
    if pct < UMBRAL_MODERADO:
        return "BAJO"
    return "MODERADO" if pct < UMBRAL_CRITICO else "CRÍTICO"


def _pct(bruto: int, minimo: int, maximo: int) -> float:
    denom = maximo - minimo
    return (bruto - minimo) / denom * 100 if denom > 0 else 0.0


def evaluar(tipo_registro: str, dominio: str, respuestas: dict, sin_emision: bool = False) -> Resultado:
    if sin_emision:
        respuestas = respuestas_minimas(AIRE + RUIDO)

    criterios = criterios_activos(dominio)
    minimo, maximo = rango(criterios)
    bruto = puntaje(criterios, respuestas)

    if dominio == DOM_INTEGRAL and INTEGRAL_MODO != "suma":
        pa = _pct(puntaje(AIRE, respuestas), *rango(AIRE))
        pr = _pct(puntaje(RUIDO, respuestas), *rango(RUIDO))
        pct = max(pa, pr) if INTEGRAL_MODO == "maximo" else (pa + pr) / 2
    else:
        pct = _pct(bruto, minimo, maximo)
    pct = round(pct, 1)

    nivel = clasificar(pct)
    es_denuncia = tipo_registro.startswith("Denuncia")
    plazo, accion = POLITICA[nivel][es_denuncia]
    prefijo = "Alerta registrada" if es_denuncia else "Monitoreo registrado"
    estado = f"{prefijo} · {plazo}"
    if sin_emision:
        accion, estado = ACCION_LIMPIA, f"Monitoreo registrado · línea base limpia · {plazo}"

    return Resultado(
        bruto=bruto, minimo=minimo, maximo=maximo, pct=pct, nivel=nivel, plazo=plazo,
        accion=accion, estado_inicial=estado, sin_emision=sin_emision,
        pts_aire=puntaje(AIRE, respuestas) if usa_aire(dominio) else None,
        pts_ruido=puntaje(RUIDO, respuestas) if usa_ruido(dominio) else None,
    )
