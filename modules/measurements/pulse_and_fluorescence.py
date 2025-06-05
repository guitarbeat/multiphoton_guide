"""
Combined pulse width and fluorescence signal estimation module for the Multiphoton Microscopy Guide application.
Implements protocols for optimizing pulse width through GDD adjustment and estimating absolute magnitudes of fluorescence signals.
"""

import streamlit as st
import numpy as np
import os
from pathlib import Path
from streamlit_pdf_viewer import pdf_viewer

from modules.ui.components import create_header, create_plot, get_image_path
from modules.core.shared_utils import create_two_column_layout
from modules.measurements.pulse_width import (
    render_pulse_width_theory_and_procedure,
    render_pulse_width_visualization,
    render_pulse_width_tips
)
from modules.measurements.fluorescence import (
    render_fluorescence_theory_and_procedure,
    render_fluorescence_visualization,
    render_fluorescence_tips
)

def render_reference_content():
    """Render the reference PDF content."""
    
    # Path to the PDF file - use absolute path
    base_dir = Path(__file__).parent.parent.parent  # Go up to project root
    pdf_path = str(base_dir / "assets" / "s41596-024-01120-w.pdf")
    
    # Check if the PDF exists
    if not os.path.exists(pdf_path):
        st.error(f"Reference PDF not found at {pdf_path}. Please ensure the file is in the correct location.")
        return
    
    # Create a more compact layout with sidebar controls
    controls_col, pdf_col = st.columns([1, 4])
    
    with controls_col:
        st.subheader("Document Controls")
        
        # Create a table of contents
        with st.expander("📑 Table of Contents", expanded=True):
            st.markdown("""
            ### Protocol Sections
            
            1. **Introduction**
               - Overview of multiphoton microscopy standardization
               - Importance of quantitative measurements
            
            2. **Laser Power at the Sample**
               - Measuring and monitoring laser power
               - Impact on sample integrity and data quality
            
            3. **Field of View Size and Homogeneity**
               - Calibrating FOV dimensions
               - Assessing uniformity across the field
            
            4. **Spatial Resolution**
               - Measuring excitation volume geometry
               - Factors affecting resolution
            
            5. **Pulse Width Control and Optimization**
               - Understanding dispersion compensation
               - Optimizing GDD for maximum signal
            
            6. **Photomultiplier Tube Performance**
               - Monitoring PMT sensitivity
               - Detecting degradation over time
            
            7. **Estimating Absolute Magnitudes of Fluorescence Signals**
               - Converting arbitrary units to photon counts
               - Using the Photon Transfer Curve method
            """)
        
        # Add notes feature
        with st.expander("📝 Add Notes", expanded=False):
            if "reference_notes" not in st.session_state:
                st.session_state.reference_notes = ""
            
            st.text_area("Your Notes:", 
                        value=st.session_state.reference_notes,
                        height=200,
                        key="notes_input")
            
            if st.button("Save Notes", use_container_width=True):
                st.session_state.reference_notes = st.session_state.notes_input
                st.success("Notes saved!")
        
        # Add citation information
        with st.expander("📚 Citation Information", expanded=False):
            st.markdown("""
            **Full Citation:**
            
            Lees, R.M., Bianco, I.H., Campbell, R.A.A. et al. Standardized measurements for monitoring and comparing multiphoton microscope systems. Nat Protoc (2024). https://doi.org/10.1038/s41596-024-01120-w
            
            **Abstract:**
            
            The goal of this protocol is to improve the characterization and performance standardization of multiphoton microscopy hardware across a large user base. We purposefully focus on hardware and only briefly touch on software and data analysis routines where relevant. Here we cover the measurement and quantification of laser power, pulse width optimization, field of view, resolution and photomultiplier tube performance. The intended audience is scientists with little expertise in optics who either build or use multiphoton microscopes in their laboratories. They can use our procedures to test whether their multiphoton microscope performs well and produces consistent data over the lifetime of their system. Individual procedures are designed to take 1–2 h to complete without the use of expensive equipment. The procedures listed here help standardize the microscopes and facilitate the reproducibility of data across setups.
            """)
    
    with pdf_col:
        # Display the PDF with a larger size
        st.markdown("## Protocol Document")
        
        # Using the streamlit-pdf-viewer package to display the PDF
        # Providing required annotations parameter as empty list
        pdf_viewer(pdf_path, width=700, height=800, annotations=[])
        
        # Add a download button for the PDF
        with open(pdf_path, "rb") as file:
            btn = st.download_button(
                label="Download PDF",
                data=file,
                file_name="multiphoton_microscope_protocol.pdf",
                mime="application/pdf"
            )

def render_pulse_and_fluorescence_tab():
    """Render the combined pulse width and fluorescence signal estimation tab content."""
    
    create_header("Signal Optimization Protocols")
    
    # Create main tabs for the three main sections
    pulse_tab, fluorescence_tab, reference_tab = st.tabs([
        "⏱️ Pulse Width Control", 
        "📊 Fluorescence Signal Estimation",
        "📚 Protocol Reference"
    ])
    
    with pulse_tab:
        # Create two columns for layout using template
        create_two_column_layout(
            render_pulse_width_theory_and_procedure,
            lambda: (render_pulse_width_visualization(), render_pulse_width_tips())
        )
    
    with fluorescence_tab:
        # Create two columns for layout using template
        create_two_column_layout(
            render_fluorescence_theory_and_procedure,
            lambda: (render_fluorescence_visualization(), render_fluorescence_tips())
        )
    
    with reference_tab:
        render_reference_content() 