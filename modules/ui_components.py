"""
UI components module for the Multiphoton Microscopy Guide application.
Provides reusable UI components for consistent styling and layout.
"""

import streamlit as st
import matplotlib.pyplot as plt
import os
from pathlib import Path
from modules.theme import get_colors

def create_header(title, subtitle=None):
    """Create a consistent header with title and optional subtitle."""
    
    st.title(title)
    
    if subtitle:
        st.caption(subtitle, help="Important context for this section")
    
    st.markdown("---")

def create_session_badges(study_name, wavelength, researcher):
    """Create badges for session information."""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.badge(f"Study: {study_name}")
    
    with col2:
        st.badge(f"Wavelength: {wavelength} nm")
    
    with col3:
        st.badge(f"Researcher: {researcher}")

def create_info_box(content):
    """Create an info box with blue styling."""
    
    st.info(content)

def create_warning_box(content):
    """Create a warning box with orange styling."""
    
    st.warning(content)

def create_success_box(content):
    """Create a success box with green styling."""
    
    st.success(content)

def create_metric_row(metrics):
    """Create a row of metrics.
    
    Args:
        metrics: List of dicts with keys 'label' and 'value'
    """
    
    cols = st.columns(len(metrics))
    
    for i, metric in enumerate(metrics):
        with cols[i]:
            delta_color = "normal"
            if "delta_color" in metric:
                delta_color = metric["delta_color"]
                
            st.metric(
                label=metric["label"],
                value=metric["value"],
                delta=metric.get("delta", None),
                delta_color=delta_color,
                help=metric.get("help", None)
            )

def create_data_editor(df, key, column_config=None, num_rows="fixed", height=None):
    """Create a data editor with consistent styling.
    
    Args:
        df: Pandas DataFrame to edit
        key: Unique key for the editor
        column_config: Column configuration
        num_rows: 'fixed' or 'dynamic'
        height: Optional height in pixels
    
    Returns:
        Edited DataFrame
    """
    
    return st.data_editor(
        df,
        key=key,
        column_config=column_config,
        num_rows=num_rows,
        height=height,
        use_container_width=True,
        hide_index=True
    )

def create_plot(plot_function, figsize=(10, 6), dpi=100):
    """Create a plot with consistent styling.
    
    Args:
        plot_function: Function that takes (fig, ax) and creates the plot
        figsize: Figure size tuple (width, height) in inches
        dpi: Dots per inch
    
    Returns:
        Matplotlib figure
    """
    
    fig, ax = plt.subplots(figsize=figsize, dpi=100)
    
    # Set style with more modern elements
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # Set background color to transparent
    fig.patch.set_alpha(0.0)
    
    # Call the plot function
    plot_function(fig, ax)
    
    # Adjust layout
    fig.tight_layout()
    
    return fig

def create_tab_section(title, content_function, expanded=False):
    """Create a collapsible section with a title.
    
    Args:
        title: Section title
        content_function: Function that renders the content
        expanded: Whether the section is expanded by default
    """
    
    with st.expander(title, expanded=expanded):
        content_function()
        
    # Add a small gap after the expander
    st.markdown("<div style='margin-bottom: 10px'></div>", unsafe_allow_html=True)

def create_form_section(title, form_key, submit_label="Submit", clear_form=True):
    """Create a form section with a title and optional clear button.
    
    Args:
        title: Form title
        form_key: Unique key for the form
        submit_label: Label for the submit button
        clear_form: Whether to add a clear form button
    
    Returns:
        Tuple of (form, submitted)
    """
    
    st.subheader(title)
    
    form = st.form(key=form_key)
    submitted = form.form_submit_button(submit_label)
    
    if clear_form:
        colors = get_colors()
        st.markdown(f"""
        <style>
        div.stButton > button.clear-form {{
            background-color: {colors['secondary']};
            color: white;
            border-radius: 4px;
            margin-top: 10px;
        }}
        div.stButton > button.clear-form:hover {{
            background-color: {colors['info']};
        }}
        </style>
        """, unsafe_allow_html=True)
    
    return form, submitted

def create_tooltip(text, tooltip_text):
    """Create text with a tooltip.
    
    Args:
        text: The visible text
        tooltip_text: The tooltip text
    """
    
    st.markdown(f"""
    <span title="{tooltip_text}" style="border-bottom: 1px dotted #999; cursor: help;">{text}</span>
    """, unsafe_allow_html=True)

def get_image_path(image_name):
    """Get the absolute path to an image in the assets/images directory.
    
    Args:
        image_name: Name of the image file
    
    Returns:
        Absolute path to the image
    """
    
    base_dir = Path(__file__).parent.parent
    image_path = base_dir / "assets" / "images" / image_name
    
    return str(image_path)

def display_image(image_name, caption=None, width=None):
    """Display an image from the assets/images directory.
    
    Args:
        image_name: Name of the image file
        caption: Optional caption for the image
        width: Optional width for the image
    """
    
    image_path = get_image_path(image_name)
    
    if os.path.exists(image_path):
        st.image(image_path, caption=caption, width=width)
    else:
        st.error(f"Image not found: {image_name}")

def create_clear_button(label="Clear Form", key=None):
    """Create a styled clear button.
    
    Args:
        label: Button label
        key: Unique key for the button
    
    Returns:
        Button click state
    """
    
    colors = get_colors()
    st.markdown(f"""
    <style>
    div.stButton > button.clear-form {{
        background-color: {colors['secondary']};
        color: white;
        border-radius: 4px;
        margin-top: 10px;
    }}
    div.stButton > button.clear-form:hover {{
        background-color: {colors['info']};
    }}
    </style>
    """, unsafe_allow_html=True)
    
    return st.button(label, key=key, help="Reset all form fields to their default values")

def create_technical_term(term, definition):
    """Create a technical term with a tooltip definition.
    
    Args:
        term: The technical term
        definition: The definition to show in the tooltip
    """
    
    st.markdown(f"""
    <span title="{definition}" style="border-bottom: 1px dotted #999; cursor: help; font-weight: bold;">{term}</span>
    """, unsafe_allow_html=True)
