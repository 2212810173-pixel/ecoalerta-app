from __future__ import annotations

import io
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

_CAMPOS_CREDS = {
    "type",
    "project_id",
    "private_key_id",
    "private_key",
    "client_email",
    "client_id",
    "auth_uri",
    "token_uri",
    "auth_provider_x509_cert_url",
    "client_x509_cert_url",
    "universe_domain",
}


def _obtener_credenciales():
    if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
        raw = dict(st.secrets["connections"]["gsheets"])
        info = {k: v for k, v in raw.items() if k in _CAMPOS_CREDS}
        return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    if "gcp_service_account" in st.secrets:
        return service_account.Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), scopes=SCOPES
        )
    raise KeyError("No se encontraron credenciales de servicio en st.secrets.")


def subir_foto_drive(ticket: str, jpeg_bytes: bytes) -> str:
    folder_id = str(st.secrets.get("DRIVE_EVIDENCIAS_FOLDER_ID", "")).strip()
    if not folder_id or not jpeg_bytes:
        return ""

    creds = _obtener_credenciales()
    service = build("drive", "v3", credentials=creds, cache_discovery=False)

    metadata = {
        "name": f"{ticket}.jpg",
        "parents": [folder_id],
    }
    media = MediaIoBaseUpload(io.BytesIO(jpeg_bytes), mimetype="image/jpeg", resumable=False)
    archivo = (
        service.files()
        .create(
            body=metadata,
            media_body=media,
            fields="id, webViewLink",
            supportsAllDrives=True,
        )
        .execute()
    )
    return archivo.get("webViewLink") or f"https://drive.google.com/file/d/{archivo['id']}/view"