"""
Pulse width page for the Multiphoton Microscopy Guide application.
"""

import streamlit as st
from modules.pulse_width import render_pulse_width_tab

def pulse_width_page():
    """
    Page function for the Pulse Width Control section.
    This is called by the navigation system.
    """
    render_pulse_width_tab() 