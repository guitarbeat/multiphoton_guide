"""
Theme configuration for the Multiphoton Microscopy Guide application.
Implements a dark theme with consistent color scheme and accessibility features.
"""

import streamlit as st

# Define color scheme for dark theme
COLORS = {
    "primary": "#BF5701",       # Primary Orange
    "secondary": "#035F86",     # Primary Blue
    "accent": "#F2A65A",        # Warm Gold
    "info": "#4BA3C4",          # Sky Blue
    "success": "#86BF01",       # Bright Lime
    "background": "#121212",    # Dark background
    "surface": "#1E1E1E",       # Slightly lighter surface
    "on_surface": "#2D2D2D",    # Card/container background
    "text": "#E0E0E0",          # Light text
    "text_secondary": "#AAAAAA", # Secondary text
    "input_background": "#3D3D3D", # Input field background (higher contrast)
    "input_text": "#FFFFFF",    # Input text (bright white for contrast)
    "input_border": "#555555",  # Input border color
    "input_focus": "#F2A65A",   # Input focus highlight color
    "warning_text": "#FF9800",  # Warning text color
    "error_text": "#FF5252"     # Error text color
}

def apply_theme():
    """Apply the dark theme to the Streamlit application."""
    
    # Create .streamlit/config.toml with dark theme settings
    import os
    os.makedirs(".streamlit", exist_ok=True)
    
    with open(".streamlit/config.toml", "w") as f:
        f.write(f"""
[theme]
primaryColor = "{COLORS['primary']}"
backgroundColor = "{COLORS['background']}"
secondaryBackgroundColor = "{COLORS['surface']}"
textColor = "{COLORS['text']}"
font = "sans serif"

[browser]
gatherUsageStats = false
        """)
    
    # Apply only essential custom CSS for basic styling
    st.markdown(f"""
    <style>
        /* Base styles */
        .main .block-container {{
            padding-top: 1rem;
            padding-bottom: 1rem;
            max-width: 95%;
        }}
        
        /* Typography */
        h1, h2, h3, h4, h5, h6 {{
            color: {COLORS['primary']};
        }}
        
        code {{
            color: {COLORS['accent']};
            background-color: {COLORS['on_surface']};
            padding: 2px 5px;
            border-radius: 3px;
        }}
        
        /* Buttons */
        .stButton button {{
            background-color: {COLORS['primary']};
            color: {COLORS['text']};
        }}
        .stButton button:hover {{
            background-color: {COLORS['accent']};
        }}
        
        /* Sidebar */
        [data-testid="stSidebar"] {{
            background-color: {COLORS['surface']};
        }}
        
        /* Input fields - Enhanced contrast */
        .stTextInput input, 
        input[type="number"],
        div[data-baseweb="select"] {{
            background-color: {COLORS['input_background']} !important;
            color: {COLORS['input_text']} !important;
            border: 1px solid {COLORS['input_border']} !important;
        }}
        
        /* Alert messages */
        .stAlert [data-baseweb="notification"][kind="info"] {{
            border-left-color: {COLORS['info']};
        }}
        .stAlert [data-baseweb="notification"][kind="success"] {{
            border-left-color: {COLORS['success']};
        }}
        .stAlert [data-baseweb="notification"][kind="warning"] {{
            border-left-color: {COLORS['warning_text']};
        }}
        .stAlert [data-baseweb="notification"][kind="error"] {{
            border-left-color: {COLORS['error_text']};
        }}
        
        /* Links */
        a {{
            color: {COLORS['secondary']};
        }}
        a:hover {{
            color: {COLORS['primary']};
            text-decoration: underline;
        }}
    </style>
    """, unsafe_allow_html=True)

def get_colors():
    """Return the color scheme dictionary."""
    return COLORS

def create_input_field(component_type, label, key, **kwargs):
    """
    Create a styled input field with consistent appearance.
    
    Args:
        component_type: The Streamlit component function (st.text_input, st.number_input, etc.)
        label: Label for the input field
        key: Unique key for the component
        **kwargs: Additional arguments to pass to the component
        
    Returns:
        The value returned by the component
    """
    # Add help text if not provided
    if 'help' not in kwargs:
        kwargs['help'] = f"Enter {label.lower()}"
    
    # Create the component
    return component_type(label=label, key=key, **kwargs)

def create_text_input(label, key, **kwargs):
    """Create a styled text input field."""
    return create_input_field(st.text_input, label, key, **kwargs)

def create_number_input(label, key, **kwargs):
    """Create a styled number input field."""
    return create_input_field(st.number_input, label, key, **kwargs)

def create_select_box(label, key, options, **kwargs):
    """Create a styled select box."""
    return create_input_field(st.selectbox, label, key, options=options, **kwargs)

def create_radio_buttons(label, key, options, **kwargs):
    """Create styled radio buttons."""
    return create_input_field(st.radio, label, key, options=options, **kwargs)

def create_checkbox(label, key, **kwargs):
    """Create a styled checkbox."""
    return create_input_field(st.checkbox, label, key, **kwargs)
