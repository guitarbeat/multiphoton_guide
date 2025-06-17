"""
Source power measurement module for the Multiphoton Microscopy Guide application.
Implements protocols for measuring and recording laser power at the source.
"""

from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
from scipy.interpolate import CubicSpline

from modules.core.constants import SOURCE_POWER_COLUMNS, SOURCE_POWER_FILE, SOP_POWER_VS_PUMP_FILE
from modules.core.data_utils import filter_dataframe, load_dataframe, save_dataframe, exponential_fit
from modules.core.shared_utils import add_to_rig_log
from modules.ui.components import create_header, create_metric_row, create_plot
from modules.ui.theme import get_colors


def render_source_power_form():
    """Render the source power measurement form."""
    # Load existing data
    source_power_df = load_dataframe(SOURCE_POWER_FILE, pd.DataFrame())

    # Get colors for styling
    colors = get_colors()

    st.markdown('<div class="measurement-form">', unsafe_allow_html=True)

    st.subheader("Add Source Power Measurement")

    # Pump Current input and expected power info box OUTSIDE the form for live update
    col1, col2 = st.columns(2)
    with col1:
        pump_current = st.number_input(
            "Pump Current (mA):",
            min_value=0,
            max_value=8000,
            value=2000,
            step=250,
            help="Current setting for the pump diode",
            key="source_power_pump_current_live",
        )
        expected_power = get_expected_power(pump_current)
        st.info(f"Expected power: {expected_power:.2f} W")
        
        # Load SOP data to show equation
        sop_df = load_dataframe(SOP_POWER_VS_PUMP_FILE, pd.DataFrame())
        if not sop_df.empty and "Pump Current (mA)" in sop_df.columns and "Expected Power (W)" in sop_df.columns:
            # Filter to current study if available
            if "Study Name" in sop_df.columns:
                filtered_df = filter_dataframe(
                    sop_df, {"Study Name": st.session_state.study_name}
                )
                if filtered_df.empty:
                    filtered_df = sop_df
            else:
                filtered_df = sop_df
                
            # Get data for fit
            curr_sop = filtered_df["Pump Current (mA)"].astype(float).values
            power_sop = filtered_df["Expected Power (W)"].astype(float).values
            
            # Calculate fit if enough data points
            if len(curr_sop) >= 3:
                fit_params = exponential_fit(curr_sop, power_sop)
                equation_text = f"Power = {fit_params['a']:.3f} × e^({fit_params['b']:.5f} × Current) + {fit_params['c']:.3f}"
                r_squared_text = f"R² = {fit_params['r_squared']:.4f}"
                st.caption(f"Exponential Fit: {equation_text} ({r_squared_text})")

    with col2:
        pass  # for layout symmetry

    # The rest of the form (Measured Power, Notes, Submit)
    with st.form(key="source_power_form"):
        col1, col2 = st.columns(2)
        with col1:
            power = st.number_input(
                "Measured Power (W):",
                min_value=0.0,
                value=0.0,
                step=0.1,
                format="%.2f",
                help="Power measured at the source",
                key="source_power_measured_power",
            )
            # Show power difference from expected
            if power > 0:
                diff = power - expected_power
                diff_percent = (diff / expected_power) * 100 if expected_power else 0
                if abs(diff_percent) > 10:
                    st.warning(f"Power differs from expected by {diff_percent:.1f}%")
                else:
                    st.success(f"Power within {abs(diff_percent):.1f}% of expected")
        with col2:
            notes = st.text_area(
                "Notes:",
                help="Optional notes about the measurement",
                key="source_power_notes",
            )
        # Submit button
        submitted = st.form_submit_button("Add Measurement")
        if submitted:
            # Validate inputs
            if power <= 0:
                st.error("Please enter a valid power value.")
            else:
                # Create new entry
                new_entry = pd.DataFrame(
                    {
                        "Study Name": [st.session_state.study_name],
                        "Date": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                        "Wavelength (nm)": [st.session_state.wavelength],
                        "Pump Current (mA)": [pump_current],
                        "Measured Power (W)": [power],
                        "Notes": [notes],
                    }
                )
                
                # Calculate expected power but don't include in database entry to avoid schema issues
                expected_power = get_expected_power(pump_current)
                
                # Append to existing data
                updated_df = pd.concat([source_power_df, new_entry], ignore_index=True)
                # Save updated data
                save_dataframe(updated_df, SOURCE_POWER_FILE)
                # Set flag for rig log entry
                st.session_state.source_power_submitted = True
                # Success message
                st.success("Source power measurement added successfully!")
                # Force a rerun to refresh the page with the new data
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Live plot below the form ---
    st.subheader("Live Power vs. Pump Current")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    # Plot expected curve
    x_curve = np.linspace(0, 8500, 100)
    y_curve = get_expected_power(x_curve)
    ax.plot(x_curve, y_curve, label="Expected (SOP)", color="#BF5701", linestyle="--")
    # Plot previous measurements
    if not source_power_df.empty:
        ax.scatter(
            source_power_df["Pump Current (mA)"],
            source_power_df["Measured Power (W)"],
            color="#4BA3C4",
            s=50,
            alpha=0.7,
            label="Previous Measurements",
        )
    # Plot current (unsaved) value if entered
    if pump_current and power > 0:
        ax.scatter(
            [pump_current],
            [power],
            color="red",
            s=100,
            label="Current Entry",
            zorder=10,
        )
    ax.set_xlabel("Pump Current (mA)")
    ax.set_ylabel("Measured Power (W)")
    ax.set_title("Fiber Amplifier Power with Pump Current")
    ax.set_xlim(0, 8500)
    ax.set_ylim(0, 8)
    ax.grid(True, linestyle="--", alpha=0.7)
    ax.legend()
    st.pyplot(fig)


