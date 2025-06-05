"""
Shared utility functions used across multiple modules.
This module centralizes common functionality to reduce code duplication.
"""

from datetime import datetime

import pandas as pd
import streamlit as st

from .constants import (
    COLUMN_SCHEMAS,
    FILE_MAPPINGS,
    LAYOUT_RATIOS,
    RIG_LOG_COLUMNS,
    RIG_LOG_FILE,
)
from .data_utils import load_dataframe, save_dataframe


def get_default_rig_log_df():
    """Return a default rig log DataFrame structure.

    Returns:
    --------
    pandas.DataFrame
        Empty DataFrame with the standard rig log columns
    """
    return pd.DataFrame({col: [] for col in RIG_LOG_COLUMNS})


def add_to_rig_log(activity, description, category="General"):
    """Add an entry to the rig log.

    This centralized function handles adding entries to the rig log,
    eliminating the need for duplicate implementations across modules.

    Parameters:
    -----------
    activity : str
        Brief description of the activity performed
    description : str
        Detailed description of what was done
    category : str, optional
        Category of the activity (default: "General")
        Common values: "Measurement", "Optimization", "Maintenance", "Calibration"

    Returns:
    --------
    bool
        True if the entry was successfully added, False otherwise
    """
    try:
        # Load existing rig log
        rig_log_df = load_dataframe(RIG_LOG_FILE, get_default_rig_log_df())

        # Get researcher from session state, with fallback
        researcher = getattr(st.session_state, "researcher", "Unknown Researcher")

        # Create new entry
        new_entry = pd.DataFrame(
            {
                "Date": [datetime.now().strftime("%Y-%m-%d %H:%M")],
                "Researcher": [researcher],
                "Activity": [activity],
                "Description": [description],
                "Category": [category],
            }
        )

        # Append new entry
        updated_log = pd.concat([rig_log_df, new_entry], ignore_index=True)

        # Save updated log
        save_dataframe(updated_log, RIG_LOG_FILE)

        return True

    except Exception as e:
        # Fail gracefully without breaking the UI
        print(f"Warning: Failed to add entry to rig log: {e}")
        return False


def get_common_dataframe_columns():
    """Get commonly used DataFrame column definitions.

    Returns:
    --------
    dict
        Dictionary of common column sets for different data types
    """
    return COLUMN_SCHEMAS


def create_default_dataframe(df_type, additional_columns=None):
    """Create a default DataFrame with standard columns.

    Parameters:
    -----------
    df_type : str
        Type of DataFrame to create ("rig_log", "laser_power", "fluorescence", "pulse_width")
    additional_columns : list, optional
        Additional columns to include beyond the standard set

    Returns:
    --------
    pandas.DataFrame
        Empty DataFrame with the specified columns
    """
    if df_type not in COLUMN_SCHEMAS:
        raise ValueError(
            f"Unknown DataFrame type: {df_type}. Available types: {list(COLUMN_SCHEMAS.keys())}"
        )

    columns = COLUMN_SCHEMAS[df_type].copy()

    if additional_columns:
        columns.extend(additional_columns)

    # Create empty DataFrame with these columns
    return pd.DataFrame({col: [] for col in columns})


def load_measurement_dataframe(df_type):
    """Load a measurement DataFrame with proper defaults.

    This template function standardizes how measurement DataFrames are loaded
    across modules, reducing code duplication.

    Parameters:
    -----------
    df_type : str
        Type of DataFrame to load ("laser_power", "fluorescence", "pulse_width", "rig_log")

    Returns:
    --------
    pandas.DataFrame
        Loaded DataFrame with all required columns
    """
    if df_type not in FILE_MAPPINGS:
        raise ValueError(
            f"Unknown DataFrame type: {df_type}. Available types: {list(FILE_MAPPINGS.keys())}"
        )

    filename = FILE_MAPPINGS[df_type]
    default_df = create_default_dataframe(df_type)

    return load_dataframe(filename, default_df)


def create_two_column_layout(
    left_function, right_function, layout_type="theory_practice"
):
    """Create a standardized two-column layout.

    This template function reduces duplication of common layout patterns across modules.

    Parameters:
    -----------
    left_function : callable
        Function to render content in the left column
    right_function : callable
        Function to render content in the right column
    layout_type : str, optional
        Type of layout ratio to use (default: "theory_practice")
        Options: "theory_practice", "form_data", "equal", "narrow_wide", "wide_narrow"
    """
    if layout_type not in LAYOUT_RATIOS:
        raise ValueError(
            f"Unknown layout type: {layout_type}. Available types: {list(LAYOUT_RATIOS.keys())}"
        )

    col1, col2 = st.columns(LAYOUT_RATIOS[layout_type])

    with col1:
        left_function()

    with col2:
        right_function()


def create_measurement_form_template(df_type, form_fields, form_key="measurement_form"):
    """Template for creating measurement forms with consistent structure.

    Parameters:
    -----------
    df_type : str
        Type of measurement ("laser_power", "fluorescence", "pulse_width")
    form_fields : dict
        Dictionary of field configurations
    form_key : str, optional
        Unique key for the form

    Returns:
    --------
    tuple
        (submitted, form_data) where submitted is bool and form_data is dict
    """
    with st.form(key=form_key):
        form_data = {}

        # Common fields first
        col1, col2 = st.columns(2)

        # Add specific form fields based on configuration
        for field_name, field_config in form_fields.items():
            field_type = field_config.get("type", "text")

            if field_type == "number":
                form_data[field_name] = st.number_input(
                    field_config["label"],
                    min_value=field_config.get("min_value", 0),
                    max_value=field_config.get("max_value", None),
                    value=field_config.get("value", 0),
                    step=field_config.get("step", 1),
                    help=field_config.get("help", ""),
                )
            elif field_type == "text":
                form_data[field_name] = st.text_input(
                    field_config["label"],
                    value=field_config.get("value", ""),
                    help=field_config.get("help", ""),
                )
            elif field_type == "textarea":
                form_data[field_name] = st.text_area(
                    field_config["label"],
                    value=field_config.get("value", ""),
                    help=field_config.get("help", ""),
                )
            elif field_type == "selectbox":
                form_data[field_name] = st.selectbox(
                    field_config["label"],
                    options=field_config.get("options", []),
                    index=field_config.get("index", 0),
                    help=field_config.get("help", ""),
                )

        submitted = st.form_submit_button("Add Measurement", type="primary")

        return submitted, form_data
