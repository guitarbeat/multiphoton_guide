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
    """Render the source power measurement editable dataframe."""
    # --- Quick Measurement Entry ---
    st.subheader("Quick Measurement Entry (Power in mW)")  # Units clarified
    if "quick_pump_currents" not in st.session_state:
        st.session_state.quick_pump_currents = [1000, 1250, 1500, 1750, 2000]
    quick_pump_currents = st.session_state.quick_pump_currents

    # Add more rows button
    col_add, col_reset = st.columns([1, 1])
    with col_add:
        if st.button("Add Row", key="add_more_quick_rows"):
            last_val = quick_pump_currents[-1] if quick_pump_currents else 2000
            next_val = last_val + 250
            quick_pump_currents.append(next_val)
            st.session_state.quick_pump_currents = quick_pump_currents
    with col_reset:
        if st.button("Reset Rows", key="reset_quick_rows"):
            st.session_state.quick_pump_currents = [1000, 1250, 1500, 1750, 2000]
            quick_pump_currents = st.session_state.quick_pump_currents

    quick_entries = []
    quick_form = st.form(key="quick_measurement_form")
    quick_cols = quick_form.columns(len(quick_pump_currents))
    quick_mw_values = []
    for i, current in enumerate(quick_pump_currents):
        with quick_cols[i]:
            mw = quick_form.number_input(f"{current} mA (Power in mW)", min_value=0.0, step=1.0, format="%.1f", key=f"quick_mw_{current}")  # Units clarified
            quick_mw_values.append(mw)
    if quick_submit := quick_form.form_submit_button("Add Quick Measurements"):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for i, current in enumerate(quick_pump_currents):
            mw = quick_mw_values[i]
            if mw > 0:
                entry = {
                    "Study Name": st.session_state.study_name,
                    "Date": now,
                    "Wavelength (nm)": st.session_state.wavelength,
                    "Pump Current (mA)": current,
                    "Temperature (°C)": 25.0,
                    "Measured Power (mW)": mw,
                    "Pulse Width (fs)": 0,
                    "Grating Position": "",
                    "Fan Status": "Unknown",
                    "Notes": "Quick entry"
                }
                quick_entries.append(entry)
        if quick_entries:
            # Load existing data
            source_power_df = load_dataframe(SOURCE_POWER_FILE, pd.DataFrame())
            # Append new entries
            new_df = pd.DataFrame(quick_entries)
            combined_df = pd.concat([source_power_df, new_df], ignore_index=True)
            save_dataframe(combined_df, SOURCE_POWER_FILE)
            st.success(f"Added {len(quick_entries)} quick measurements.")
            st.session_state.source_power_submitted = True
            st.rerun()
    # --- End Quick Measurement Entry ---

    # Load existing data
    source_power_df = load_dataframe(SOURCE_POWER_FILE, pd.DataFrame())

    st.subheader("Source Power Measurements (All values in mW)")  # Units clarified

    # Initialize with default structure if empty
    if source_power_df.empty:
        source_power_df = pd.DataFrame(columns=SOURCE_POWER_COLUMNS)
        # Add one empty row for editing
        source_power_df.loc[0] = [
            st.session_state.study_name,                           # Study Name
            datetime.now(),                                        # Date (as datetime object)
            st.session_state.wavelength,                           # Wavelength (nm)
            2000,                                                  # Pump Current (mA)
            25.0,                                                  # Temperature (°C)
            0.0,                                                   # Measured Power (mW)
            0,                                                     # Pulse Width (fs)
            "",                                                    # Grating Position
            "Unknown",                                            # Fan Status
            ""                                                     # Notes
        ]

    # Convert Date column to datetime if it exists and is string type
    if not source_power_df.empty and "Date" in source_power_df.columns and source_power_df["Date"].dtype == 'object':
        try:
            source_power_df["Date"] = pd.to_datetime(source_power_df["Date"])
        except Exception:
            # If conversion fails, keep as string and use text column config
            pass

    # Create column configuration for the data editor
    column_config = {
        "Study Name": st.column_config.TextColumn(
            "Study Name",
            default=st.session_state.study_name,
            help="Name of the study."
        ),
        "Wavelength (nm)": st.column_config.NumberColumn(
            "Wavelength (nm)",
            default=st.session_state.wavelength,
            help="Wavelength setting."
        ),
        "Pump Current (mA)": st.column_config.NumberColumn(
            "Pump Current (mA)",
            min_value=0,
            max_value=8000,
            step=250,
            help="Current setting for the pump diode."
        ),
        "Temperature (°C)": st.column_config.NumberColumn(
            "Temperature (°C)",
            min_value=0.0,
            max_value=50.0,
            step=0.1,
            format="%.1f",
            help="Operating temperature."
        ),
        "Measured Power (mW)": st.column_config.NumberColumn(
            "Measured Power (mW)",  # Units explicit
            min_value=0.0,
            step=1.0,
            format="%.0f",
            help="Power measured at the source (in mW)."
        ),
        "Pulse Width (fs)": st.column_config.NumberColumn(
            "Pulse Width (fs)",
            min_value=0,
            step=1,
            help="Pulse width in femtoseconds."
        ),
        "Grating Position": st.column_config.TextColumn(
            "Grating Position",
            help="Position of the grating."
        ),
        "Fan Status": st.column_config.SelectboxColumn(
            "Fan Status",
            options=["Running", "Stopped", "Unknown"],
            help="Status of the cooling fan."
        ),
        "Notes": st.column_config.TextColumn(
            "Notes",
            help="Optional notes about the measurement."
        )
    }

    # Add Date column configuration based on data type
    if not source_power_df.empty and "Date" in source_power_df.columns:
        if pd.api.types.is_datetime64_any_dtype(source_power_df["Date"]):
            column_config["Date"] = st.column_config.DatetimeColumn(
                "Date",
                help="Date and time of measurement."
            )
        else:
            column_config["Date"] = st.column_config.TextColumn(
                "Date",
                help="Date and time of measurement (YYYY-MM-DD HH:MM:SS)."
            )
    else:
        # Default for new dataframes
        column_config["Date"] = st.column_config.DatetimeColumn(
            "Date",
            help="Date and time of measurement."
        )

    # Display editable dataframe
    edited_df = st.data_editor(
        source_power_df,
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        key="source_power_editor"
    )

    # Save button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("💾 Save Changes", use_container_width=True, key="save_source_power_changes"):
            # Remove empty rows (rows where key measurement fields are empty or zero)
            filtered_df = edited_df[
                (edited_df["Pump Current (mA)"] > 0) |
                (edited_df["Measured Power (mW)"] > 0) |
                (edited_df["Notes"].str.strip() != "") |
                (edited_df["Pulse Width (fs)"] > 0) |
                (edited_df["Grating Position"].str.strip() != "")
            ].copy()

            # Validate required fields
            if not filtered_df.empty:
                # Check for missing values in critical columns
                missing_power = filtered_df["Measured Power (mW)"].isna() | (filtered_df["Measured Power (mW)"] <= 0)
                missing_current = filtered_df["Pump Current (mA)"].isna() | (filtered_df["Pump Current (mA)"] <= 0)

                if missing_power.any() or missing_current.any():
                    st.error("Please ensure all rows have valid Pump Current and Measured Power values.")
                else:
                    # Fill in missing optional values
                    filtered_df["Temperature (°C)"] = filtered_df["Temperature (°C)"].fillna(25.0)
                    filtered_df["Pulse Width (fs)"] = filtered_df["Pulse Width (fs)"].fillna(0)
                    filtered_df["Grating Position"] = filtered_df["Grating Position"].fillna("")
                    filtered_df["Fan Status"] = filtered_df["Fan Status"].fillna("Unknown")
                    filtered_df["Notes"] = filtered_df["Notes"].fillna("")

                    # Convert datetime back to string format for storage consistency
                    if "Date" in filtered_df.columns and pd.api.types.is_datetime64_any_dtype(filtered_df["Date"]):
                        filtered_df["Date"] = filtered_df["Date"].dt.strftime("%Y-%m-%d %H:%M:%S")

                    # Save the data
                    save_dataframe(filtered_df, SOURCE_POWER_FILE)
                    st.session_state.source_power_submitted = True
                    st.success(f"Saved {len(filtered_df)} source power measurements.")
                    st.rerun()
            else:
                st.warning("No valid measurements to save.")

    # Show expected power info
    if not edited_df.empty and len(edited_df) > 0:
        st.subheader("Expected Power Reference (mW)")  # Units clarified

        # Load SOP data to show equation
        sop_df = load_dataframe(SOP_POWER_VS_PUMP_FILE, pd.DataFrame())

        # Check for column names (backward compatibility)
        power_col = None
        if not sop_df.empty and "Pump Current (mA)" in sop_df.columns:
            if "Expected Power (mW)" in sop_df.columns:
                power_col = "Expected Power (mW)"
            elif "Expected Power (W)" in sop_df.columns:
                power_col = "Expected Power (W)"

        if power_col is not None:
            # Filter to current study if available
            if "Study Name" in sop_df.columns:
                filtered_sop_df = filter_dataframe(
                    sop_df, {"Study Name": st.session_state.study_name}
                )
                if filtered_sop_df.empty:
                    filtered_sop_df = sop_df
            else:
                filtered_sop_df = sop_df

            # Get data for fit
            curr_sop = filtered_sop_df["Pump Current (mA)"].astype(float).values
            power_sop = filtered_sop_df[power_col].astype(float).values

            # Convert W to mW if needed for consistency
            if power_col == "Expected Power (W)":
                power_sop = power_sop * 1000  # Convert W to mW

            # Calculate fit if enough data points
            if len(curr_sop) >= 3:
                fit_params = exponential_fit(curr_sop, power_sop)
                equation_text = f"Power (mW) = {fit_params['a']:.1f} × e^({fit_params['b']:.5f} × Current) + {fit_params['c']:.1f}"
                r_squared_text = f"R² = {fit_params['r_squared']:.4f}"
                st.info(f"**Expected Power Formula:** {equation_text} ({r_squared_text})")

        # Show expected power for current entries
        expected_powers = []
        for _, row in edited_df.iterrows():
            if pd.notna(row["Pump Current (mA)"]) and row["Pump Current (mA)"] > 0:
                expected = get_expected_power(row["Pump Current (mA)"])
                expected_powers.append(f"{row['Pump Current (mA)']} mA → {expected:.0f} mW expected")  # Units explicit

        if expected_powers:
            st.caption("**Current Entries:** " + " | ".join(expected_powers))