def get_expected_power(current):
    """Interpolate expected power based on pump current using SOP data from Supabase."""
    # Load SOP data from Supabase
    sop_df = load_dataframe(SOP_POWER_VS_PUMP_FILE, pd.DataFrame())
    
    # If no SOP data exists, use default values
    if sop_df.empty or "Pump Current (mA)" not in sop_df.columns or "Expected Power (W)" not in sop_df.columns:
        # Default values as fallback
        currents = np.array(
            [
                0,
                1000,
                1500,
                2000,
                2500,
                3000,
                3500,
                4000,
                4500,
                5000,
                5500,
                6000,
                6500,
                7000,
                7500,
                8000,
                8500,
                9000,
            ]
        )
        powers = np.array(
            [
                0.0,
                0.0,
                0.2,
                0.2,
                0.9,
                1.4,
                2.0,
                2.3,
                3.2,
                3.8,
                4.4,
                4.8,
                5.7,
                6.3,
                7.0,
                7.5,
                8.0,
                8.2,
            ]
        )
    else:
        # Filter to current study if available
        if "Study Name" in sop_df.columns:
            filtered_df = filter_dataframe(
                sop_df, {"Study Name": st.session_state.study_name}
            )
            # If no data for current study, use all SOP data
            if filtered_df.empty:
                filtered_df = sop_df
        else:
            filtered_df = sop_df
            
        # Sort by pump current
        filtered_df = filtered_df.sort_values("Pump Current (mA)")
        
        # Extract arrays for interpolation
        currents = filtered_df["Pump Current (mA)"].astype(float).values
        powers = filtered_df["Expected Power (W)"].astype(float).values
        
        # Add zero point if not present
        if currents[0] > 0:
            currents = np.insert(currents, 0, 0)
            powers = np.insert(powers, 0, 0)
    
    # Convert input to numpy array if it's not already
    current_input = np.asarray(current)
    # Clamp values to the range
    current_clipped = np.clip(current_input, currents[0], currents[-1])
    
    # Try to use exponential fit if we have enough points (preferred)
    if len(currents) >= 3:
        try:
            # Use exponential fit (preferred for laser power curves)
            fit_params = exponential_fit(currents, powers)
            
            # Apply the exponential model to get result
            result = fit_params["a"] * np.exp(fit_params["b"] * current_clipped) + fit_params["c"]
        except Exception:
            # Fallback to cubic spline or linear interpolation
            if len(currents) >= 4:
                try:
                    cs = CubicSpline(currents, powers, bc_type="natural")
                    result = cs(current_clipped)
                except Exception:
                    # Fallback to linear interpolation
                    result = np.interp(current_clipped, currents, powers)
            else:
                # Linear interpolation for few points
                result = np.interp(current_clipped, currents, powers)
    elif len(currents) >= 4:
        try:
            # Use cubic spline if exponential fit isn't possible but we have enough points
            cs = CubicSpline(currents, powers, bc_type="natural")
            result = cs(current_clipped)
        except Exception:
            # Fallback to linear interpolation
            result = np.interp(current_clipped, currents, powers)
    else:
        # Linear interpolation for few points
        result = np.interp(current_clipped, currents, powers)
    
    # Convert the result to a Python native type to ensure JSON serialization works
    if isinstance(result, np.ndarray):
        return result.tolist() if result.size > 1 else float(result)
    elif isinstance(result, np.generic):
        return result.item()  # Convert numpy scalar to Python scalar
    else:
        return result


