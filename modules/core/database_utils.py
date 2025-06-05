import os
from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine


def get_connection(url: str | None = None):
    """Return a SQLAlchemy engine using Streamlit secrets or environment vars."""
    try:
        conn = st.connection("postgresql")
        if hasattr(conn, "engine"):
            return conn.engine
        # `st.connection` may return an object with .url attribute
        return create_engine(conn.url)
    except Exception:
        db_url = url or st.secrets.get("database_url") or os.environ.get(
            "DATABASE_URL", "sqlite:///data.db"
        )
        return create_engine(db_url)


def _sanitize_table_name(name: str) -> str:
    return Path(name).stem


def save_dataframe_to_table(df: pd.DataFrame, table_name: str, if_exists: str = "replace") -> None:
    """Save a DataFrame to the specified SQL table."""
    engine = get_connection()
    tbl = _sanitize_table_name(table_name)
    df.to_sql(tbl, engine, if_exists=if_exists, index=False)


def load_dataframe_from_table(table_name: str) -> pd.DataFrame:
    """Load a DataFrame from a SQL table. Returns empty DataFrame if not found."""
    engine = get_connection()
    tbl = _sanitize_table_name(table_name)
    try:
        return pd.read_sql(f"SELECT * FROM {tbl}", engine)
    except Exception:
        return pd.DataFrame()