def get_expected_power(current):
    """Interpolate expected power based on pump current using SOP data from Supabase. Returns power in mW."""
    # Load SOP data from Supabase
    sop_df = load_dataframe(SOP_POWER_VS_PUMP_FILE, pd.DataFrame())
    
    # Check for both old and new column names (backward compatibility)
    power_col = None
    if not sop_df.empty and "Pump Current (mA)" in sop_df.columns:
        if "Expected Power (mW)" in sop_df.columns:
            power_col = "Expected Power (mW)"
        elif "Expected Power (W)" in sop_df.columns:
            power_col = "Expected Power (W)"
            # Convert W to mW for consistency
    
    # If no SOP data exists or required columns are missing, use default values
    if sop_df.empty or "Pump Current (mA)" not in sop_df.columns or power_col is None:
        # Default values as fallback (all in mW)
        currents = np.array([
            0, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 6500, 7000, 7500, 8000, 8500, 9000
        ])
        powers = np.array([
            0.0, 0.0, 200.0, 200.0, 900.0, 1400.0, 2000.0, 2300.0, 3200.0, 3800.0, 4400.0, 4800.0, 5700.0, 6300.0, 7000.0, 7500.0, 8000.0, 8200.0
        ])
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
        powers = filtered_df[power_col].astype(float).values
        
        # Convert W to mW if needed for consistency
        if power_col == "Expected Power (W)":
            powers = powers * 1000  # Convert W to mW
        
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
            # Use exponential fit (preferred for laser power curves, returns mW)
            fit_params = exponential_fit(currents, powers)
            
            # Apply the exponential model to get result
            result = fit_params["a"] * np.exp(fit_params["b"] * current_clipped) + fit_params["c"]
        except Exception:
            # Fallback to cubic spline or linear interpolation (all in mW)
            if len(currents) >= 4:
                try:
                    cs = CubicSpline(currents, powers, bc_type="natural")  # mW
                    result = cs(current_clipped)
                except Exception:
                    # Fallback to linear interpolation (mW)
                    result = np.interp(current_clipped, currents, powers)
            else:
                # Linear interpolation for few points (mW)
                result = np.interp(current_clipped, currents, powers)
    elif len(currents) >= 4:
        try:
            # Use cubic spline if exponential fit isn't possible but we have enough points (mW)
            cs = CubicSpline(currents, powers, bc_type="natural")
            result = cs(current_clipped)
        except Exception:
            # Fallback to linear interpolation (mW)
            result = np.interp(current_clipped, currents, powers)
    else:
        # Linear interpolation for few points (mW)
        result = np.interp(current_clipped, currents, powers)
    
    # Convert the result to a Python native type to ensure JSON serialization works
    if isinstance(result, np.ndarray):
        return result.tolist() if result.size > 1 else float(result)
    elif isinstance(result, np.generic):
        return result.item()  # Convert numpy scalar to Python scalar
    else:
        return result


