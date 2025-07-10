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
    SOP_POWER_VS_PUMP_FILE,
    SOP_POWER_VS_PUMP_COLUMNS,
)
from modules.core.data_utils import (
    calculate_statistics,
    ensure_columns,
    filter_dataframe,
    linear_regression,
    load_dataframe,
    safe_numeric_conversion,
    save_dataframe,
    exponential_fit,
    save_fit_parameters,
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


def render_quick_laser_power_entry():
    """Render a quick entry form for laser power measurements at the sample (Power in mW, Modulation in %)."""
    st.subheader("Quick Measurement Entry (Power in mW, Modulation in %)")  # Units clarified
    if "quick_modulations" not in st.session_state:
        st.session_state.quick_modulations = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    quick_modulations = st.session_state.quick_modulations

    # Add more rows and reset buttons
    col_add, col_reset = st.columns([1, 1])
    with col_add:
        if st.button("Add Row", key="add_more_quick_mod_rows"):
            last_val = quick_modulations[-1] if quick_modulations else 100
            next_val = min(last_val + 10, 100)
            if next_val <= 100:
                quick_modulations.append(next_val)
                st.session_state.quick_modulations = quick_modulations
    with col_reset:
        if st.button("Reset Rows", key="reset_quick_mod_rows"):
            st.session_state.quick_modulations = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
            quick_modulations = st.session_state.quick_modulations

    quick_form = st.form(key="quick_laser_power_form")
    quick_cols = quick_form.columns(len(quick_modulations))
    quick_mw_values = []
    for i, mod in enumerate(quick_modulations):
        with quick_cols[i]:
            mw = quick_form.number_input(f"{mod}% (Power in mW)", min_value=0.0, step=0.1, format="%.1f", key=f"quick_laser_mw_{mod}")  # Units clarified
            quick_mw_values.append(mw)
    if quick_submit := quick_form.form_submit_button("Add Quick Measurements"):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        quick_entries = []
        for i, mod in enumerate(quick_modulations):
            mw = quick_mw_values[i]
            if mw > 0:
                entry = {
                    "Study Name": st.session_state.study_name,
                    "Date": now,
                    "Wavelength (nm)": st.session_state.wavelength,
                    "Researcher": st.session_state.get("researcher", ""),
                    "Sensor Model": st.session_state.get("sensor_model", ""),
                    "Measurement Mode": st.session_state.get("measurement_mode", "Stationary"),
                    "Fill Fraction (%)": st.session_state.get("fill_fraction", 100.0),
                    "Modulation (%)": mod,
                    "Measured Power (mW)": mw,
                    "Notes": "Quick entry"
                }
                quick_entries.append(entry)
        if quick_entries:
            # Load existing data
            laser_power_df = load_dataframe(LASER_POWER_FILE, pd.DataFrame())
            # Append new entries
            new_df = pd.DataFrame(quick_entries)
            combined_df = pd.concat([laser_power_df, new_df], ignore_index=True)
            save_dataframe(combined_df, LASER_POWER_FILE)
            st.success(f"Added {len(quick_entries)} quick measurements.")
            st.session_state.laser_power_submitted = True
            st.rerun()


def render_laser_power_tab(use_sidebar_values=False):
    """Render the fiber laser power measurement tab content."""

    create_header("Fiber Laser Power Measurements (at Sample)")  # Clarified context

    # Create tabs for different measurement locations
    source_tab, sample_tab = st.tabs(
        ["Laser Power at the Source", "Laser Power at the Sample"]
    )

    with sample_tab:
        # Quick Measurement Entry at the top
        render_quick_laser_power_entry()
        # Create main layout with the measurement form prominently displayed at the top
        render_simplified_measurement_form(use_sidebar_values)
        # Show combined theory and procedure below the form
        st.markdown("---")
        render_laser_power_theory_and_procedure()
        # Show visualization
        render_laser_power_visualization()

    with source_tab:
        # Show the form and live plot at the top
        render_source_power_form()
        # Create tabs for SOP and Theory
        tab_sop, tab_theory = st.tabs(["Expected SOP", "Theory & Procedure"])

        with tab_sop:
            st.subheader("Expected SOP: Power vs. Pump Current")
            st.markdown("""
            Edit the Standard Operating Procedure (SOP) values for expected power output at different pump current levels.
            These values represent the expected performance of your system and are used as a reference for comparison.
            """)

            # Load SOP data from Supabase
            sop_df = load_dataframe(SOP_POWER_VS_PUMP_FILE, pd.DataFrame())

            # If empty, create a dataframe with the required columns
            if sop_df.empty:
                sop_df = pd.DataFrame(columns=SOP_POWER_VS_PUMP_COLUMNS)

            # Filter to current study
            filtered_sop_df = filter_dataframe(
                sop_df, {"Study Name": st.session_state.study_name}
            )

            # Create an editable data frame
            edited_sop_df = st.data_editor(
                filtered_sop_df,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "Pump Current (mA)": st.column_config.NumberColumn(
                        "Pump Current (mA)",
                        help="Pump current in milliamperes.",
                        min_value=0,
                        max_value=100,
                        step=1,
                        format="%.1f",
                        width="small",
                    ),
                    "Expected Power (mW)": st.column_config.NumberColumn(
                        "Expected Power (mW)",
                        help="Expected power output in milliwatts.",
                        min_value=0,
                        max_value=10000,
                        step=1,
                        format="%.0f",
                        width="small",
                    ),
                    "Wavelength (nm)": st.column_config.NumberColumn(
                        "Wavelength (nm)",
                        help="Laser wavelength in nanometers.",
                        min_value=700,
                        max_value=1300,
                        step=1,
                        format="%.1f",
                        width="small",
                    ),
                    "Temperature (°C)": st.column_config.NumberColumn(
                        "Temperature (°C)",
                        help="Operating temperature in degrees Celsius.",
                        min_value=15,
                        max_value=35,
                        step=0.1,
                        format="%.1f",
                        width="small",
                    ),
                },
                key="sop_editor"
            )

            if st.button("💾 Save SOP Changes"):
                if not edited_sop_df.equals(filtered_sop_df):
                    # Make sure Study Name is set for all rows
                    if "Study Name" in edited_sop_df.columns:
                        edited_sop_df["Study Name"].fillna(st.session_state.study_name, inplace=True)
                    else:
                        edited_sop_df["Study Name"] = st.session_state.study_name

                    # Save the SOP data
                    save_dataframe(edited_sop_df, SOP_POWER_VS_PUMP_FILE)

                    # Calculate and save exponential fit parameters if we have enough data points
                    if len(edited_sop_df) >= 3:
                        try:
                            # Prepare data for fitting
                            sorted_df = edited_sop_df.sort_values("Pump Current (mA)")
                            pump_currents = sorted_df["Pump Current (mA)"].astype(float).values
                            powers = sorted_df["Expected Power (mW)"].astype(float).values

                            # Calculate exponential fit
                            fit_params = exponential_fit(pump_currents, powers)

                            # Add metadata
                            metadata = {
                                "study_name": st.session_state.study_name,
                                "wavelength": st.session_state.wavelength,
                                "fit_type": "exponential",
                                "notes": f"Auto-calculated from SOP data with {len(edited_sop_df)} points"
                            }

                            # Save fit parameters
                            save_fit_parameters("sop_power_vs_pump", fit_params, metadata)

                            # Show the fit equation
                            equation = f"Power (mW) = {fit_params['a']:.1f} × e^({fit_params['b']:.5f} × Current) + {fit_params['c']:.1f}"
                            st.success(f"SOP data and fit saved successfully. Exponential fit: {equation}")
                        except Exception as e:
                            # Still show success even if fit calculation fails
                            st.success("SOP data saved successfully.")
                            st.warning(f"Could not calculate fit parameters: {str(e)}")
                    else:
                        st.success("SOP data saved successfully. Add at least 3 points to calculate fit parameters.")
                    st.rerun()
                else:
                    st.info("No changes to save.")

            # Show a plot of the SOP data
            if not edited_sop_df.empty and "Pump Current (mA)" in edited_sop_df.columns and "Expected Power (mW)" in edited_sop_df.columns:
                st.subheader("SOP Power Curve")

                # Sort by pump current for proper plotting
                plot_df = edited_sop_df.sort_values("Pump Current (mA)")

                # Create a plot function to pass to create_plot
                def plot_sop_data(fig, ax):
                    ax.plot(
                        plot_df["Pump Current (mA)"].values,
                        plot_df["Expected Power (mW)"].values,
                        marker='o',
                        linestyle='-',
                        color="#1f77b4",
                        label="Expected Power"
                    )
                    ax.set_xlabel("Pump Current (mA)")
                    ax.set_ylabel("Expected Power (mW)")
                    ax.set_title("Expected Power vs. Pump Current")
                    ax.grid(True, linestyle='--', alpha=0.7)
                    ax.legend()

                # Pass the plot function to create_plot
                fig = create_plot(plot_sop_data)
                st.pyplot(fig)

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
            "Source Power Measurement", "Measured source power", "Measurement"
        )
        # Reset the flag
        st.session_state.source_power_submitted = False


