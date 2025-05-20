"""
Reference page for the Multiphoton Microscopy Guide application.
"""

import streamlit as st
from modules.reference import render_reference_tab

def reference_page():
    """
    Page function for the Reference section.
    This is called by the navigation system.
    """
    render_reference_tab() 