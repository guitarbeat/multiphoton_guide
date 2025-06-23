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


def render_pulse_width_theory_and_procedure():
    """Render the theory and procedure sections for pulse width optimization using expandable sections."""

    with st.expander("📖 Introduction & Theory", expanded=True):
        st.markdown(
            """
            Nearly all multiphoton microscopy uses **modelocked ultrafast lasers** with pulse durations on the order of 100 femtoseconds (100 × 10⁻¹⁵ s). Due to the **nonlinearity of multiphoton excitation**, peak intensity matters significantly more than average power for efficient excitation. The temporal compression of energy into ultrashort pulses creates the extremely high instantaneous intensities required for multiphoton processes.

            The **enhancement factor** for multiphoton excitation using pulsed lasers versus continuous wave (CW) lasers, with the same time-averaged power, follows a fundamental relationship:

            **g⁽ⁿ⁾ = g⁽ⁿ⁾ₚ / (τfᵣ)ⁿ⁻¹**

            Where **g⁽ⁿ⁾** represents the enhancement factor, **τ** is the pulse width, **fᵣ** is the repetition rate, and **n** is the number of photons in the absorption process. For **two-photon imaging** with a standard Ti-sapphire laser operating at 80 MHz with 150 fs pulses, this enhancement over CW lasers reaches approximately **50,000-fold** and demonstrates strong dependence on pulse width.

            As pulses travel through **optical components**, they experience **dispersion** which temporally broadens or "stretches" the pulse, dramatically reducing excitation efficiency. This broadening occurs because different wavelength components of the broadband pulse travel at different velocities through dispersive materials. The effect can be counteracted through **dispersion compensation**, which is critical for maintaining optimal performance in multiphoton systems.
        """
        )

        with st.expander("🔬 Group Delay Dispersion Details"):
            st.markdown(
                """
                **Group Delay Dispersion (GDD)** quantifies how different wavelength components of a pulse are delayed relative to each other as they travel through optical materials. Understanding GDD is essential for optimizing pulse width at the sample plane.

                **Positive GDD** occurs when blue components travel slower than red components, causing temporal stretching of the pulse. Most **optical materials** including glass, water, and biological tissues introduce positive GDD. Conversely, **negative GDD** causes red components to travel slower than blue components.

                The **optimal GDD setting** represents the precise balance where negative GDD from the compensation unit exactly cancels the positive GDD accumulated through the microscope's optical path. This results in the **shortest possible pulse duration** at the sample, maximizing multiphoton excitation efficiency.

                **Dispersion accumulation** increases proportionally with the amount of material the pulse traverses. Microscopes with elaborate optical systems containing numerous glass elements require more extensive dispersion compensation. The **wavelength dependence** of dispersion means that optimal GDD values must be determined independently for each excitation wavelength used in experiments.
            """
            )

    with st.expander("📋 Optimization Procedure", expanded=True):
        st.markdown(
            """
            ### Systematic Approach to Pulse Width Optimization

            Begin by preparing a **fluorescent sample** such as a thin, bright fluorescent slide or coverslip with fluorescent beads. The sample should provide uniform, bright fluorescence to enable accurate intensity measurements. Place the sample under the objective and establish proper focus using standard microscopy techniques.

            Configure the microscope by setting the **wavelength** to your desired excitation value and adjusting **laser power** to a moderate level that avoids saturation while providing sufficient signal. Enable **live scanning mode** to allow real-time monitoring of signal changes during optimization.

            **GDD optimization** involves systematically adjusting the dispersion compensation while monitoring signal intensity. View the **live image histogram** and adjust GDD values in incremental steps, typically **±500 fs²** initially. For each GDD setting, record both the **mean pixel intensity** and **maximum pixel values** from the histogram. The goal is to identify the GDD value that maximizes fluorescence signal intensity.

            **Verification** requires plotting pixel intensity versus GDD value to confirm that the optimal setting corresponds to the peak of the response curve. This **optimal GDD value** should be saved for future reference at this specific wavelength, as optimization is wavelength-dependent and must be repeated for each excitation wavelength commonly used.
        """
        )

        st.warning(
            "**CRITICAL:** Optimal GDD values are **wavelength-dependent**. The procedure must be repeated for each wavelength used in your experiments."
        )
        st.warning(
            "**CRITICAL:** Maintain **constant laser power** throughout the optimization process to ensure accurate comparisons."
        )

        # Display the pixel histogram image
        st.image(
            get_image_path("pixel_histogram.png"),
            caption="Pixel intensity distribution during live scanning. The histogram shape and peak values are used to optimize laser pulse width through GDD adjustment.",
        )


def render_pulse_width_visualization():
    """Render visualizations for pulse width optimization."""

    st.subheader("GDD Optimization Example")

    # Create example GDD optimization plot
    def plot_gdd_optimization_example(fig, ax):
        # Example data based on typical optimization curves
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
        ax.set_title(f"Example GDD Optimization at {st.session_state.get('wavelength', 920)} nm")

        # Add grid and legend
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.legend()

    # Display the plot
    gdd_plot = create_plot(plot_gdd_optimization_example)
    st.pyplot(gdd_plot)

    # Enhanced explanation based on Nature article insights
    with st.popover("📊 Understanding the Optimization Curve", use_container_width=True):
        st.markdown(
            """
            This **GDD optimization curve** demonstrates how fluorescence signal intensity varies with dispersion compensation settings. The **peak intensity** corresponds to minimal pulse width at the sample plane, where multiphoton excitation efficiency is maximized.

            **Key characteristics** of the optimization curve include the **peak position** representing optimal GDD compensation, the **curve width** indicating system sensitivity to dispersion changes, and the **maximum intensity** reflecting the quality of pulse compression achieved.

            **Typical GDD values** range from **-5000 to +5000 fs²** depending on the microscope's optical path complexity. Systems with more glass elements generally require **larger negative GDD** values for optimal compensation. The **sharpness of the peak** indicates how precisely the GDD must be set for optimal performance.

            **Wavelength dependence** means that each excitation wavelength requires its own optimization curve. **Shorter wavelengths** typically require less negative GDD compensation due to reduced material dispersion, while **longer wavelengths** may need more extensive correction.
        """
        )


def render_pulse_width_quick_reference():
    """Render quick reference content for sidebar documentation."""
    return {
        "title": "Pulse Width Optimization Quick Reference",
        "content": """
        **Essential Parameters:**
        - **Pulse Duration**: ~100 fs for Ti:sapphire lasers
        - **Enhancement Factor**: ~50,000× over CW at same average power
        - **Typical GDD Range**: -5000 to +5000 fs²
        - **Optimization Step Size**: ±500 fs² initially, ±250 fs² for fine tuning

        **Key Relationships:**
        - **Shorter pulses** → Higher peak intensity → Better multiphoton efficiency
        - **More glass elements** → More positive dispersion → Need more negative GDD
        - **Longer wavelengths** → Greater material dispersion → More compensation needed

        **Critical Considerations:**
        - Optimization is **wavelength-dependent**
        - Maintain **constant laser power** during optimization
        - Use **uniform fluorescent samples** for accurate measurements
        - Record optimal values for each wavelength/objective combination

        **Common Issues:**
        - **No signal change**: Check dispersion unit, laser mode-locking, sample focus
        - **Signal decreases everywhere**: May be near optimal, try smaller steps
        - **Optimal at range limits**: May need additional dispersion compensation
        """
    }
