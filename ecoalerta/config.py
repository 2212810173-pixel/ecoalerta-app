from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

APP_NOMBRE = "EcoAlerta"
APP_VERSION = "9.0"
DIRECTORIO_BASE = Path(__file__).resolve().parent.parent
ZONA_HORARIA = ZoneInfo("America/Lima")

# --- Geografía ---------------------------------------------------------------
HUANTA_LAT, HUANTA_LON = -12.939, -74.249
LIMITES_MAPA = (-18.40, -81.40, -0.02, -68.60)  # lat_min, lon_min, lat_max, lon_max

# ⚠️ Reemplaza los puntos "EDITAR" por tus puntos de monitoreo reales (ruta de monitores).
PUNTOS_CONTROL = (
    {"codigo": "HUA-P01", "nombre": "Plaza Principal", "lat": -12.9390, "lon": -74.2490},
    {"codigo": "HUA-P02", "nombre": "Punto 2 (EDITAR)", "lat": -12.9355, "lon": -74.2490},
    {"codigo": "HUA-P03", "nombre": "Punto 3 (EDITAR)", "lat": -12.9425, "lon": -74.2455},
    {"codigo": "HUA-P04", "nombre": "Punto 4 (EDITAR)", "lat": -12.9390, "lon": -74.2535},
)

# --- Persistencia ------------------------------------------------------------
HOJA_GSHEET = "Hoja 1"
COLUMNAS = [
    "ID_Reporte", "Tipo_Registro", "Dominio_Ambiental", "Nivel_Experiencia",
    "Estado_Atencion", "Plazo_Sugerido", "Fecha_Hora", "Rol_Usuario",
    "Usuario_Inspector", "Anonimo", "Referencia_Lugar", "Observaciones",
    "A1_Fuente_Aire", "A2_Humo_Visibilidad", "A3_Olor_Entorno",
    "A4_Viento_Dispersión", "A5_Direccion_Afectación", "A6_Distancia_Receptores",
    "A7_Control_Aire", "A8_Salud_Rutina",
    "R1_Fuente_Ruido", "R2_Intensidad_Sonora", "R3_Afectacion_Entorno",
    "Datos_Tecnicos_Extra", "Puntaje_Aire", "Puntaje_Ruido", "Puntaje_Bruto",
    "Puntaje_Max_Posible", "Indice_Riesgo_Pct", "Nivel_Riesgo",
    "Latitud", "Longitud", "Evidencia_Foto",
    # --- nuevas en v9.0 (se agregan al final: los datos antiguos siguen válidos) ---
    "Sin_Emision", "Momento_Observacion", "Punto_Control", "Precision_GPS_m",
    "Meteo_Auto", "Confirmaciones", "Historial_Estados", "Nota_Institucional",
    "Fecha_Actualizacion",
]
COLUMNAS_NUMERICAS = [
    "Puntaje_Aire", "Puntaje_Ruido", "Puntaje_Bruto", "Puntaje_Max_Posible",
    "Indice_Riesgo_Pct", "Latitud", "Longitud", "Precision_GPS_m", "Confirmaciones",
]
COLUMNAS_PRIVADAS = ["Usuario_Inspector"]

# --- Opciones de formulario --------------------------------------------------
TIPOS_REGISTRO = ("Denuncia / Alerta", "Monitoreo / Línea Base")
DOM_AIRE, DOM_RUIDO, DOM_INTEGRAL = "Calidad del Aire", "Ruido Ambiental", "Integral (Aire + Ruido)"
DOMINIOS = (DOM_AIRE, DOM_RUIDO, DOM_INTEGRAL)
NIVELES_EXPERIENCIA = ("Ciudadano", "Monitor con experiencia")
ROLES = ("Ciudadano / Vecino", "Monitor ambiental", "Inspector / Técnico")
MOMENTOS = ("Ahora mismo", "Hace menos de 1 hora", "Hoy, más temprano", "Ayer o antes")
TEXTO_SIN_EMISION = "Sin emisión / condición normal (línea base)"

ESTADO_CERRADO = "Atendido / Cerrado"
ESTADOS_EN_GESTION = (
    "Pendiente de verificación técnica",
    "En evaluación / monitoreo",
    "Priorizado para fiscalización",
)
ESTADOS_ATENCION = ("Registrado · Seguimiento rutinario", *ESTADOS_EN_GESTION, ESTADO_CERRADO)

# --- Riesgo ------------------------------------------------------------------
NIVELES = ("BAJO", "MODERADO", "CRÍTICO")
UMBRAL_MODERADO = 40.0
UMBRAL_CRITICO = 70.0
COLOR_NIVEL = {"BAJO": "#16a34a", "MODERADO": "#d97706", "CRÍTICO": "#dc2626"}
EMOJI_NIVEL = {"BAJO": "🟢", "MODERADO": "🟡", "CRÍTICO": "🔴"}
INTEGRAL_MODO = "suma"

# --- Calidad de muestra, privacidad y comunidad ------------------------------
CELDA_GRADOS = 0.0025          # ≈ 275 m: celda para detectar concentración y focos
MIN_FOCO = 3                   # reportes mínimos para declarar un foco recurrente
MIN_MUESTRA = 30               # por debajo, los resultados son solo indicativos
DESPLAZAMIENTO_M = 80          # desplazamiento máximo de coordenadas públicas
CONFIRM_RADIO_M = 100
CONFIRM_HORAS = 72
CAL_MIC_DB = 90                # offset de calibración del micrófono (ajústalo con un sonómetro)

# --- Anti-abuso --------------------------------------------------------------
COOLDOWN_SEGUNDOS = 45


def ahora() -> datetime:
    """Hora actual de Perú (la nube corre en UTC)."""
    return datetime.now(ZONA_HORARIA)
