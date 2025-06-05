"""
Source power measurement module for the Multiphoton Microscopy Guide application.
Implements protocols for measuring and recording laser power at the source.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np
from scipy.interpolate import CubicSpline

from modules.core.data_utils import load_dataframe, save_dataframe, filter_dataframe
from modules.ui.components import create_metric_row, create_plot
from modules.core.constants import SOURCE_POWER_FILE


def render_source_power_form():
    """Render the source power measurement form."""
    # Load existing data
    source_power_df = load_dataframe(SOURCE_POWER_FILE, pd.DataFrame())

    # Get colors for styling

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
                        "Expected Power (W)": [expected_power],
                        "Notes": [notes],
                    }
                )
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
    """Interpolate expected power based on pump current. Uses cubic spline for smoothness."""
    # Combined anchor points (with exact values) and visually extracted data
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
    current = np.asarray(current)
    # Clamp values to the range
    current_clipped = np.clip(current, currents[0], currents[-1])
    try:
        cs = CubicSpline(currents, powers, bc_type="natural")
        return cs(current_clipped)
    except Exception:
        # Fallback to linear interpolation if scipy is not available
        return np.interp(current_clipped, currents, powers)


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

        # Add reference line for expected values
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

        # Add grid and legend
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.legend()

    # Display the plot
    power_plot = create_plot(plot_power_vs_current)
    st.pyplot(power_plot)

    # Add explanation
    with st.popover("📊 Understanding This Plot", use_container_width=True):
        st.markdown(
            """
        This plot shows the relationship between pump current and measured power at the source.

        **Key insights:**
        - The dashed line shows expected power values at different current levels
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
