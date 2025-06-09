import os
import sys
from unittest.mock import patch

import pandas as pd
import pytest

from modules.core import database_utils
from modules.core.data_utils import load_dataframe, save_dataframe
from modules.core.constants import FILE_MAPPINGS
from modules.ui.templates import _save_measurement_data


class DummyGSheets:
    def __init__(self):
        self.tables = {}

    def update(self, worksheet: str, data):
        self.tables[worksheet] = data.copy()

    def read(self, worksheet: str):
        return self.tables.get(worksheet, pd.DataFrame())


@pytest.fixture
def mock_gsheets(monkeypatch):
    conn = DummyGSheets()
    monkeypatch.setattr(database_utils, "get_gsheets_connection", lambda: conn)
    return conn


@pytest.mark.unit
def test_save_measurement_data_appends(mock_gsheets):
    initial = pd.DataFrame({
        "Study Name": ["Existing"],
        "Date": ["2024-01-01"],
        "Researcher": ["Alice"],
    })
    save_dataframe(initial, FILE_MAPPINGS["laser_power"])

    form_data = {"Notes": "test note"}
    with patch.object(
        sys.modules["streamlit"], "session_state", {
            "current_timestamp": "2024-01-02",
            "study_name": "New Study",
            "researcher": "Bob",
        },
    ):
        result = _save_measurement_data("laser_power", form_data)

    assert result is True

    df = load_dataframe(FILE_MAPPINGS["laser_power"])
    assert len(df) == 2
    assert df.iloc[-1]["Study Name"] == "New Study"
    assert df.iloc[-1]["Researcher"] == "Bob"
    assert df.iloc[-1]["Date"] == "2024-01-02"
    assert df.iloc[-1]["Notes"] == "test note"
