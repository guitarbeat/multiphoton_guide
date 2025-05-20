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

from modules.theme import apply_theme, get_colors
from modules.pages.laser_power_page import laser_power_page
from modules.pages.pulse_width_page import pulse_width_page
from modules.pages.fluorescence_page import fluorescence_page
from modules.pages.rig_log_page import rig_log_page
from modules.pages.reference_page import reference_page

def get_image_base64(image_path):
    """Get base64 encoding of an image file."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

def initialize_session_state():
    """Initialize session state variables if they don't exist."""
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

def apply_sidebar_styling():
    """Apply custom styling to the sidebar."""
    # Get theme colors
    colors = get_colors()
    
    # Apply custom CSS for sidebar styling
    st.markdown(f"""
    <style>
    /* Sidebar background and padding */
    [data-testid="stSidebar"] {{
        background-color: {colors['background']};
        padding: 1rem 0.5rem;
        border-right: 1px solid {colors['surface']};
        display: flex;
        flex-direction: column;
    }}
    
    /* Sidebar title styling */
    [data-testid="stSidebar"] h1 {{
        color: {colors['primary']};
        font-size: 1.5rem;
        margin-top: 0.5rem;
        margin-bottom: 0.2rem;
    }}
    
    /* Sidebar caption styling */
    [data-testid="stSidebar"] .stCaption {{
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }}
    
    /* Divider styling */
    [data-testid="stSidebar"] hr {{
        margin: 1rem 0;
        border-color: {colors['surface']};
    }}
    
    /* Form container styling */
    [data-testid="stSidebar"] div[data-testid="stForm"] {{
        border: 1px solid {colors['surface']};
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1.5rem;
        background-color: rgba(255, 255, 255, 0.03);
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }}
    
    /* Form title styling */
    [data-testid="stSidebar"] div[data-testid="stForm"] h3 {{
        color: {colors['primary']};
        font-size: 1.2rem;
        margin-top: 0;
        margin-bottom: 1rem;
        border-bottom: 1px solid {colors['surface']};
        padding-bottom: 0.5rem;
    }}
    
    /* Form submit button styling */
    [data-testid="stSidebar"] div[data-testid="stForm"] button[kind="formSubmit"] {{
        background-color: {colors['primary']};
        color: white;
        border-radius: 4px;
        padding: 0.25rem 1rem;
        font-weight: bold;
        width: 100%;
        transition: background-color 0.3s, transform 0.2s;
    }}
    
    [data-testid="stSidebar"] div[data-testid="stForm"] button[kind="formSubmit"]:hover {{
        background-color: {colors['accent']};
        transform: translateY(-1px);
    }}
    
    /* Session info styling */
    .session-info {{
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 0.8rem;
        margin-top: 0.5rem;
        border-left: 3px solid {colors['primary']};
    }}
    
    .session-info-title {{
        color: {colors['primary']};
        font-weight: bold;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }}
    
    .session-info-item {{
        display: flex;
        justify-content: space-between;
        padding: 0.2rem 0;
        font-size: 0.85rem;
    }}
    
    .session-info-label {{
        color: rgba(255, 255, 255, 0.7);
    }}
    
    .session-info-value {{
        font-weight: bold;
    }}
    
    /* Navigation styling - improve spacing and highlight current page */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{
        gap: 0.5rem;
    }}
    
    /* Make the logo container more compact */
    [data-testid="stSidebar"] [data-testid="stImage"] {{
        margin-bottom: 0.5rem;
    }}
    
    /* Custom class for navigation container */
    .nav-container {{
        margin-top: auto;
        padding-top: 1rem;
        border-top: 1px solid {colors['surface']};
    }}
    </style>
    """, unsafe_allow_html=True)

def render_session_info():
    """Render the session info display with enhanced styling."""
    st.markdown("""
    <div class="session-info">
        <div class="session-info-title">Current Session</div>
        <div class="session-info-item">
            <span class="session-info-label">Study:</span>
            <span class="session-info-value">{study_name}</span>
        </div>
        <div class="session-info-item">
            <span class="session-info-label">Wavelength:</span>
            <span class="session-info-value">{wavelength} nm</span>
        </div>
        <div class="session-info-item">
            <span class="session-info-label">Researcher:</span>
            <span class="session-info-value">{researcher}</span>
        </div>
        <div class="session-info-item">
            <span class="session-info-label">Mode:</span>
            <span class="session-info-value">{mode}</span>
        </div>
    </div>
    """.format(
        study_name=st.session_state.study_name,
        wavelength=st.session_state.wavelength,
        researcher=st.session_state.researcher,
        mode=st.session_state.measurement_mode
    ), unsafe_allow_html=True)

def render_session_setup_form():
    """Render the session setup form."""
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

def main():
    """Main application entry point."""
    # Initialize session state
    initialize_session_state()
    
    # Set page theme
    apply_theme()
    
    # Define the pages for navigation
    pages = {
        "Microscope Tools": [
            st.Page(laser_power_page, title="Laser Power at the Sample", icon="🔍"),
            st.Page(pulse_width_page, title="Pulse Width Control", icon="⏱️"),
            st.Page(fluorescence_page, title="Fluorescence Signal Estimation", icon="📊"),
        ],
        "Documentation": [
            st.Page(rig_log_page, title="Rig Log", icon="📝"),
            st.Page(reference_page, title="Reference", icon="📚"),
        ]
    }
    
    # Set up navigation with expanded option for better visibility
    current_page = st.navigation(pages, position="hidden")
    
    # Apply custom sidebar styling
    apply_sidebar_styling()
    
    # Render the sidebar with session setup form
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
        
        # Render session setup form
        render_session_setup_form()
        
        # Add session info display with enhanced styling
        st.markdown("---")
        render_session_info()
        
        # Add navigation at the bottom of the sidebar
        st.markdown('<div class="nav-container">', unsafe_allow_html=True)
        st.subheader("Navigation")
        
        # Create custom navigation links
        for section, section_pages in pages.items():
            st.markdown(f"**{section}**")
            for page in section_pages:
                if st.button(f"{page.icon} {page.title}", key=f"nav_{page.title}", use_container_width=True):
                    # Switch to the selected page
                    st.switch_page(page._target)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Run the current page
    current_page.run()

if __name__ == "__main__":
    main()
