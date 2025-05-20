import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os
from pathlib import Path
import base64

# Set page title and icon - must be the first Streamlit command
st.set_page_config(
    page_title="Multiphoton Microscopy Guide",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

from modules.laser_power import render_laser_power_tab
from modules.pulse_width import render_pulse_width_tab
from modules.fluorescence import render_fluorescence_tab
from modules.rig_log import render_rig_log_tab
from modules.reference import render_reference_tab
from modules.theme import apply_theme, get_colors

def get_image_base64(image_path):
    """Get base64 encoding of an image file."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

def main():
    """Main application entry point."""
    
    # Set page theme
    apply_theme()
    colors = get_colors()
    
    # Initialize session state variables if they don't exist
    if "study_name" not in st.session_state:
        st.session_state.study_name = "Default Study"
    
    if "wavelength" not in st.session_state:
        st.session_state.wavelength = 920
    
    if "researcher" not in st.session_state:
        st.session_state.researcher = "Anonymous Researcher"
        
    if "sensor_model" not in st.session_state:
        st.session_state.sensor_model = ""
        
    if "measurement_mode" not in st.session_state:
        st.session_state.measurement_mode = "Stationary"
        
    if "fill_fraction" not in st.session_state:
        st.session_state.fill_fraction = 100
    
    # Create sidebar
    with st.sidebar:
        # Display logo at the top of the sidebar
        base_dir = Path(__file__).parent
        logo_path = str(base_dir / "assets" / "images" / "logo.svg")
        
        if os.path.exists(logo_path):
            with st.container():
                st.image(logo_path, use_container_width=True)
        
        st.title("Multiphoton Microscopy Guide")
        st.caption("Standardized measurements for monitoring and comparing multiphoton microscope systems")
        
        st.markdown("---")
        
        # Study setup form with improved styling
        with st.container():
            st.markdown(f"""
            <style>
            div[data-testid="stForm"] {{
                border: 1px solid {colors['surface']};
                border-radius: 10px;
                padding: 10px;
                margin-bottom: 20px;
            }}
            div[data-testid="stForm"] button[kind="formSubmit"] {{
                background-color: {colors['primary']};
                color: white;
                border-radius: 4px;
                padding: 0.25rem 1rem;
                font-weight: bold;
                width: 100%;
            }}
            div[data-testid="stForm"] button[kind="formSubmit"]:hover {{
                background-color: {colors['accent']};
            }}
            </style>
            """, unsafe_allow_html=True)
            
            with st.form(key="study_setup_form"):
                st.subheader("Session Setup")
                
                study_name = st.text_input(
                    "Study Name:", 
                    value=st.session_state.study_name,
                    key="Study Name:",
                    help="Enter a name for your study or experiment"
                )
                
                wavelength = st.number_input(
                    "Wavelength (nm):", 
                    min_value=700, 
                    max_value=1100, 
                    value=int(st.session_state.wavelength),
                    step=10,
                    key="Wavelength (nm):",
                    help="Enter the laser wavelength in nanometers (typical range: 700-1100 nm)"
                )
                
                researcher = st.text_input(
                    "Researcher:", 
                    value=st.session_state.researcher,
                    key="Researcher:",
                    help="Enter your name or identifier for record keeping"
                )
                
                # Add sensor model to sidebar
                sensor_model = st.text_input(
                    "Sensor Model:", 
                    value=st.session_state.sensor_model,
                    key="Sidebar_Sensor_Model",
                    help="Enter the model of your power meter sensor"
                )
                
                # Add measurement mode to sidebar
                measurement_mode = st.radio(
                    "Measurement Mode:", 
                    ["Stationary", "Scanning"],
                    index=0 if st.session_state.measurement_mode == "Stationary" else 1,
                    key="Sidebar_Measurement_Mode",
                    help="Stationary: beam fixed at center. Scanning: beam continuously scanning."
                )
                
                # Add fill fraction to sidebar (only shown if scanning mode is selected)
                fill_fraction = st.session_state.fill_fraction  # Default from session state
                if measurement_mode == "Scanning":
                    fill_fraction = st.number_input(
                        "Fill Fraction (%):", 
                        min_value=1, max_value=100, 
                        value=int(st.session_state.fill_fraction),
                        key="Sidebar_Fill_Fraction",
                        help="Percentage of time the beam is 'on' during scanning"
                    )
                
                submitted = st.form_submit_button("Update Session")
                
                if submitted:
                    # Validate inputs
                    if not study_name.strip():
                        st.error("Study name cannot be empty")
                    elif wavelength < 700 or wavelength > 1100:
                        st.error("Wavelength must be between 700 and 1100 nm")
                    else:
                        # Update all session state variables
                        st.session_state.study_name = study_name
                        st.session_state.wavelength = wavelength
                        st.session_state.researcher = researcher if researcher.strip() else "Anonymous Researcher"
                        st.session_state.sensor_model = sensor_model
                        st.session_state.measurement_mode = measurement_mode
                        st.session_state.fill_fraction = fill_fraction
                        
                        st.success("Session updated successfully!")
        
        st.markdown("---")
        
        # Navigation with improved styling
        st.subheader("Navigation")
        
        # Custom CSS for the radio buttons
        st.markdown(f"""
        <style>
        div.row-widget.stRadio > div {{
            display: flex;
            flex-direction: column;
        }}
        div.row-widget.stRadio > div[role="radiogroup"] > label {{
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 5px;
            transition: background-color 0.3s;
        }}
        div.row-widget.stRadio > div[role="radiogroup"] > label:hover {{
            background-color: {colors['surface']};
        }}
        </style>
        """, unsafe_allow_html=True)
        
        tab_selection = st.radio(
            "Select a section:",
            [
                "🔍 Laser Power at the Sample",
                "⏱️ Pulse Width Control",
                "📊 Fluorescence Signal Estimation",
                "📝 Rig Log",
                "📚 Reference"
            ]
        )
        
        # Add session info display
        st.markdown("---")
        st.caption("**Current Session**")
        st.caption(f"Study: **{st.session_state.study_name}**")
        st.caption(f"Wavelength: **{st.session_state.wavelength} nm**")
        st.caption(f"Researcher: **{st.session_state.researcher}**")
    
    # Render the selected tab
    if tab_selection == "🔍 Laser Power at the Sample":
        render_laser_power_tab()
    elif tab_selection == "⏱️ Pulse Width Control":
        render_pulse_width_tab()
    elif tab_selection == "📊 Fluorescence Signal Estimation":
        render_fluorescence_tab()
    elif tab_selection == "📝 Rig Log":
        render_rig_log_tab()
    elif tab_selection == "📚 Reference":
        render_reference_tab()

if __name__ == "__main__":
    main()
