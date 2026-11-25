from __future__ import annotations

import hmac

import streamlit as st


def _pin() -> str | None:
    try:
        return str(st.secrets["admin"]["pin"])
    except Exception:
        return None


def es_staff() -> bool:
    return bool(st.session_state.get("staff", False))


def widget_acceso() -> None:
    with st.expander("🔐 Acceso institucional", expanded=False):
        if es_staff():
            st.success("Sesión activa")
            if st.button("Cerrar sesión", use_container_width=True):
                st.session_state.staff = False
                st.rerun()
            return
        pin = _pin()
        if not pin:
            st.caption("Define `[admin] pin` en `secrets.toml` para habilitar la gestión de estados.")
            return
        clave = st.text_input("Clave", type="password", key="clave_staff")
        if st.button("Ingresar", use_container_width=True):
            if hmac.compare_digest(clave, pin):
                st.session_state.staff = True
                st.rerun()
            st.error("Clave incorrecta")
