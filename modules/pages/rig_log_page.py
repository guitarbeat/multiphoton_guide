"""
Rig log page for the Multiphoton Microscopy Guide application.
"""

import streamlit as st
from modules.rig_log import render_rig_log_tab

def rig_log_page():
    """
    Page function for the Rig Log section.
    This is called by the navigation system.
    """
    render_rig_log_tab() 