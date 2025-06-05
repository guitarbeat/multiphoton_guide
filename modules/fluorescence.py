"""
Fluorescence signal estimation module for the Multiphoton Microscopy Guide application.
Implements protocols for estimating absolute magnitudes of fluorescence signals.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import os
from pathlib import Path

from modules.data_utils import load_dataframe, save_dataframe, ensure_columns, safe_numeric_conversion, filter_dataframe, calculate_statistics, linear_regression
from modules.ui_components import create_header, create_info_box, create_warning_box, create_success_box, create_metric_row, create_data_editor, create_plot, create_tab_section, create_form_section, display_image, get_image_path
from modules.shared_utils import add_to_rig_log

# Constants
FLUORESCENCE_FILE = "fluorescence_measurements.csv"
RIG_LOG_FILE = "rig_log.csv"

def render_fluorescence_tab():
    """Render the fluorescence signal estimation tab content."""
    
    create_header("Estimating Absolute Magnitudes of Fluorescence Signals")

    
    # Create two columns for layout
    col1, col2 = st.columns([3, 2])
    
    with col1:
        render_fluorescence_theory_and_procedure()
    
    with col2:
        render_fluorescence_visualization()
        render_fluorescence_tips()

def render_fluorescence_theory_and_procedure():
    """Render the theory and procedure sections for fluorescence signal estimation using tabs."""
    
    tab1, tab2 = st.tabs(["📖 Introduction & Theory", "📋 Measurement Procedure"])
    
    with tab1:
        st.markdown("""
            Fluorescence signals are commonly expressed in arbitrary units or relative scales (like dF/F ratio), masking any degradation in signal magnitude. This can lead to vastly different signal strengths between laboratories following similar protocols, without realizing the discrepancy.

            Low signal magnitudes lead to noisier, less precise measurements. Without a method to evaluate quantitative signal magnitudes, laboratories may miss opportunities for improving primary data quality.

            We suggest reporting fluorescence signals in absolute physical units such as **detected photon counts per second**. This standardized method offers a consistent way to demonstrate signal levels, making it invaluable for:
            
            1. Longitudinal system performance monitoring
            2. Comparisons between different imaging systems
            3. Establishing quantitative benchmarks across laboratories
            
            While direct photon counting requires specialized electronics, we can use signal-noise statistics to accurately estimate detector photon sensitivity and translate detected signals into estimated photon counts.
        """)
        
        with st.expander("🔬 Photon Transfer Curve Theory"):
            st.markdown("""
                ### Understanding the Photon Transfer Curve (PTC)

                The Photon Transfer Curve (PTC) is a powerful tool for characterizing imaging detectors. It exploits the fundamental relationship between signal and noise in photon-limited imaging.

                **Key Principles:**

                1. **Photon Shot Noise**: The arrival of photons follows Poisson statistics, where the variance equals the mean
                2. **Signal-Variance Relationship**: For an ideal detector, the variance of the signal is proportional to the mean signal
                3. **Photon Sensitivity**: The slope of the signal-variance plot gives the conversion factor between digital units and photons

                **Mathematical Relationship:**

                For a detector with photon sensitivity K (digital units per photon):
                
                Variance = K × Mean
                
                Where:
                - Variance is the pixel-to-pixel or frame-to-frame variance
                - Mean is the average signal intensity
                - K is the photon sensitivity (digital units per photon)

                By measuring pairs of mean and variance values and plotting them, we can determine K from the slope of the linear fit. Once K is known, we can convert any measured signal from arbitrary units to absolute photon counts.
            """)
    
    with tab2:
        st.markdown("""
            ### Procedure for Estimating Absolute Fluorescence Signals

            1. **Prepare a fluorescent sample**
               - Use a sample with uniform fluorescence (e.g., fluorescent slide)
               - Alternatively, use a biological sample with regions of different intensities

            2. **Configure the microscope**
               - Set the camera gain to a fixed value
               - Ensure the detector is operating in its linear range
               - Disable any automatic gain control or signal processing

            3. **Acquire calibration data**
               - Capture multiple frames of the same field of view (approximately 500 consecutive frames)
               - Select regions with different intensity levels
               - For each region, measure the mean intensity and variance
               - Calculate the variance between consecutive frames to isolate quantum noise

            4. **Calculate photon sensitivity**
               - Plot variance vs. mean intensity (the Photon Transfer Curve)
               - Fit a linear regression to the data
               - The slope of this line is the photon sensitivity (K)
               - K represents digital units per photon

            5. **Convert signals to photon counts**
               - For any measured signal (S), the photon count (N) is:
               - N = S / K
               - This gives absolute photon counts, independent of detector settings
        """)
        
        st.warning("**CRITICAL:** Ensure the detector is operating in its linear range. Saturation will cause the variance to decrease at high intensities.")
        st.warning("**CRITICAL:** For accurate measurements, acquire multiple frames of the same field to separate temporal noise from spatial variations.")

def render_fluorescence_visualization():
    """Render visualizations for fluorescence signal estimation."""
    
    st.subheader("Photon Transfer Curve Example")
    
    # Create example PTC plot
    def plot_ptc_example(fig, ax):
        # Example data
        x = np.array([100, 200, 300, 400, 500, 600, 700, 800])
        y = np.array([25, 50, 75, 100, 125, 150, 175, 200])
        
        # Linear regression
        slope, intercept = 0.25, 0
        x_line = np.linspace(0, 900, 100)
        y_line = slope * x_line + intercept
        
        # Plot data points
        ax.scatter(x, y, color='#4BA3C4', s=80, alpha=0.7, label='Measurements')
        
        # Plot regression line
        ax.plot(x_line, y_line, color='#BF5701', linewidth=2, 
               label=f'Linear Fit (K = {slope:.2f})')
        
        # Add labels and title
        ax.set_xlabel('Mean Intensity (a.u.)')
        ax.set_ylabel('Variance')
        ax.set_title('Example Photon Transfer Curve')
        
        # Add grid and legend
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()
        
        # Add text annotation
        ax.text(600, 50, f"Photon Sensitivity (K) = {slope:.2f}\nZero Level = {intercept:.1f}", 
               bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.5'))
    
    # Display the plot
    ptc_plot = create_plot(plot_ptc_example)
    st.pyplot(ptc_plot)
    
    # Add explanation
    with st.popover("📊 Understanding This Plot", use_container_width=True):
        st.markdown("""
        The Photon Transfer Curve (PTC) plots variance against mean intensity:
        
        **Key features:**
        - The linear relationship confirms photon-limited detection
        - The slope (K) is the photon sensitivity in digital units per photon
        - The x-intercept represents the true zero-intensity level
        
        **Using the results:**
        - To convert any intensity value to photon counts: Photons = Intensity / K
        - For example, with K = 0.25, an intensity of 100 represents 400 photons
        - Higher K values mean more digital units per photon (more sensitive detection)
        """)
    
    # Add photon calculator
    with st.popover("🧮 Photon Count Calculator", use_container_width=True):
        st.markdown("### Convert Intensity to Photon Count")
        
        col1, col2 = st.columns(2)
        with col1:
            k_value = st.number_input("Photon Sensitivity (K):", 
                                     min_value=0.01, max_value=10.0, value=0.25, step=0.01)
        with col2:
            intensity = st.number_input("Intensity Value:", 
                                       min_value=0, max_value=10000, value=100, step=10)
        
        photon_count = intensity / k_value if k_value > 0 else 0
        
        st.metric("Estimated Photon Count", f"{photon_count:.1f} photons")
        
        st.markdown("""
        **Formula:** Photons = Intensity / K
        
        This calculator helps you convert arbitrary intensity units to absolute photon counts
        using the photon sensitivity (K) determined from your PTC analysis.
        """)

def render_fluorescence_tips():
    """Render tips and best practices for fluorescence signal estimation."""
    
    st.subheader("Tips & Best Practices")
    
    with st.expander("🔍 Data Collection", expanded=True):
        st.markdown("""
        ### Collecting Quality Data for PTC Analysis

        For accurate photon sensitivity estimation:

        1. **Collect sufficient frames**
           - Aim for at least 500 consecutive frames
           - Ensure the sample is stable (minimal bleaching or motion)
           - Extract frames before any processing (no motion correction or filtering)

        2. **Select diverse regions**
           - Include regions with different intensity levels
           - Cover the full dynamic range of your detector
           - Avoid saturated regions

        3. **Calculate variance correctly**
           - Use frame-to-frame differences to isolate quantum noise
           - For consecutive frames X and X', calculate:
             - Mean = [½X' + ½X]
             - Variance = ½(X' - X)²
           - This approach eliminates correlated noise sources
        """)
    
    with st.expander("⚠️ Common Issues"):
        st.markdown("""
        ### Troubleshooting PTC Analysis

        **Non-linear PTC:**
        - At low intensities: Check for detector offset or electronic noise
        - At high intensities: Check for detector saturation
        - Throughout range: Check for signal processing or gain adjustments

        **Excessive variance:**
        - Sample motion or drift
        - Laser power fluctuations
        - PMT gain instability
        - Biological activity (e.g., calcium transients)

        **Insufficient variance:**
        - Signal processing or filtering
        - Pixel binning
        - Detector non-linearity
        """)
    
    with st.expander("📝 Applications"):
        st.markdown("""
        ### Using Absolute Fluorescence Measurements

        **System monitoring:**
        - Track photon sensitivity over time
        - Detect PMT degradation or alignment issues
        - Compare performance before and after maintenance

        **Experimental design:**
        - Determine minimum detectable signal
        - Optimize imaging parameters for best signal-to-noise ratio
        - Calculate required integration time for desired precision

        **Data analysis:**
        - Convert dF/F to absolute photon flux
        - Estimate signal-to-noise ratio from first principles
        - Compare signals across different imaging sessions
        """)

# add_to_rig_log function moved to modules/shared_utils.py to eliminate duplication
