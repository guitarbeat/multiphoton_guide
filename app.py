import base64
import os

import streamlit as st

from modules.analysis import run_usaf_analyzer
from modules.measurements import (
    render_laser_power_tab,
    render_pulse_and_fluorescence_tab,
    render_rig_log_tab,
)
from modules.ui.theme import apply_theme, get_colors

# Set page title and icon - must be the first Streamlit command
st.set_page_config(
    page_title="Multiphoton Microscopy Guide",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)


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

    # Initialize current page if not set
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Laser Power Measurements"


def apply_sidebar_styling():
    """Apply custom styling to the sidebar."""
    # Get theme colors
    get_colors()

    # Construct the path to the CSS file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    css_file_path = os.path.join(base_dir, "assets", "styles.css")

    # Read the CSS file and replace placeholders with actual theme colors
    if os.path.exists(css_file_path):
        with open(css_file_path, "r") as f:
            css_content = f.read()
            # Replace placeholders with actual colors using .format()
            # Ensure CSS variables are defined in styles.css e.g. var(--background-color)
            # These will be dynamically replaced if needed, or can be static in the CSS.
            # For now, we assume CSS variables are used and colors are set in `apply_theme()`
            # or directly in the CSS file if they are static.
            # Example of dynamic replacement if needed:
            # css_content = css_content.replace("var(--background-color)", colors['background'])
            # css_content = css_content.replace("var(--surface-color)", colors['surface'])
            # css_content = css_content.replace("var(--primary-color)", colors['primary'])
            # css_content = css_content.replace("var(--accent-color)", colors['accent'])
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    else:
        st.error(f"CSS file not found at {css_file_path}")


