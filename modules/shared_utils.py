"""
Shared utility functions used across multiple modules.
This module centralizes common functionality to reduce code duplication.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from modules.data_utils import load_dataframe, save_dataframe

# Constants - these should eventually move to a constants.py file
RIG_LOG_FILE = "rig_log.csv"

def get_default_rig_log_df():
    """Return a default rig log DataFrame structure.
    
    Returns:
    --------
    pandas.DataFrame
        Empty DataFrame with the standard rig log columns
    """
    return pd.DataFrame({
        "Date": [],
        "Researcher": [],
        "Activity": [],
        "Description": [],
        "Category": []
    })

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
        researcher = getattr(st.session_state, 'researcher', 'Unknown Researcher')
        
        # Create new entry
        new_entry = pd.DataFrame({
            "Date": [datetime.now().strftime("%Y-%m-%d %H:%M")],
            "Researcher": [researcher],
            "Activity": [activity],
            "Description": [description],
            "Category": [category]
        })
        
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
    return {
        "rig_log": ["Date", "Researcher", "Activity", "Description", "Category"],
        "measurements": ["Study Name", "Date", "Wavelength (nm)", "Researcher"],
        "laser_power": ["Study Name", "Date", "Wavelength (nm)", "Sensor Model", 
                       "Measurement Mode", "Fill Fraction (%)", "Modulation (%)", 
                       "Measured Power (mW)", "Notes"],
        "fluorescence": ["Study Name", "Date", "Wavelength (nm)", "Sample Type",
                        "Mean Intensity", "Variance", "Photon Sensitivity", "Notes"],
        "pulse_width": ["Study Name", "Date", "Wavelength (nm)", "GDD Value (fs²)",
                       "Mean Pixel Value", "Max Pixel Value", "Notes"]
    }

def create_default_dataframe(df_type, additional_columns=None):
    """Create a default DataFrame with standard columns.
    
    Parameters:
    -----------
    df_type : str
        Type of DataFrame to create ("rig_log", "measurements", etc.)
    additional_columns : list, optional
        Additional columns to include beyond the standard set
    
    Returns:
    --------
    pandas.DataFrame
        Empty DataFrame with the specified columns
    """
    column_sets = get_common_dataframe_columns()
    
    if df_type not in column_sets:
        raise ValueError(f"Unknown DataFrame type: {df_type}. Available types: {list(column_sets.keys())}")
    
    columns = column_sets[df_type].copy()
    
    if additional_columns:
        columns.extend(additional_columns)
    
    # Create empty DataFrame with these columns
    return pd.DataFrame({col: [] for col in columns}) 