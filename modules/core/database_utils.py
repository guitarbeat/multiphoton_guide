from pathlib import Path

import pandas as pd
import streamlit as st

try:
    from streamlit_gsheets import GSheetsConnection
except Exception:  # pragma: no cover - gsheets optional
    GSheetsConnection = None  # type: ignore


def get_gsheets_connection() -> "GSheetsConnection":
    """Return a configured GSheetsConnection or raise an error."""
    if GSheetsConnection is None:
        raise RuntimeError(
            "streamlit-gsheets is required for Google Sheets storage but is not installed"
        )
    try:
        return st.connection("gsheets", type=GSheetsConnection)
    except Exception as exc:  # pragma: no cover - configuration errors
        raise RuntimeError("Google Sheets connection 'gsheets' is not configured") from exc




def _sanitize_table_name(name: str) -> str:
    return Path(name).stem


def save_dataframe_to_table(
    df: pd.DataFrame, table_name: str, if_exists: str = "replace"
) -> None:
    """Save a DataFrame to the specified Google Sheet."""
    conn = get_gsheets_connection()
    tbl = _sanitize_table_name(table_name)
    conn.update(worksheet=tbl, data=df)


def load_dataframe_from_table(table_name: str) -> pd.DataFrame:
    """Load a DataFrame from a Google Sheet."""
    tbl = _sanitize_table_name(table_name)
    conn = get_gsheets_connection()
    try:
        return conn.read(worksheet=tbl)
    except Exception:
        return pd.DataFrame()
