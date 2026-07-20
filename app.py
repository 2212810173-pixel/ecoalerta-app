# ==============================================================================
# EcoAlerta v3.0
# Aplicación de Fiscalización y Registro de Fuentes de Contaminación Atmosférica
# Ciudad de Huanta, Ayacucho - Perú
# ==============================================================================
# Proyecto: Universidad Nacional Autónoma de Huanta (UNAH)
# Carrera: Ingeniería Ambiental
# Tecnologías: Streamlit, Folium, Pandas, Plotly, Google Sheets
# ==============================================================================
# ACTUALIZACIONES v3.0:
#   [GSHEETS] Persistencia en Google Sheets (reemplaza CSV local)
#             Usa st-gsheets-connection para leer/escribir datos.
#   Se mantienen intactos:
#     - Marcador visual rojo en mapa (session_state)
#     - Branding institucional UNAH (logo + sidebar)
#     - Diseño de pestañas, CSS, metodología
# ==============================================================================
#
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  CONFIGURACIÓN DE SECRETS.TOML PARA GOOGLE SHEETS                         ║
# ║                                                                            ║
# ║  Crea el archivo .streamlit/secrets.toml con esta estructura:              ║
# ║                                                                            ║
# ║  [connections.gsheets]                                                     ║
# ║  spreadsheet = "https://docs.google.com/spreadsheets/d/TU_ID_AQUI/edit"   ║
# ║  type = "service_account"                                                  ║
# ║                                                                            ║
# ║  [connections.gsheets.credentials]                                         ║
# ║  type = "service_account"                                                  ║
# ║  project_id = "tu-proyecto-id"                                             ║
# ║  private_key_id = "abc123..."                                              ║
# ║  private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END..."            ║
# ║  client_email = "tu-cuenta@tu-proyecto.iam.gserviceaccount.com"            ║
# ║  client_id = "123456789"                                                   ║
# ║  auth_uri = "https://accounts.google.com/o/oauth2/auth"                    ║
# ║  token_uri = "https://oauth2.googleapis.com/token"                         ║
# ║  auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/..."  ║
# ║  client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/..." ║
# ║                                                                            ║
# ║  PASOS PREVIOS:                                                            ║
# ║  1. Crear un proyecto en Google Cloud Console.                              ║
# ║  2. Habilitar la API de Google Sheets y Google Drive.                       ║
# ║  3. Crear una cuenta de servicio y descargar el JSON de credenciales.       ║
# ║  4. Compartir la hoja de Google Sheets con el client_email de la cuenta.    ║
# ║  5. La hoja debe tener una pestaña llamada "Hoja 1" (nombre por defecto).  ║
# ║  6. En Streamlit Cloud: pegar el contenido en Settings > Secrets.           ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import io

# [GSHEETS] Importar el conector de Google Sheets
from streamlit_gsheets import GSheetsConnection

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="EcoAlerta · Huanta · UNAH",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==============================================================================
# [GSHEETS] CONEXIÓN A GOOGLE SHEETS
# ==============================================================================
# Se establece la conexión usando las credenciales definidas en secrets.toml.
# El parámetro ttl=0 desactiva la caché para siempre leer datos frescos.
# En producción, puedes usar ttl=300 (5 minutos) para reducir llamadas a la API.
conn = st.connection("gsheets", type=GSheetsConnection)

# Nombre de la hoja (worksheet) donde se almacenan los reportes.
# Debe coincidir con el nombre de la pestaña en tu Google Sheet.
NOMBRE_HOJA = "Hoja 1"

# Columnas esperadas en la hoja de Google Sheets
COLUMNAS_GSHEET = [
    "Fecha_Hora", "Inspector", "Observaciones",
    "P1_Tipo_Fuente", "P2_Opacidad", "P3_Olores",
    "P4_Viento_Vel", "P5_Viento_Dir", "P6_Distancia",
    "P7_Mitigacion", "P8_Sintomas",
    "Puntaje_Total", "Nivel_Riesgo",
    "Latitud", "Longitud",
]

# Ruta relativa para el logo (se mantiene igual que v2.0)
DIRECTORIO_BASE = os.path.dirname(os.path.abspath(__file__))

# ==============================================================================
# [REQ-2] INICIALIZACIÓN DE SESSION STATE PARA COORDENADAS DEL MAPA
# ==============================================================================
if "lat_seleccionada" not in st.session_state:
    st.session_state.lat_seleccionada = None
if "lon_seleccionada" not in st.session_state:
    st.session_state.lon_seleccionada = None

