"""
Reference viewer module for the Multiphoton Microscopy Guide application.
Implements a PDF viewer for the protocol reference document.
"""

import streamlit as st
import os
from pathlib import Path
from streamlit_pdf_viewer import pdf_viewer

from modules.ui_components import create_header, create_info_box, create_tab_section

def render_reference_tab():
    """Render the reference tab content."""
    
    create_header("Protocol Reference", 
                 "Standardized measurements for monitoring and comparing multiphoton microscope systems")
    
    # Path to the PDF file - use absolute path
    base_dir = Path(__file__).parent.parent
    pdf_path = str(base_dir / "assets" / "s41596-024-01120-w.pdf")
    
    # Check if the PDF exists
    if not os.path.exists(pdf_path):
        st.error(f"Reference PDF not found at {pdf_path}. Please ensure the file is in the correct location.")
        return
    
    # Create a table of contents
    with st.popover("📑 Table of Contents", use_container_width=True):
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
    with st.popover("📝 Add Notes", use_container_width=True):
        if "reference_notes" not in st.session_state:
            st.session_state.reference_notes = ""
        
        st.text_area("Your Notes:", 
                    value=st.session_state.reference_notes,
                    height=200,
                    key="notes_input")
        
        if st.button("Save Notes"):
            st.session_state.reference_notes = st.session_state.notes_input
            st.success("Notes saved!")
    
    # Display the PDF
    st.markdown("### Protocol Document")
    
    # Using the streamlit-pdf-viewer package to display the PDF
    # Setting width to 100% for responsive display and height to 600 pixels
    pdf_viewer(pdf_path, width="100%", height=600, render_text=True)
    
    # Add citation information
    with st.expander("📚 Citation Information"):
        st.markdown("""
        **Full Citation:**
        
        Lees, R.M., Bianco, I.H., Campbell, R.A.A. et al. Standardized measurements for monitoring and comparing multiphoton microscope systems. Nat Protoc (2024). https://doi.org/10.1038/s41596-024-01120-w
        
        **Abstract:**
        
        The goal of this protocol is to improve the characterization and performance standardization of multiphoton microscopy hardware across a large user base. We purposefully focus on hardware and only briefly touch on software and data analysis routines where relevant. Here we cover the measurement and quantification of laser power, pulse width optimization, field of view, resolution and photomultiplier tube performance. The intended audience is scientists with little expertise in optics who either build or use multiphoton microscopes in their laboratories. They can use our procedures to test whether their multiphoton microscope performs well and produces consistent data over the lifetime of their system. Individual procedures are designed to take 1–2 h to complete without the use of expensive equipment. The procedures listed here help standardize the microscopes and facilitate the reproducibility of data across setups.
        """)
