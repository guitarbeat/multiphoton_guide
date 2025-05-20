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
    render_laser_power_tab() 