def render_source_power_theory_and_procedure(theory_only=False, procedure_only=False):
    """Render the theory and/or procedure sections for source power measurement."""
    if not procedure_only:
        st.markdown(
            """
            ### Fiber Laser Source Power
            
            The fiber laser source power is a critical parameter that affects both the imaging quality and the overall system performance. Understanding and monitoring the source power helps:
            
            - Ensure consistent imaging conditions
            - Detect potential system issues early
            - Optimize laser performance
            - Maintain system stability
            
            The source power is primarily controlled by the pump current, with typical values ranging from 2000-8000 mA. The relationship between pump current and output power should be linear within the operating range.
        """
        )
    if not theory_only:
        st.markdown(
            """
            ### Procedure for Measuring Source Power
            
            1. **Start-up Sequence**
               - Turn key to "on" on the fiber laser controller box
               - Turn on pump temperature controller (I/O switch)
               - Start Arroyo control software and set temperature to 25°C
               - Turn on pump power controller
               - Press red button on controller box to enable seed laser
               - **VERIFY** that the TEC fan is spinning before proceeding
            
            2. **Power Measurement**
               - Position power meter between F-Shutter and F-HWP2
               - Open shutter ("enable")
               - Engage pump diode (press "Output" button)
               - Ramp up pump current in 250 mA steps
               - Record power at each current level
            
            3. **Expected Power Levels**
               - ~0.2 W at 2000 mA
               - ~2.3 W at 4000 mA
               - ~4.8 W at 6000 mA
               - ~7.5 W at 8000 mA
            
            4. **Pulse Width Control** (for reference)
               - Use grating pair (F-G1 & F-G2) to adjust pulse width
               - Typical positions for shortest pulse:
                 * 6.625 @ 4000 mA
                 * 4.75 @ 6000 mA
                 * 2.5 @ 8000 mA
        """
        )
        st.warning(
            """
        **CRITICAL CHECKS:**
        - Always ensure the TEC fan is spinning before increasing pump current
        - Do not raise pump current if power seems low at previous checkpoints
        - Monitor temperature (should be ~25°C)
        """
        )