def render_laser_power_theory_and_procedure():
    """Render the combined theory and procedure sections for laser power measurement. All power values are in mW, modulation is in percent as set in ScanImage."""
    st.markdown(
        """
        ### Introduction & Theory
        Measuring and monitoring laser power at the sample is critical in multiphoton microscopy for maintaining sample integrity and data quality.

        Fluorescence emission is proportional to the square of the average laser power, so small changes in laser power can result in large changes to your data. Exposing your sample to excessive laser power can cause photobleaching and photodamage, altering your sample and measurements.

        There are two types of laser-induced photodamage in multiphoton microscopy:
        1. **Local heating** of the imaged area, which is linearly related to average laser power (in mW).
        2. **Photochemical degradation** (bleaching or ablation), which is nonlinearly related to average laser power.

        Knowing the laser power (in mW) and the modulation percentage (as set in ScanImage) is essential for consistency between experiments, minimizing photodamage, and monitoring system health.

        ---

        ### Measurement Procedure
        1. **Prepare the power meter**
           - Place the power meter sensor under the objective.
           - Ensure the sensor is centered in the field of view.
        2. **Configure the microscope**
           - Select the measurement mode (stationary or scanning).
           - If scanning, set the temporal fill fraction.
        3. **Take measurements**
           - Start at 0% modulation (ScanImage power percentage) and increase in 5-10% increments.
           - Record the measured power (in mW) at each modulation level.
           - Continue until reaching 100% or the maximum safe power.
        4. **Calculate the power/modulation ratio**
           - Plot modulation percentage (ScanImage) vs. measured power (mW).
           - Calculate the slope of the linear relationship (units: mW/% modulation).
           - This ratio is useful for system monitoring over time.

        **CRITICAL:** Always measure with the same objective, as transmission efficiency varies between objectives.

        **CRITICAL:** For consistent measurements, use the same measurement mode (stationary or scanning) each time.
    """
    )


