"""
Module initialization file for the Multiphoton Microscopy Guide application.
"""

# Import all module components for easy access
from modules.theme import apply_theme, get_colors
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
from modules.ui_components import (
    create_header,
    create_info_box,
    create_warning_box,
    create_success_box,
    create_metric_row,
    create_data_editor,
    create_plot,
    create_tab_section,
    create_form_section
)

# Version information
__version__ = "5.0"
