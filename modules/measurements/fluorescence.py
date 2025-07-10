"""
Fluorescence signal estimation module for the Multiphoton Microscopy Guide application.
Implements protocols for estimating absolute magnitudes of fluorescence signals.
"""

import numpy as np
import streamlit as st

from modules.core.shared_utils import create_two_column_layout
from modules.ui.components import create_header, create_plot


def render_fluorescence_tab():
    """Render the fluorescence signal estimation tab content."""

    create_header("Estimating Absolute Magnitudes of Fluorescence Signals")

    # Render content in a single column layout
    render_fluorescence_theory_and_procedure()
    render_fluorescence_visualization()


def render_fluorescence_theory_and_procedure():
    """Render the theory and procedure sections for fluorescence signal estimation using expandable sections."""

    with st.expander("📖 Introduction & Theory", expanded=True):
        st.markdown(
            """
            Fluorescence signals are often reported in **arbitrary units** or as a **dF/F ratio**, which can hide signal degradation over time. This practice can result in large differences in signal strength between labs using similar protocols, often without realizing it. Such variation undermines the **reproducibility** of quantitative measurements across imaging systems and research groups.

            **Low signal magnitudes** lead to noisier, less precise measurements and limit the quality of scientific conclusions. Without a standardized way to evaluate signal magnitude, labs may miss key opportunities to improve data quality by optimizing imaging parameters and hardware.

            We strongly recommend reporting fluorescence signals in **absolute physical units** such as **detected photon counts per second**. This standardization provides a consistent framework for comparing signal levels across systems, supporting **long-term system monitoring**, **inter-lab comparisons**, and **quantitative benchmarks** for multiphoton microscopy.

            Direct photon counting requires specialized electronics, but you can use the fundamental **signal-noise statistics** of photon detection to estimate detector photon sensitivity. This lets you convert detected signals from arbitrary units to estimated **absolute photon counts**, providing a solid foundation for rigorous scientific comparison.
        """
        )

        with st.expander("🔬 Photon Transfer Curve Theory Details"):
            st.markdown(
                """
                The **Photon Transfer Curve (PTC)** is a powerful tool for characterizing imaging detectors. It uses the fundamental relationship between signal and noise in photon-limited systems to provide quantitative insight into detector performance and enables absolute calibration of fluorescence measurements.

                **Photon shot noise** follows **Poisson statistics**: the variance of photon arrivals equals the mean number of photons detected. For an ideal detector in the photon-limited regime, the **variance of the detected signal is directly proportional to the mean signal intensity**.

                The **photon sensitivity** parameter K is the conversion factor between digital units and actual photons detected. For a detector with photon sensitivity K (in digital units per photon):

                **Variance = K × Mean + Offset**

                Here, **Variance** is the pixel-to-pixel or frame-to-frame variance, **Mean** is the average signal intensity, **K** is the photon sensitivity, and **Offset** accounts for electronic noise. By measuring mean and variance pairs at different intensities and plotting them, you can determine K from the **slope of the linear fit**.

                Once you know K from PTC analysis, you can convert any measured signal from arbitrary units to **absolute photon counts**: **Photons = Signal / K**. This conversion is the basis for rigorous scientific analysis and cross-system comparisons.
            """
            )

    with st.expander("📋 Measurement Procedure", expanded=True):
        st.markdown(
            """
            ### Protocol for Absolute Fluorescence Signal Estimation

            1. **Prepare a fluorescent sample** that provides uniform fluorescence across the field of view. A fluorescent slide or coverslip with beads is ideal. Biological samples with stable regions can work, but uniform samples are best for calibration.

            2. **Set up the microscope.** Fix the detector gain for all measurements. Make sure the detector operates in its **linear range**. Turn off any automatic gain, temporal averaging, or signal processing that could affect noise.

            3. **Acquire calibration data.** Capture about **500 consecutive frames** of the same field. Select several **regions of interest** at different intensities to cover your detector’s dynamic range. For each region, measure the **mean intensity** and **variance** across frames.

            4. **Calculate photon sensitivity.** Use the frame-to-frame difference method to isolate quantum noise. For consecutive frames X and X', compute the mean as ½(X + X') and variance as ½(X' - X)². This removes correlated noise and preserves photon shot noise for accurate PTC analysis.

            5. **Plot the Photon Transfer Curve.** Graph variance versus mean intensity for all regions. **Fit a linear regression** to the data. The **slope** is the photon sensitivity K (digital units per photon); the **y-intercept** is the electronic noise floor.

            6. **Convert signals to photon counts.** For any measured signal S, calculate photon count N as N = S / K. This gives absolute photon counts, independent of detector settings, for quantitative comparison across sessions and systems.
        """
        )

        st.warning(
            "**CRITICAL:** Keep the detector in its **linear range** for all measurements. Saturation causes variance to decrease at high intensities and invalidates PTC analysis."
        )
        st.warning(
            "**CRITICAL:** Acquire **multiple frames** of the same field to separate quantum noise from spatial variations in intensity."
        )


