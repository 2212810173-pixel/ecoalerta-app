"""Casos de uso: orquestan scoring + persistencia."""
from __future__ import annotations

import secrets
from dataclasses import dataclass

import pandas as pd

from ecoalerta import repository
from ecoalerta.catalogos import AIRE, RUIDO, usa_aire, usa_ruido
from ecoalerta.config import COLUMNAS, TEXTO_SIN_EMISION, ahora
from ecoalerta.scoring import Resultado, evaluar

SEP_HIST = " || "


@dataclass
class SolicitudRegistro:
    tipo_registro: str
    dominio: str
    nivel_experiencia: str
    rol: str
    alias: str
    anonimo: bool
    referencia: str
    observaciones: str
    respuestas: dict
    datos_tecnicos: str
    lat: float
    lon: float
    evidencia: str
    sin_emision: bool = False
    momento: str = "Ahora mismo"
    punto_control: str | None = None
    precision_gps: float | None = None
    meteo: str = "No disponible"


def _txt(v) -> str:
    return "" if pd.isna(v) else str(v)


def _entero(v) -> int:
    return 0 if pd.isna(v) else int(v)


def generar_ticket() -> str:
    return f"ECO-{ahora():%y%m%d-%H%M%S}-{secrets.token_hex(1).upper()}"


def registrar(s: SolicitudRegistro) -> tuple[str, Resultado]:
    res = evaluar(s.tipo_registro, s.dominio, s.respuestas, sin_emision=s.sin_emision)
    ticket = generar_ticket()
    sello = ahora().strftime("%Y-%m-%d %H:%M:%S")

    fila = {c: None for c in COLUMNAS}
    fila.update({
        "ID_Reporte": ticket, "Tipo_Registro": s.tipo_registro, "Dominio_Ambiental": s.dominio,
        "Nivel_Experiencia": s.nivel_experiencia, "Estado_Atencion": res.estado_inicial,
        "Plazo_Sugerido": res.plazo, "Fecha_Hora": sello, "Rol_Usuario": s.rol,
        "Usuario_Inspector": "Anónimo" if s.anonimo else (s.alias.strip() or "No especificado"),
        "Anonimo": "Sí" if s.anonimo else "No",
        "Referencia_Lugar": s.referencia.strip(),
        "Observaciones": s.observaciones.strip() or "Sin observaciones",
        "Datos_Tecnicos_Extra": s.datos_tecnicos,
        "Puntaje_Aire": res.pts_aire, "Puntaje_Ruido": res.pts_ruido,
        "Puntaje_Bruto": res.bruto, "Puntaje_Max_Posible": res.maximo,
        "Indice_Riesgo_Pct": res.pct, "Nivel_Riesgo": res.nivel,
        "Latitud": round(s.lat, 6), "Longitud": round(s.lon, 6),
        "Evidencia_Foto": s.evidencia,
        "Sin_Emision": "Sí" if s.sin_emision else "No",
        "Momento_Observacion": s.momento,
        "Punto_Control": s.punto_control or "—",
        "Precision_GPS_m": None if s.precision_gps is None else round(float(s.precision_gps), 1),
        "Meteo_Auto": s.meteo,
        "Confirmaciones": 0,
        "Historial_Estados": f"{sello[:16]} · {res.estado_inicial}",
        "Nota_Institucional": "",
        "Fecha_Actualizacion": sello,
    })
    for c in AIRE:
        fila[c.columna] = (
            "No aplica (dominio ruido)" if not usa_aire(s.dominio)
            else TEXTO_SIN_EMISION if s.sin_emision else s.respuestas[c.codigo])
    for c in RUIDO:
        fila[c.columna] = (
            "No aplica (dominio aire)" if not usa_ruido(s.dominio)
            else TEXTO_SIN_EMISION if s.sin_emision else s.respuestas[c.codigo])

    repository.obtener_repo().agregar(fila)
    repository.invalidar_cache()
    return ticket, res


def cambiar_estado(id_reporte: str, nuevo_estado: str, nota: str = "") -> bool:
    def aplicar(df: pd.DataFrame, i: int) -> None:
        ahora_txt = ahora().strftime("%Y-%m-%d %H:%M")
        entrada = f"{ahora_txt} · {nuevo_estado}" + (f" · {nota.strip()}" if nota.strip() else "")
        previo = _txt(df.at[i, "Historial_Estados"])
        df.at[i, "Estado_Atencion"] = nuevo_estado
        df.at[i, "Historial_Estados"] = f"{previo}{SEP_HIST}{entrada}" if previo else entrada
        if nota.strip():
            df.at[i, "Nota_Institucional"] = nota.strip()
        df.at[i, "Fecha_Actualizacion"] = ahora().strftime("%Y-%m-%d %H:%M:%S")

    ok = repository.obtener_repo().modificar(id_reporte, aplicar)
    repository.invalidar_cache()
    return ok


def confirmar(id_reporte: str) -> bool:
    def aplicar(df: pd.DataFrame, i: int) -> None:
        df.at[i, "Confirmaciones"] = _entero(df.at[i, "Confirmaciones"]) + 1
        df.at[i, "Fecha_Actualizacion"] = ahora().strftime("%Y-%m-%d %H:%M:%S")

    ok = repository.obtener_repo().modificar(id_reporte, aplicar)
    repository.invalidar_cache()
    return ok
