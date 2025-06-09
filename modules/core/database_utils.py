from pathlib import Path

import pandas as pd
import streamlit as st

try:
    import gspread
    from gspread_dataframe import get_as_dataframe, set_with_dataframe
except Exception:  # pragma: no cover - optional dependency
    gspread = None  # type: ignore
    get_as_dataframe = None  # type: ignore
    set_with_dataframe = None  # type: ignore


class GSpreadWrapper:
    """Thin wrapper around gspread to mimic the GSheetsConnection API."""

    def __init__(self, creds: dict, spreadsheet_url: str):
        self.client = gspread.service_account_from_dict(creds)
        self.sheet = self.client.open_by_url(spreadsheet_url)

    def _worksheet(self, name: str):
        try:
            return self.sheet.worksheet(name)
        except gspread.exceptions.WorksheetNotFound:
            return self.sheet.add_worksheet(title=name, rows="100", cols="20")

    def update(self, worksheet: str, data: pd.DataFrame) -> None:
        ws = self._worksheet(worksheet)
        ws.clear()
        set_with_dataframe(ws, data, include_index=False, resize=True)

    def read(self, worksheet: str) -> pd.DataFrame:
        ws = self._worksheet(worksheet)
        df = get_as_dataframe(ws, evaluate_formulas=True)
        df.dropna(axis=0, how="all", inplace=True)
        df.dropna(axis=1, how="all", inplace=True)
        return df


def get_gsheets_connection() -> "GSpreadWrapper":
    """Return a configured gspread wrapper or raise an error."""
    if gspread is None:
        raise RuntimeError("gspread is required for Google Sheets storage but is not installed")

    try:
        cfg = st.secrets["connections"]["gsheets"]
        creds = {k: v for k, v in cfg.items() if k not in {"spreadsheet", "worksheet"}}
        url = cfg["spreadsheet"]
    except Exception as exc:  # pragma: no cover - configuration errors
        raise RuntimeError("Google Sheets connection 'gsheets' is not configured") from exc

    return GSpreadWrapper(creds, url)




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
    try:
        conn = get_gsheets_connection()
        return conn.read(worksheet=tbl)
    except Exception as exc:
        # Surface the error to the UI for easier debugging
        st.error(f"Failed to load data from worksheet '{tbl}': {exc}")
        return pd.DataFrame()
