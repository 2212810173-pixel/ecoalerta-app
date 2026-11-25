"""Capa de persistencia. La UI solo conoce `cargar_reportes()` y `obtener_repo()`."""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

import pandas as pd
import streamlit as st

from ecoalerta.config import COLUMNAS, COLUMNAS_NUMERICAS, DIRECTORIO_BASE, HOJA_GSHEET

_LOCK = threading.Lock()
_ULTIMO_OK: dict = {}


def _normalizar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(how="all").copy()
    for c in COLUMNAS:
        if c not in df.columns:
            df[c] = None
    df = df[COLUMNAS].reset_index(drop=True)
    for c in COLUMNAS:
        if c in COLUMNAS_NUMERICAS:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        else:
            df[c] = df[c].astype("object")
    return df


class _RepoTabular:
    etiqueta = ""
    es_persistente = True

    def listar(self) -> pd.DataFrame:
        raise NotImplementedError

    def _escribir(self, df: pd.DataFrame) -> None:
        raise NotImplementedError

    def agregar(self, fila: dict) -> None:
        with _LOCK:
            actual = self.listar()
            nuevo = pd.DataFrame([fila])
            df = nuevo if actual.empty else pd.concat([actual, nuevo], ignore_index=True)
            self._escribir(df[COLUMNAS])

    def modificar(self, id_reporte: str, cambio: Callable[[pd.DataFrame, int], None]) -> bool:
        with _LOCK:
            df = self.listar()
            mask = df["ID_Reporte"].astype(str) == str(id_reporte)
            if not mask.any():
                return False
            cambio(df, df.index[mask][0])
            self._escribir(df)
            return True


class RepoGSheets(_RepoTabular):
    etiqueta = "☁️ Google Sheets"

    def __init__(self):
        from streamlit_gsheets import GSheetsConnection
        self._conn = st.connection("gsheets", type=GSheetsConnection)

    def listar(self):
        return _normalizar(self._conn.read(worksheet=HOJA_GSHEET, ttl=0))

    def _escribir(self, df):
        self._conn.update(worksheet=HOJA_GSHEET, data=df)


class RepoCSV(_RepoTabular):
    etiqueta = "💾 Modo local (demo)"
    es_persistente = False

    def __init__(self, ruta: Path):
        self._ruta = ruta
        ruta.parent.mkdir(parents=True, exist_ok=True)

    def listar(self):
        if not self._ruta.exists():
            return pd.DataFrame(columns=COLUMNAS)
        return _normalizar(pd.read_csv(self._ruta))

    def _escribir(self, df):
        df.to_csv(self._ruta, index=False)


@st.cache_resource(show_spinner=False)
def obtener_repo() -> _RepoTabular:
    try:
        if "gsheets" in st.secrets.get("connections", {}):
            return RepoGSheets()
    except Exception:
        pass
    return RepoCSV(DIRECTORIO_BASE / "data" / "reportes.csv")


@st.cache_data(ttl=45, show_spinner=False)
def _leer() -> pd.DataFrame:
    return obtener_repo().listar()


def cargar_reportes() -> pd.DataFrame:
    try:
        df = _leer()
        _ULTIMO_OK["df"] = df
        return df
    except Exception as e:
        if "df" in _ULTIMO_OK:
            st.warning("Google Sheets no respondió (posible límite de peticiones). "
                       "Se muestran los últimos datos conocidos.", icon="⏳")
            return _ULTIMO_OK["df"]
        st.error(f"No se pudieron cargar los datos: {e}")
        return pd.DataFrame(columns=COLUMNAS)


def invalidar_cache() -> None:
    _leer.clear()