def render_fluorescence_visualization():
    """Render visualizations for fluorescence signal estimation."""

    st.subheader("Photon Transfer Curve Example")

    # Create example PTC plot
    def plot_ptc_example(fig, ax):
        # Example data based on realistic PTC measurements
        x = np.array([100, 200, 300, 400, 500, 600, 700, 800])
        y = np.array([25, 50, 75, 100, 125, 150, 175, 200])

        # Linear regression parameters
        slope, intercept = 0.25, 0
        x_line = np.linspace(0, 900, 100)
        y_line = slope * x_line + intercept

        # Plot data points
        ax.scatter(x, y, color="#4BA3C4", s=80, alpha=0.7, label="Measurements")

        # Plot regression line
        ax.plot(
            x_line,
            y_line,
            color="#BF5701",
            linewidth=2,
            label=f"Linear Fit (K = {slope:.2f})",
        )

        # Add labels and title
        ax.set_xlabel("Mean Intensity (Digital Units)")
        ax.set_ylabel("Variance (Digital Units²)")
        ax.set_title("Example Photon Transfer Curve Analysis")

        # Add grid and legend
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.legend()

        # Add annotation with key parameters
        ax.text(
            600,
            50,
            f"Photon Sensitivity (K) = {slope:.2f}\nElectronic Noise = {intercept:.1f}",
            bbox=dict(facecolor="white", alpha=0.7, boxstyle="round,pad=0.5"),
        )

    # Display the plot
    ptc_plot = create_plot(plot_ptc_example)
    st.pyplot(ptc_plot)

    # Enhanced explanation based on Nature article insights
    with st.popover("📊 Understanding the Photon Transfer Curve", use_container_width=True):
        st.markdown(
            """
            The **Photon Transfer Curve** shows the fundamental relationship between signal intensity and detection noise in photon-limited imaging. A **linear relationship** confirms your detector is operating in the photon-limited regime, where quantum shot noise dominates.

            **Key parameters:**
            - **Photon sensitivity K (slope):** How many digital units correspond to each detected photon.
            - **Electronic noise floor (y-intercept):** Detector noise independent of signal level.

            **Use PTC analysis to convert intensity units to absolute photon counts:**
            - **Photons = Intensity / K**
            - Example: With K = 0.25, an intensity of 100 digital units means **400 detected photons**.

            **Monitor your system:**
            - **Decreasing photon sensitivity** may mean PMT degradation.
            - **Increasing electronic noise** may signal detector or amplifier issues.
            """
        )

    # Enhanced photon calculator with additional features
    with st.popover("🧮 Photon Count Calculator", use_container_width=True):
        st.markdown("### Convert Intensity to Photon Count")

        col1, col2 = st.columns(2)
        with col1:
            k_value = st.number_input(
                "Photon Sensitivity (K):",
                min_value=0.01,
                max_value=10.0,
                value=0.25,
                step=0.01,
                help="Digital units per photon from PTC analysis."
            )
        with col2:
            intensity = st.number_input(
                "Intensity Value:", 
                min_value=0, 
                max_value=10000, 
                value=100, 
                step=10,
                help="Measured signal in digital units."
            )

        photon_count = intensity / k_value if k_value > 0 else 0
        photon_rate = photon_count * 1000  # Assumes 1 ms integration time

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Estimated Photon Count", f"{photon_count:.1f} photons")
        with col2:
            st.metric("Photon Rate (1 ms)", f"{photon_rate:.0f} photons/s")

        st.markdown(
            """
            **Formula:** Photons = Intensity / K
            
            This calculator converts intensity units to **absolute photon counts** using the photon sensitivity from PTC analysis. The photon rate assumes a 1 ms integration time and can be scaled for other exposure durations.
            """
        )


def render_fluorescence_quick_reference():
    """Render quick reference content for sidebar documentation."""
    return {
        "title": "Fluorescence Signal Estimation Quick Reference",
        "content": """
        **Key Relationships:**
        - **Variance = K × Mean** (for photon-limited detection)
        - **Photons = Intensity / K** (conversion formula)
        - **K = Slope of PTC** (photon sensitivity in digital units/photon)

        **Essential Requirements:**
        - **500+ frames** for sufficient statistical power
        - **Multiple intensity levels** covering detector dynamic range
        - **Fixed gain settings** throughout measurement
        - **Linear detector response** (avoid saturation)

        **Critical Analysis Steps:**
        1. Use **frame-to-frame differences** to isolate quantum noise
        2. Calculate: Mean = ½(X + X'), Variance = ½(X' - X)²
        3. Plot **variance vs. mean intensity**
        4. Fit **linear regression** to determine slope K
        5. Convert signals using **Photons = Signal / K**

        **Applications:**
        - **System monitoring**: Track PMT sensitivity over time
        - **Optimization**: Determine optimal imaging parameters
        - **Standardization**: Enable cross-system comparisons
        - **Quality control**: Establish quantitative benchmarks

        **Troubleshooting:**
        - **Non-linear PTC**: Check for saturation or gain changes
        - **High variance**: Look for sample motion or laser instability
        - **Low variance**: Verify no signal processing is applied
        """
    }

# add_to_rig_log function moved to modules/shared_utils.py to eliminate duplication
