"""
Combined pulse width and fluorescence signal estimation module for the Multiphoton Microscopy Guide application.
Implements protocols for optimizing pulse width through GDD adjustment and estimating absolute magnitudes of fluorescence signals.
"""

import os
from pathlib import Path

import numpy as np
import streamlit as st
from streamlit_pdf_viewer import pdf_viewer

from modules.core.shared_utils import create_two_column_layout
from modules.measurements.fluorescence import (
    render_fluorescence_theory_and_procedure,
    render_fluorescence_visualization,
    render_fluorescence_quick_reference,
)
from modules.measurements.pulse_width import (
    render_pulse_width_theory_and_procedure,
    render_pulse_width_visualization,
    render_pulse_width_quick_reference,
)
from modules.ui.components import create_header, create_plot, get_image_path


def render_reference_content():
    """Render the reference PDF content with enhanced citation and navigation."""

    # Path to the PDF file - use absolute path
    base_dir = Path(__file__).parent.parent.parent  # Go up to project root
    pdf_path = str(base_dir / "assets" / "s41596-024-01120-w.pdf")

    # Check if the PDF exists
    if not os.path.exists(pdf_path):
        st.error(
            f"Reference PDF not found at {pdf_path}. Please ensure the file is in the correct location."
        )
        return

    # Enhanced citation information
    with st.expander("📚 Citation Information", expanded=True):
        st.markdown(
            """
        **Full Citation:**
        
        Lees, R.M., Bianco, I.H., Campbell, R.A.A. et al. **Standardized measurements for monitoring and comparing multiphoton microscope systems**. *Nat Protoc* (2025). https://doi.org/10.1038/s41596-024-01120-w
        
        **Key Contributions:**
        
        This **Nature Protocols** paper provides the first comprehensive standardization framework for multiphoton microscopy systems. The protocols address critical **hardware characterization** needs that have long hindered reproducibility across laboratories. Each procedure is designed to take **1-2 hours** to complete without expensive specialized equipment.
        
        **Scope and Impact:**
        
        The standardization covers **laser power measurement**, **pulse width optimization**, **field of view calibration**, **spatial resolution assessment**, and **photomultiplier tube performance monitoring**. These measurements enable laboratories to demonstrate consistent performance, identify degradation over time, and facilitate meaningful comparisons between different imaging systems and experimental results.
        """
        )

    # Enhanced table of contents with key insights
    with st.expander("📑 Protocol Sections & Key Insights"):
        st.markdown(
            """
        ### Protocol Sections
        
        **1. Laser Power at the Sample**
        - **Critical for**: Avoiding photodamage while maintaining signal quality
        - **Key insight**: Power variations significantly affect multiphoton efficiency
        - **Outcome**: Standardized power measurement and monitoring protocols
        
        **2. Field of View Size and Homogeneity** 
        - **Critical for**: Accurate spatial measurements and uniform illumination
        - **Key insight**: FOV distortions affect quantitative analysis accuracy
        - **Outcome**: Calibration methods for spatial dimensions and uniformity
        
        **3. Spatial Resolution Assessment**
        - **Critical for**: Understanding imaging capabilities and limitations
        - **Key insight**: Resolution depends on multiple optical and sample factors
        - **Outcome**: Standardized resolution measurement using point spread functions
        
        **4. Pulse Width Control and Optimization**
        - **Critical for**: Maximizing multiphoton excitation efficiency
        - **Key insight**: Dispersion compensation is wavelength-dependent and critical
        - **Outcome**: Systematic GDD optimization for each excitation wavelength
        
        **5. Photomultiplier Tube Performance**
        - **Critical for**: Maintaining consistent detection sensitivity
        - **Key insight**: PMT degradation significantly impacts data quality
        - **Outcome**: Quantitative monitoring methods for detector performance
        
        **6. Absolute Fluorescence Signal Estimation**
        - **Critical for**: Converting arbitrary units to meaningful physical quantities
        - **Key insight**: Photon Transfer Curves enable absolute calibration
        - **Outcome**: Methods for reporting signals in photon counts per second
        """
        )

    # Enhanced notes and reference features
    with st.expander("📝 Research Notes & Quick Reference"):
        # Quick reference for current protocols
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Pulse Width Optimization")
            pulse_ref = render_pulse_width_quick_reference()
            with st.container():
                st.markdown(pulse_ref["content"])
        
        with col2:
            st.markdown("### Fluorescence Signal Estimation")
            fluor_ref = render_fluorescence_quick_reference()
            with st.container():
                st.markdown(fluor_ref["content"])

        st.markdown("---")
        
        # Personal notes section
        if "reference_notes" not in st.session_state:
            st.session_state.reference_notes = ""

        st.text_area(
            "Your Research Notes:",
            value=st.session_state.reference_notes,
            height=150,
            key="notes_input",
            help="Add your own notes, observations, and protocol modifications here"
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Save Notes", use_container_width=True):
                st.session_state.reference_notes = st.session_state.notes_input
                st.success("Notes saved!")
        with col2:
            # Add a download button for the PDF
            with open(pdf_path, "rb") as file:
                st.download_button(
                    label="📥 Download Protocol PDF",
                    data=file,
                    file_name="multiphoton_microscope_standardization_protocol.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

    # Display the PDF with full width
    st.markdown("## Complete Protocol Document")
    st.markdown(
        """
        The full **Nature Protocols** paper provides detailed methodological guidance, troubleshooting advice, 
        and expected results for each standardization protocol. Use this reference alongside the interactive 
        tools above for comprehensive system characterization.
        """
    )

    # Using the streamlit-pdf-viewer package to display the PDF
    pdf_viewer(pdf_path, width=None, height=800, annotations=[])


def render_pulse_and_fluorescence_tab():
    """Render the combined pulse width and fluorescence signal estimation tab content."""

    create_header("Signal Optimization Protocols")
    
    st.markdown(
        """
        These **signal optimization protocols** implement key standardization procedures from the Nature Protocols paper. 
        **Pulse width optimization** maximizes multiphoton excitation efficiency through systematic dispersion compensation, 
        while **fluorescence signal estimation** provides absolute calibration methods for quantitative measurements.
        
        Both protocols are essential for establishing **reproducible, quantitative multiphoton microscopy** that enables 
        meaningful comparisons across different systems and laboratories.
        """
    )

    # Create main tabs for the three main sections
    pulse_tab, fluorescence_tab, reference_tab = st.tabs(
        [
            "⏱️ Pulse Width Control",
            "📊 Fluorescence Signal Estimation", 
            "📚 Protocol Reference",
        ]
    )

    with pulse_tab:
        # Enhanced content flow for pulse width optimization
        st.markdown(
            """
            **Pulse width optimization** represents one of the most critical yet often overlooked aspects of multiphoton microscopy. 
            The **temporal compression** of laser energy into ultrashort pulses creates the extreme instantaneous intensities required 
            for efficient multiphoton processes. However, **optical dispersion** in the microscope's light path can dramatically 
            reduce this efficiency by temporally stretching the pulses.
            """
        )
        render_pulse_width_theory_and_procedure()
        render_pulse_width_visualization()

    with fluorescence_tab:
        # Enhanced content flow for fluorescence estimation
        st.markdown(
            """
            **Absolute fluorescence signal estimation** transforms arbitrary detector outputs into meaningful physical quantities. 
            This **quantitative approach** enables rigorous system monitoring, optimization, and standardization across different 
            laboratories. The **Photon Transfer Curve method** provides a robust framework for converting detector signals into 
            absolute photon counts without requiring specialized photon-counting electronics.
            """
        )
        render_fluorescence_theory_and_procedure()
        render_fluorescence_visualization()

    with reference_tab:
        render_reference_content()
