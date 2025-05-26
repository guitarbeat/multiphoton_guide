"""
USAF Target Analyzer page for the Multiphoton Microscopy Guide application.
"""

import streamlit as st
from modules.usaf_analyzer import run_usaf_analyzer


def usaf_analyzer_page():
    """
    Page function for the USAF Target Analyzer section.
    This is called by the navigation system.
    """
    run_usaf_analyzer()
