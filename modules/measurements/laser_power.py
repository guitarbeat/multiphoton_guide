"""
Laser power measurement module for the Multiphoton Microscopy Guide application.
Implements protocols for measuring and recording laser power at the sample.
"""

from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st

from modules.core.constants import (
    LASER_POWER_COLUMNS,
    LASER_POWER_FILE,
    MEASUREMENT_MODES,
    SOURCE_POWER_FILE,
)
from modules.core.data_utils import (
    calculate_statistics,
    ensure_columns,
    filter_dataframe,
    linear_regression,
    load_dataframe,
    safe_numeric_conversion,
    save_dataframe,
)
from modules.core.shared_utils import (
    add_to_rig_log,
    create_two_column_layout,
    load_measurement_dataframe,
)
from modules.measurements.source_power import (
    render_source_power_form,
    render_source_power_theory_and_procedure,
    render_source_power_visualization,
)
from modules.ui.components import create_header, create_metric_row, create_plot
from modules.ui.theme import get_colors


def render_laser_power_tab(use_sidebar_values=False):
    """Render the laser power measurement tab content.

    Args:
        use_sidebar_values: If True, use values from the sidebar instead of showing duplicate form fields.
    """

    create_header("Laser Power Measurements")

    # Create tabs for different measurement locations
    sample_tab, source_tab = st.tabs(
        ["Laser Power at the Sample", "Laser Power at the Source"]
    )

    with sample_tab:
        # Create main layout with the measurement form prominently displayed at the top
        render_simplified_measurement_form(use_sidebar_values)

        # Create tabs for recent measurements and combined theory/procedure below the form
        recent_tab, theory_tab = st.tabs(["Recent Measurements", "Theory & Procedure"])

        with recent_tab:
            # Show recent measurements
            st.subheader("Recent Measurements")

            # Load existing data
            laser_power_df = load_dataframe(LASER_POWER_FILE, pd.DataFrame())

            if laser_power_df.empty:
                st.info(
                    "No measurements found. Check your Google Sheets connection or "
                    "add data to the sheet."
                )
            else:
                # Filter to current study
                filtered_df = filter_dataframe(
                    laser_power_df, {"Study Name": st.session_state.study_name}
                )

                if filtered_df.empty:
                    st.info("No measurements found for the current study.")
                else:
                    # Sort by date (newest first) and select only the most recent measurements
                    filtered_df = filtered_df.sort_values("Date", ascending=False).head(
                        5
                    )

                    # Display the table with selected columns
                    st.dataframe(
                        filtered_df[
                            [
                                "Date",
                                "Modulation (%)",
                                "Measured Power (mW)",
                                "Measurement Mode",
                                "Sensor Model",
                            ]
                        ],
                        hide_index=True,
                        use_container_width=True,
                    )

        with theory_tab:
            # Show combined theory and procedure
            render_laser_power_theory_and_procedure()
            # Optionally, also show visualization here if desired
            render_laser_power_visualization()

    with source_tab:
        # Show the form and live plot at the top
        render_source_power_form()
        # Create a single row of two tabs for the source section
        tab_recent, tab_theory = st.tabs(["Recent Measurements", "Theory & Procedure"])

        with tab_recent:
            # Only show the recent measurements table (not the form or plot)
            source_power_df = load_dataframe(SOURCE_POWER_FILE, pd.DataFrame())
            st.subheader("Recent Measurements")
            if not source_power_df.empty:
                filtered_df = filter_dataframe(
                    source_power_df, {"Study Name": st.session_state.study_name}
                )
                if not filtered_df.empty:
                    filtered_df = filtered_df.sort_values("Date", ascending=False).head(
                        5
                    )
                    st.dataframe(
                        filtered_df[
                            [
                                "Date",
                                "Pump Current (mA)",
                                "Measured Power (W)",
                                "Expected Power (W)",
                                "Notes",
                            ]
                        ],
                        hide_index=True,
                        use_container_width=True,
                    )
        with tab_theory:
            render_source_power_theory_and_procedure()

    # Add entry to rig log if measurements were taken
    if st.session_state.get("laser_power_submitted", False):
        add_to_rig_log(
            "Laser Power Measurement",
            f"Measured laser power using {st.session_state.get('sensor_model', 'unknown sensor')}",
            "Measurement",
        )
        # Reset the flag
        st.session_state.laser_power_submitted = False

    if st.session_state.get("source_power_submitted", False):
        add_to_rig_log(
            "Source Power Measurement", f"Measured source power", "Measurement"
        )
        # Reset the flag
        st.session_state.source_power_submitted = False


