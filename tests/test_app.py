import unittest
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from streamlit.testing.v1 import AppTest
    STREAMLIT_TESTING_AVAILABLE = True
except ImportError:
    STREAMLIT_TESTING_AVAILABLE = False
    AppTest = None

@pytest.mark.streamlit
class TestApp(unittest.TestCase):
    """Test the Streamlit application."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        if not STREAMLIT_TESTING_AVAILABLE:
            self.skipTest("Streamlit testing framework not available")
    
    @pytest.mark.slow
    def test_app_loads_without_errors(self):
        """Test that the app loads without exceptions."""
        at = AppTest.from_file("app.py")
        at.run()
        
        # Check that the app loaded successfully
        self.assertIsNone(at.exception, f"App failed to load: {at.exception}")
        
    @pytest.mark.slow
    def test_sidebar_elements_exist(self):
        """Test that expected sidebar elements are present."""
        at = AppTest.from_file("app.py")
        at.run()
        
        # Check sidebar exists
        self.assertIsNotNone(at.sidebar, "Sidebar should exist")
        
        # Check for title (more flexible check)
        sidebar_content = str(at.sidebar)
        self.assertIn("Multiphoton", sidebar_content.lower(), 
                     "Sidebar should contain multiphoton-related content")
        
    @pytest.mark.slow
    def test_main_page_structure(self):
        """Test that the main page has expected structure."""
        at = AppTest.from_file("app.py")
        at.run()
        
        # Check that main content exists
        self.assertIsNotNone(at.main, "Main content should exist")
        
        # The app should have some content
        main_content = str(at.main)
        self.assertGreater(len(main_content), 0, "Main content should not be empty")
    
    @pytest.mark.slow
    def test_session_state_initialization(self):
        """Test that session state is properly initialized."""
        at = AppTest.from_file("app.py")
        at.run()
        
        # Check that key session state variables exist
        expected_keys = ["study_name", "wavelength", "researcher"]
        for key in expected_keys:
            self.assertIn(key, at.session_state, 
                         f"Session state should contain '{key}'")
    
    @patch('streamlit.error')
    @pytest.mark.slow
    def test_error_handling(self, mock_error):
        """Test that the app handles errors gracefully."""
        # This test would need to be expanded based on specific error scenarios
        # in your app
        at = AppTest.from_file("app.py")
        
        # Test with invalid session state
        at.session_state["wavelength"] = "invalid"
        at.run()
        
        # App should still run (error handling should prevent crashes)
        self.assertIsNone(at.exception, "App should handle invalid input gracefully")

@pytest.mark.skipif(not STREAMLIT_TESTING_AVAILABLE, 
                   reason="Streamlit testing framework not available")
@pytest.mark.streamlit
class TestAppPytest:
    """Pytest-style tests for the Streamlit application."""
    
    def test_app_import(self):
        """Test that app modules can be imported."""
        try:
            import app
            assert hasattr(app, 'main'), "App should have a main function"
        except ImportError as e:
            pytest.fail(f"Failed to import app module: {e}")
    
    def test_modules_import(self):
        """Test that required modules can be imported."""
        required_modules = [
            'modules.data_utils',
            'modules.ui_components',
            'modules.theme'
        ]
        
        for module_name in required_modules:
            try:
                __import__(module_name)
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")

if __name__ == "__main__":
    # Run both unittest and pytest
    unittest.main(verbosity=2, exit=False)
    if STREAMLIT_TESTING_AVAILABLE:
        pytest.main(["-v", __file__])