def render_source_power_visualization():
    """Render visualizations for source power measurements."""
    st.subheader("Source Power Analysis")

    # Load existing data
    source_power_df = load_dataframe(SOURCE_POWER_FILE, pd.DataFrame())

    if source_power_df.empty:
        st.info("Add measurements to see analysis")
        return

    # Filter data for current study and wavelength
    filtered_df = filter_dataframe(
        source_power_df,
        {
            "Study Name": st.session_state.study_name,
            "Wavelength (nm)": st.session_state.wavelength,
        },
    )

    if filtered_df.empty:
        st.info("No measurements found for current study and wavelength")
        return

    # Display metrics
    create_metric_row(
        [
            {
                "label": "Latest Power",
                "value": f"{filtered_df['Measured Power (W)'].iloc[-1]:.2f} W",
            },
            {
                "label": "Pump Current",
                "value": f"{filtered_df['Pump Current (mA)'].iloc[-1]} mA",
            },
            {
                "label": "Power Ratio",
                "value": f"{filtered_df['Measured Power (W)'].iloc[-1] / filtered_df['Expected Power (W)'].iloc[-1]:.2f}",
            },
        ]
    )

    # Create power vs current plot
    def plot_power_vs_current(fig, ax):
        # Get data
        x = filtered_df["Pump Current (mA)"].values
        y = filtered_df["Measured Power (W)"].values

        # Plot data points
        ax.scatter(x, y, color="#4BA3C4", s=50, alpha=0.7, label="Measurements")

        # Load SOP data for expected power curve
        sop_df = load_dataframe(SOP_POWER_VS_PUMP_FILE, pd.DataFrame())
        
        if not sop_df.empty and "Pump Current (mA)" in sop_df.columns and "Expected Power (W)" in sop_df.columns:
            # Get SOP data
            curr_sop = sop_df["Pump Current (mA)"].astype(float).values
            power_sop = sop_df["Expected Power (W)"].astype(float).values
            
            # Sort by current for plotting
            sort_indices = np.argsort(curr_sop)
            curr_sop = curr_sop[sort_indices]
            power_sop = power_sop[sort_indices]
            
            # Plot the SOP points
            ax.scatter(curr_sop, power_sop, color="#BF5701", s=60, marker='s', 
                      label="SOP Data Points")
            
            # Create exponential fit for SOP data
            if len(curr_sop) >= 3:
                fit_params = exponential_fit(curr_sop, power_sop)
                
                # Generate smooth curve for plotting
                x_curve = np.linspace(0, max(curr_sop) * 1.1, 100)
                y_curve = fit_params["a"] * np.exp(fit_params["b"] * x_curve) + fit_params["c"]
                
                # Plot the fit
                ax.plot(
                    x_curve, 
                    y_curve, 
                    color="#BF5701", 
                    linestyle="-", 
                    label=f"Exp Fit: {fit_params['a']:.3f}*e^({fit_params['b']:.5f}*x) + {fit_params['c']:.3f}"
                )
                
                # Display formula and R²
                equation_text = f"Power = {fit_params['a']:.3f} × e^({fit_params['b']:.5f} × Current) + {fit_params['c']:.3f}"
                r_squared_text = f"R² = {fit_params['r_squared']:.4f}"
                ax.text(0.05, 0.95, equation_text + "\n" + r_squared_text,
                      transform=ax.transAxes, fontsize=9,
                      verticalalignment='top',
                      bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            else:
                # Just connect the dots if not enough points for fitting
                ax.plot(curr_sop, power_sop, color="#BF5701", linestyle="--", 
                      label="Expected Values")
        else:
            # Fallback to hardcoded expected values if no SOP data
            expected_x = [2000, 4000, 6000, 8000]
            expected_y = [0.2, 2.3, 4.8, 7.5]
            ax.plot(
                expected_x,
                expected_y,
                color="#BF5701",
                linestyle="--",
                label="Expected Values",
            )

        # Add labels and title
        ax.set_xlabel("Pump Current (mA)")
        ax.set_ylabel("Measured Power (W)")
        ax.set_title("Source Power vs. Pump Current")
        
        # Set reasonable axis limits
        ax.set_xlim(0, max(filtered_df["Pump Current (mA)"].max() * 1.1, 8500))
        ax.set_ylim(0, max(filtered_df["Measured Power (W)"].max() * 1.1, 8.0))

        # Add grid and legend
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.legend(loc="best")

    # Display the plot
    power_plot = create_plot(plot_power_vs_current)
    st.pyplot(power_plot)

    # Add explanation
    with st.popover("📊 Understanding This Plot", use_container_width=True):
        st.markdown(
            """
        This plot shows the relationship between pump current and measured power at the source.
        
        **Key insights:**
        - The exponential curve shows the expected power values at different current levels
        - The curve follows the form: Power = a × e^(b × Current) + c
        - Exponential behavior is expected due to the physics of laser gain media
        - Deviations from expected values may indicate:
          * Alignment issues
          * Component degradation
          * Temperature control problems
        - Regular monitoring helps detect system changes over time
        
        **Typical values:**
        - ~0.2 W at 2000 mA
        - ~2.3 W at 4000 mA
        - ~4.8 W at 6000 mA
        - ~7.5 W at 8000 mA
        """
        )