def render_laser_power_theory_and_procedure():
    """Render the combined theory and procedure sections for laser power measurement."""
    st.markdown(
        """
        ### Introduction & Theory
        Measuring and monitoring laser power at the sample is critical in multiphoton microscopy for maintaining sample integrity and data quality. 
        
        Fluorescence emission is proportional to the average laser power squared, so small changes in laser power can result in large changes to your data. Exposing your sample to excessive laser power can cause photobleaching and photodamage, altering your sample and measurements.
        
        There are two types of laser-induced photodamage in multiphoton microscopy:
        1. **Local heating** of the imaged area, which is linearly related to average laser power
        2. **Photochemical degradation** (bleaching or ablation), which is nonlinearly related to average laser power
        
        Knowing the laser power is essential for consistency between experiments, for minimizing photodamage, and for monitoring system health.
        
        ---
        
        ### Measurement Procedure
        1. **Prepare the power meter**
           - Place the power meter sensor under the objective
           - Ensure the sensor is centered in the field of view
        2. **Configure the microscope**
           - Select measurement mode (stationary or scanning)
           - If scanning, set the temporal fill fraction
        3. **Take measurements**
           - Start at 0% modulation and increase in 5-10% increments
           - Record the measured power at each modulation level
           - Continue until reaching 100% or maximum safe power
        4. **Calculate the power/modulation ratio**
           - Plot modulation percentage vs. measured power
           - Calculate the slope of the linear relationship
           - This ratio is useful for system monitoring over time
        
        **CRITICAL:** Always measure with the same objective, as transmission efficiency varies between objectives.
        
        **CRITICAL:** For consistent measurements, use the same measurement mode (stationary or scanning) each time.
    """
    )


