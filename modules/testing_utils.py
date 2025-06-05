"""
Testing utilities for the Multiphoton Microscopy Guide application.
This module provides functions to test and validate template functions and modules.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Callable
import time
from datetime import datetime

from modules.constants import COLUMN_SCHEMAS, FILE_MAPPINGS
from modules.shared_utils import create_default_dataframe, load_measurement_dataframe

class TestResult:
    """Class to represent the result of a test operation."""
    
    def __init__(self, test_name: str, passed: bool, message: str = "", execution_time: float = 0.0):
        self.test_name = test_name
        self.passed = passed
        self.message = message
        self.execution_time = execution_time

class ModuleTester:
    """Class for testing module functionality and template compliance."""
    
    def __init__(self):
        self.test_results: List[TestResult] = []
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all available tests and return summary.
        
        Returns:
        --------
        Dict[str, Any]
            Test summary with results and statistics
        """
        self.test_results.clear()
        
        # Test basic functionality
        self._test_constants_availability()
        self._test_dataframe_schemas()
        self._test_template_functions()
        self._test_validation_functions()
        self._test_pdf_viewer_functionality()
        
        return self._generate_test_summary()
    
    def _test_constants_availability(self) -> None:
        """Test that all required constants are available."""
        start_time = time.time()
        
        try:
            # Test that column schemas exist
            assert COLUMN_SCHEMAS is not None, "COLUMN_SCHEMAS not available"
            assert len(COLUMN_SCHEMAS) > 0, "COLUMN_SCHEMAS is empty"
            
            # Test that file mappings exist
            assert FILE_MAPPINGS is not None, "FILE_MAPPINGS not available"
            assert len(FILE_MAPPINGS) > 0, "FILE_MAPPINGS is empty"
            
            # Test that keys match
            schema_keys = set(COLUMN_SCHEMAS.keys())
            mapping_keys = set(FILE_MAPPINGS.keys())
            assert schema_keys == mapping_keys, f"Schema and mapping keys don't match: {schema_keys} vs {mapping_keys}"
            
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                "Constants Availability", 
                True, 
                f"All constants available with {len(COLUMN_SCHEMAS)} schemas",
                execution_time
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                "Constants Availability", 
                False, 
                f"Constants test failed: {str(e)}",
                execution_time
            ))
    
    def _test_dataframe_schemas(self) -> None:
        """Test that DataFrame schemas are valid."""
        start_time = time.time()
        
        try:
            for df_type, columns in COLUMN_SCHEMAS.items():
                # Test that columns is a list
                assert isinstance(columns, list), f"Columns for {df_type} is not a list"
                
                # Test that columns are not empty
                assert len(columns) > 0, f"Columns for {df_type} is empty"
                
                # Test that all columns are strings
                for col in columns:
                    assert isinstance(col, str), f"Column {col} in {df_type} is not a string"
                
                # Test that create_default_dataframe works
                df = create_default_dataframe(df_type)
                assert isinstance(df, pd.DataFrame), f"create_default_dataframe failed for {df_type}"
                assert list(df.columns) == columns, f"DataFrame columns don't match schema for {df_type}"
            
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                "DataFrame Schemas", 
                True, 
                f"All {len(COLUMN_SCHEMAS)} schemas are valid",
                execution_time
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                "DataFrame Schemas", 
                False, 
                f"Schema test failed: {str(e)}",
                execution_time
            ))
    
    def _test_template_functions(self) -> None:
        """Test that template functions work correctly."""
        start_time = time.time()
        
        try:
            # Test create_default_dataframe for all types
            for df_type in COLUMN_SCHEMAS.keys():
                df = create_default_dataframe(df_type)
                assert isinstance(df, pd.DataFrame), f"create_default_dataframe failed for {df_type}"
                assert df.empty, f"Default DataFrame for {df_type} should be empty"
            
            # Test load_measurement_dataframe (should not fail)
            for df_type in FILE_MAPPINGS.keys():
                df = load_measurement_dataframe(df_type)
                assert isinstance(df, pd.DataFrame), f"load_measurement_dataframe failed for {df_type}"
            
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                "Template Functions", 
                True, 
                "All template functions work correctly",
                execution_time
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                "Template Functions", 
                False, 
                f"Template function test failed: {str(e)}",
                execution_time
            ))
    
    def _test_validation_functions(self) -> None:
        """Test that validation functions work correctly."""
        start_time = time.time()
        
        try:
            from modules.validation_utils import (
                validate_numeric_input, validate_wavelength, 
                validate_power, validate_required_field
            )
            
            # Test numeric validation
            result = validate_numeric_input(100, min_value=0, max_value=200)
            assert result.is_valid, "Numeric validation failed for valid input"
            
            result = validate_numeric_input(-10, min_value=0)
            assert not result.is_valid, "Numeric validation should fail for negative input"
            
            # Test wavelength validation
            result = validate_wavelength(900)
            assert result.is_valid, "Wavelength validation failed for valid input"
            
            result = validate_wavelength(50)
            assert not result.is_valid, "Wavelength validation should fail for invalid input"
            
            # Test power validation
            result = validate_power(50)
            assert result.is_valid, "Power validation failed for valid input"
            
            # Test required field validation
            result = validate_required_field("test")
            assert result.is_valid, "Required field validation failed for valid input"
            
            result = validate_required_field("")
            assert not result.is_valid, "Required field validation should fail for empty input"
            
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                "Validation Functions", 
                True, 
                "All validation functions work correctly",
                execution_time
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                "Validation Functions", 
                False, 
                f"Validation function test failed: {str(e)}",
                execution_time
            ))
    
    def _test_pdf_viewer_functionality(self) -> None:
        """Test PDF viewer functionality and annotation handling."""
        start_time = time.time()
        
        try:
            # Try to import pdf_viewer
            try:
                from streamlit_pdf_viewer import pdf_viewer
            except ImportError:
                execution_time = time.time() - start_time
                self.test_results.append(TestResult(
                    "PDF Viewer", 
                    False, 
                    "streamlit-pdf-viewer package not installed",
                    execution_time
                ))
                return
            
            # Test that we can call pdf_viewer with proper annotations parameter
            from pathlib import Path
            from unittest.mock import patch
            
            # Mock the pdf_viewer to avoid actual rendering during tests
            with patch('streamlit_pdf_viewer.pdf_viewer') as mock_viewer:
                mock_viewer.return_value = None
                
                # Test with empty annotations list - this should not raise TypeError
                test_path = "test.pdf"  # We're mocking anyway
                pdf_viewer(test_path, width=700, height=800, annotations=[])
                
                # Verify the call was made with correct parameters
                mock_viewer.assert_called_with(test_path, width=700, height=800, annotations=[])
            
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                "PDF Viewer", 
                True, 
                "PDF viewer can be called with annotations parameter",
                execution_time
            ))
            
        except TypeError as e:
            execution_time = time.time() - start_time
            if "annotations must be a list of dictionaries" in str(e):
                self.test_results.append(TestResult(
                    "PDF Viewer", 
                    False, 
                    f"PDF viewer annotations error: {str(e)}",
                    execution_time
                ))
            else:
                self.test_results.append(TestResult(
                    "PDF Viewer", 
                    False, 
                    f"PDF viewer other error: {str(e)}",
                    execution_time
                ))
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                "PDF Viewer", 
                False, 
                f"PDF viewer test failed: {str(e)}",
                execution_time
            ))
    
    def _generate_test_summary(self) -> Dict[str, Any]:
        """Generate a summary of test results."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.passed)
        failed_tests = total_tests - passed_tests
        total_time = sum(result.execution_time for result in self.test_results)
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "pass_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "total_execution_time": total_time,
            "test_results": self.test_results,
            "summary": f"{passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)"
        }

def create_test_data(df_type: str, num_records: int = 5) -> pd.DataFrame:
    """Create test data for a given DataFrame type.
    
    Parameters:
    -----------
    df_type : str
        Type of DataFrame to create test data for
    num_records : int
        Number of test records to create
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with test data
    """
    if df_type not in COLUMN_SCHEMAS:
        raise ValueError(f"Unknown DataFrame type: {df_type}")
    
    df = create_default_dataframe(df_type)
    
    # Generate test data based on the DataFrame type
    for i in range(num_records):
        if df_type == "rig_log":
            record = {
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Researcher": f"Test User {i+1}",
                "Activity": f"Test Activity {i+1}",
                "Description": f"Test description {i+1}",
                "Category": ["Measurement", "Optimization", "Maintenance"][i % 3]
            }
        elif df_type == "laser_power":
            record = {
                "Study Name": f"Test Study {i+1}",
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Wavelength (nm)": 900 + i * 10,
                "Researcher": f"Test User {i+1}",
                "Sensor Model": f"Sensor {i+1}",
                "Measurement Mode": "Stationary" if i % 2 == 0 else "Scanning",
                "Fill Fraction (%)": 100,
                "Modulation (%)": 10 + i * 5,
                "Measured Power (mW)": 1.0 + i * 0.5,
                "Notes": f"Test notes {i+1}"
            }
        elif df_type == "fluorescence":
            record = {
                "Study Name": f"Test Study {i+1}",
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Wavelength (nm)": 900 + i * 10,
                "Researcher": f"Test User {i+1}",
                "Sample Type": f"Sample {i+1}",
                "Mean Intensity": 100 + i * 50,
                "Variance": 25 + i * 10,
                "Photon Sensitivity": 0.25 + i * 0.01,
                "Notes": f"Test notes {i+1}"
            }
        elif df_type == "pulse_width":
            record = {
                "Study Name": f"Test Study {i+1}",
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Wavelength (nm)": 900 + i * 10,
                "Researcher": f"Test User {i+1}",
                "GDD Value (fs²)": -2000 + i * 1000,
                "Mean Pixel Value": 500 + i * 100,
                "Max Pixel Value": 800 + i * 100,
                "Notes": f"Test notes {i+1}"
            }
        else:
            # Generic record for unknown types
            record = {col: f"Test value {i+1}" for col in COLUMN_SCHEMAS[df_type]}
        
        # Convert to DataFrame row and append
        new_row = pd.DataFrame([record])
        df = pd.concat([df, new_row], ignore_index=True)
    
    return df

def benchmark_function(func: Callable, *args, iterations: int = 100, **kwargs) -> Dict[str, float]:
    """Benchmark a function's performance.
    
    Parameters:
    -----------
    func : Callable
        Function to benchmark
    iterations : int
        Number of iterations to run
    *args, **kwargs
        Arguments to pass to the function
    
    Returns:
    --------
    Dict[str, float]
        Benchmark results with timing statistics
    """
    times = []
    
    for _ in range(iterations):
        start_time = time.time()
        try:
            func(*args, **kwargs)
        except Exception:
            # If function fails, still record the time
            pass
        execution_time = time.time() - start_time
        times.append(execution_time)
    
    return {
        "iterations": iterations,
        "total_time": sum(times),
        "average_time": np.mean(times),
        "min_time": min(times),
        "max_time": max(times),
        "std_time": np.std(times)
    }

def validate_module_structure(module_name: str, 
                            required_functions: List[str],
                            module) -> TestResult:
    """Validate that a module follows the expected structure.
    
    Parameters:
    -----------
    module_name : str
        Name of the module being tested
    required_functions : List[str]
        List of function names that should exist in the module
    module : module
        The imported module to test
    
    Returns:
    --------
    TestResult
        Result of the structure validation
    """
    start_time = time.time()
    
    try:
        missing_functions = []
        for func_name in required_functions:
            if not hasattr(module, func_name):
                missing_functions.append(func_name)
        
        execution_time = time.time() - start_time
        
        if missing_functions:
            return TestResult(
                f"{module_name} Structure",
                False,
                f"Missing functions: {', '.join(missing_functions)}",
                execution_time
            )
        else:
            return TestResult(
                f"{module_name} Structure",
                True,
                f"All {len(required_functions)} required functions found",
                execution_time
            )
    
    except Exception as e:
        execution_time = time.time() - start_time
        return TestResult(
            f"{module_name} Structure",
            False,
            f"Structure validation failed: {str(e)}",
            execution_time
        )

def run_quick_validation_test() -> bool:
    """Run a quick validation test to ensure the system is working.
    
    Returns:
    --------
    bool
        True if all quick tests pass
    """
    try:
        # Test that we can create DataFrames
        for df_type in COLUMN_SCHEMAS.keys():
            df = create_default_dataframe(df_type)
            if not isinstance(df, pd.DataFrame):
                return False
        
        # Test that validation functions work
        from modules.validation_utils import validate_numeric_input
        result = validate_numeric_input(100)
        if not result.is_valid:
            return False
        
        return True
        
    except Exception:
        return False 