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
    
    try:
        # Try to get table info to check available columns
        table_info_response = supabase.table(tbl).select("*").limit(1).execute()
        
        # Get available columns from response
        if table_info_response and table_info_response.data:
            if len(table_info_response.data) > 0:
                available_columns = set(table_info_response.data[0].keys())
                
                # Create a mapping that only includes columns that exist in the database
                filtered_mapping = {}
                for col in df_copy.columns:
                    if col in db_column_mapping:
                        # Only include mappings where the target column exists in the database
                        if db_column_mapping[col] in available_columns:
                            filtered_mapping[col] = db_column_mapping[col]
                
                # Only rename with valid columns
                if filtered_mapping:
                    df_copy = df_copy.rename(columns=filtered_mapping)
                    
                # Filter out columns that don't exist in the database
                mapped_columns = set([db_column_mapping.get(col, col) for col in df_copy.columns])
                columns_to_drop = mapped_columns - available_columns - {'id'}  # Keep 'id' if present
                if columns_to_drop:
                    for col in df_copy.columns[:]:
                        mapped_col = db_column_mapping.get(col, col)
                        if mapped_col in columns_to_drop:
                            df_copy = df_copy.drop(columns=[col])
            else:
                # Default renaming if we can't determine the schema
                column_renames = {col: db_column_mapping.get(col, col) for col in df_copy.columns if col in db_column_mapping}
                if column_renames:
                    df_copy = df_copy.rename(columns=column_renames)
        else:
            # Default renaming if we can't determine the schema
            column_renames = {col: db_column_mapping.get(col, col) for col in df_copy.columns if col in db_column_mapping}
            if column_renames:
                df_copy = df_copy.rename(columns=column_renames)
                
    except Exception as e:
        st.warning(f"Could not verify database schema, attempting save with best guess: {str(e)}")
        # Default renaming if exception occurred
        column_renames = {col: db_column_mapping.get(col, col) for col in df_copy.columns if col in db_column_mapping}
        if column_renames:
            df_copy = df_copy.rename(columns=column_renames)
    
    # Convert NumPy values to Python native types for JSON serialization
    for col in df_copy.columns:
        if df_copy[col].dtype.kind in 'fiubO':  # float, integer, unsigned, boolean, object types
            df_copy[col] = df_copy[col].apply(lambda x: x.item() if hasattr(x, 'item') else x)
    
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
