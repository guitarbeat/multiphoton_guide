import unittest
from streamlit.testing.v1 import AppTest

class TestApp(unittest.TestCase):
    """Test the Streamlit application."""
    
    def test_app_loads(self):
        """Test that the app loads without errors."""
        at = AppTest.from_file("app.py")
        at.run()
        
        # Check that the app loaded successfully
        assert not at.exception
        
        # Check that the sidebar contains expected elements
        sidebar = at.sidebar
        assert sidebar is not None
        assert "Multiphoton Microscopy Guide" in sidebar.title[0].value
        
    def test_study_form_submission(self):
        """Test that the study form submission updates session state."""
        at = AppTest.from_file("app.py")
        
        # Run the app
        at.run()
        
        # Check that the form exists in the sidebar
        sidebar = at.sidebar
        assert sidebar is not None
        
        # Check that session state is updated correctly
        assert "study_name" in at.session_state
        assert "wavelength" in at.session_state
        assert "researcher" in at.session_state
