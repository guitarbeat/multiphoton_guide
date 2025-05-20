"""
Laser power measurement module for the Multiphoton Microscopy Guide application.
Implements protocols for measuring and recording laser power at the sample.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

from modules.data_utils import load_dataframe, save_dataframe, ensure_columns, safe_numeric_conversion, filter_dataframe, calculate_statistics, linear_regression
from modules.ui_components import create_header, create_metric_row, create_plot
from modules.theme import get_colors

# Constants
LASER_POWER_FILE = "laser_power_measurements.csv"
RIG_LOG_FILE = "rig_log.csv"

def render_laser_power_tab(use_sidebar_values=False):
    """Render the laser power measurement tab content.
    
    Args:
        use_sidebar_values: If True, use values from the sidebar instead of showing duplicate form fields.
    """
    
    create_header("Laser Power at the Sample")
    
    # Create main layout with the measurement form prominently displayed
    render_simplified_measurement_form(use_sidebar_values)
    
    # Create two columns for theory/procedure and visualization
    col1, col2 = st.columns([1, 1])
    
    with col1:
        render_laser_power_theory_and_procedure()
    
    with col2:
        render_laser_power_visualization()
    
    # Add entry to rig log if measurements were taken
    if st.session_state.get('laser_power_submitted', False):
        add_to_rig_log("Laser Power Measurement", 
                      f"Measured laser power at {st.session_state.wavelength} nm using {st.session_state.get('sensor_model', 'unknown sensor')}")
        # Reset the flag
        st.session_state.laser_power_submitted = False

def render_laser_power_theory_and_procedure():
    """Render the theory and procedure sections for laser power measurement using tabs."""
    
    tab1, tab2 = st.tabs(["📖 Introduction & Theory", "📋 Measurement Procedure"])
    
    with tab1:
        st.markdown("""
            Measuring and monitoring laser power at the sample is critical in multiphoton microscopy for maintaining sample integrity and data quality. 
            
            Fluorescence emission is proportional to the average laser power squared, so small changes in laser power can result in large changes to your data. Exposing your sample to excessive laser power can cause photobleaching and photodamage, altering your sample and measurements.
            
            There are two types of laser-induced photodamage in multiphoton microscopy:
            
            1. **Local heating** of the imaged area, which is linearly related to average laser power
            2. **Photochemical degradation** (bleaching or ablation), which is nonlinearly related to average laser power
            
            Knowing the laser power is essential for consistency between experiments, for minimizing photodamage, and for monitoring system health.
        """)
    
    with tab2:
        st.markdown("""
            ### Procedure for Measuring Laser Power at the Sample
            
            1. **Prepare the power meter**
               - Place the power meter sensor under the objective
               - Ensure the sensor is centered in the field of view
            
            2. **Configure the microscope**
               - Set the wavelength to the desired value
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
        """)
        
        st.warning("**CRITICAL:** Always measure with the same objective, as transmission efficiency varies between objectives.")
        st.warning("**CRITICAL:** For consistent measurements, use the same measurement mode (stationary or scanning) each time.")

def render_simplified_measurement_form(use_sidebar_values=False):
    """Render a simplified, prominent measurement form for laser power.
    
    Args:
        use_sidebar_values: If True, use values from the sidebar instead of showing duplicate form fields.
    """
    
    # Get theme colors
    colors = get_colors()
    
    # Load existing data
    laser_power_df = load_dataframe(LASER_POWER_FILE, pd.DataFrame({
        "Study Name": [],
        "Date": [],
        "Wavelength (nm)": [],
        "Sensor Model": [],
        "Measurement Mode": [],
        "Fill Fraction (%)": [],
        "Modulation (%)": [],
        "Measured Power (mW)": [],
        "Notes": []
    }))
    
    # Ensure all required columns exist
    required_columns = ["Study Name", "Date", "Wavelength (nm)", "Sensor Model", 
                        "Measurement Mode", "Fill Fraction (%)", "Modulation (%)", 
                        "Measured Power (mW)", "Notes"]
    
    laser_power_df = ensure_columns(laser_power_df, required_columns)
    
    # Convert numeric columns
    numeric_columns = ["Wavelength (nm)", "Fill Fraction (%)", "Modulation (%)", "Measured Power (mW)"]
    laser_power_df = safe_numeric_conversion(laser_power_df, numeric_columns)
    
    # Create a container with a border and background that matches the dark theme
    with st.container():
        st.markdown('<div class="measurement-form">', unsafe_allow_html=True)
        
        # Display current settings from sidebar if using sidebar values
        if use_sidebar_values:
            # Display current settings from sidebar
            st.subheader("Current Settings")
            settings_col1, settings_col2, settings_col3 = st.columns([1, 1, 1])
            
            with settings_col1:
                st.info(f"**Sensor Model:** {st.session_state.sensor_model}")
            
            with settings_col2:
                st.info(f"**Measurement Mode:** {st.session_state.measurement_mode}")
            
            with settings_col3:
                if st.session_state.measurement_mode == "Scanning":
                    st.info(f"**Fill Fraction:** {st.session_state.fill_fraction}%")
                else:
                    st.info("**Fill Fraction:** 100%")
            
            # Use session state values
            sensor_model = st.session_state.sensor_model
            measurement_mode = st.session_state.measurement_mode
            fill_fraction = st.session_state.fill_fraction if st.session_state.measurement_mode == "Scanning" else 100
        else:
            # Initialize session state variables before widget creation
            if 'sensor_model' not in st.session_state:
                st.session_state.sensor_model = ""
            
            if 'measurement_mode' not in st.session_state:
                st.session_state.measurement_mode = "Stationary"
            
            if 'fill_fraction' not in st.session_state:
                st.session_state.fill_fraction = 100
                
            # Session setup in a compact layout
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                # Use the widget's key for state management
                sensor_model = st.text_input(
                    "Sensor Model:", 
                    value=st.session_state.sensor_model,
                    key="sensor_model",
                    help="Enter the model of your power meter sensor"
                )
            
            with col2:
                # Use the widget's key for state management
                measurement_mode = st.radio(
                    "Measurement Mode:", 
                    ["Stationary", "Scanning"],
                    index=0 if st.session_state.measurement_mode == "Stationary" else 1,
                    key="measurement_mode",
                    help="Stationary: beam fixed at center. Scanning: beam continuously scanning."
                )
            
            with col3:
                # Fill fraction (only shown if scanning mode is selected)
                fill_fraction = st.session_state.fill_fraction  # Default from session state
                if measurement_mode == "Scanning":
                    fill_fraction = st.number_input(
                        "Fill Fraction (%):", 
                        min_value=1, max_value=100, 
                        value=int(st.session_state.fill_fraction),
                        key="fill_fraction",
                        help="Percentage of time the beam is 'on' during scanning"
                    )
                else:
                    st.info("Fill fraction: 100%")
                    fill_fraction = 100
        
        # Horizontal line
        st.markdown(f"<hr style='border-color: {colors['surface']};'>", unsafe_allow_html=True)
        
        # Single measurement form
        st.subheader("Add Single Measurement")
        
        with st.form(key="quick_measurement_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                modulation = st.number_input(
                    "Modulation (%):", 
                    min_value=0, max_value=100, value=10, step=5,
                    key="modulation_input",
                    help="Percentage of maximum laser power"
                )
                
                # Validation message for modulation
                if modulation <= 0:
                    st.warning("Modulation must be greater than 0%")
            
            with col2:
                power = st.number_input(
                    "Measured Power (mW):", 
                    min_value=0.0, value=0.0, step=0.1, format="%.2f",
                    key="power_input",
                    help="Power measured at the sample"
                )
                
                # Validation message for power
                if power <= 0:
                    st.warning("Power must be greater than 0 mW")
            
            notes = st.text_area(
                "Notes:", 
                key="notes_input",
                help="Optional notes about the measurement"
            )
            
            # Submit button
            submitted = st.form_submit_button("Add Measurement")
            
            if submitted:
                # Validate inputs
                if power <= 0 or modulation <= 0:
                    st.error("Please enter valid power and modulation values.")
                else:
                    # Create new entry
                    new_entry = pd.DataFrame({
                        "Study Name": [st.session_state.study_name],
                        "Date": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                        "Wavelength (nm)": [st.session_state.wavelength],
                        "Sensor Model": [sensor_model],
                        "Measurement Mode": [measurement_mode],
                        "Fill Fraction (%)": [fill_fraction],
                        "Modulation (%)": [modulation],
                        "Measured Power (mW)": [power],
                        "Notes": [notes]
                    })
                    
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
        
        # Horizontal line
        st.markdown(f"<hr style='border-color: {colors['surface']};'>", unsafe_allow_html=True)
        
        # Show recent measurements
        st.subheader("Recent Measurements")
        
        if not laser_power_df.empty:
            # Filter to current study and wavelength
            filtered_df = filter_dataframe(
                laser_power_df, 
                {"Study Name": st.session_state.study_name, 
                 "Wavelength (nm)": st.session_state.wavelength}
            )
            
            if not filtered_df.empty:
                # Sort by date (newest first) and select only the most recent measurements
                filtered_df = filtered_df.sort_values("Date", ascending=False).head(5)
                
                # Display the table with selected columns
                st.dataframe(
                    filtered_df[["Date", "Modulation (%)", "Measured Power (mW)", "Measurement Mode"]],
                    hide_index=True,
                    use_container_width=True
                )
                
                # Calculate and display the power/modulation ratio
                if len(filtered_df) >= 2:
                    # Use only measurements with the same measurement mode and fill fraction
                    mode_filtered = filtered_df[
                        (filtered_df["Measurement Mode"] == filtered_df["Measurement Mode"].iloc[0]) &
                        (filtered_df["Fill Fraction (%)"] == filtered_df["Fill Fraction (%)"].iloc[0])
                    ]
                    
                    if len(mode_filtered) >= 2:
                        # Linear regression
                        X = mode_filtered["Modulation (%)"].values
                        y = mode_filtered["Measured Power (mW)"].values
                        
                        # Get regression results
                        regression_result = linear_regression(X, y)
                        slope = regression_result['slope']
                        intercept = regression_result['intercept']
                        r_squared = regression_result['r_squared']
                        
                        # Display metrics
                        metrics = [
                            {"label": "Power/Modulation Ratio", "value": f"{slope:.4f} mW/%"},
                            {"label": "R² Value", "value": f"{r_squared:.4f}"},
                            {"label": "Offset", "value": f"{intercept:.4f} mW"}
                        ]
                        
                        create_metric_row(metrics)
            else:
                st.info("No measurements for the current study and wavelength.")
        else:
            st.info("No measurements recorded yet.")
        
        st.markdown('</div>', unsafe_allow_html=True)

def render_laser_power_visualization():
    """Render visualizations for laser power measurements."""
    
    st.subheader("Power Analysis")
    
    # Check if we have measurements in session state first
    has_measurements = False
    measurements_df = pd.DataFrame()
    
    if 'latest_measurements' in st.session_state and len(st.session_state.latest_measurements) >= 2:
        # Convert session state measurements to DataFrame for analysis
        measurements_df = pd.DataFrame(st.session_state.latest_measurements)
        has_measurements = True
    else:
        # Load existing data
        laser_power_df = load_dataframe(LASER_POWER_FILE, pd.DataFrame())
        
        if not laser_power_df.empty:
            # Filter data for current study and wavelength
            current_filters = {
                "Study Name": st.session_state.study_name,
                "Wavelength (nm)": float(st.session_state.wavelength),
                "Sensor Model": st.session_state.sensor_model,
                "Measurement Mode": st.session_state.measurement_mode,
                "Fill Fraction (%)": float(st.session_state.fill_fraction)
            }
            
            filtered_df = filter_dataframe(laser_power_df, current_filters)
            
            if len(filtered_df) >= 2:
                # Convert to numeric to ensure calculations work
                filtered_df = safe_numeric_conversion(
                    filtered_df, 
                    ["Modulation (%)", "Measured Power (mW)"]
                )
                
                measurements_df = filtered_df[["Modulation (%)", "Measured Power (mW)"]]
                has_measurements = True
    
    if not has_measurements or len(measurements_df) < 2:
        st.info("Add at least two measurements to see analysis")
        return
    
    # Calculate statistics
    power_stats = calculate_statistics(measurements_df, "Measured Power (mW)")
    
    # Display metrics
    create_metric_row([
        {"label": "Average Power", "value": f"{power_stats['mean']:.2f} mW"},
        {"label": "Maximum Power", "value": f"{power_stats['max']:.2f} mW"},
        {"label": "Measurements", "value": power_stats['count']}
    ])
    
    # Create power vs modulation plot
    def plot_power_vs_modulation(fig, ax):
        # Get data
        x = measurements_df["Modulation (%)"].values
        y = measurements_df["Measured Power (mW)"].values
        
        # Calculate regression
        reg = linear_regression(x, y)
        
        # Plot data points
        ax.scatter(x, y, color='#4BA3C4', s=50, alpha=0.7, label='Measurements')
        
        # Plot regression line
        x_line = np.linspace(0, max(x) * 1.1, 100)
        y_line = reg['slope'] * x_line + reg['intercept']
        ax.plot(x_line, y_line, color='#BF5701', linestyle='-', linewidth=2, 
                label=f'Slope: {reg["slope"]:.3f} mW/%')
        
        # Add labels and title
        ax.set_xlabel('Modulation (%)')
        ax.set_ylabel('Measured Power (mW)')
        ax.set_title(f'Power vs. Modulation at {st.session_state.wavelength} nm')
        
        # Add grid and legend
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()
        
        # Set limits
        ax.set_xlim(0, max(x) * 1.1)
        ax.set_ylim(0, max(y) * 1.1)
    
    # Display the plot
    power_plot = create_plot(plot_power_vs_modulation)
    st.pyplot(power_plot)
    
    # Add explanation
    with st.popover("📊 Understanding This Plot", use_container_width=True):
        st.markdown("""
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
        """)

def add_to_rig_log(activity, description):
    """Add an entry to the rig log."""
    
    # Load existing rig log
    rig_log_df = load_dataframe(RIG_LOG_FILE, pd.DataFrame({
        "Date": [],
        "Researcher": [],
        "Activity": [],
        "Description": [],
        "Category": []
    }))
    
    # Create new entry
    new_entry = pd.DataFrame({
        "Date": [datetime.now().strftime("%Y-%m-%d %H:%M")],
        "Researcher": [st.session_state.researcher or "Unknown Researcher"],
        "Activity": [activity],
        "Description": [description],
        "Category": ["Measurement"]
    })
    
    # Append new entry
    rig_log_df = pd.concat([rig_log_df, new_entry], ignore_index=True)
    
    # Save updated log
    save_dataframe(rig_log_df, RIG_LOG_FILE)
