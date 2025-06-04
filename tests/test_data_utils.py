"""
Module-specific test file for the data utilities module.
Tests the data handling functionality.
"""

import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import data utilities for testing
from modules.data_utils import (
    ensure_data_dir, 
    load_dataframe, 
    save_dataframe, 
    ensure_columns, 
    safe_numeric_conversion,
    filter_dataframe,
    calculate_statistics,
    linear_regression
)

# Test fixtures
@pytest.fixture
def test_dataframe():
    """Create a test dataframe for testing data utilities."""
    return pd.DataFrame({
        "Study Name": ["Test Study", "Test Study", "Another Study"],
        "Wavelength (nm)": [920, 920, 800],
        "Modulation (%)": [10, 20, 30],
        "Measured Power (mW)": [1.5, 3.0, 4.5]
    })

@pytest.fixture
def test_data_dir(tmp_path):
    """Create a temporary data directory for testing."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir

# Test data utilities
@pytest.mark.unit
def test_ensure_columns(test_dataframe):
    """Test that ensure_columns adds missing columns with default values."""
    required_columns = ["Study Name", "Wavelength (nm)", "Modulation (%)", "Measured Power (mW)", "Notes"]
    defaults = {"Notes": ""}
    
    result = ensure_columns(test_dataframe, required_columns, defaults)
    
    assert "Notes" in result.columns
    assert result["Notes"].iloc[0] == ""
    assert len(result.columns) == 5

@pytest.mark.unit
def test_safe_numeric_conversion(test_dataframe):
    """Test that safe_numeric_conversion properly converts string values to numeric."""
    # Add a string value that should be converted
    test_dataframe.loc[3] = ["Test Study", "920", "30", "5.5"]
    
    numeric_columns = ["Wavelength (nm)", "Modulation (%)", "Measured Power (mW)"]
    result = safe_numeric_conversion(test_dataframe, numeric_columns)
    
    assert result["Wavelength (nm)"].dtype.kind in 'iuf'  # integer, unsigned int, or float
    assert result["Modulation (%)"].dtype.kind in 'iuf'
    assert result["Measured Power (mW)"].dtype.kind in 'iuf'
    assert result["Wavelength (nm)"].iloc[3] == 920
    assert result["Modulation (%)"].iloc[3] == 30
    assert result["Measured Power (mW)"].iloc[3] == 5.5

@pytest.mark.unit
def test_filter_dataframe(test_dataframe):
    """Test that filter_dataframe correctly filters based on column values."""
    filters = {"Study Name": "Test Study"}
    result = filter_dataframe(test_dataframe, filters)
    
    assert len(result) == 2
    assert all(result["Study Name"] == "Test Study")
    
    # Test with multiple filters
    filters = {"Study Name": "Test Study", "Wavelength (nm)": 920}
    result = filter_dataframe(test_dataframe, filters)
    
    assert len(result) == 2
    assert all(result["Study Name"] == "Test Study")
    assert all(result["Wavelength (nm)"] == 920)

@pytest.mark.unit
def test_calculate_statistics(test_dataframe):
    """Test that calculate_statistics correctly computes basic statistics."""
    stats = calculate_statistics(test_dataframe, "Measured Power (mW)")
    
    assert stats["mean"] == 3.0
    assert stats["median"] == 3.0
    assert stats["min"] == 1.5
    assert stats["max"] == 4.5
    assert stats["count"] == 3

@pytest.mark.unit
def test_linear_regression():
    """Test that linear_regression correctly computes regression parameters."""
    x = [1, 2, 3, 4, 5]
    y = [2, 4, 6, 8, 10]  # Perfect linear relationship: y = 2x
    
    result = linear_regression(x, y)
    
    assert round(result["slope"], 1) == 2.0
    assert round(result["intercept"], 1) == 0.0
    assert round(result["r_squared"], 1) == 1.0

@pytest.mark.unit
def test_linear_regression_edge_cases():
    """Test linear regression with edge cases."""
    # Test with single point
    result = linear_regression([1], [2])
    assert result["slope"] == 0
    assert result["intercept"] == 0
    assert result["r_squared"] == 0
    
    # Test with NaN values
    x = [1, 2, np.nan, 4, 5]
    y = [2, 4, np.nan, 8, 10]
    result = linear_regression(x, y)
    assert result["slope"] > 0  # Should still compute with valid points
    
    # Test with empty arrays
    result = linear_regression([], [])
    assert result["slope"] == 0
    assert result["intercept"] == 0
    assert result["r_squared"] == 0

@pytest.mark.unit
def test_filter_dataframe_edge_cases():
    """Test filter_dataframe with edge cases."""
    # Test with empty dataframe
    empty_df = pd.DataFrame()
    result = filter_dataframe(empty_df, {"column": "value"})
    assert result.empty
    
    # Test with non-existent column
    test_df = pd.DataFrame({"A": [1, 2, 3], "B": ["x", "y", "z"]})
    result = filter_dataframe(test_df, {"nonexistent": "value"})
    assert len(result) == len(test_df)  # Should return original if column doesn't exist

@pytest.mark.unit
def test_safe_numeric_conversion_edge_cases(test_dataframe):
    """Test safe_numeric_conversion with problematic data."""
    # Add some problematic data
    problematic_df = test_dataframe.copy()
    problematic_df.loc[len(problematic_df)] = ["Test", "not_a_number", "also_not_number", "definitely_not"]
    
    result = safe_numeric_conversion(problematic_df, ["Wavelength (nm)", "Modulation (%)", "Measured Power (mW)"])
    
    # Should convert what it can and set others to NaN
    assert pd.isna(result["Wavelength (nm)"].iloc[-1])
    assert pd.isna(result["Modulation (%)"].iloc[-1])
    assert pd.isna(result["Measured Power (mW)"].iloc[-1])

# Test file operations
@pytest.mark.unit
def test_save_and_load_dataframe(test_dataframe, test_data_dir):
    """Test that save_dataframe and load_dataframe work correctly."""
    file_path = test_data_dir / "test.csv"
    
    # Save the dataframe
    save_dataframe(test_dataframe, file_path)
    
    # Load the dataframe
    loaded_df = load_dataframe(file_path)
    
    # Check that the loaded dataframe matches the original
    pd.testing.assert_frame_equal(test_dataframe, loaded_df)

@pytest.mark.unit
def test_load_dataframe_with_default(test_data_dir):
    """Test that load_dataframe returns the default dataframe when file doesn't exist."""
    file_path = test_data_dir / "nonexistent.csv"
    default_df = pd.DataFrame({"A": [1, 2, 3]})
    
    loaded_df = load_dataframe(file_path, default_df)
    
    # Check that the loaded dataframe matches the default
    pd.testing.assert_frame_equal(default_df, loaded_df)

# Run tests if file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