def render_simplified_measurement_form(use_sidebar_values=False):
    """Render the editable dataframe for laser power measurements. All power values are in mW, modulation is in percent as set in ScanImage."""
    # Load existing data
    laser_power_df = load_dataframe(LASER_POWER_FILE, pd.DataFrame())

    st.subheader("Fiber Laser Power Measurements (at Sample, Power in mW, Modulation in %)")  # Clarified units

    # Initialize with default structure if empty
    if laser_power_df.empty:
        laser_power_df = pd.DataFrame(columns=LASER_POWER_COLUMNS)
        # Add one empty row for editing
        laser_power_df.loc[0] = [
            st.session_state.study_name,                           # Study Name
            datetime.now(),                                        # Date (as datetime object)  
            st.session_state.wavelength,                           # Wavelength (nm)
            st.session_state.get("researcher", ""),               # Researcher
            st.session_state.get("sensor_model", ""),             # Sensor Model
            "Stationary",                                          # Measurement Mode
            100.0,                                                 # Fill Fraction (%)
            10,                                                    # Modulation (%)
            0.0,                                                   # Measured Power (mW)
            ""                                                     # Notes
        ]

    # Convert Date column to datetime if it exists and is string type
    if not laser_power_df.empty and "Date" in laser_power_df.columns and laser_power_df["Date"].dtype == 'object':
        try:
            laser_power_df["Date"] = pd.to_datetime(laser_power_df["Date"])
        except Exception:
            # If conversion fails, keep as string and use text column config
            pass

    # Create column configuration for the data editor
    column_config = {
        "Study Name": st.column_config.TextColumn(
            "Study Name",
            default=st.session_state.study_name,
            help="Name of the study",
            width="medium",
        ),
        "Wavelength (nm)": st.column_config.NumberColumn(
            "Wavelength (nm)",
            default=st.session_state.wavelength,
            help="Wavelength setting",
            width="small",
        ),
        "Researcher": st.column_config.TextColumn(
            "Researcher", help="Name of the researcher", width="small"
        ),
        "Sensor Model": st.column_config.TextColumn(
            "Sensor Model",
            help="Model of the power meter sensor",
            width="medium",
        ),
        "Measurement Mode": st.column_config.SelectboxColumn(
            "Measurement Mode",
            options=MEASUREMENT_MODES,
            help="Stationary: beam fixed at center. Scanning: beam continuously scanning.",
            width="medium",
        ),
        "Fill Fraction (%)": st.column_config.NumberColumn(
            "Fill Fraction (%)",
            min_value=1,
            max_value=100,
            step=1,
            format="%.0f",
            help="Percentage of time the beam is 'on' during scanning",
            width="small",
        ),
        "Modulation (%)": st.column_config.NumberColumn(
            "Modulation (%)",
            min_value=0,
            max_value=100,
            step=1,
            format="%.0f",
            help="Power percentage as set in ScanImage (0-100%)",
            width="small",
        ),
        "Measured Power (mW)": st.column_config.NumberColumn(
            "Measured Power (mW)",
            min_value=0.0,
            step=0.1,
            format="%.1f",
            help="Power measured at the sample (in mW)",
            width="small",
        ),
        "Notes": st.column_config.TextColumn(
            "Notes", help="Optional notes about the measurement", width="large"
        ),
    }

    # Add Date column configuration based on data type
    if not laser_power_df.empty and "Date" in laser_power_df.columns:
        if pd.api.types.is_datetime64_any_dtype(laser_power_df["Date"]):
            column_config["Date"] = st.column_config.DatetimeColumn(
                "Date", help="Date and time of measurement", width="medium"
            )
        else:
            column_config["Date"] = st.column_config.TextColumn(
                "Date",
                help="Date and time of measurement (YYYY-MM-DD HH:MM:SS)",
                width="medium",
            )
    else:
        # Default for new dataframes
        column_config["Date"] = st.column_config.DatetimeColumn(
            "Date", help="Date and time of measurement", width="medium"
        )

    # Display editable dataframe
    edited_df = st.data_editor(
        laser_power_df,
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        key="laser_power_editor"
    )

    # Save button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("💾 Save Changes", use_container_width=True):
            # Remove empty rows (rows where key measurement fields are empty or zero)
            filtered_df = edited_df[
                (edited_df["Modulation (%)"] > 0) | 
                (edited_df["Measured Power (mW)"] > 0) | 
                (edited_df["Notes"].str.strip() != "")
            ].copy()

            # Validate required fields
            if not filtered_df.empty:
                # Check for missing values in critical columns
                missing_power = filtered_df["Measured Power (mW)"].isna() | (filtered_df["Measured Power (mW)"] <= 0)
                missing_modulation = filtered_df["Modulation (%)"].isna() | (filtered_df["Modulation (%)"] <= 0)

                if missing_power.any() or missing_modulation.any():
                    st.error("Please ensure all rows have valid Modulation and Measured Power values.")
                else:
                    # Fill in missing optional values
                    filtered_df["Researcher"] = filtered_df["Researcher"].fillna("")
                    filtered_df["Sensor Model"] = filtered_df["Sensor Model"].fillna("")
                    filtered_df["Measurement Mode"] = filtered_df["Measurement Mode"].fillna("Stationary")
                    filtered_df["Fill Fraction (%)"] = filtered_df["Fill Fraction (%)"].fillna(100.0)
                    filtered_df["Notes"] = filtered_df["Notes"].fillna("")

                    # Convert datetime back to string format for storage consistency
                    if "Date" in filtered_df.columns and pd.api.types.is_datetime64_any_dtype(filtered_df["Date"]):
                        filtered_df["Date"] = filtered_df["Date"].dt.strftime("%Y-%m-%d %H:%M:%S")

                    # Save the data
                    save_dataframe(filtered_df, LASER_POWER_FILE)
                    st.session_state.laser_power_submitted = True
                    st.success(f"Saved {len(filtered_df)} laser power measurements.")
                    st.rerun()
            else:
                st.info("No changes to save.")


