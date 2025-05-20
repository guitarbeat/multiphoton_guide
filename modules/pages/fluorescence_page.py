"""
Fluorescence page for the Multiphoton Microscopy Guide application.
"""

import streamlit as st
from modules.fluorescence import render_fluorescence_tab

def fluorescence_page():
    """
    Page function for the Fluorescence Signal Estimation section.
    This is called by the navigation system.
    """
    render_fluorescence_tab() 