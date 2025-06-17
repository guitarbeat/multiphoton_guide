"""
Shared constants used across multiple modules.
This module centralizes all constants to reduce duplication and provide a single source of truth.
"""

# =============================================================================
# FILE PATHS
# =============================================================================

# Data file names
RIG_LOG_FILE = "rig_log.csv"
LASER_POWER_FILE = "laser_power_measurements.csv"
FLUORESCENCE_FILE = "fluorescence_measurements.csv"
PULSE_WIDTH_FILE = "pulse_width_measurements.csv"

# Source Power Measurement
SOURCE_POWER_FILE = "data/source_power_measurements.csv"
SOURCE_POWER_COLUMNS = [
    "Study Name",
    "Date",
    "Wavelength (nm)",
    "Pump Current (mA)",
    "Temperature (°C)",
    "Measured Power (W)",
    "Pulse Width (fs)",
    "Grating Position",
    "Fan Status",
    "Notes",
]

# SOP for Power vs Pump Current
SOP_POWER_VS_PUMP_FILE = "sop_power_vs_pump"
SOP_POWER_VS_PUMP_COLUMNS = [
    "Pump Current (mA)",
    "Expected Power (W)",
    "Wavelength (nm)",
    "Temperature (°C)",
    "Study Name",
    "Notes",
]

# =============================================================================
# COMMON DATAFRAME COLUMN SCHEMAS
# =============================================================================

# Base columns shared across measurement files
BASE_MEASUREMENT_COLUMNS = ["Study Name", "Date", "Wavelength (nm)", "Researcher"]

# Rig log columns
RIG_LOG_COLUMNS = ["Date", "Researcher", "Activity", "Description", "Category"]

# Laser power measurement columns
LASER_POWER_COLUMNS = BASE_MEASUREMENT_COLUMNS + [
    "Sensor Model",
    "Measurement Mode",
    "Fill Fraction (%)",
    "Modulation (%)",
    "Measured Power (mW)",
    "Notes",
]

# Fluorescence measurement columns
FLUORESCENCE_COLUMNS = BASE_MEASUREMENT_COLUMNS + [
    "Sample Type",
    "Mean Intensity",
    "Variance",
    "Photon Sensitivity",
    "Notes",
]

# Pulse width measurement columns
PULSE_WIDTH_COLUMNS = BASE_MEASUREMENT_COLUMNS + [
    "GDD Value (fs²)",
    "Mean Pixel Value",
    "Max Pixel Value",
    "Notes",
]

# =============================================================================
# DEFAULT VALUES
# =============================================================================

# Default category values for rig log entries
RIG_LOG_CATEGORIES = [
    "Measurement",
    "Optimization",
    "Maintenance",
    "Calibration",
    "Software",
    "Hardware",
]

# Common measurement modes
MEASUREMENT_MODES = ["Stationary", "Scanning"]

# =============================================================================
# UI LAYOUT CONSTANTS
# =============================================================================

# Standard column ratios for two-column layouts
LAYOUT_RATIOS = {
    "theory_practice": [3, 2],  # Theory/procedure on left, visualization on right
    "form_data": [2, 1],  # Form on left, data/stats on right
    "equal": [1, 1],  # Equal width columns
    "narrow_wide": [1, 2],  # Narrow left, wide right
    "wide_narrow": [2, 1],  # Wide left, narrow right
}

# =============================================================================
# VALIDATION CONSTANTS
# =============================================================================

# Wavelength ranges (in nm)
WAVELENGTH_RANGE = {
    "min": 700,
    "max": 1300,
    "common": [780, 820, 850, 900, 920, 980, 1020, 1040, 1070],
}

# Power ranges (in mW)
POWER_RANGE = {
    "min": 0.0,
    "max": 1000.0,  # Adjust based on your system capabilities
    "typical_max": 100.0,
}

# GDD ranges (in fs²)
GDD_RANGE = {"min": -10000, "max": 20000, "step": 500}

# =============================================================================
# HELPER DICTIONARIES
# =============================================================================

# Map file types to their column schemas
COLUMN_SCHEMAS = {
    "rig_log": RIG_LOG_COLUMNS,
    "laser_power": LASER_POWER_COLUMNS,
    "fluorescence": FLUORESCENCE_COLUMNS,
    "pulse_width": PULSE_WIDTH_COLUMNS,
    "sop_power_vs_pump": SOP_POWER_VS_PUMP_COLUMNS,
}

# Map file types to their file names
FILE_MAPPINGS = {
    "rig_log": RIG_LOG_FILE,
    "laser_power": LASER_POWER_FILE,
    "fluorescence": FLUORESCENCE_FILE,
    "pulse_width": PULSE_WIDTH_FILE,
    "sop_power_vs_pump": SOP_POWER_VS_PUMP_FILE,
}
