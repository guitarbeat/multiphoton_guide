"""
Validation utilities for the Multiphoton Microscopy Guide application.
This module provides standardized validation functions and error handling patterns.
"""

import streamlit as st
import numpy as np
from typing import Union, Dict, Any, Optional
from .constants import WAVELENGTH_RANGE, POWER_RANGE, GDD_RANGE

class ValidationResult:
    """Class to represent the result of a validation operation."""
    
    def __init__(self, is_valid: bool, message: str = "", field_name: str = "", value: Any = None):
        self.is_valid = is_valid
        self.message = message
        self.field_name = field_name
        self.value = value

class UIMessageType:
    """Standardized message types for consistent UI feedback."""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"

def validate_numeric_input(value: Union[int, float, str], 
                          min_value: Optional[float] = None,
                          max_value: Optional[float] = None,
                          field_name: str = "Value",
                          allow_zero: bool = True) -> ValidationResult:
    """Validate numeric input with optional range checking.
    
    Parameters:
    -----------
    value : Union[int, float, str]
        The value to validate
    min_value : Optional[float]
        Minimum allowed value (inclusive)
    max_value : Optional[float]  
        Maximum allowed value (inclusive)
    field_name : str
        Name of the field being validated for error messages
    allow_zero : bool
        Whether zero is allowed (default: True)
    
    Returns:
    --------
    ValidationResult
        Validation result with is_valid flag and message
    """
    try:
        numeric_value = float(value)
        
        # Check for NaN
        if np.isnan(numeric_value):
            return ValidationResult(False, f"{field_name} cannot be NaN", field_name, value)
        
        # Check for zero if not allowed
        if not allow_zero and numeric_value == 0:
            return ValidationResult(False, f"{field_name} must be greater than 0", field_name, value)
        
        # Check minimum value
        if min_value is not None and numeric_value < min_value:
            return ValidationResult(False, f"{field_name} must be at least {min_value}", field_name, value)
        
        # Check maximum value
        if max_value is not None and numeric_value > max_value:
            return ValidationResult(False, f"{field_name} must not exceed {max_value}", field_name, value)
        
        return ValidationResult(True, f"{field_name} is valid", field_name, numeric_value)
        
    except (ValueError, TypeError):
        return ValidationResult(False, f"{field_name} must be a valid number", field_name, value)

def validate_wavelength(wavelength: Union[int, float, str]) -> ValidationResult:
    """Validate wavelength input using application-specific ranges.
    
    Parameters:
    -----------
    wavelength : Union[int, float, str]
        Wavelength value in nanometers
    
    Returns:
    --------
    ValidationResult
        Validation result with context-specific messaging
    """
    result = validate_numeric_input(
        wavelength, 
        min_value=WAVELENGTH_RANGE["min"], 
        max_value=WAVELENGTH_RANGE["max"],
        field_name="Wavelength",
        allow_zero=False
    )
    
    if result.is_valid:
        # Add helpful context for common wavelengths
        if result.value in WAVELENGTH_RANGE["common"]:
            result.message = f"Wavelength {result.value} nm is commonly used for multiphoton microscopy"
        else:
            result.message = f"Wavelength {result.value} nm is within valid range ({WAVELENGTH_RANGE['min']}-{WAVELENGTH_RANGE['max']} nm)"
    
    return result

def validate_power(power: Union[int, float, str]) -> ValidationResult:
    """Validate laser power input.
    
    Parameters:
    -----------
    power : Union[int, float, str]
        Power value in milliwatts
    
    Returns:
    --------
    ValidationResult
        Validation result with power-specific messaging
    """
    result = validate_numeric_input(
        power,
        min_value=POWER_RANGE["min"],
        max_value=POWER_RANGE["max"],
        field_name="Power",
        allow_zero=False
    )
    
    if result.is_valid and result.value > POWER_RANGE["typical_max"]:
        result.message = f"Power {result.value} mW is high - ensure sample safety"
    
    return result

def validate_gdd(gdd: Union[int, float, str]) -> ValidationResult:
    """Validate Group Delay Dispersion (GDD) input.
    
    Parameters:
    -----------
    gdd : Union[int, float, str]
        GDD value in fs²
    
    Returns:
    --------
    ValidationResult
        Validation result with GDD-specific messaging
    """
    return validate_numeric_input(
        gdd,
        min_value=GDD_RANGE["min"],
        max_value=GDD_RANGE["max"],
        field_name="GDD",
        allow_zero=True
    )

