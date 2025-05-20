"""
Test file to display the logo and PDF.
"""

import streamlit as st
from pathlib import Path
import os
from streamlit_pdf_viewer import pdf_viewer

def test_assets():
    """Test displaying logo and PDF."""
    
    st.title("Asset Display Test")
    
    # Test logo display
    base_dir = Path(__file__).parent.parent
    logo_path = str(base_dir / "assets" / "images" / "logo.svg")
    
    st.subheader("Logo Display")
    if os.path.exists(logo_path):
        with st.container():
            st.image(logo_path, use_container_width=True)
        st.success(f"Logo exists at {logo_path}")
    else:
        st.error(f"Logo not found at {logo_path}")
    
    # Test PDF display
    pdf_path = str(base_dir / "assets" / "s41596-024-01120-w.pdf")
    
    st.subheader("PDF Display")
    if os.path.exists(pdf_path):
        # Using the streamlit-pdf-viewer package
        pdf_viewer(pdf_path, width="100%", height=300, render_text=True)
        st.success(f"PDF exists at {pdf_path}")
    else:
        st.error(f"PDF not found at {pdf_path}")

if __name__ == "__main__":
    test_assets() 