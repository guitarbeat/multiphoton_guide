"""
Module structure templates for the Multiphoton Microscopy Guide application.
This module provides standardized templates and patterns for creating measurement modules.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List

import streamlit as st
import pandas as pd

from modules.core.constants import FILE_MAPPINGS
from modules.core.data_utils import save_dataframe

from modules.core.shared_utils import (
    add_to_rig_log,
    create_two_column_layout,
    load_measurement_dataframe,
)
from modules.core.validation_utils import (
    display_form_validation_results,
    safe_execute,
    validate_form_data,
)
from modules.ui.components import create_header, create_info_box


class BaseMeasurementModule(ABC):
    """Abstract base class for measurement modules.

    Defines the standard structure for all measurement modules, providing a consistent interface and reducing code duplication.
    """

    def __init__(self, module_name: str, data_file_type: str):
        """Initialize the measurement module.

        Parameters:
        -----------
        module_name : str
            Human-readable name of the module (e.g., "Laser Power Measurement")
        data_file_type : str
            Data file type for loading/saving (e.g., "laser_power")
        """
        self.module_name = module_name
        self.data_file_type = data_file_type

    @abstractmethod
    def render_theory_and_procedure(self) -> None:
        """Render the theory and procedure section."""

    @abstractmethod
    def render_visualization(self) -> None:
        """Render the visualization section."""

    @abstractmethod
    def render_measurement_form(self) -> None:
        """Render the measurement input form."""

    def render_tips(self) -> None:
        """Render tips and best practices (optional override)."""
        create_info_box(
            "Override render_tips() to provide module-specific tips."
        )

    def render_tab(self, subtitle: str = "", use_sidebar_values: bool = False) -> None:
        """Main tab rendering method using standardized structure.

        Parameters:
        -----------
        subtitle : str, optional
            Subtitle for the header
        use_sidebar_values : bool, optional
            Whether to use values from the sidebar
        """
        # Standard header
        create_header(self.module_name, subtitle)

        # Standard measurement form
        self.render_measurement_form()

        # Standard two-column layout for theory/visualization
        create_two_column_layout(
            self.render_theory_and_procedure,
            lambda: (self.render_visualization(), self.render_tips()),
        )

    def log_measurement(
        self, activity: str, description: str, category: str = "Measurement"
    ) -> None:
        """Log a measurement to the rig log using standardized format.

        Parameters:
        -----------
        activity : str
            Brief description of the activity
        description : str
            Detailed description
        category : str, optional
            Category for the log entry
        """
        add_to_rig_log(activity, description, category)


def create_standard_theory_procedure_tabs(
    theory_content: str, procedure_content: str, warnings: List[str] = None
) -> None:
    """Create standardized theory and procedure tabs.

    Parameters:
    -----------
    theory_content : str
        Markdown content for the theory tab
    procedure_content : str
        Markdown content for the procedure tab
    warnings : List[str], optional
        List of critical warnings to display
    """
    tab1, tab2 = st.tabs(["📖 Introduction & Theory", "📋 Measurement Procedure"])

    with tab1:
        st.markdown(theory_content)

    with tab2:
        st.markdown(procedure_content)

        if warnings:
            for warning in warnings:
                st.warning(f"**CRITICAL:** {warning}")


def create_standard_measurement_form(
    df_type: str,
    form_fields: Dict[str, Dict],
    form_key: str = "measurement_form",
    validation_config: Dict[str, Dict] = None,
) -> bool:
    """Create a standardized measurement form with validation.

    Parameters:
    -----------
    df_type : str
        Type of measurement data
    form_fields : Dict[str, Dict]
        Configuration for form fields
    form_key : str
        Unique key for the form
    validation_config : Dict[str, Dict], optional
        Validation configuration for fields

    Returns:
    --------
    bool
        True if form was submitted and validated successfully
    """
    with st.form(key=form_key):
        form_data = {}

        # Create form fields based on configuration
        col1, col2 = st.columns(2)

        # Split fields between columns
        field_items = list(form_fields.items())
        left_fields = field_items[: len(field_items) // 2 + len(field_items) % 2]
        right_fields = field_items[len(field_items) // 2 + len(field_items) % 2 :]

        with col1:
            for field_name, field_config in left_fields:
                form_data[field_name] = _create_form_field(field_name, field_config)

        with col2:
            for field_name, field_config in right_fields:
                form_data[field_name] = _create_form_field(field_name, field_config)

        if submitted := st.form_submit_button(
            "Add Measurement", type="primary"
        ):
            # Validate form data if validation config provided
            if validation_config:
                validation_results = validate_form_data(form_data, validation_config)
                if not display_form_validation_results(validation_results):
                    return False

            # Save measurement data
            return _save_measurement_data(df_type, form_data)

    return False


def _create_form_field(field_name: str, field_config: Dict[str, Any]) -> Any:
    """Create a form field based on configuration."""
    field_type = field_config.get("type", "text")

    if field_type == "number":
        return st.number_input(
            field_config["label"],
            min_value=field_config.get("min_value", 0),
            max_value=field_config.get("max_value"),
            value=field_config.get("value", 0),
            step=field_config.get("step", 1),
            help=field_config.get("help", ""),
            format=field_config.get("format"),
        )
    elif field_type == "text":
        return st.text_input(
            field_config["label"],
            value=field_config.get("value", ""),
            help=field_config.get("help", ""),
        )
    elif field_type == "textarea":
        return st.text_area(
            field_config["label"],
            value=field_config.get("value", ""),
            help=field_config.get("help", ""),
            height=field_config.get("height", 100),
        )
    elif field_type == "selectbox":
        return st.selectbox(
            field_config["label"],
            options=field_config.get("options", []),
            index=field_config.get("index", 0),
            help=field_config.get("help", ""),
        )
    elif field_type == "radio":
        return st.radio(
            field_config["label"],
            options=field_config.get("options", []),
            index=field_config.get("index", 0),
            help=field_config.get("help", ""),
            horizontal=field_config.get("horizontal", False),
        )
    else:
        st.error(f"Unknown field type: {field_type}")
        return None


def _save_measurement_data(df_type: str, form_data: Dict[str, Any]) -> bool:
    """Save measurement data using standardized approach."""

    def save_operation():
        # Load existing data
        df = load_measurement_dataframe(df_type)

        # Create new entry
        new_entry = {**form_data}
        new_entry["Date"] = st.session_state.get("current_timestamp", "")
        new_entry["Study Name"] = st.session_state.get("study_name", "")
        new_entry["Researcher"] = st.session_state.get("researcher", "")

        # Append and save
        new_row = pd.DataFrame([new_entry])
        updated_df = pd.concat([df, new_row], ignore_index=True)
        save_dataframe(updated_df, FILE_MAPPINGS[df_type])

        return True

    return safe_execute(
        save_operation,
        error_message="Failed to save measurement data",
        default_return=False,
        show_error=True,
    )


def create_standard_visualization_section(
    df_type: str,
    plot_function: Callable,
    metrics_function: Callable = None,
    explanation_text: str = "",
) -> None:
    """Create a standardized visualization section.

    Parameters:
    -----------
    df_type : str
        Type of data to visualize
    plot_function : Callable
        Function that creates the plot
    metrics_function : Callable, optional
        Function that calculates and displays metrics
    explanation_text : str, optional
        Explanation text for the visualization
    """
    st.subheader("Data Analysis")

    # Load data for visualization
    df = safe_execute(
        lambda: load_measurement_dataframe(df_type),
        error_message="Failed to load measurement data",
        default_return=None,
    )

    if df is None or df.empty:
        st.info("Add measurements to see analysis and visualizations.")
        return

    # Display metrics if function provided
    if metrics_function:
        safe_execute(
            lambda: metrics_function(df), error_message="Failed to calculate metrics"
        )

    # Create and display plot
    safe_execute(
        lambda: plot_function(df), error_message="Failed to create visualization"
    )

    # Add explanation if provided
    if explanation_text:
        with st.expander("📊 Understanding This Analysis", expanded=False):
            st.markdown(explanation_text)


def create_tips_section(tips_content: Dict[str, str]) -> None:
    """Create a standardized tips and best practices section.

    Parameters:
    -----------
    tips_content : Dict[str, str]
        Dictionary with tip titles as keys and content as values
    """
    st.subheader("Tips & Best Practices")

    for title, content in tips_content.items():
        with st.expander(title, expanded=False):
            st.markdown(content)


def create_module_status_indicator(
    module_name: str, has_data: bool, data_count: int = 0, last_updated: str = ""
) -> None:
    """Create a status indicator for the module.

    Parameters:
    -----------
    module_name : str
        Name of the module
    has_data : bool
        Whether the module has any data
    data_count : int
        Number of data entries
    last_updated : str
        Timestamp of last update
    """
    if has_data:
        if data_count > 0:
            st.success(f"✅ {module_name}: {data_count} measurements recorded.")
            if last_updated:
                st.caption(f"Last updated: {last_updated}")
        else:
            st.info(f"📊 {module_name}: Ready to record measurements.")
    else:
        st.warning(f"⚠️ {module_name}: No data available.")


# Common validation configurations for different measurement types
VALIDATION_CONFIGS = {
    "laser_power": {
        "modulation": {
            "validation_type": "numeric",
            "min_value": 0,
            "max_value": 100,
            "required": True,
            "allow_zero": False,
        },
        "power": {"validation_type": "power", "required": True},
    },
    "fluorescence": {
        "wavelength": {"validation_type": "wavelength", "required": True},
        "mean_intensity": {
            "validation_type": "numeric",
            "min_value": 0,
            "required": True,
            "allow_zero": False,
        },
    },
    "pulse_width": {
        "wavelength": {"validation_type": "wavelength", "required": True},
        "gdd_value": {"validation_type": "gdd", "required": True},
    },
}
