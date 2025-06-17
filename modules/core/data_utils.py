"""
Data utilities for the Multiphoton Microscopy Guide application.
Handles data loading, saving, and processing.
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

from .database_utils import (
    load_dataframe_from_table,
    save_dataframe_to_table,
)

# Define data directory (legacy compatibility for table name conversion)
DATA_DIR = Path("data")


def ensure_data_dir():
    """Ensure the data directory exists (retained for backward compatibility)."""
    os.makedirs(DATA_DIR, exist_ok=True)


def save_dataframe(df, filename):
    """
    Save a dataframe to a Google Sheet table.

    Parameters:
    -----------
    df : pandas.DataFrame
        The dataframe to save
    filename : str
        The filename to save to (without path)

    Returns:
    --------
    str
        Path to the saved file
    """
    save_dataframe_to_table(df, filename)
    return filename


def load_dataframe(filename, default_df=None):
    """
    Load a dataframe from a Google Sheet or return a default if it doesn't exist.

    Parameters:
    -----------
    filename : str
        The filename to load from (without path)
    default_df : pandas.DataFrame, optional
        Default dataframe to return if file doesn't exist

    Returns:
    --------
    pandas.DataFrame
        The loaded or default dataframe
    """
    df = load_dataframe_from_table(filename)
    if not df.empty:
        return df
    if default_df is not None:
        return default_df
    return pd.DataFrame()


def ensure_columns(df, required_columns, defaults=None):
    """
    Ensure dataframe has all required columns, adding them with defaults if missing.

    Parameters:
    -----------
    df : pandas.DataFrame
        The dataframe to check
    required_columns : list
        List of column names that should exist
    defaults : dict, optional
        Dictionary of default values for each column

    Returns:
    --------
    pandas.DataFrame
        DataFrame with all required columns
    """
    if defaults is None:
        defaults = {}

    # Create a copy to avoid modifying the original
    result_df = df.copy()

    # Add any missing columns with default values
    for col in required_columns:
        if col not in result_df.columns:
            default_val = defaults.get(col, "")
            result_df[col] = default_val

    return result_df


def safe_numeric_conversion(df, columns):
    """
    Safely convert specified columns to numeric, coercing errors to NaN.

    Parameters:
    -----------
    df : pandas.DataFrame
        The dataframe to process
    columns : list
        List of column names to convert to numeric

    Returns:
    --------
    pandas.DataFrame
        DataFrame with specified columns converted to numeric
    """
    result_df = df.copy()
    for col in columns:
        if col in result_df.columns:
            result_df[col] = pd.to_numeric(result_df[col], errors="coerce")
    return result_df


def filter_dataframe(df, filters):
    """
    Filter a dataframe based on column-value pairs.

    Parameters:
    -----------
    df : pandas.DataFrame
        The dataframe to filter
    filters : dict
        Dictionary of column-value pairs to filter on

    Returns:
    --------
    pandas.DataFrame
        Filtered dataframe
    """
    if df.empty:
        return df

    filtered_df = df.copy()
    for column, value in filters.items():
        if column in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[column] == value]

    return filtered_df


def calculate_statistics(df, value_column):
    """
    Calculate basic statistics for a numeric column.

    Parameters:
    -----------
    df : pandas.DataFrame
        The dataframe to analyze
    value_column : str
        The column to calculate statistics for

    Returns:
    --------
    dict
        Dictionary of statistics
    """
    if df.empty or value_column not in df.columns:
        return {"mean": 0, "median": 0, "min": 0, "max": 0, "count": 0}

    # Ensure numeric conversion
    values = pd.to_numeric(df[value_column], errors="coerce").dropna()

    if len(values) == 0:
        return {"mean": 0, "median": 0, "min": 0, "max": 0, "count": 0}

    return {
        "mean": values.mean(),
        "median": values.median(),
        "min": values.min(),
        "max": values.max(),
        "count": len(values),
    }


def linear_regression(x_values, y_values):
    """
    Calculate linear regression between x and y values.

    Parameters:
    -----------
    x_values : array-like
        Independent variable values
    y_values : array-like
        Dependent variable values

    Returns:
    --------
    dict
        Dictionary with slope, intercept, and r_squared
    """
    # Ensure x_values is 1D
    if hasattr(x_values, "shape") and len(x_values.shape) > 1:
        x_values = x_values.flatten()

    # Convert to numpy arrays if they aren't already
    x_values = np.array(x_values)
    y_values = np.array(y_values)

    # Remove NaN values
    valid_indices = ~(np.isnan(x_values) | np.isnan(y_values))
    x = x_values[valid_indices]
    y = y_values[valid_indices]

    if len(x) < 2:
        return {"slope": 0, "intercept": 0, "r_squared": 0}

    # Calculate linear regression
    n = len(x)
    sum_x = np.sum(x)
    sum_y = np.sum(y)
    sum_xy = np.sum(x * y)
    sum_xx = np.sum(x * x)

    # Calculate slope and intercept
    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
    intercept = (sum_y - slope * sum_x) / n

    # Calculate R-squared
    y_pred = slope * x + intercept
    ss_total = np.sum((y - np.mean(y)) ** 2)
    ss_residual = np.sum((y - y_pred) ** 2)
    r_squared = 1 - (ss_residual / ss_total) if ss_total != 0 else 0

    return {"slope": slope, "intercept": intercept, "r_squared": r_squared}


def exponential_fit(x_values, y_values):
    """
    Calculate exponential fit between x and y values of form y = a * exp(b * x) + c

    Parameters:
    -----------
    x_values : array-like
        Independent variable values
    y_values : array-like
        Dependent variable values

    Returns:
    --------
    dict
        Dictionary with fit parameters (a, b, c) and r_squared
    """
    # Function for exponential curve y = a * exp(b * x) + c
    def exp_func(x, a, b, c):
        return a * np.exp(b * x) + c

    # Ensure x_values is 1D
    if hasattr(x_values, "shape") and len(x_values.shape) > 1:
        x_values = x_values.flatten()

    # Convert to numpy arrays if they aren't already
    x_values = np.array(x_values)
    y_values = np.array(y_values)

    # Remove NaN values
    valid_indices = ~(np.isnan(x_values) | np.isnan(y_values))
    x = x_values[valid_indices]
    y = y_values[valid_indices]

    if len(x) < 3:
        return {"a": 0, "b": 0, "c": 0, "r_squared": 0}

    try:
        # Initial guess for parameters
        p0 = [1.0, 0.001, 0.0]
        
        # Perform the curve fit
        popt, pcov = curve_fit(exp_func, x, y, p0=p0, maxfev=10000)
        a, b, c = popt
        
        # Calculate R-squared
        y_pred = exp_func(x, a, b, c)
        ss_total = np.sum((y - np.mean(y)) ** 2)
        ss_residual = np.sum((y - y_pred) ** 2)
        r_squared = 1 - (ss_residual / ss_total) if ss_total != 0 else 0
        
        return {"a": a, "b": b, "c": c, "r_squared": r_squared}
    
    except Exception as e:
        # If fitting fails, return zeros
        return {"a": 0, "b": 0, "c": 0, "r_squared": 0, "error": str(e)}


def save_fit_parameters(table_name, fit_params, metadata=None):
    """
    Save fit parameters to a database table.
    
    Parameters:
    -----------
    table_name : str
        Name of the table to save to
    fit_params : dict
        Dictionary of fit parameters
    metadata : dict, optional
        Additional metadata to save with the parameters
        
    Returns:
    --------
    bool
        Success or failure
    """
    if metadata is None:
        metadata = {}
        
    # Create a dataframe with the fit parameters
    df = pd.DataFrame({
        **fit_params,
        **metadata,
        'date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
    }, index=[0])
    
    try:
        save_dataframe_to_table(df, f"{table_name}_fits", "append")
        return True
    except Exception:
        return False
