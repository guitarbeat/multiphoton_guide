"""
Pulse width optimization module for the Multiphoton Microscopy Guide application.
Implements protocols for optimizing pulse width through GDD adjustment.
"""

import numpy as np
import streamlit as st

from modules.core.shared_utils import create_two_column_layout
from modules.ui.components import create_header, create_plot, get_image_path


def render_pulse_width_tab():
    """Render the pulse width optimization tab content."""

    create_header("Pulse Width Control and Optimization")

    # Render content in a single column layout
    render_pulse_width_theory_and_procedure()
    render_pulse_width_visualization()
    render_pulse_width_tips()


def render_pulse_width_theory_and_procedure():
    """Render the theory and procedure sections for pulse width optimization using expandable sections."""

    with st.expander("📖 Introduction & Theory", expanded=True):
        st.markdown(
            """
            Nearly all multiphoton microscopy uses modelocked ultrafast lasers with pulse durations on the order of 100 femtoseconds (100 × 10⁻¹⁵ s). Due to the nonlinearity of multiphoton excitation, peak intensity matters more than average power for efficient excitation.

            The efficiency of multiphoton excitation using pulsed lasers versus continuous wave (CW) lasers, with the same time-averaged power, is given by:

            g⁽ⁿ⁾ = g⁽ⁿ⁾ₚ / (τfᵣ)ⁿ⁻¹

            Where:
            - g⁽ⁿ⁾ is the enhancement factor
            - τ is the pulse width
            - fᵣ is the repetition rate
            - n is number of photons in the absorption process

            For two-photon imaging with a standard Ti-sapphire laser (80 MHz, 150 fs pulses), this enhancement over CW lasers is ~50,000 and is strongly dependent on pulse width.

            As pulses travel through optical components, they experience dispersion which can temporally broaden or "stretch" the pulse, reducing excitation efficiency. This broadening can be counteracted with dispersion compensation.
        """
        )

        with st.expander("🔬 Group Delay Dispersion Details"):
            st.markdown(
                """
                ### Understanding Group Delay Dispersion (GDD)

                Group Delay Dispersion (GDD) is a measure of how different wavelength components of a pulse are delayed relative to each other as they travel through optical materials.

                - **Positive GDD**: Blue components travel slower than red components, stretching the pulse
                - **Negative GDD**: Red components travel slower than blue components

                Most optical materials (glass, water) introduce positive GDD. To compensate, we introduce negative GDD using specialized optics.

                The optimal GDD setting is where the negative GDD from the compensation unit exactly balances the positive GDD from the microscope's optical path, resulting in the shortest possible pulse at the sample.

                For a given material, the more material the pulse propagates through, the greater the temporal broadening. Microscopes with elaborate optical systems have more glass elements, resulting in more dispersion that needs to be compensated.
            """
            )

    with st.expander("📋 Optimization Procedure", expanded=True):
        st.markdown(
            """
            ### Step-by-Step Procedure for Optimizing Pulse Width

            1. **Prepare a fluorescent sample**
               - Use a thin, bright fluorescent sample (e.g., fluorescent slide)
               - Place the sample under the objective and focus

            2. **Configure the microscope**
               - Set the wavelength to the desired value
               - Set laser power to a moderate level (avoid saturation)
               - Enable live scanning mode

            3. **Optimize GDD**
               - View the live image histogram
               - Adjust the GDD value in steps (typically ±500 fs²)
               - For each GDD value, record the mean and maximum pixel values
               - Find the GDD value that maximizes the signal intensity

            4. **Verify optimization**
               - Plot pixel intensity vs. GDD value
               - The optimal GDD value should be at the peak of the curve
               - Save this value for future reference at this wavelength
        """
        )

        st.warning(
            "**CRITICAL:** Optimal GDD values are wavelength-dependent. Repeat this procedure for each wavelength you commonly use."
        )
        st.warning(
            "**CRITICAL:** Keep the laser power constant throughout the optimization process."
        )

        # Display only the pixel histogram image which we know exists
        st.image(
            get_image_path("pixel_histogram.png"),
            caption="The pixel intensity value distribution is shown for one image frame while live scanning. The spread of this distribution is used to optimize laser pulse width.",
        )