def render_session_info():
    """Render the session info display with enhanced styling and inline editing capability."""
    # List of available researchers (PI and graduate students)
    researchers = [
        "Andrew Dunn",  # PI
        "Jewel Ashbrook",
        "Sam Melvin",
        "Hengfa Lu",
        "Aaron Woods",
        "Logan Parker",
    ]
    # Create a container for the session info
    with st.container():
        st.markdown('<div class="session-info-title">Current Session</div>', unsafe_allow_html=True)
        
        # Create expandable container for editing
        with st.expander("Edit Session Info", expanded=False):
            # Study name input
            new_study_name = st.text_input(
                "Study Name",
                value=st.session_state.study_name,
                key="sidebar_study_name",
                help="Enter a name for your study or experiment"
            )
            
            # Researcher dropdown (PI and grad students)
            new_researcher = st.selectbox(
                "Researcher",
                options=researchers,
                index=researchers.index(st.session_state.researcher) if st.session_state.researcher in researchers else 0,
                key="sidebar_researcher",
                help="Select the researcher for this session"
            )
            
            # Update button
            if st.button("Update", key="update_session_btn", use_container_width=True):
                if new_study_name.strip():
                    st.session_state.study_name = new_study_name
                    st.session_state.researcher = new_researcher
                    st.success("Session updated!")
                    st.rerun()
                else:
                    st.error("Study name cannot be empty")
        
        # Display current values
        st.markdown(
            f"""
            <div class="session-info">
                <div class="session-info-item">
                    <span class="session-info-label">Study:</span>
                    <span class="session-info-value">{st.session_state.study_name}</span>
                </div>
                <div class="session-info-item">
                    <span class="session-info-label">Researcher:</span>
                    <span class="session-info-value">{st.session_state.researcher}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_study_inputs():
    """Render study name and researcher input fields."""
    study_name = st.text_input(
        "Study Name:",
        value=st.session_state.study_name,
        key="Study Name:",
        help="Enter a name for your study or experiment",
    )
    researcher = st.text_input(
        "Researcher:",
        value=st.session_state.researcher,
        key="Researcher:",
        help="Enter your name or identifier for record keeping",
    )
    return study_name, researcher


def render_laser_inputs():
    """Render laser wavelength input field."""
    # This function is deprecated - wavelength management removed
    return None


def render_measurement_inputs():
    """Render measurement mode, sensor model, and fill fraction input fields."""
    # Only show fill fraction for Laser Power at the Sample page
    if st.session_state.current_page == "Laser Power at the Sample":
        fill_fraction = st.session_state.fill_fraction
        if st.session_state.measurement_mode == "Scanning":
            fill_fraction = st.number_input(
                "Fill Fraction (%):",
                min_value=1,
                max_value=100,
                value=int(st.session_state.fill_fraction),
                key="Sidebar_Fill_Fraction",
                help="Percentage of time the beam is 'on' during scanning",
            )
        return fill_fraction
    else:
        # Return default value for other pages
        return st.session_state.fill_fraction


def render_session_setup_form():
    """Render the session setup form."""
    with st.form(key="study_setup_form"):
        st.subheader("Session Setup")

        study_name, researcher = render_study_inputs()
        # Add sensor model input
        sensor_model = st.text_input(
            "Sensor Model (optional):",
            value=st.session_state.get("sensor_model", ""),
            key="Session_Sensor_Model",
            help="Enter the model of your power meter sensor (optional)",
        )
        fill_fraction = render_measurement_inputs()

        submitted = st.form_submit_button("Update Session")

        if submitted:
            if not study_name.strip():
                st.error("Study name cannot be empty")
            else:
                st.session_state.study_name = study_name
                st.session_state.researcher = (
                    researcher if researcher.strip() else "Anonymous Researcher"
                )
                st.session_state.sensor_model = sensor_model
                st.session_state.fill_fraction = fill_fraction
                st.success("Session updated successfully!")


def main():
    """Main application entry point."""
    # Initialize session state
    initialize_session_state()

    # Set page theme
    apply_theme()

    # Define the pages for navigation with their functions directly
    pages = {
        "Microscope Tools": [
            {
                "title": "Laser Power Measurements",
                "icon": "🔍",
                "function": lambda: render_laser_power_tab(use_sidebar_values=True),
            },
            {
                "title": "Signal Optimization Protocols",
                "icon": "⚡",
                "function": render_pulse_and_fluorescence_tab,
            },
        ],
        "Analysis Tools": [
            {
                "title": "USAF Target Analyzer",
                "icon": "🎯",
                "function": run_usaf_analyzer,
            },
        ],
        "Documentation": [
            {"title": "Rig Log", "icon": "📝", "function": render_rig_log_tab},
        ],
    }

    # Apply custom sidebar styling
    apply_sidebar_styling()

    # Render the sidebar with session info and navigation
    with st.sidebar:
        st.title("Multiphoton Microscopy Guide")
        # Display logo at the top of the sidebar
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(base_dir, "assets", "images", "logo.svg")

        if os.path.exists(logo_path):
            with st.container():
                st.image(logo_path, use_container_width=True)

        st.caption(
            "Standardized measurements for monitoring and comparing multiphoton microscope systems"
        )

        st.markdown("---")

        # Only render session info in the sidebar
        render_session_info()

        # Render session setup form in the sidebar (always visible)
        # render_session_setup_form()  # Removed as requested

        # Add navigation at the bottom of the sidebar
        st.markdown('<div class="nav-container">', unsafe_allow_html=True)
        st.subheader("Navigation")

        # Create custom navigation links
        for section, section_pages in pages.items():
            st.markdown(f"**{section}**")
            for page in section_pages:
                # Check if this is the current page
                is_active = st.session_state.current_page == page["title"]
                button_style = "primary" if is_active else "secondary"

                # Create a button for each page
                if st.button(
                    f"{page['icon']} {page['title']}",
                    key=f"nav_{page['title']}",
                    use_container_width=True,
                    type=button_style,
                    disabled=is_active,
                ):
                    st.session_state.current_page = page["title"]
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # Get the function for the current page
    current_page_function = None
    for section, section_pages in pages.items():
        for page in section_pages:
            if page["title"] == st.session_state.current_page:
                current_page_function = page["function"]
                break
        if current_page_function:
            break

    # Run the current page function
    if current_page_function:
        current_page_function()
    else:
        st.error(f"Page '{st.session_state.current_page}' not found.")


if __name__ == "__main__":
    main()