def render_source_power_theory_and_procedure(theory_only=False, procedure_only=False):
    """Render the theory and/or procedure sections for source power measurement. All power values are in mW unless otherwise noted."""
    if not procedure_only:
        st.markdown(
            """
            ### Fiber Laser Source Power
            
            The fiber laser source power is a critical parameter that affects both imaging quality and overall system performance. Monitoring and understanding the source power helps to:
            
            - Ensure consistent imaging conditions
            - Detect potential system issues early
            - Optimize laser performance
            - Maintain system stability
            
            The source power is primarily controlled by the pump current, typically ranging from 2000 to 8000 mA. The relationship between pump current and output power should be approximately linear within the operating range.  
            **All power values below are in mW unless otherwise noted.**
        """
        )
    if not theory_only:
        st.markdown(
            """
            ### Procedure for Measuring Source Power
            
            1. **Startup Sequence**
               - Turn the key to "on" on the fiber laser controller box.
               - Turn on the pump temperature controller (I/O switch).
               - Start the Arroyo control software and set the temperature to 25°C.
               - Turn on the pump power controller.
               - Press the red button on the controller box to enable the seed laser.
               - **VERIFY** that the TEC fan is spinning before proceeding.
            
            2. **Power Measurement**
               - Position the power meter between F-Shutter and F-HWP2.
               - Open the shutter ("enable").
               - Engage the pump diode (press the "Output" button).
               - Increase the pump current in 250 mA steps.
               - Record the power at each current level.
            
            3. **Expected Power Levels**
               - ~200 mW at 2000 mA
               - ~2300 mW at 4000 mA
               - ~4800 mW at 6000 mA
               - ~7500 mW at 8000 mA
            
            4. **Pulse Width Control** (for reference)
               - Use the grating pair (F-G1 & F-G2) to adjust the pulse width.
               - Typical positions for shortest pulse:
                 * 6.625 @ 4000 mA
                 * 4.75 @ 6000 mA
                 * 2.5 @ 8000 mA
        """
        )
        st.warning(
            """
        **CRITICAL CHECKS:**
        - Always ensure the TEC fan is spinning before increasing the pump current.
        - Do not increase the pump current if the power is low at previous checkpoints.
        - Monitor temperature (should be ~25°C).
        """
        )


