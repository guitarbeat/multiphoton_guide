"""
Laser power page for the Multiphoton Microscopy Guide application.
"""

import streamlit as st
from modules.laser_power import render_laser_power_tab

def laser_power_page():
    """
    Page function for the Laser Power at the Sample section.
    This is called by the navigation system.
    """
    # Ensure session state variables are used by the laser power module
    render_laser_power_tab(use_sidebar_values=True) 