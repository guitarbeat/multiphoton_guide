"""
Simple script to test if the Supabase connection is working properly.
This script loads data from the fluorescence_measurements table, adds a test entry,
and then verifies if the entry was saved correctly.
"""

import pandas as pd
from datetime import datetime
from modules.core.database_utils import get_supabase_client, load_dataframe_from_table, save_dataframe_to_table
import streamlit as st

def test_supabase_connection():
    """Test if the Supabase connection is working."""
    try:
        # Test client connection
        supabase = get_supabase_client()
        print("✅ Successfully connected to Supabase!")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return False

def test_data_loading():
    """Test if data loading from Supabase works."""
    try:
        # Load fluorescence measurements
        df = load_dataframe_from_table("fluorescence_measurements")
        if df.empty:
            print("⚠️ Fluorescence measurements table exists but is empty")
        else:
            print(f"✅ Successfully loaded {len(df)} fluorescence measurements")
            print("\nSample data:")
            print(df.head(3))
        return True
    except Exception as e:
        print(f"❌ Failed to load data: {e}")
        return False

def test_data_saving():
    """Test if data saving to Supabase works."""
    try:
        # Create a test record with ISO format string for date instead of Timestamp
        current_time = datetime.now().isoformat()
        test_data = pd.DataFrame({
            "intensity_value": [999],
            "variance_value": [888.8],
            "pixel_count": [777],
            "notes": ["Test entry - please ignore"],
            "Date": [current_time],
            "Researcher": ["Test Script"],
            "Study Name": ["Backend Test"],
            "Wavelength (nm)": [920.0]
        })
        
        # Save the test record
        save_dataframe_to_table(test_data, "fluorescence_measurements", "append")
        print("✅ Successfully saved test data")
        
        # Verify the save worked by loading the data again
        df = load_dataframe_from_table("fluorescence_measurements")
        
        # Find test entries by checking intensity value (unique identifier)
        test_entries = df[df["intensity_value"] == 999]
        
        if not test_entries.empty:
            print("✅ Successfully verified test data was saved")
            print("\nRetrieved test data:")
            print(test_entries.iloc[-1:])
            return True
        else:
            print("❌ Test data was not found after saving")
            return False
            
    except Exception as e:
        print(f"❌ Failed to save data: {e}")
        return False

if __name__ == "__main__":
    print("\n===== TESTING SUPABASE BACKEND =====\n")
    
    # Run tests
    connection_ok = test_supabase_connection()
    if not connection_ok:
        print("\n❌ Connection test failed. Check your .streamlit/secrets.toml file.")
        exit(1)
        
    load_ok = test_data_loading()
    if not load_ok:
        print("\n❌ Data loading test failed.")
    
    save_ok = test_data_saving()
    if not save_ok:
        print("\n❌ Data saving test failed.")
    
    # Summary
    if connection_ok and load_ok and save_ok:
        print("\n✅ All tests passed! Your Supabase backend is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.") 