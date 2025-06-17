from pathlib import Path

import pandas as pd
import streamlit as st
from supabase import create_client, Client

def get_supabase_client() -> Client:
    """Return a configured Supabase client."""
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["api_key"]
        return create_client(url, key)
    except Exception as exc:
        raise RuntimeError("Supabase connection is not configured correctly") from exc

def _sanitize_table_name(name: str) -> str:
    return Path(name).stem

def save_dataframe_to_table(
    df: pd.DataFrame, table_name: str, if_exists: str = "replace"
) -> None:
    """Save a DataFrame to the specified Supabase table."""
    supabase = get_supabase_client()
    tbl = _sanitize_table_name(table_name)
    
    # Create a copy to avoid modifying the original dataframe
    df_copy = df.copy()
    
    # Standardize column names for database storage
    db_column_mapping = {
        "Date": "date",
        "Researcher": "researcher",
        "Activity": "activity", 
        "Description": "description",
        "Category": "category", 
        "Notes": "notes",
        "Wavelength (nm)": "wavelength", 
        "Modulation (%)": "modulation",
        "Fill Fraction (%)": "fill_fraction", 
        "Measured Power (mW)": "measured_power",
        "Sensor Model": "sensor_model", 
        "Measurement Mode": "measurement_mode",
        "Study Name": "study_name",
        "Pump Current (mA)": "pump_current_ma",
        "Expected Power (W)": "expected_power_w",
        "Temperature (°C)": "temperature_c",
        "Measured Power (W)": "measured_power_w",
        "Pulse Width (fs)": "pulse_width_fs",
        "Grating Position": "grating_position",
        "Fan Status": "fan_status"
    }
    
    # Rename columns using the mapping
    column_renames = {col: db_column_mapping.get(col, col) for col in df_copy.columns if col in db_column_mapping}
    if column_renames:
        df_copy = df_copy.rename(columns=column_renames)
    
    # Convert DataFrame to records
    records = df_copy.to_dict(orient="records")
    
    if if_exists == "replace":
        # Delete all records from the table first (requires WHERE clause)
        supabase.table(tbl).delete().neq('id', 0).execute()
    
    # Insert the records
    if records:
        supabase.table(tbl).insert(records).execute()

def load_dataframe_from_table(table_name: str) -> pd.DataFrame:
    """Load a DataFrame from a Supabase table."""
    tbl = _sanitize_table_name(table_name)
    try:
        supabase = get_supabase_client()
        response = supabase.table(tbl).select("*").execute()
        data = response.data
        df = pd.DataFrame(data) if data else pd.DataFrame()
        
        # Standardize column names to match expected format
        # Convert any lowercase "date" to "Date", etc.
        column_mapping = {}
        expected_columns = {"date": "Date", "researcher": "Researcher", 
                           "activity": "Activity", "description": "Description", 
                           "category": "Category", "notes": "Notes",
                           "wavelength": "Wavelength (nm)", "modulation": "Modulation (%)",
                           "fill_fraction": "Fill Fraction (%)", "measured_power": "Measured Power (mW)",
                           "sensor_model": "Sensor Model", "measurement_mode": "Measurement Mode",
                           "study_name": "Study Name",
                           "pump_current_ma": "Pump Current (mA)", "expected_power_w": "Expected Power (W)",
                           "temperature_c": "Temperature (°C)", "measured_power_w": "Measured Power (W)",
                           "pulse_width_fs": "Pulse Width (fs)", "grating_position": "Grating Position",
                           "fan_status": "Fan Status"}
        
        for col in df.columns:
            lower_col = col.lower()
            if lower_col in expected_columns:
                column_mapping[col] = expected_columns[lower_col]
        
        if column_mapping:
            df = df.rename(columns=column_mapping)
            
        # Ensure created_at doesn't interfere with Date
        if "created_at" in df.columns and "Date" not in df.columns:
            df["Date"] = df["created_at"]
            
        return df
    except Exception as exc:
        # Surface the error to the UI for easier debugging
        st.error(f"Failed to load data from table '{tbl}': {exc}")
        return pd.DataFrame()
