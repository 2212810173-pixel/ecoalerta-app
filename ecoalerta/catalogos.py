"""Catálogo de criterios. Agregar o editar una pregunta = editar solo este archivo."""
from __future__ import annotations

from dataclasses import dataclass

from ecoalerta.config import DOM_AIRE, DOM_INTEGRAL, DOM_RUIDO


@dataclass(frozen=True)
class Criterio:
    codigo: str
    columna: str
    etiqueta: str
    opciones: dict


AIRE = (
    Criterio("A1", "A1_Fuente_Aire", "Fuente de emisión", {
        "Quema abierta a ras de suelo (residuos, rastrojos, polvo)": 1,
        "Vehículos o maquinaria en movimiento (escape)": 2,
        "Chimenea fija o actividad industrial (ladrillera, taller, horno)": 3,
    }),
    Criterio("A2", "A2_Humo_Visibilidad", "Visibilidad / aspecto del humo", {
        "Aire claro o vapor transparente (se ve el fondo con normalidad)": 1,
        "Humo gris claro o blanquecino (se ve borroso, pasa algo de luz)": 2,
        "Humo negro o muy oscuro y denso (tapa la visibilidad)": 3,
    }),
    Criterio("A3", "A3_Olor_Entorno", "Olor en el entorno", {
        "Sin olor extraño o muy leve que pasa rápido": 1,
        "Olor molesto evidente (obliga a cerrar ventanas o apartarse)": 2,
        "Olor fuerte, químico o tóxico (causa ardor en nariz/garganta o náuseas)": 3,
    }),
    Criterio("A4", "A4_Viento_Dispersión", "Viento y dispersión", {
        "Viento moderado o fuerte (mueve ramas y dispersa rápido)": 1,
        "Brisa ligera (mueve hojas, el humo se inclina)": 2,
        "Calma o aire quieto (el humo sube recto o se queda estancado)": 3,
    }),
    Criterio("A5", "A5_Direccion_Afectación", "Hacia dónde se dirige el aire / humo", {
        "Hacia zonas descampadas o agrícolas sin viviendas": 1,
        "Hacia zonas mixtas con pocas casas": 2,
        "Directamente hacia viviendas, calles concurridas o barrios": 3,
    }),
    Criterio("A6", "A6_Distancia_Receptores", "Cercanía a viviendas, colegios o postas", {
        "Lejos: más de 200 m (> 2 cuadras) de colegios, postas o casas": 1,
        "Cerca: entre 50 m y 200 m (1 a 2 cuadras) de zonas habitadas": 2,
        "Muy cerca: menos de 50 m (< media cuadra) de colegios, postas o casas": 3,
    }),
    Criterio("A7", "A7_Control_Aire", "Medidas de control visibles", {
        "Se ven filtros, campanas altas o medidas de control activas": 1,
        "Medidas precarias, incompletas o en mal estado": 2,
        "Sin ningún control (emisión directa al aire)": 3,
    }),
    Criterio("A8", "A8_Salud_Rutina", "Malestares o cambios en la rutina", {
        "Sin malestares ni cambios en la rutina diaria": 1,
        "Molestias leves (ojos irritados, estornudos o cerrar ventanas)": 2,
        "Malestares notorios o suspensión de actividades (tos persistente, falta de aire, evitar salir)": 3,
    }),
)

RUIDO = (
    Criterio("R1", "R1_Fuente_Ruido", "Fuente del ruido", {
        "Tránsito ocasional o actividad cotidiana baja": 1,
        "Tránsito frecuente, mototaxis, comercios o talleres pequeños": 2,
        "Maquinaria pesada, perifoneo/parlantes intensos, bocinas constantes o locales ruidosos": 3,
    }),
    Criterio("R2", "R2_Intensidad_Sonora", "Intensidad percibida del sonido", {
        "Tranquilo / suave (se conversa normal sin elevar la voz)": 1,
        "Molesto / moderado (obliga a elevar la voz o incomoda al estar en casa/calle)": 2,
        "Muy alto / agobiante (dificulta escuchar, genera vibración o incomodidad severa)": 3,
    }),
    Criterio("R3", "R3_Afectacion_Entorno", "Afectación a vecinos, estudio o descanso", {
        "No interfiere con descanso, estudio ni trabajo": 1,
        "Interrumpe parcialmente la concentración, conversación o descanso": 2,
        "Afecta el descanso, el aula/trabajo o genera malestar continuo en vecinos": 3,
    }),
)


def usa_aire(dominio: str) -> bool:
    return dominio in (DOM_AIRE, DOM_INTEGRAL)


def usa_ruido(dominio: str) -> bool:
    return dominio in (DOM_RUIDO, DOM_INTEGRAL)


def criterios_activos(dominio: str) -> tuple:
    return (AIRE if usa_aire(dominio) else ()) + (RUIDO if usa_ruido(dominio) else ())


def rango(criterios) -> tuple[int, int]:
    if not criterios:
        return (0, 0)
    return (
        sum(min(c.opciones.values()) for c in criterios),
        sum(max(c.opciones.values()) for c in criterios),
    )