# ==============================================================================
# ESTILOS CSS PERSONALIZADOS
# ==============================================================================
st.markdown("""
<style>
    /* --- Fuente global --- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* --- Encabezado principal --- */
    .main-header {
        background: linear-gradient(135deg, #0d9488 0%, #065f46 50%, #1e3a5f 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        color: white;
        box-shadow: 0 8px 32px rgba(13, 148, 136, 0.25);
        position: relative;
        overflow: hidden;
    }
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
        border-radius: 50%;
    }
    .main-header h1 {
        margin: 0;
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    .main-header p {
        margin: 0.3rem 0 0 0;
        font-size: 1rem;
        opacity: 0.85;
        font-weight: 300;
    }

    /* --- Tarjetas de métricas --- */
    .metric-card {
        background: linear-gradient(145deg, #ffffff, #f0fdfa);
        border: 1px solid #ccfbf1;
        border-radius: 14px;
        padding: 1.4rem;
        text-align: center;
        box-shadow: 0 4px 16px rgba(0,0,0,0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(13, 148, 136, 0.12);
    }
    .metric-card .metric-icon {
        font-size: 2rem;
        margin-bottom: 0.3rem;
    }
    .metric-card .metric-value {
        font-size: 2rem;
        font-weight: 800;
        color: #0d9488;
        margin: 0.2rem 0;
    }
    .metric-card .metric-label {
        font-size: 0.82rem;
        color: #6b7280;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-card .metric-delta {
        font-size: 0.78rem;
        font-weight: 600;
        margin-top: 0.3rem;
    }
    .metric-delta.up { color: #dc2626; }
    .metric-delta.down { color: #16a34a; }

    /* --- Alerta de riesgo --- */
    .risk-badge {
        display: inline-block;
        padding: 0.5rem 1.5rem;
        border-radius: 50px;
        font-weight: 700;
        font-size: 1rem;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    .risk-bajo {
        background: linear-gradient(135deg, #d1fae5, #a7f3d0);
        color: #065f46;
        border: 2px solid #6ee7b7;
    }
    .risk-moderado {
        background: linear-gradient(135deg, #fef3c7, #fde68a);
        color: #92400e;
        border: 2px solid #fbbf24;
    }
    .risk-critico {
        background: linear-gradient(135deg, #fee2e2, #fecaca);
        color: #991b1b;
        border: 2px solid #f87171;
        animation: pulse-critico 2s infinite;
    }
    @keyframes pulse-critico {
        0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
        50% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
    }

    /* --- Panel de resultado --- */
    .resultado-panel {
        background: #f8fafc;
        border-radius: 14px;
        padding: 1.8rem;
        border: 1px solid #e2e8f0;
        margin-top: 1rem;
    }

    /* --- Sección de metodología --- */
    .metodo-card {
        background: linear-gradient(145deg, #f0fdfa, #f0f9ff);
        border-radius: 14px;
        padding: 1.6rem;
        border-left: 4px solid #0d9488;
        margin-bottom: 1rem;
    }

    /* --- Tabs personalizados --- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px 10px 0 0;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
    }

    /* --- Sidebar branding --- */
    .sidebar-brand {
        text-align: center;
        padding: 1rem 0.5rem;
    }
    .sidebar-brand h3 {
        color: #0d9488;
        margin: 0.5rem 0 0.2rem 0;
        font-size: 1.1rem;
    }
    .sidebar-brand p {
        color: #6b7280;
        font-size: 0.78rem;
        line-height: 1.4;
    }
    .sidebar-divider {
        border: none;
        border-top: 1px solid #e5e7eb;
        margin: 1rem 0;
    }

    /* --- Footer --- */
    .footer {
        text-align: center;
        padding: 1.5rem;
        color: #9ca3af;
        font-size: 0.8rem;
        border-top: 1px solid #e5e7eb;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# CONSTANTES Y DICCIONARIOS DE EVALUACIÓN
# ==============================================================================

# Coordenadas centrales de Huanta
HUANTA_LAT = -12.939
HUANTA_LON = -74.249

# --- Diccionarios de puntajes para cada parámetro ---
TIPO_FUENTE = {
    "Fuente de Área (quemas agrícolas, polvo difuso)": 1,
    "Fuente Móvil (vehículos, maquinaria)": 2,
    "Fuente Fija Puntual (chimeneas industriales, ladrilleras)": 3,
}

OPACIDAD_RINGELMANN = {
    "N° 0 - Transparente / sin emisión visible": 1,
    "N° 1 - Humo ligeramente gris (20% opacidad)": 1,
    "N° 2 - Humo gris medio (40% opacidad)": 2,
    "N° 3 - Humo gris oscuro (60% opacidad)": 2,
    "N° 4 - Humo negro denso (80% opacidad)": 3,
    "N° 5 - Humo totalmente negro (100% opacidad)": 3,
}

PERCEPCION_OLORES = {
    "Sin olor perceptible": 1,
    "Olor leve, intermitente (menos de 30 min/día)": 1,
    "Olor moderado, frecuente (30 min - 2 h/día)": 2,
    "Olor fuerte, persistente (más de 2 h/día)": 3,
    "Olor insoportable y continuo (todo el día)": 3,
}

VELOCIDAD_VIENTO = {
    "Calma (< 2 km/h) — humo sube vertical": 3,
    "Brisa ligera (2 - 12 km/h) — humo se desvía levemente": 2,
    "Viento moderado (12 - 30 km/h) — dispersión notable": 1,
    "Viento fuerte (> 30 km/h) — dispersión rápida": 1,
}

DIRECCION_VIENTO = {
    "Hacia zonas descampadas o terrenos agrícolas": 1,
    "Hacia zonas mixtas (residencial-agrícola)": 2,
    "Directamente hacia zonas urbanas densas": 3,
}

DISTANCIA_RECEPTORES = {
    "> 200 m de colegios, hospitales, asilos": 1,
    "Entre 50 m y 200 m de receptores sensibles": 2,
    "< 50 m de colegios, hospitales o centros de salud": 3,
}

MEDIDAS_MITIGACION = {
    "Se observan sistemas de control instalados y operativos": 1,
    "Se observan medidas parciales o en mal estado": 2,
    "No se observa ninguna medida de mitigación": 3,
}

SINTOMAS_POBLACION = {
    "Ningún síntoma reportado por los vecinos": 1,
    "Molestias leves (irritación ocular esporádica, estornudos)": 2,
    "Síntomas moderados (tos persistente, dolor de cabeza frecuente)": 2,
    "Síntomas severos (dificultad respiratoria, náuseas, visitas al centro de salud)": 3,
}


# ==============================================================================
# FUNCIONES AUXILIARES
# ==============================================================================

def calcular_indice_riesgo(puntaje_total: int) -> dict:
    """
    Calcula el Índice de Riesgo Ambiental a partir del puntaje total.

    Rangos:
        8 - 12 : Bajo     (cumple normativa, vigilancia rutinaria)
        13 - 18 : Moderado (requiere seguimiento y correctivas)
        19 - 24 : Crítico  (acción inmediata, posible sanción)

    Retorna un diccionario con nivel, color, clase CSS y recomendación.
    """
    if puntaje_total <= 12:
        return {
            "nivel": "BAJO",
            "emoji": "🟢",
            "clase": "risk-bajo",
            "color": "#16a34a",
            "tipo_alerta": "success",
            "recomendacion": (
                "La fuente opera dentro de parámetros aceptables. "
                "Se recomienda mantener la vigilancia rutinaria y "
                "programar una reinspección en 90 días."
            ),
        }
    elif puntaje_total <= 18:
        return {
            "nivel": "MODERADO",
            "emoji": "🟡",
            "clase": "risk-moderado",
            "color": "#d97706",
            "tipo_alerta": "warning",
            "recomendacion": (
                "Se detectaron condiciones que requieren seguimiento. "
                "Emitir notificación preventiva al operador y programar "
                "reinspección en 30 días con verificación de medidas correctivas."
            ),
        }
    else:
        return {
            "nivel": "CRÍTICO",
            "emoji": "🔴",
            "clase": "risk-critico",
            "color": "#dc2626",
            "tipo_alerta": "error",
            "recomendacion": (
                "⚠️ ALERTA MÁXIMA: Se requiere acción inmediata. "
                "Notificar a la autoridad ambiental competente (OEFA / Municipalidad). "
                "Posible inicio de procedimiento administrativo sancionador. "
                "Evaluar medidas cautelares de suspensión de actividades."
            ),
        }

# ==========================================
# SECCIÓN DEL DASHBOARD
# ==========================================
st.markdown("## 📊 Dashboard de Fiscalización Ambiental")

# Colocamos un botón para forzar la actualización de los datos
if st.button("🔄 Actualizar Datos del Dashboard"):
    st.cache_data.clear() # Borra la memoria caché de los 10 minutos
    st.rerun()            # Recarga la página para traer los datos frescos de Google Sheets
    

# ==============================================================================
# [GSHEETS] FUNCIONES DE PERSISTENCIA EN GOOGLE SHEETS
# ==============================================================================
# Reemplazan completamente las funciones cargar_reportes() y guardar_reporte()
# que antes usaban reportes_bd.csv. Ahora leen y escriben en Google Sheets.

def cargar_reportes() -> pd.DataFrame:
    """
    Lee todos los reportes almacenados en la hoja de Google Sheets.

    Usa conn.read() con ttl="10m" para usar la memoria caché y evitar 
    el error 429 de límite de peticiones de Google.
    """
    try:
        df = conn.read(
            worksheet=NOMBRE_HOJA,
            usecols=list(range(len(COLUMNAS_GSHEET))),  # Leer solo las columnas esperadas
            ttl="10m",  # Modificado: guarda los datos en caché por 10 minutos
        )
        # Eliminar filas completamente vacías (Google Sheets a veces las incluye)
        df = df.dropna(how="all")

        if df.empty:
            return pd.DataFrame(columns=COLUMNAS_GSHEET)
        return df
    except Exception:
        # Si la hoja no existe, está vacía, o hay error de conexión
        return pd.DataFrame(columns=COLUMNAS_GSHEET)

def guardar_reporte(datos_fila: dict) -> bool:
    """
    Guarda un nuevo reporte en Google Sheets.
    """
    try:
        # Paso 1: Leer datos existentes (ahora usará caché si está disponible)
        df_existente = cargar_reportes()

        # Paso 2: Crear DataFrame con la nueva fila
        df_nuevo = pd.DataFrame([datos_fila])

        # Paso 3: Concatenar (append) la nueva fila a los datos existentes
        if df_existente.empty:
            df_actualizado = df_nuevo
        else:
            df_actualizado = pd.concat([df_existente, df_nuevo], ignore_index=True)

        # Paso 4: Sobrescribir la hoja con todos los datos (existentes + nuevo)
        conn.update(
            worksheet=NOMBRE_HOJA,
            data=df_actualizado,
        )

        # NUEVO PASO: Limpiar la memoria caché para que la próxima lectura 
        # traiga los datos actualizados inmediatamente.
        st.cache_data.clear()

        return True
    except Exception as e:
        st.error(f"❌ Error al guardar en Google Sheets: {e}")
        return False


# ==============================================================================
# [REQ-2] FUNCIÓN DE MAPA CON MARCADOR VISUAL PERSISTENTE
# ==============================================================================

def crear_mapa_registro(lat_marcador=None, lon_marcador=None) -> folium.Map:
    """
    Crea un mapa interactivo centrado en Huanta.
    Si se proporcionan coordenadas de marcador (desde session_state),
    agrega un Pin rojo visible en esa ubicación para que el usuario
    vea su selección antes de enviar el formulario.
    """
    mapa = folium.Map(
        location=[HUANTA_LAT, HUANTA_LON],
        zoom_start=15,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    # Capa satelital adicional
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
              "World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Vista Satelital",
        overlay=False,
    ).add_to(mapa)

    # Control de capas
    folium.LayerControl().add_to(mapa)

    # Marcador central de referencia (Plaza de Armas)
    folium.Marker(
        location=[HUANTA_LAT, HUANTA_LON],
        popup="<b>Plaza de Armas de Huanta</b><br>Punto de referencia central",
        tooltip="📍 Centro de Huanta",
        icon=folium.Icon(color="green", icon="info-sign"),
    ).add_to(mapa)

    # Círculo de zona urbana
    folium.Circle(
        location=[HUANTA_LAT, HUANTA_LON],
        radius=800,
        color="#0d9488",
        fill=True,
        fill_opacity=0.05,
        tooltip="Radio urbano de referencia (800m)",
    ).add_to(mapa)

    # [REQ-2] MARCADOR ROJO VISUAL: Si el usuario ya hizo clic, mostrar pin rojo
    if lat_marcador is not None and lon_marcador is not None:
        folium.Marker(
            location=[lat_marcador, lon_marcador],
            popup=(
                f"<b>📍 Punto de Inspección</b><br>"
                f"Lat: {lat_marcador:.6f}<br>"
                f"Lon: {lon_marcador:.6f}"
            ),
            tooltip="🔴 Fuente seleccionada — Punto de inspección",
            icon=folium.Icon(color="red", icon="exclamation-sign"),
        ).add_to(mapa)

    return mapa


def crear_mapa_dashboard(df: pd.DataFrame) -> folium.Map:
    """
    Crea un mapa con marcadores circulares coloreados por nivel de riesgo
    para visualización en el dashboard con datos reales de Google Sheets.
    """
    mapa = folium.Map(
        location=[HUANTA_LAT, HUANTA_LON],
        zoom_start=14,
        tiles="CartoDB positron",
    )

    colores_nivel = {
        "BAJO": "green",
        "MODERADO": "orange",
        "CRÍTICO": "red",
    }

    for _, fila in df.iterrows():
        nivel = fila.get("Nivel_Riesgo", "BAJO")
        color = colores_nivel.get(nivel, "gray")
        radio = 6 if nivel == "BAJO" else 8 if nivel == "MODERADO" else 10

        # Manejar formato de fecha de forma segura
        fecha_str = str(fila.get("Fecha_Hora", ""))[:10]

        folium.CircleMarker(
            location=[fila.get("Latitud", HUANTA_LAT), fila.get("Longitud", HUANTA_LON)],
            radius=radio,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            tooltip=(
                f"📅 {fecha_str}<br>"
                f"👤 {fila.get('Inspector', 'N/A')}<br>"
                f"⚠️ Riesgo: {nivel} ({fila.get('Puntaje_Total', 0)} pts)"
            ),
        ).add_to(mapa)

    return mapa


# ==============================================================================
# [REQ-3] BARRA LATERAL — BRANDING INSTITUCIONAL UNAH
# ==============================================================================
with st.sidebar:
    # Intentar cargar el logo desde ruta relativa
    ruta_logo = os.path.join(DIRECTORIO_BASE, "logo_unah.png")

    if os.path.exists(ruta_logo):
        st.image(ruta_logo, use_container_width=True)
    else:
        # Si no existe el logo, mostrar un placeholder elegante
        st.markdown("""
        <div style="text-align:center; padding:1.5rem; background:linear-gradient(135deg,#0d9488,#065f46);
             border-radius:14px; margin-bottom:0.5rem;">
            <span style="font-size:3rem;">🏛️</span>
            <p style="color:white; font-size:0.75rem; margin-top:0.3rem; opacity:0.8;">
                Coloque <code>logo_unah.png</code><br>en el directorio del proyecto
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Información institucional
    st.markdown("""
    <div class="sidebar-brand">
        <h3>Universidad Nacional Autónoma de Huanta</h3>
        <p>Facultad de Ingeniería Ambiental<br>
        Proyecto de Fiscalización Atmosférica</p>
    </div>
    <hr class="sidebar-divider">
    """, unsafe_allow_html=True)

    # Información del sistema
    st.markdown("#### 🌿 EcoAlerta v3.0")
    st.caption("Sistema de Fiscalización y Registro de Fuentes de Contaminación Atmosférica")
    st.caption("☁️ Conectado a Google Sheets")

    st.divider()

    # [GSHEETS] Estadísticas rápidas desde Google Sheets
    df_sidebar = cargar_reportes()
    total_registros = len(df_sidebar)
    st.metric("📋 Reportes en Base de Datos", total_registros)

    if total_registros > 0:
        criticos_total = len(df_sidebar[df_sidebar["Nivel_Riesgo"] == "CRÍTICO"]) if "Nivel_Riesgo" in df_sidebar.columns else 0
        st.metric("🔴 Alertas Críticas", criticos_total)

    st.divider()

    # Botón para limpiar selección del mapa
    if st.button("🗑️ Limpiar punto del mapa", use_container_width=True):
        st.session_state.lat_seleccionada = None
        st.session_state.lon_seleccionada = None
        st.rerun()

    st.caption(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")


# ==============================================================================
# ENCABEZADO PRINCIPAL
# ==============================================================================
st.markdown("""
<div class="main-header">
    <h1>🌿 EcoAlerta · Huanta</h1>
    <p>Sistema de Fiscalización y Registro de Fuentes de Contaminación Atmosférica — UNAH · Ayacucho, Perú</p>
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# PESTAÑAS PRINCIPALES
# ==============================================================================
tab1, tab2, tab3 = st.tabs([
    "📋 Registro de Inspección",
    "📊 Analítica y Reportes",
    "📖 Metodología",
])


# ==============================================================================
# PESTAÑA 1: REGISTRO DE INSPECCIÓN AVANZADO
# ==============================================================================
with tab1:
    st.markdown("### 🔍 Nueva Inspección Ambiental")
    st.markdown(
        "Complete la matriz de evaluación y georreferencie la fuente "
        "de contaminación haciendo clic en el mapa."
    )

    col_form, col_mapa = st.columns([1.1, 0.9], gap="large")

    # ---- COLUMNA IZQUIERDA: Formulario de Evaluación ----
    with col_form:
        st.markdown("#### 📝 Matriz de Evaluación Ambiental")

        # Datos generales del inspector
        with st.expander("👤 Datos del Inspector", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                nombre_inspector = st.text_input(
                    "Nombre del Inspector",
                    placeholder="Ej: Ing. María Quispe",
                )
            with c2:
                fecha_inspeccion = st.date_input(
                    "Fecha de Inspección",
                    value=datetime.now(),
                )
            observaciones = st.text_area(
                "Observaciones Generales",
                placeholder="Describa brevemente la situación observada en campo...",
                height=80,
            )

        st.divider()

        # ---- 8 Parámetros Técnicos de Evaluación ----
        st.markdown("##### ⚙️ Parámetros Técnicos (8 criterios)")

        p1_seleccion = st.selectbox(
            "1️⃣ Tipo de Fuente de Emisión",
            options=list(TIPO_FUENTE.keys()),
            help="Clasifique la fuente según su naturaleza operativa.",
        )

        p2_seleccion = st.selectbox(
            "2️⃣ Opacidad / Pluma de Humo (Escala de Ringelmann)",
            options=list(OPACIDAD_RINGELMANN.keys()),
            help="Evalúe la densidad visual del humo emitido usando la escala simplificada de Ringelmann (0-5).",
        )

        p3_seleccion = st.selectbox(
            "3️⃣ Percepción de Olores en el Entorno",
            options=list(PERCEPCION_OLORES.keys()),
            help="Registre la intensidad y frecuencia de olores percibidos en el punto de inspección.",
        )

        p4_seleccion = st.selectbox(
            "4️⃣ Condiciones Meteorológicas — Velocidad del Viento",
            options=list(VELOCIDAD_VIENTO.keys()),
            help="Viento en calma concentra contaminantes (mayor riesgo). Viento fuerte dispersa la pluma (menor riesgo).",
        )

        p5_seleccion = st.selectbox(
            "5️⃣ Dirección Predominante del Viento",
            options=list(DIRECCION_VIENTO.keys()),
            help="Evalúe si los contaminantes se dirigen hacia zonas pobladas.",
        )

        p6_seleccion = st.selectbox(
            "6️⃣ Distancia a Receptores Sensibles",
            options=list(DISTANCIA_RECEPTORES.keys()),
            help="Receptores sensibles: colegios, hospitales, asilos, centros de salud, guarderías.",
        )

        p7_seleccion = st.selectbox(
            "7️⃣ Medidas de Mitigación Observadas",
            options=list(MEDIDAS_MITIGACION.keys()),
            help="Verifique si el operador ha implementado sistemas de control de emisiones.",
        )

        p8_seleccion = st.selectbox(
            "8️⃣ Síntomas Reportados en la Población Aledaña",
            options=list(SINTOMAS_POBLACION.keys()),
            help="Registre cualquier queja o síntoma reportado por residentes cercanos.",
        )

    # ---- COLUMNA DERECHA: Mapa Interactivo con Marcador Visual ----
    with col_mapa:
        st.markdown("#### 🗺️ Georreferenciación del Punto")
        st.info("📌 **Haga clic en el mapa** para marcar la ubicación exacta de la fuente de contaminación.")

        # [REQ-2] Crear mapa con marcador persistente desde session_state
        mapa_registro = crear_mapa_registro(
            lat_marcador=st.session_state.lat_seleccionada,
            lon_marcador=st.session_state.lon_seleccionada,
        )

        # Renderizar mapa con captura de clic
        datos_mapa = st_folium(
            mapa_registro,
            height=480,
            width=None,
            key="mapa_registro",
        )

        # [REQ-2] Capturar clic y persistir en session_state
        if datos_mapa and datos_mapa.get("last_clicked"):
            nueva_lat = datos_mapa["last_clicked"]["lat"]
            nueva_lon = datos_mapa["last_clicked"]["lng"]

            # Solo actualizar si las coordenadas cambiaron (evitar rerun infinito)
            if (nueva_lat != st.session_state.lat_seleccionada or
                    nueva_lon != st.session_state.lon_seleccionada):
                st.session_state.lat_seleccionada = nueva_lat
                st.session_state.lon_seleccionada = nueva_lon
                st.rerun()

        # Mostrar estado de coordenadas al usuario
        if st.session_state.lat_seleccionada is not None:
            st.success(
                f"📍 **Coordenadas capturadas:**  \n"
                f"Lat: `{st.session_state.lat_seleccionada:.6f}` | "
                f"Lon: `{st.session_state.lon_seleccionada:.6f}`"
            )
        else:
            st.warning("⚠️ Aún no ha seleccionado un punto en el mapa.")

    # ---- MOTOR DE PROCESAMIENTO Y GUARDADO EN GOOGLE SHEETS ----
    st.divider()
    st.markdown("### ⚡ Procesamiento del Índice de Riesgo")

    if st.button("🔬 Evaluar y Enviar Reporte", type="primary", use_container_width=True):

        # Validación estricta: verificar que se haya hecho clic en el mapa
        if st.session_state.lat_seleccionada is None or st.session_state.lon_seleccionada is None:
            st.error(
                "🚫 **Error de validación:** Debe hacer clic en el mapa para "
                "georreferenciar la fuente antes de enviar el reporte. "
                "Seleccione un punto en el mapa y vuelva a intentar."
            )
        else:
            # Calcular puntaje total sumando los 8 parámetros
            puntajes = {
                "Tipo de Fuente": TIPO_FUENTE[p1_seleccion],
                "Opacidad (Ringelmann)": OPACIDAD_RINGELMANN[p2_seleccion],
                "Percepción de Olores": PERCEPCION_OLORES[p3_seleccion],
                "Velocidad del Viento": VELOCIDAD_VIENTO[p4_seleccion],
                "Dirección del Viento": DIRECCION_VIENTO[p5_seleccion],
                "Distancia a Receptores": DISTANCIA_RECEPTORES[p6_seleccion],
                "Medidas de Mitigación": MEDIDAS_MITIGACION[p7_seleccion],
                "Síntomas Población": SINTOMAS_POBLACION[p8_seleccion],
            }

            puntaje_total = sum(puntajes.values())
            resultado = calcular_indice_riesgo(puntaje_total)

            # ==============================================================
            # [GSHEETS] GUARDAR EN GOOGLE SHEETS — Persistencia en la nube
            # ==============================================================
            datos_para_gsheet = {
                "Fecha_Hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Inspector": nombre_inspector or "No especificado",
                "Observaciones": observaciones or "Sin observaciones",
                "P1_Tipo_Fuente": p1_seleccion,
                "P2_Opacidad": p2_seleccion,
                "P3_Olores": p3_seleccion,
                "P4_Viento_Vel": p4_seleccion,
                "P5_Viento_Dir": p5_seleccion,
                "P6_Distancia": p6_seleccion,
                "P7_Mitigacion": p7_seleccion,
                "P8_Sintomas": p8_seleccion,
                "Puntaje_Total": puntaje_total,
                "Nivel_Riesgo": resultado["nivel"],
                "Latitud": round(st.session_state.lat_seleccionada, 6),
                "Longitud": round(st.session_state.lon_seleccionada, 6),
            }

            guardado_ok = guardar_reporte(datos_para_gsheet)

            # Mostrar resultado con alerta visual
            st.markdown('<div class="resultado-panel">', unsafe_allow_html=True)

            # Confirmación de guardado
            if guardado_ok:
                st.toast("✅ Reporte guardado en Google Sheets", icon="☁️")

            # Alerta de nivel
            alerta_fn = {
                "success": st.success,
                "warning": st.warning,
                "error": st.error,
            }
            alerta_fn[resultado["tipo_alerta"]](
                f"{resultado['emoji']} **ÍNDICE DE RIESGO: {resultado['nivel']}** — "
                f"Puntaje total: **{puntaje_total}/24**"
            )

            # Barra de progreso visual
            progreso = (puntaje_total - 8) / 16  # Normalizar de 0 a 1
            st.progress(min(progreso, 1.0))

            # Desglose de puntajes
            st.markdown("##### 📊 Desglose de Puntajes por Parámetro")
            col_desg1, col_desg2 = st.columns(2)

            items = list(puntajes.items())
            for idx, (parametro, puntaje) in enumerate(items):
                icono_p = "🟢" if puntaje == 1 else "🟡" if puntaje == 2 else "🔴"
                col_target = col_desg1 if idx < 4 else col_desg2
                with col_target:
                    st.markdown(f"{icono_p} **{parametro}:** {puntaje}/3")

            # Recomendación técnica
            st.divider()
            st.markdown("##### 💡 Recomendación Técnica")
            st.markdown(resultado["recomendacion"])

            # Resumen de georreferenciación
            st.markdown(
                f"##### 📍 Ubicación Registrada\n"
                f"- **Latitud:** {st.session_state.lat_seleccionada:.6f}  \n"
                f"- **Longitud:** {st.session_state.lon_seleccionada:.6f}  \n"
                f"- **Fecha:** {fecha_inspeccion.strftime('%d/%m/%Y')}  \n"
                f"- **Inspector:** {nombre_inspector or 'No especificado'}"
            )

            if guardado_ok:
                st.info("☁️ Registro almacenado en: **Google Sheets**")

            st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# PESTAÑA 2: ANALÍTICA Y REPORTES (DASHBOARD CON DATOS DE GOOGLE SHEETS)
# ==============================================================================
with tab2:
    st.markdown("### 📊 Dashboard de Monitoreo Ambiental")
    st.markdown("Análisis de incidencias registradas en Huanta — datos en tiempo real desde Google Sheets.")

    # [GSHEETS] Leer datos directamente de Google Sheets
    df_incidencias = cargar_reportes()

    # Verificar si hay datos disponibles
    if df_incidencias.empty or len(df_incidencias) == 0:
        st.warning(
            "📭 **No hay reportes registrados aún.** Vaya a la pestaña "
            "'📋 Registro de Inspección' para crear su primer reporte. "
            "Los gráficos se generarán automáticamente con los datos reales."
        )
        st.info("💡 **Tip:** Complete el formulario de evaluación, marque un punto en el mapa "
                "y presione 'Evaluar y Enviar Reporte'.")
    else:
        # Convertir la columna de fecha para operaciones temporales
        df_incidencias["Fecha_Hora"] = pd.to_datetime(
            df_incidencias["Fecha_Hora"], errors="coerce"
        )

        # ---- MÉTRICAS CLAVE (calculadas de datos reales) ----
        total_inspecciones = len(df_incidencias)
        casos_criticos = len(df_incidencias[df_incidencias["Nivel_Riesgo"] == "CRÍTICO"])
        casos_moderados = len(df_incidencias[df_incidencias["Nivel_Riesgo"] == "MODERADO"])
        puntaje_promedio = pd.to_numeric(
            df_incidencias["Puntaje_Total"], errors="coerce"
        ).mean()

        m1, m2, m3, m4 = st.columns(4)

        with m1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">📋</div>
                <div class="metric-value">{total_inspecciones}</div>
                <div class="metric-label">Inspecciones Totales</div>
            </div>
            """, unsafe_allow_html=True)

        with m2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">🔴</div>
                <div class="metric-value">{casos_criticos}</div>
                <div class="metric-label">Casos Críticos</div>
            </div>
            """, unsafe_allow_html=True)

        with m3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">🟡</div>
                <div class="metric-value">{casos_moderados}</div>
                <div class="metric-label">Casos Moderados</div>
            </div>
            """, unsafe_allow_html=True)

        with m4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">📈</div>
                <div class="metric-value">{puntaje_promedio:.1f}</div>
                <div class="metric-label">Puntaje Promedio</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ---- GRÁFICOS CON DATOS REALES ----
        col_g1, col_g2 = st.columns(2)

        # Gráfico Circular: Distribución por nivel de riesgo
        with col_g1:
            st.markdown("##### 🥧 Distribución por Nivel de Riesgo")
            conteo_niveles = df_incidencias["Nivel_Riesgo"].value_counts().reset_index()
            conteo_niveles.columns = ["Nivel de Riesgo", "Cantidad"]

            fig_pie = px.pie(
                conteo_niveles,
                values="Cantidad",
                names="Nivel de Riesgo",
                color="Nivel de Riesgo",
                color_discrete_map={
                    "BAJO": "#22c55e",
                    "MODERADO": "#f59e0b",
                    "CRÍTICO": "#ef4444",
                },
                hole=0.45,
            )
            fig_pie.update_traces(
                textposition="inside",
                textinfo="percent+label",
                hovertemplate="<b>%{label}</b><br>Cantidad: %{value}<br>Porcentaje: %{percent}<extra></extra>",
            )
            fig_pie.update_layout(
                font=dict(family="Inter", size=13),
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
                margin=dict(t=20, b=40, l=20, r=20),
                height=380,
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        # Gráfico de Barras: Puntaje por inspector
        with col_g2:
            st.markdown("##### 📊 Puntaje Promedio por Inspector")
            df_incidencias["Puntaje_Total"] = pd.to_numeric(
                df_incidencias["Puntaje_Total"], errors="coerce"
            )
            conteo_inspector = (
                df_incidencias
                .groupby("Inspector")["Puntaje_Total"]
                .mean()
                .reset_index()
            )
            conteo_inspector.columns = ["Inspector", "Puntaje Promedio"]

            fig_bar = px.bar(
                conteo_inspector,
                x="Inspector",
                y="Puntaje Promedio",
                color="Puntaje Promedio",
                color_continuous_scale=["#22c55e", "#f59e0b", "#ef4444"],
                range_color=[8, 24],
            )
            fig_bar.update_layout(
                font=dict(family="Inter", size=12),
                xaxis=dict(tickangle=-45, title=""),
                yaxis=dict(title="Puntaje Promedio"),
                margin=dict(t=40, b=100, l=40, r=20),
                height=380,
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # ---- GRÁFICO TEMPORAL ----
        st.markdown("##### 📈 Evolución Temporal de Inspecciones")
        df_temporal = df_incidencias.dropna(subset=["Fecha_Hora"]).copy()
        df_temporal["Fecha"] = df_temporal["Fecha_Hora"].dt.date

        serie_temporal = (
            df_temporal
            .groupby(["Fecha", "Nivel_Riesgo"])
            .size()
            .reset_index(name="Cantidad")
        )

        if not serie_temporal.empty:
            fig_linea = px.area(
                serie_temporal,
                x="Fecha",
                y="Cantidad",
                color="Nivel_Riesgo",
                color_discrete_map={
                    "BAJO": "#22c55e",
                    "MODERADO": "#f59e0b",
                    "CRÍTICO": "#ef4444",
                },
                labels={"Nivel_Riesgo": "Nivel de Riesgo"},
            )
            fig_linea.update_layout(
                font=dict(family="Inter", size=12),
                xaxis=dict(title="Fecha"),
                yaxis=dict(title="N° de Inspecciones"),
                legend=dict(
                    title="", orientation="h",
                    yanchor="bottom", y=1.02, xanchor="right", x=1,
                ),
                margin=dict(t=40, b=40, l=40, r=20),
                height=320,
            )
            st.plotly_chart(fig_linea, use_container_width=True)
        else:
            st.caption("📉 Se necesitan más datos para el gráfico temporal.")

        # ---- MAPA DE INCIDENCIAS REALES ----
        st.markdown("##### 🗺️ Mapa de Incidencias Registradas")
        mapa_dash = crear_mapa_dashboard(df_incidencias)
        st_folium(mapa_dash, height=420, width=None, key="mapa_dashboard")

        # ---- TABLA DE DATOS ----
        st.markdown("##### 📋 Registro Detallado de Inspecciones")

        # Filtro interactivo
        niveles_disponibles = df_incidencias["Nivel_Riesgo"].dropna().unique().tolist()
        filtro_nivel = st.multiselect(
            "Filtrar por Nivel de Riesgo:",
            options=niveles_disponibles,
            default=niveles_disponibles,
        )

        df_filtrado = df_incidencias[df_incidencias["Nivel_Riesgo"].isin(filtro_nivel)]

        # Preparar DataFrame para visualización
        df_display = df_filtrado.copy()
        if "Fecha_Hora" in df_display.columns:
            df_display["Fecha_Hora"] = df_display["Fecha_Hora"].dt.strftime("%d/%m/%Y %H:%M")
        if "Latitud" in df_display.columns:
            df_display["Latitud"] = pd.to_numeric(df_display["Latitud"], errors="coerce").round(5)
        if "Longitud" in df_display.columns:
            df_display["Longitud"] = pd.to_numeric(df_display["Longitud"], errors="coerce").round(5)

        st.dataframe(
            df_display,
            use_container_width=True,
            height=300,
            hide_index=True,
        )

    # ---- BOTÓN DE DESCARGA CSV (siempre visible) ----
    # [GSHEETS] Descarga los datos desde Google Sheets como archivo CSV
    st.divider()
    st.markdown("##### 📥 Exportar Base de Datos")

    df_descarga = cargar_reportes()
    if not df_descarga.empty:
        # Convertir el DataFrame de Google Sheets a CSV en memoria
        csv_buffer = io.StringIO()
        df_descarga.to_csv(csv_buffer, index=False, encoding="utf-8")
        csv_data = csv_buffer.getvalue()

        st.download_button(
            label="📥 Descargar reportes como CSV",
            data=csv_data,
            file_name=f"ecoalerta_reportes_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True,
        )
    else:
        st.info(
            "📭 No hay reportes en Google Sheets aún. "
            "Registre al menos una inspección para poder descargar el reporte."
        )


# ==============================================================================
# PESTAÑA 3: METODOLOGÍA
# ==============================================================================
with tab3:
    st.markdown("### 📖 Metodología del Índice de Riesgo Ambiental")
    st.markdown(
        "Documentación técnica sobre los pesos asignados a cada variable y "
        "la base científica del cálculo del Índice de Riesgo."
    )

    # --- Introducción ---
    st.markdown("""
    <div class="metodo-card">
    <h4>🎯 Objetivo del Instrumento</h4>
    <p>
    El Índice de Riesgo Ambiental (IRA) de EcoAlerta es una herramienta de evaluación
    semicuantitativa diseñada para la <strong>fiscalización rápida en campo</strong> de fuentes
    de contaminación atmosférica en la ciudad de Huanta, Ayacucho. Permite al inspector
    asignar un nivel de riesgo objetivo basado en 8 parámetros técnicos medibles u observables,
    reduciendo la subjetividad en la toma de decisiones.
    </p>
    </div>
    """, unsafe_allow_html=True)

    # --- Tabla de pesos ---
    st.markdown("#### ⚖️ Tabla de Pesos y Criterios de Evaluación")
    st.markdown(
        "Cada parámetro se evalúa en una escala de **1 a 3 puntos**, donde:"
    )
    st.markdown(
        "- **1 punto** = Condición de bajo riesgo / impacto mínimo\n"
        "- **2 puntos** = Condición de riesgo moderado / impacto intermedio\n"
        "- **3 puntos** = Condición de alto riesgo / impacto severo"
    )

    # Tabla de criterios detallada
    tabla_criterios = pd.DataFrame([
        {
            "N°": 1,
            "Parámetro": "Tipo de Fuente",
            "Peso 1 (Bajo)": "Fuente de Área",
            "Peso 2 (Moderado)": "Fuente Móvil",
            "Peso 3 (Alto)": "Fuente Fija Puntual",
            "Base Técnica": "Las fuentes fijas puntuales generan emisiones concentradas y continuas (D.S. 003-2017-MINAM).",
        },
        {
            "N°": 2,
            "Parámetro": "Opacidad (Ringelmann)",
            "Peso 1 (Bajo)": "N° 0 - 1 (0-20%)",
            "Peso 2 (Moderado)": "N° 2 - 3 (40-60%)",
            "Peso 3 (Alto)": "N° 4 - 5 (80-100%)",
            "Base Técnica": "Escala de Ringelmann (EPA Method 9). Opacidad > 60% indica combustión incompleta.",
        },
        {
            "N°": 3,
            "Parámetro": "Percepción de Olores",
            "Peso 1 (Bajo)": "Sin olor / Leve intermitente",
            "Peso 2 (Moderado)": "Moderado frecuente",
            "Peso 3 (Alto)": "Fuerte persistente / Insoportable",
            "Base Técnica": "NTP 900.030 y criterios de molestia olfativa (OMS Guidelines 2021).",
        },
        {
            "N°": 4,
            "Parámetro": "Velocidad del Viento",
            "Peso 1 (Bajo)": "Moderado a Fuerte (>12 km/h)",
            "Peso 2 (Moderado)": "Brisa ligera (2-12 km/h)",
            "Peso 3 (Alto)": "Calma (< 2 km/h)",
            "Base Técnica": "La inversión térmica y calma incrementan concentración de PM (EPA AP-42, Cap. 1).",
        },
        {
            "N°": 5,
            "Parámetro": "Dirección del Viento",
            "Peso 1 (Bajo)": "Hacia descampados",
            "Peso 2 (Moderado)": "Hacia zonas mixtas",
            "Peso 3 (Alto)": "Hacia zonas urbanas densas",
            "Base Técnica": "Modelo gaussiano de dispersión: dirección determina población expuesta.",
        },
        {
            "N°": 6,
            "Parámetro": "Distancia a Receptores",
            "Peso 1 (Bajo)": "> 200 m",
            "Peso 2 (Moderado)": "50 - 200 m",
            "Peso 3 (Alto)": "< 50 m",
            "Base Técnica": "Zonas de amortiguamiento del D.S. 003-2017-MINAM y OMS (buffer zones).",
        },
        {
            "N°": 7,
            "Parámetro": "Medidas de Mitigación",
            "Peso 1 (Bajo)": "Sistemas operativos",
            "Peso 2 (Moderado)": "Medidas parciales",
            "Peso 3 (Alto)": "Sin medidas",
            "Base Técnica": "Ley N° 28611 (Ley General del Ambiente) y principio de prevención.",
        },
        {
            "N°": 8,
            "Parámetro": "Síntomas en Población",
            "Peso 1 (Bajo)": "Ninguno reportado",
            "Peso 2 (Moderado)": "Leves a moderados",
            "Peso 3 (Alto)": "Severos (dific. respiratoria)",
            "Base Técnica": "Indicadores de salud ambiental (OMS 2005, actualización 2021).",
        },
    ])

    st.dataframe(
        tabla_criterios,
        use_container_width=True,
        hide_index=True,
        height=340,
    )

    # --- Rangos del Índice ---
    st.markdown("#### 🎚️ Rangos del Índice de Riesgo Ambiental (IRA)")
    st.markdown(
        "El puntaje total se obtiene sumando los valores de los 8 parámetros. "
        "El rango posible es de **8 puntos** (mínimo) a **24 puntos** (máximo)."
    )

    col_r1, col_r2, col_r3 = st.columns(3)

    with col_r1:
        st.markdown("""
        <div class="metodo-card" style="border-left-color: #22c55e;">
        <h4>🟢 BAJO (8 – 12 pts)</h4>
        <p>La fuente opera dentro de parámetros aceptables.
        Se recomienda vigilancia rutinaria y reinspección programada cada 90 días.
        No se requieren medidas correctivas inmediatas.</p>
        </div>
        """, unsafe_allow_html=True)

    with col_r2:
        st.markdown("""
        <div class="metodo-card" style="border-left-color: #f59e0b;">
        <h4>🟡 MODERADO (13 – 18 pts)</h4>
        <p>Se detectan condiciones que requieren seguimiento activo.
        Emitir notificación preventiva al operador.
        Reinspección obligatoria en 30 días con verificación de medidas correctivas.</p>
        </div>
        """, unsafe_allow_html=True)

    with col_r3:
        st.markdown("""
        <div class="metodo-card" style="border-left-color: #ef4444;">
        <h4>🔴 CRÍTICO (19 – 24 pts)</h4>
        <p>Alerta máxima. Acción inmediata requerida.
        Notificar a la OEFA y/o Municipalidad.
        Posible inicio de procedimiento administrativo sancionador.
        Evaluar suspensión de actividades como medida cautelar.</p>
        </div>
        """, unsafe_allow_html=True)

    # --- Fórmula ---
    st.markdown("#### 📐 Fórmula de Cálculo")
    st.latex(
        r"IRA = \sum_{i=1}^{8} P_i \quad \text{donde } P_i \in \{1, 2, 3\}"
    )
    st.markdown(
        "Donde $P_i$ es el puntaje asignado al $i$-ésimo parámetro de evaluación."
    )

    # --- Marco Legal ---
    st.markdown("#### 📜 Marco Normativo de Referencia")
    st.markdown("""
    <div class="metodo-card">
    <ul>
        <li><strong>D.S. N° 003-2017-MINAM</strong> — Estándares de Calidad Ambiental (ECA) para Aire.</li>
        <li><strong>D.S. N° 014-2017-MINAM</strong> — Límites Máximos Permisibles (LMP) para emisiones.</li>
        <li><strong>Ley N° 28611</strong> — Ley General del Ambiente (Principios de prevención y precaución).</li>
        <li><strong>R.M. N° 182-2016-MINAM</strong> — Protocolo Nacional de Monitoreo de la Calidad Ambiental del Aire.</li>
        <li><strong>EPA Method 9</strong> — Determinación visual de opacidad de emisiones (Escala de Ringelmann).</li>
        <li><strong>OMS</strong> — Guías de Calidad del Aire (actualización 2021) para PM₂.₅, PM₁₀, SO₂, NO₂, O₃.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# FOOTER
# ==============================================================================
st.markdown("""
<div class="footer">
    🌿 <strong>EcoAlerta v3.0</strong> · Sistema de Fiscalización Ambiental · Huanta, Ayacucho<br>
    Proyecto académico — Universidad Nacional Autónoma de Huanta (UNAH) · {año}<br>
    <small>☁️ Datos almacenados en Google Sheets</small>
</div>
""".format(año=datetime.now().year), unsafe_allow_html=True)
