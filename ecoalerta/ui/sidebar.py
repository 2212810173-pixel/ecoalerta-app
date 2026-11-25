import io

import streamlit as st

from ecoalerta import estado
from ecoalerta.auth import widget_acceso
from ecoalerta.config import DIRECTORIO_BASE
from ecoalerta.repository import obtener_repo


def _qr_png(url: str) -> bytes:
    import qrcode
    buf = io.BytesIO()
    qrcode.make(url).save(buf, format="PNG")
    return buf.getvalue()


def _url_app() -> str:
    try:
        return str(st.secrets["app"]["url"])
    except Exception:
        return ""


def render(df) -> None:
    with st.sidebar:
        for ruta in (DIRECTORIO_BASE / "assets" / "logo_unah.png", DIRECTORIO_BASE / "logo_unah.png"):
            if ruta.exists():
                st.image(str(ruta), use_container_width=True)
                break
        else:
            st.markdown("### 🌿 EcoAlerta")
        st.caption("UNAH · Ingeniería Ambiental · Huanta")
        st.divider()

        if st.session_state.ultimo_ticket:
            st.info(f"Último ticket\n\n`{st.session_state.ultimo_ticket}`")

        if st.button("📍 Limpiar punto del mapa", use_container_width=True):
            estado.limpiar_punto()
            st.rerun()

        with st.expander("📱 Compartir con código QR"):
            url = st.text_input("Dirección de la app", value=_url_app(), placeholder="https://...")
            if url.strip():
                png = _qr_png(url.strip())
                st.image(png, width=190)
                st.download_button("Descargar QR", png, "ecoalerta_qr.png", "image/png", use_container_width=True)
                st.caption("Pégalo en afiches de colegios, mercados y juntas vecinales.")

        widget_acceso()

        st.divider()
        repo = obtener_repo()
        st.caption(f"Almacenamiento: **{repo.etiqueta}**")
        if not repo.es_persistente:
            st.warning("Sin Google Sheets configurado: los datos se guardan en CSV local (`data/reportes.csv`).", icon="⚠️")
