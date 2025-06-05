"""
Module initialization file for the Multiphoton Microscopy Guide application.
Reorganized into logical subdirectories for better maintainability.
"""

# =============================================================================
# CORE INFRASTRUCTURE
# =============================================================================

# Import core utilities and constants

# =============================================================================
# USER INTERFACE
# =============================================================================

# Import UI components, theme, and templates

# =============================================================================
# MEASUREMENTS
# =============================================================================

# Import measurement modules

# =============================================================================
# ANALYSIS & REFERENCE
# =============================================================================

# Import analysis tools

# =============================================================================
# TESTING UTILITIES (available separately from tests directory)
# =============================================================================

# Note: Testing utilities are available separately:
# from tests.testing_utils import ModuleTester, TestResult, etc.
# They are not auto-imported to avoid circular dependencies

# =============================================================================
# VERSION & METADATA
# =============================================================================

# Version information
__version__ = "6.0"
__organization_version__ = "reorganized"

# Module structure information
__structure__ = {
    "core": ["constants", "shared_utils", "validation_utils", "data_utils"],
    "ui": ["components", "theme", "templates"],
    "measurements": ["laser_power", "fluorescence", "pulse_width", "rig_log"],
    "analysis": ["usaf_analyzer", "reference"],
    "tests": ["testing_utils (available separately)"],
}