def render_simplified_measurement_form(use_sidebar_values=False):
    """Render the simplified measurement form for laser power measurements."""
    # Load existing data
    laser_power_df = load_dataframe(LASER_POWER_FILE, pd.DataFrame())

    # Get colors for styling
    colors = get_colors()

    st.markdown('<div class="measurement-form">', unsafe_allow_html=True)

    # Single measurement form
    st.subheader("Add Single Measurement")

    with st.form(key="quick_measurement_form"):
        # Create three columns for the form
        col1, col2, col3 = st.columns(3)

        with col1:
            # Sensor Model input (optional)
            sensor_model = st.text_input(
                "Sensor Model (optional):",
                value=st.session_state.get("sensor_model", ""),
                help="Enter the model of your power meter sensor (optional)",
            )

            modulation = st.number_input(
                "Modulation (%):",
                min_value=0,
                max_value=100,
                value=10,
                step=5,
                help="Percentage of maximum laser power",
            )

        with col2:
            # Measurement Mode selection
            measurement_mode = st.radio(
                "Measurement Mode:",
                MEASUREMENT_MODES,
                index=(
                    0
                    if st.session_state.get("measurement_mode", "Stationary")
                    == "Stationary"
                    else 1
                ),
                help="Stationary: beam fixed at center. Scanning: beam continuously scanning.",
            )

            power = st.number_input(
                "Measured Power (mW):",
                min_value=0.0,
                value=0.0,
                step=0.1,
                format="%.2f",
                help="Power measured at the sample",
            )

        with col3:
            # Fill fraction (only shown if scanning mode is selected)
            fill_fraction = st.session_state.get(
                "fill_fraction", 100
            )  # Default from session state
            if measurement_mode == "Scanning":
                fill_fraction = st.number_input(
                    "Fill Fraction (%):",
                    min_value=1,
                    max_value=100,
                    value=int(st.session_state.get("fill_fraction", 100)),
                    help="Percentage of time the beam is 'on' during scanning",
                )
            else:
                st.info("Fill fraction: 100%")
                fill_fraction = 100

        notes = st.text_area("Notes:", help="Optional notes about the measurement")

        # Submit button
        submitted = st.form_submit_button("Add Measurement")

        if submitted:
            # Validate inputs
            if power <= 0 or modulation <= 0:
                st.error("Please enter valid power and modulation values.")
            else:
                # Create new entry
                new_entry = pd.DataFrame(
                    {
                        "Study Name": [st.session_state.study_name],
                        "Date": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                        "Sensor Model": [sensor_model],
                        "Measurement Mode": [measurement_mode],
                        "Fill Fraction (%)": [fill_fraction],
                        "Modulation (%)": [modulation],
                        "Measured Power (mW)": [power],
                        "Notes": [notes],
                    }
                )

                # Append to existing data
                updated_df = pd.concat([laser_power_df, new_entry], ignore_index=True)

                # Save updated data
                save_dataframe(updated_df, LASER_POWER_FILE)

                # Set flag for rig log entry
                st.session_state.laser_power_submitted = True

                # Success message
                st.success("Measurement added successfully!")

                # Force a rerun to refresh the page with the new data
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def render_laser_power_visualization():
    """Render visualizations for laser power measurements."""
    st.subheader("Power Analysis")

    # Check if we have measurements in session state first
    has_measurements = False
    measurements_df = pd.DataFrame()

    if (
        "latest_measurements" in st.session_state
        and len(st.session_state.latest_measurements) >= 2
    ):
        # Convert session state measurements to DataFrame for analysis
        measurements_df = pd.DataFrame(st.session_state.latest_measurements)
        has_measurements = True
    else:
        # Load existing data
        laser_power_df = load_dataframe(LASER_POWER_FILE, pd.DataFrame())

        if not laser_power_df.empty:
            # Filter data for current study
            # Robustly handle invalid session state values
            try:
                fill_fraction = float(st.session_state.fill_fraction)
            except (ValueError, TypeError):
                fill_fraction = 100.0
            current_filters = {
                "Study Name": st.session_state.study_name,
                "Sensor Model": st.session_state.sensor_model,
                "Measurement Mode": st.session_state.measurement_mode,
                "Fill Fraction (%)": fill_fraction,
            }

            filtered_df = filter_dataframe(laser_power_df, current_filters)

            if len(filtered_df) >= 2:
                # Convert to numeric to ensure calculations work
                filtered_df = safe_numeric_conversion(
                    filtered_df, ["Modulation (%)", "Measured Power (mW)"]
                )

                measurements_df = filtered_df[["Modulation (%)", "Measured Power (mW)"]]
                has_measurements = True

    if not has_measurements or len(measurements_df) < 2:
        st.info("Add at least two measurements to see analysis")
        return

    # Calculate statistics
    power_stats = calculate_statistics(measurements_df, "Measured Power (mW)")

    # Display metrics
    create_metric_row(
        [
            {"label": "Average Power", "value": f"{power_stats['mean']:.2f} mW"},
            {"label": "Maximum Power", "value": f"{power_stats['max']:.2f} mW"},
            {"label": "Measurements", "value": power_stats["count"]},
        ]
    )

    # Create power vs modulation plot
    def plot_power_vs_modulation(fig, ax):
        # Get data
        x = measurements_df["Modulation (%)"].values
        y = measurements_df["Measured Power (mW)"].values

        # Calculate regression
        reg = linear_regression(x, y)

        # Plot data points
        ax.scatter(x, y, color="#4BA3C4", s=50, alpha=0.7, label="Measurements")

        # Plot regression line
        x_line = np.linspace(0, max(x) * 1.1, 100)
        y_line = reg["slope"] * x_line + reg["intercept"]
        ax.plot(
            x_line,
            y_line,
            color="#BF5701",
            linestyle="-",
            linewidth=2,
            label=f'Slope: {reg["slope"]:.3f} mW/%',
        )

        # Add labels and title
        ax.set_xlabel("Modulation (%)")
        ax.set_ylabel("Measured Power (mW)")
        ax.set_title("Power vs. Modulation")

        # Add grid and legend
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.legend()

        # Set limits
        ax.set_xlim(0, max(x) * 1.1)
        ax.set_ylim(0, max(y) * 1.1)

    # Display the plot
    power_plot = create_plot(plot_power_vs_modulation)
    st.pyplot(power_plot)

    # Add explanation
    with st.popover("📊 Understanding This Plot", use_container_width=True):
        st.markdown(
            """
        This plot shows the relationship between laser modulation percentage and measured power at the sample.
        
        **Key insights:**
        - The slope represents the power/modulation ratio (mW per % modulation)
        - A linear relationship indicates proper laser and modulator function
        - Deviations from linearity may indicate issues with the laser or power modulator
        - Monitoring this ratio over time helps detect system degradation
        
        **Typical values:**
        - Slope values vary by laser and objective
        - For a given setup, this value should remain stable over time
        - Significant changes may indicate alignment issues or component degradation
        """
        )


# add_to_rig_log function moved to modules/shared_utils.py to eliminate duplication