def render_pulse_width_visualization():
    """Render visualizations for pulse width optimization."""

    st.subheader("GDD Optimization Example")

    # Create example GDD optimization plot
    def plot_gdd_optimization_example(fig, ax):
        # Example data
        x = np.array([-4000, -2000, 0, 2000, 4000, 6000, 8000, 10000, 12000, 14000])
        y1 = np.array([350, 420, 500, 600, 850, 1200, 1400, 1800, 2050, 1450])

        # Plot data points
        ax.plot(
            x,
            y1,
            "o-",
            color="#4BA3C4",
            linewidth=2,
            markersize=8,
            label="Mean Pixel Value",
        )

        # Mark optimal GDD
        optimal_gdd = 12000
        ax.axvline(
            x=optimal_gdd,
            color="#BF5701",
            linestyle="--",
            alpha=0.7,
            label=f"Optimal GDD: {optimal_gdd} fs²",
        )

        # Add labels and title
        ax.set_xlabel("GDD Value (fs²)")
        ax.set_ylabel("Pixel Intensity")
        ax.set_title(f"Example GDD Optimization at {st.session_state.wavelength} nm")

        # Add grid and legend
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.legend()

    # Display the plot
    gdd_plot = create_plot(plot_gdd_optimization_example)
    st.pyplot(gdd_plot)

    # Add explanation
    with st.popover("📊 Understanding This Plot", use_container_width=True):
        st.markdown(
            """
        This plot shows how pixel intensity varies with different GDD values.
        
        **Key insights:**
        - The peak of the curve represents the optimal GDD value
        - At this value, the pulse is shortest at the sample, maximizing two-photon excitation
        - The width of the curve indicates how sensitive your system is to GDD changes
        - Optimal GDD values are wavelength-dependent
        
        **Typical values:**
        - Optimal GDD values typically range from -5000 to +5000 fs²
        - The exact value depends on your microscope's optical path
        - More complex optical paths generally require more negative GDD compensation
        """
        )


def render_pulse_width_tips():
    """Render tips and best practices for pulse width optimization."""

    st.subheader("Tips & Best Practices")

    with st.expander("🔍 Histogram Analysis", expanded=True):
        st.markdown(
            """
        ### Using the Pixel Histogram

        The pixel intensity histogram is a powerful tool for optimizing pulse width:

        1. Set the vertical scale to logarithmic to see low pixel counts
        2. Adjust the x-axis to show the full range of possible pixel values
        3. Set laser power so pixel values occupy ~25% of the full intensity range
        4. Record the histogram shape, mean, and maximum values for each GDD setting
        5. Look for the GDD value that gives the highest mean and maximum values
        """
        )

        st.image(
            get_image_path("pixel_histogram.png"),
            caption="Example pixel histogram showing intensity distribution during live scanning",
        )

    with st.expander("⚠️ Common Issues"):
        st.markdown(
            """
        ### Troubleshooting Pulse Width Optimization

        **If signal doesn't change with GDD adjustment:**
        - Ensure your dispersion compensation unit is working properly
        - Check that the laser is mode-locked
        - Verify that the sample is fluorescent and in focus

        **If signal decreases at all GDD values:**
        - Your starting point may be near optimal
        - Try smaller GDD adjustment steps (±250 fs²)
        - Check for laser power fluctuations

        **If optimal GDD is at the extreme of your adjustment range:**
        - Your system may have more dispersion than your compensation unit can handle
        - Consider adding additional dispersion compensation
        - For very short pulses (<80 fs), higher-order dispersion may be significant
        """
        )

    with st.expander("📝 Record Keeping"):
        st.markdown(
            """
        ### Maintaining Records

        For each wavelength and objective combination:
        1. Record the optimal GDD value
        2. Note the date of optimization
        3. Document any changes to the optical path
        4. Re-optimize after any significant system modifications
        5. Periodically verify optimization (monthly recommended)

        This information should be recorded in your system's rig log for future reference.
        """
        )


# add_to_rig_log function moved to modules/shared_utils.py to eliminate duplication