def render_laser_power_visualization():
    """Render visualizations for laser power measurements. All power values are in mW, modulation is in percent as set in ScanImage."""
    st.subheader("Power Analysis (Power in mW, Modulation in %)")  # Clarified units

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
        st.info("Add at least two measurements to see analysis.")
        return

    # Calculate statistics
    power_stats = calculate_statistics(measurements_df, "Measured Power (mW)")

    # Display metrics
    create_metric_row(
        [
            {"label": "Average Power (mW)", "value": f"{power_stats['mean']:.2f} mW"},  # Units explicit
            {"label": "Maximum Power (mW)", "value": f"{power_stats['max']:.2f} mW"},  # Units explicit
            {"label": "Measurements", "value": power_stats["count"]},
        ]
    )

    # Create power vs modulation plot
    def plot_power_vs_modulation(fig, ax):
        # Get data
        x = measurements_df["Modulation (%)"].values  # %
        y = measurements_df["Measured Power (mW)"].values  # mW

        # Calculate regression
        reg = linear_regression(x, y)

        # Plot data points
        ax.scatter(x, y, color="#4BA3C4", s=50, alpha=0.7, label="Measurements (mW vs %)")  # Units explicit

        # Plot regression line
        x_line = np.linspace(0, max(x) * 1.1, 100)
        y_line = reg["slope"] * x_line + reg["intercept"]
        ax.plot(
            x_line,
            y_line,
            color="#BF5701",
            linestyle="-",
            linewidth=2,
            label=f'Slope: {reg["slope"]:.3f} mW/% (Power per % Modulation)'
        )

        # Add labels and title
        ax.set_xlabel("Modulation (%) (ScanImage Power %)")  # Clarified
        ax.set_ylabel("Measured Power (mW)")  # Units explicit
        ax.set_title("Measured Power vs. Modulation Percentage (mW vs %)")  # Clarified

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
        This plot shows the relationship between laser modulation percentage (as set in ScanImage, 0-100%) and measured power at the sample (in mW).
        
        **Key insights:**
        - The slope represents the power/modulation ratio (mW per % modulation).
        - A linear relationship indicates proper laser and modulator function.
        - Deviations from linearity may indicate issues with the laser or power modulator.
        - Monitoring this ratio over time helps detect system degradation.
        
        **Typical values:**
        - Slope values (mW/%) vary by laser and objective.
        - For a given setup, this value should remain stable over time.
        - Significant changes may indicate alignment issues or component degradation.
        
        **Units:**
        - X-axis: Modulation (%) (ScanImage Power %)
        - Y-axis: Measured Power (mW)
        - Slope: mW/% (Power per % Modulation)
        """
        )


# add_to_rig_log function moved to modules/shared_utils.py to eliminate duplication
