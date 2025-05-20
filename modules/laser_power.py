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

def render_laser_power_tab():
    """Render the laser power measurement tab content."""
    
    create_header("Laser Power at the Sample")
    
    # Create main layout with the measurement form prominently displayed
    render_simplified_measurement_form()
    
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

def render_simplified_measurement_form():
    """Render a simplified, prominent measurement form for laser power."""
    
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
            
            notes = st.text_input(
                "Notes:", 
                key="notes_input",
                help="Optional notes about this measurement"
            )
            
            # Custom styling for the submit button
            st.markdown(f"""
            <style>
            div[data-testid="stForm"] button[kind="formSubmit"] {{
                background-color: {colors['primary']};
                color: white;
                border-radius: 4px;
                padding: 0.25rem 1rem;
                font-weight: bold;
            }}
            div[data-testid="stForm"] button[kind="formSubmit"]:hover {{
                background-color: {colors['accent']};
            }}
            </style>
            """, unsafe_allow_html=True)
            
            submitted = st.form_submit_button("Add Measurement", use_container_width=True)
        
        if submitted:
            if modulation <= 0:
                st.error("Cannot add measurement: Modulation must be greater than 0%")
            elif power <= 0:
                st.error("Cannot add measurement: Power must be greater than 0 mW")
            else:
                # Create a new measurement row
                new_measurement = pd.DataFrame({
                    "Study Name": [st.session_state.study_name],
                    "Date": [datetime.now().strftime("%Y-%m-%d %H:%M")],
                    "Wavelength (nm)": [float(st.session_state.wavelength)],
                    "Sensor Model": [sensor_model],
                    "Measurement Mode": [measurement_mode],
                    "Fill Fraction (%)": [float(fill_fraction)],
                    "Modulation (%)": [float(modulation)],
                    "Measured Power (mW)": [float(power)],
                    "Notes": [notes]
                })
                
                # Append to the existing dataframe
                laser_power_df = pd.concat([laser_power_df, new_measurement], ignore_index=True)
                
                # Save the updated dataframe
                save_dataframe(laser_power_df, LASER_POWER_FILE)
                
                # Set flag for rig log entry
                st.session_state.laser_power_submitted = True
                
                # Store the latest measurement in session state for immediate display
                if 'latest_measurements' not in st.session_state:
                    st.session_state.latest_measurements = []
                
                st.session_state.latest_measurements.append({
                    "Modulation (%)": float(modulation),
                    "Measured Power (mW)": float(power),
                    "Notes": notes
                })
                
                st.success(f"Added measurement: {modulation}% modulation = {power} mW")
        
        # Add clear form button
        if st.button("Clear Form", key="clear_form_button", help="Reset all form fields to their default values"):
            # Reset form values but keep session settings
            st.session_state.modulation_input = 10
            st.session_state.power_input = 0.0
            st.session_state.notes_input = ""
            st.experimental_rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Display current measurements table
    st.subheader("Current Measurements")
    
    # First check if we have any measurements in the session state
    has_measurements = False
    
    if 'latest_measurements' in st.session_state and st.session_state.latest_measurements:
        # Convert session state measurements to DataFrame for display
        session_measurements_df = pd.DataFrame(st.session_state.latest_measurements)
        has_measurements = True
    else:
        # If no session state measurements, try to load from file with proper filtering
        # Filter for current study and wavelength first
        current_filters = {
            "Study Name": st.session_state.study_name,
            "Wavelength (nm)": float(st.session_state.wavelength)
        }
        
        filtered_df = filter_dataframe(laser_power_df, current_filters)
        
        # Then filter for current session parameters
        session_filters = {
            "Sensor Model": sensor_model,
            "Measurement Mode": measurement_mode,
            "Fill Fraction (%)": float(fill_fraction)
        }
        
        session_df = filter_dataframe(filtered_df, session_filters)
        
        if not session_df.empty:
            # Configure columns for display
            display_columns = ["Modulation (%)", "Measured Power (mW)", "Notes"]
            session_measurements_df = session_df[display_columns].copy()
            has_measurements = True
        else:
            session_measurements_df = pd.DataFrame()
    
    if not has_measurements:
        st.info("No measurements recorded for current session. Add measurements using the form above.")
    else:
        # Display the table
        st.dataframe(
            session_measurements_df.sort_values("Modulation (%)") if "Modulation (%)" in session_measurements_df.columns else session_measurements_df,
            use_container_width=True,
            column_config={
                "Modulation (%)": st.column_config.NumberColumn(
                    "Modulation (%)",
                    format="%d %%"
                ),
                "Measured Power (mW)": st.column_config.NumberColumn(
                    "Measured Power (mW)",
                    format="%.2f mW"
                )
            }
        )
        
        # Add clear button with custom styling
        st.markdown(f"""
        <style>
        div.stButton > button:first-child {{
            background-color: {colors['secondary']};
            color: white;
        }}
        div.stButton > button:hover {{
            background-color: {colors['info']};
        }}
        </style>
        """, unsafe_allow_html=True)
        
        if st.button("Clear Session Measurements"):
            # Clear session state measurements
            if 'latest_measurements' in st.session_state:
                st.session_state.latest_measurements = []
            
            # Find rows in the original dataframe that match the current session
            mask = (
                (laser_power_df["Study Name"] == st.session_state.study_name) &
                (laser_power_df["Wavelength (nm)"] == float(st.session_state.wavelength)) &
                (laser_power_df["Sensor Model"] == sensor_model) &
                (laser_power_df["Measurement Mode"] == measurement_mode) &
                (laser_power_df["Fill Fraction (%)"] == float(fill_fraction))
            )
            
            # Remove those rows
            laser_power_df = laser_power_df[~mask]
            
            # Save the updated dataframe
            save_dataframe(laser_power_df, LASER_POWER_FILE)
            
            st.success("All measurements for this session have been cleared.")
            st.experimental_rerun()

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
