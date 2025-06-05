import os
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

try:
    from sqlalchemy import create_engine
except ImportError:  # pragma: no cover - SQLAlchemy optional when using gsheets
    create_engine = None  # type: ignore

try:
    from streamlit_gsheets import GSheetsConnection
except Exception:  # pragma: no cover - gsheets optional
    GSheetsConnection = None  # type: ignore


def get_gsheets_connection() -> Optional["GSheetsConnection"]:
    """Return a GSheetsConnection if configured via Streamlit secrets."""
    if GSheetsConnection is None:
        return None
    try:
        return st.connection("gsheets", type=GSheetsConnection)
    except Exception:
        return None


def get_connection(url: str | None = None):
    """Return a SQLAlchemy engine using Streamlit secrets or environment vars."""
    if create_engine is None:
        raise RuntimeError(
            "SQLAlchemy is required for SQL database access but is not installed."
        )
    try:
        conn = st.connection("postgresql")
        if hasattr(conn, "engine"):
            return conn.engine
        return create_engine(conn.url)
    except Exception:
        db_url = url or st.secrets.get("database_url") or os.environ.get(
            "DATABASE_URL", "sqlite:///data.db"
        )
        return create_engine(db_url)


def _sanitize_table_name(name: str) -> str:
    return Path(name).stem


def save_dataframe_to_table(df: pd.DataFrame, table_name: str, if_exists: str = "replace") -> None:
    """Save a DataFrame to the specified table (SQL or Google Sheet)."""
    gs_conn = get_gsheets_connection()
    tbl = _sanitize_table_name(table_name)
    if gs_conn is not None:
        gs_conn.update(worksheet=tbl, data=df)
    else:
        engine = get_connection()
        df.to_sql(tbl, engine, if_exists=if_exists, index=False)


def load_dataframe_from_table(table_name: str) -> pd.DataFrame:
    """Load a DataFrame from a SQL table or Google Sheet."""
    tbl = _sanitize_table_name(table_name)
    gs_conn = get_gsheets_connection()
    if gs_conn is not None:
        try:
            return gs_conn.read(worksheet=tbl)
        except Exception:
            return pd.DataFrame()
    engine = get_connection()
    try:
        return pd.read_sql(f"SELECT * FROM {tbl}", engine)
    except Exception:
        return pd.DataFrame()
