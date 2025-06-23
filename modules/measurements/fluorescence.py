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
            Fluorescence signals are commonly expressed in **arbitrary units** or relative scales such as **dF/F ratio**, which mask any degradation in signal magnitude over time. This practice can lead to vastly different signal strengths between laboratories following seemingly similar protocols, without realizing the discrepancy exists. Such variations compromise the **reproducibility** of quantitative measurements across different imaging systems and research groups.

            **Low signal magnitudes** inevitably lead to noisier, less precise measurements that limit the quality of scientific conclusions. Without a standardized method to evaluate quantitative signal magnitudes, laboratories may miss critical opportunities for improving their primary data quality through systematic optimization of imaging parameters and hardware performance.

            We strongly recommend reporting fluorescence signals in **absolute physical units** such as **detected photon counts per second**. This standardized approach offers a consistent framework to demonstrate signal levels across different systems, making it invaluable for **longitudinal system performance monitoring**, **inter-laboratory comparisons**, and **establishing quantitative benchmarks** for multiphoton microscopy applications.

            While direct photon counting requires specialized electronics not available on most systems, we can exploit the fundamental **signal-noise statistics** of photon detection to accurately estimate detector photon sensitivity. This approach enables translation of detected signals from arbitrary units into estimated **absolute photon counts**, providing the quantitative foundation necessary for rigorous scientific comparisons.
        """
        )

        with st.expander("🔬 Photon Transfer Curve Theory Details"):
            st.markdown(
                """
                The **Photon Transfer Curve (PTC)** represents a powerful characterization tool for imaging detectors that exploits the fundamental relationship between signal and noise in photon-limited imaging systems. This technique provides quantitative insight into detector performance and enables absolute calibration of fluorescence measurements.

                **Photon Shot Noise** follows **Poisson statistics**, where the variance of photon arrivals equals the mean number of photons detected. This fundamental relationship forms the theoretical basis for the PTC method. For an ideal detector operating in the photon-limited regime, the **signal-variance relationship** demonstrates that variance of the detected signal is directly proportional to the mean signal intensity.

                The **photon sensitivity** parameter K represents the conversion factor between digital units and actual photons detected. Mathematically, for a detector with photon sensitivity K (expressed in digital units per photon), the relationship becomes:

                **Variance = K × Mean + Offset**

                Where **Variance** represents the pixel-to-pixel or frame-to-frame variance, **Mean** indicates the average signal intensity, **K** is the photon sensitivity, and **Offset** accounts for electronic noise sources. By measuring pairs of mean and variance values across different intensity levels and plotting them, we can determine K from the **slope of the linear fit**.

                Once the photon sensitivity K is established through PTC analysis, any measured signal can be converted from arbitrary units to **absolute photon counts** using the simple relationship: **Photons = Signal / K**. This conversion provides the quantitative foundation necessary for rigorous scientific analysis and cross-system comparisons.
            """
            )

    with st.expander("📋 Measurement Procedure", expanded=True):
        st.markdown(
            """
            ### Systematic Protocol for Absolute Fluorescence Signal Estimation

            Begin by preparing a **fluorescent sample** that provides uniform fluorescence across the field of view. A fluorescent slide or coverslip with fluorescent beads works well for this purpose. Alternatively, biological samples with regions of different but stable intensities can be used, though uniform samples provide more reliable calibration data.

            **Configure the microscope** by setting the detector gain to a fixed value throughout the measurement process. Ensure the detector is operating within its **linear response range** and disable any automatic gain control, temporal averaging, or other signal processing features that might affect the noise characteristics of the measurements.

            **Acquire calibration data** by capturing approximately **500 consecutive frames** of the same field of view to provide sufficient statistical power for variance calculations. Select multiple **regions of interest** with different intensity levels to cover the dynamic range of your detector. For each region, measure both the **mean intensity** and **variance** across the frame sequence.

            **Calculate photon sensitivity** using the frame-to-frame difference method to isolate quantum noise from other sources. For consecutive frames X and X', compute the mean as ½(X + X') and variance as ½(X' - X)². This approach effectively eliminates correlated noise sources while preserving the photon shot noise characteristics essential for accurate PTC analysis.

            **Plot the Photon Transfer Curve** by graphing variance versus mean intensity for all measured regions. **Fit a linear regression** to the data points, ensuring the relationship remains linear across your measurement range. The **slope of this line** represents the photon sensitivity K in digital units per photon, while the y-intercept indicates the electronic noise floor of your detector system.

            **Convert signals to photon counts** using the determined photon sensitivity. For any measured signal intensity S, the corresponding **photon count N** is calculated as N = S / K. This provides absolute photon counts that are independent of detector settings and enable quantitative comparisons across different imaging sessions and systems.
        """
        )

        st.warning(
            "**CRITICAL:** Ensure the detector operates in its **linear range** throughout the measurement. Saturation causes variance to decrease at high intensities, invalidating the PTC analysis."
        )
        st.warning(
            "**CRITICAL:** Acquire **multiple frames** of identical fields to separate temporal quantum noise from spatial variations in fluorescence intensity."
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
            The **Photon Transfer Curve** demonstrates the fundamental relationship between signal intensity and detection noise in photon-limited imaging systems. The **linear relationship** confirms that your detector is operating in the photon-limited regime where quantum shot noise dominates.

            **Key parameters** derived from PTC analysis include the **photon sensitivity K** (slope), which quantifies how many digital units correspond to each detected photon, and the **electronic noise floor** (y-intercept), which represents detector noise independent of signal level.

            **Practical applications** of PTC analysis enable conversion of arbitrary intensity units to absolute photon counts using the relationship **Photons = Intensity / K**. For example, with K = 0.25, a measured intensity of 100 digital units corresponds to **400 detected photons**.

            **System monitoring** using PTC analysis allows detection of performance changes over time. **Decreasing photon sensitivity** may indicate PMT degradation, while **increasing electronic noise** suggests detector or amplifier issues requiring attention.
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
                help="Digital units per photon from PTC analysis"
            )
        with col2:
            intensity = st.number_input(
                "Intensity Value:", 
                min_value=0, 
                max_value=10000, 
                value=100, 
                step=10,
                help="Measured signal in digital units"
            )

        photon_count = intensity / k_value if k_value > 0 else 0
        photon_rate = photon_count * 1000  # Assuming 1ms integration time

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Estimated Photon Count", f"{photon_count:.1f} photons")
        with col2:
            st.metric("Photon Rate (1ms)", f"{photon_rate:.0f} photons/s")

        st.markdown(
            """
            **Formula:** Photons = Intensity / K
            
            This calculator converts arbitrary intensity units to **absolute photon counts** using the photon sensitivity determined from PTC analysis. The photon rate assumes a 1 millisecond integration time and can be scaled for different exposure durations.
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