def validate_required_field(value: Any, field_name: str = "Field") -> ValidationResult:
    """Validate that a required field is not empty.
    
    Parameters:
    -----------
    value : Any
        The value to check
    field_name : str
        Name of the field for error messages
    
    Returns:
    --------
    ValidationResult
        Validation result
    """
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return ValidationResult(False, f"{field_name} is required", field_name, value)
    
    return ValidationResult(True, f"{field_name} is provided", field_name, value)

def validate_form_data(form_data: Dict[str, Any], field_configs: Dict[str, Dict]) -> Dict[str, ValidationResult]:
    """Validate an entire form's data using field-specific configurations.
    
    Parameters:
    -----------
    form_data : Dict[str, Any]
        Dictionary of form field values
    field_configs : Dict[str, Dict]
        Dictionary of field configurations with validation rules
    
    Returns:
    --------
    Dict[str, ValidationResult]
        Dictionary mapping field names to their validation results
    """
    results = {}
    
    for field_name, field_config in field_configs.items():
        value = form_data.get(field_name)
        
        # Check if field is required
        if field_config.get('required', False):
            required_result = validate_required_field(value, field_name)
            if not required_result.is_valid:
                results[field_name] = required_result
                continue
        
        # Apply specific validation based on field type
        field_type = field_config.get('validation_type', 'none')
        
        if field_type == 'numeric':
            results[field_name] = validate_numeric_input(
                value,
                min_value=field_config.get('min_value'),
                max_value=field_config.get('max_value'),
                field_name=field_name,
                allow_zero=field_config.get('allow_zero', True)
            )
        elif field_type == 'wavelength':
            results[field_name] = validate_wavelength(value)
        elif field_type == 'power':
            results[field_name] = validate_power(value)
        elif field_type == 'gdd':
            results[field_name] = validate_gdd(value)
        else:
            # Default: just check if required
            results[field_name] = ValidationResult(True, f"{field_name} passed validation", field_name, value)
    
    return results

def display_validation_message(result: ValidationResult, message_type: str = None) -> None:
    """Display a validation message using appropriate Streamlit component.
    
    Parameters:
    -----------
    result : ValidationResult
        The validation result to display
    message_type : str, optional
        Override the message type (success, warning, error, info)
    """
    if message_type is None:
        # Auto-determine message type based on validation result
        message_type = UIMessageType.SUCCESS if result.is_valid else UIMessageType.ERROR
    
    if message_type == UIMessageType.SUCCESS:
        st.success(result.message)
    elif message_type == UIMessageType.WARNING:
        st.warning(result.message)
    elif message_type == UIMessageType.ERROR:
        st.error(result.message)
    else:  # INFO
        st.info(result.message)

def display_form_validation_results(results: Dict[str, ValidationResult], 
                                   show_success: bool = False) -> bool:
    """Display validation results for an entire form.
    
    Parameters:
    -----------
    results : Dict[str, ValidationResult]
        Dictionary of validation results by field name
    show_success : bool
        Whether to show success messages for valid fields
    
    Returns:
    --------
    bool
        True if all validations passed, False otherwise
    """
    all_valid = True
    
    for field_name, result in results.items():
        if not result.is_valid:
            all_valid = False
            display_validation_message(result, UIMessageType.ERROR)
        elif show_success and result.is_valid:
            display_validation_message(result, UIMessageType.SUCCESS)
    
    return all_valid

def safe_execute(func, error_message: str = "An error occurred", 
                default_return=None, show_error: bool = True):
    """Safely execute a function with standardized error handling.
    
    Parameters:
    -----------
    func : callable
        Function to execute
    error_message : str
        Custom error message to display
    default_return : Any
        Value to return if function fails
    show_error : bool
        Whether to display error message to user
    
    Returns:
    --------
    Any
        Function result or default_return if function failed
    """
    try:
        return func()
    except Exception as e:
        if show_error:
            st.error(f"{error_message}: {str(e)}")
        return default_return

def create_validation_summary(results: Dict[str, ValidationResult]) -> Dict[str, Any]:
    """Create a summary of validation results.
    
    Parameters:
    -----------
    results : Dict[str, ValidationResult]
        Dictionary of validation results
    
    Returns:
    --------
    Dict[str, Any]
        Summary with counts and lists of valid/invalid fields
    """
    valid_fields = [name for name, result in results.items() if result.is_valid]
    invalid_fields = [name for name, result in results.items() if not result.is_valid]
    
    return {
        "total_fields": len(results),
        "valid_count": len(valid_fields),
        "invalid_count": len(invalid_fields),
        "all_valid": len(invalid_fields) == 0,
        "valid_fields": valid_fields,
        "invalid_fields": invalid_fields,
        "error_messages": [result.message for result in results.values() if not result.is_valid]
    } 