def render_source_power_visualization():
    """Render visualizations for source power measurements. All power values are in mW."""
    st.subheader("Source Power Analysis (Power in mW)")  # Units clarified

    # Load existing data
    source_power_df = load_dataframe(SOURCE_POWER_FILE, pd.DataFrame())

    if source_power_df.empty:
        st.info("Add measurements to see analysis.")
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
        st.info("No measurements found for the current study and wavelength.")
        return

    # Display metrics
    create_metric_row(
        [
            {
                "label": "Latest Power (mW)",  # Units explicit
                "value": f"{filtered_df['Measured Power (mW)'].iloc[-1]:.0f} mW",
            },
            {
                "label": "Pump Current (mA)",
                "value": f"{filtered_df['Pump Current (mA)'].iloc[-1]} mA",
            },
            {
                "label": "Power Ratio (Measured/Expected)",  # Units explicit
                "value": f"{filtered_df['Measured Power (mW)'].iloc[-1] / get_expected_power(filtered_df['Pump Current (mA)'].iloc[-1]):.2f}",
            },
        ]
    )

    # --- New: Time Series Plot ---
    st.subheader("Time Series: Source Power Over Time")
    if "Date" in filtered_df.columns and not filtered_df["Date"].isna().all():
        # Ensure Date is datetime
        if filtered_df["Date"].dtype == 'object':
            try:
                filtered_df["Date"] = pd.to_datetime(filtered_df["Date"])
            except Exception:
                pass
        # Sort by date
        ts_df = filtered_df.sort_values("Date")
        import matplotlib.dates as mdates
        def plot_time_series(fig, ax):
            scatter = ax.scatter(
                ts_df["Date"],
                ts_df["Measured Power (mW)"],
                c=ts_df["Pump Current (mA)"],
                cmap="viridis",
                s=60,
                alpha=0.8,
                label=None
            )
            ax.set_xlabel("Date/Time")
            ax.set_ylabel("Measured Power (mW)")
            ax.set_title("Measured Power Over Time (colored by Pump Current)")
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d\n%H:%M'))
            fig.autofmt_xdate()
            cbar = fig.colorbar(scatter, ax=ax, label="Pump Current (mA)")
            ax.grid(True, linestyle="--", alpha=0.5)
        ts_plot = create_plot(plot_time_series)
        st.pyplot(ts_plot)
        with st.popover("📈 Understanding This Time Series", use_container_width=True):
            st.markdown(
                """
                This plot shows the measured source power (in mW) over time, with each point colored by the pump current (in mA).
                
                **How to use:**
                - Track system stability and performance trends over time.
                - Identify any sudden drops or increases in power.
                - Observe how power at different pump currents changes with date/time.
                
                **Tip:** Hover or zoom in to see details for each measurement.
                """
            )
    else:
        st.info("No valid date/time data available for the time series plot.")

    # Create power vs current plot
    def plot_power_vs_current(fig, ax):
        # Get data
        x = filtered_df["Pump Current (mA)"].values
        y = filtered_df["Measured Power (mW)"].values  # mW

        # Plot data points
        ax.scatter(x, y, color="#4BA3C4", s=50, alpha=0.7, label="Measurements")

        # Load SOP data for expected power curve
        sop_df = load_dataframe(SOP_POWER_VS_PUMP_FILE, pd.DataFrame())
        
        # Check for column names (backward compatibility)
        power_col = None
        if not sop_df.empty and "Pump Current (mA)" in sop_df.columns:
            if "Expected Power (mW)" in sop_df.columns:
                power_col = "Expected Power (mW)"
            elif "Expected Power (W)" in sop_df.columns:
                power_col = "Expected Power (W)"
        
        if power_col is not None:
            # Get SOP data
            curr_sop = sop_df["Pump Current (mA)"].astype(float).values
            power_sop = sop_df[power_col].astype(float).values
            
            # Convert W to mW if needed for consistency
            if power_col == "Expected Power (W)":
                power_sop = power_sop * 1000  # Convert W to mW
            
            # Sort by current for plotting
            sort_indices = np.argsort(curr_sop)
            curr_sop = curr_sop[sort_indices]
            power_sop = power_sop[sort_indices]
            
            # Plot the SOP points
            ax.scatter(curr_sop, power_sop, color="#BF5701", s=60, marker='s', 
                      label="SOP Data Points (mW)")  # Units explicit
            
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
                    label=f"Exp Fit: {fit_params['a']:.3f}*e^({fit_params['b']:.5f}*x) + {fit_params['c']:.3f} (mW)"  # Units explicit
                )
                
                # Display formula and R²
                equation_text = f"Power (mW) = {fit_params['a']:.3f} × e^({fit_params['b']:.5f} × Current) + {fit_params['c']:.3f}"
                r_squared_text = f"R² = {fit_params['r_squared']:.4f}"
                ax.text(0.05, 0.95, equation_text + "\n" + r_squared_text,
                      transform=ax.transAxes, fontsize=9,
                      verticalalignment='top',
                      bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            else:
                # Just connect the dots if not enough points for fitting
                ax.plot(curr_sop, power_sop, color="#BF5701", linestyle="--", 
                      label="Expected Values (mW)")  # Units explicit
        else:
            # Fallback to hardcoded expected values if no SOP data (converted to mW)
            expected_x = [2000, 4000, 6000, 8000]
            expected_y = [200, 2300, 4800, 7500]  # mW
            ax.plot(
                expected_x,
                expected_y,
                color="#BF5701",
                linestyle="--",
                label="Expected Values (mW)",  # Units explicit
            )

        # Add labels and title
        ax.set_xlabel("Pump Current (mA)")
        ax.set_ylabel("Measured Power (mW)")  # Units explicit
        ax.set_title("Source Power vs. Pump Current (Power in mW)")  # Units explicit
        
        # Set reasonable axis limits
        ax.set_xlim(0, max(filtered_df["Pump Current (mA)"].max() * 1.1, 8500))
        ax.set_ylim(0, max(filtered_df["Measured Power (mW)"].max() * 1.1, 8000.0))  # mW

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
        This plot shows the relationship between pump current and measured power at the source (all power values in mW).
        
        **Key insights:**
        - The exponential curve shows the expected power values at different current levels.
        - The curve follows the form: Power = a × e^(b × Current) + c
        - Exponential behavior is expected due to the physics of laser gain media.
        - Deviations from expected values may indicate:
          * Alignment issues
          * Component degradation
          * Temperature control problems
        - Regular monitoring helps detect system changes over time.
        
        **Typical values:**
        - ~200 mW at 2000 mA
        - ~2300 mW at 4000 mA
        - ~4800 mW at 6000 mA
        - ~7500 mW at 8000 mA
        """
        )
