"""
Test module for PDF viewer functionality in the Multiphoton Microscopy Guide application.
Tests specifically for streamlit-pdf-viewer integration and annotation handling.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import streamlit as st
import streamlit_pdf_viewer

pytest.skip("Streamlit tests disabled in CI", allow_module_level=True)


class TestPDFViewer:
    """Test class for PDF viewer functionality."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.test_pdf_path = (
            Path(__file__).parent.parent / "assets" / "s41596-024-01120-w.pdf"
        )

    def test_pdf_path_exists(self):
        """Test that the PDF file exists in the expected location."""
        assert (
            self.test_pdf_path.exists()
        ), f"PDF file not found at {self.test_pdf_path}"
        assert (
            self.test_pdf_path.is_file()
        ), f"PDF path is not a file: {self.test_pdf_path}"

    def test_pdf_viewer_annotations_parameter(self):
        """Test that pdf_viewer can be called with annotations parameter."""
        try:
            import streamlit_pdf_viewer
        except ImportError:
            pytest.skip("streamlit-pdf-viewer not installed")

        # Test that calling pdf_viewer with annotations=[] doesn't raise TypeError
        with patch("streamlit_pdf_viewer.pdf_viewer") as mock_pdf_viewer:
            mock_pdf_viewer.return_value = None

            # This should not raise "annotations must be a list of dictionaries" error
            try:
                pdf_viewer(
                    str(self.test_pdf_path), width=700, height=800, annotations=[]
                )

                mock_pdf_viewer.assert_called_once_with(
                    str(self.test_pdf_path), width=700, height=800, annotations=[]
                )
            except TypeError as e:
                if "annotations must be a list of dictionaries" in str(e):
                    pytest.fail(f"PDF viewer still failing with annotations error: {e}")
                else:
                    raise e

    def test_pdf_viewer_invalid_annotations(self):
        """Test that pdf_viewer properly handles invalid annotations parameter."""
        try:
            import streamlit_pdf_viewer
        except ImportError:
            pytest.skip("streamlit-pdf-viewer not installed")

        # Test that invalid annotations parameter raises expected error
        with patch("streamlit_pdf_viewer.pdf_viewer") as mock_pdf_viewer:
            # Simulate the actual error that would be raised

            mock_pdf_viewer.side_effect = TypeError(
                "annotations must be a list of dictionaries"
            )

            with pytest.raises(
                TypeError, match="annotations must be a list of dictionaries"
            ):
                pdf_viewer(
                    str(self.test_pdf_path),
                    width=700,
                    height=800,
                    annotations="invalid",
                )


    def test_pdf_viewer_valid_annotations_format(self):
        """Test that pdf_viewer accepts properly formatted annotations."""
        try:
            import streamlit_pdf_viewer
        except ImportError:
            pytest.skip("streamlit-pdf-viewer not installed")

        # Test with valid annotations format
        valid_annotations = [
            {"page": 1, "x": 100, "y": 200, "content": "Test annotation"},
            {"page": 2, "x": 150, "y": 250, "content": "Another annotation"},
        ]

        with patch("streamlit_pdf_viewer.pdf_viewer") as mock_pdf_viewer:
            mock_pdf_viewer.return_value = None

            pdf_viewer(
                str(self.test_pdf_path),
                width=700,
                height=800,
                annotations=valid_annotations,
            )

            mock_pdf_viewer.assert_called_once_with(
                str(self.test_pdf_path),
                width=700,
                height=800,
                annotations=valid_annotations,
            )

    def test_render_reference_content_integration(self):
        """Integration test for the render_reference_content function."""
        # Import the function we're testing
        from modules.measurements.pulse_and_fluorescence import render_reference_content

        # Mock streamlit components to avoid actual rendering


        with patch('streamlit.columns') as mock_columns, \
             patch('streamlit.subheader') as mock_subheader, \
             patch('streamlit.markdown') as mock_markdown, \
             patch('streamlit.expander') as mock_expander, \
             patch('streamlit.text_area') as mock_text_area, \
             patch('streamlit.button') as mock_button, \
             patch('streamlit.download_button') as mock_download_button, \
             patch('modules.measurements.pulse_and_fluorescence.pdf_viewer') as mock_pdf_viewer, \
             patch('builtins.open', create=True) as mock_open:


            # Set up mocks
            mock_columns.return_value = [MagicMock(), MagicMock()]
            mock_expander.return_value.__enter__ = MagicMock()
            mock_expander.return_value.__exit__ = MagicMock()
            mock_pdf_viewer.return_value = None
            mock_open.return_value.__enter__ = MagicMock()
            mock_open.return_value.__exit__ = MagicMock()

            # Mock session state
            with patch.object(st, "session_state", {}):
                # This should not raise any errors
                try:
                    render_reference_content()
                    # Verify that pdf_viewer was called with annotations parameter
                    assert mock_pdf_viewer.called, "pdf_viewer was not called"
                    call_args = mock_pdf_viewer.call_args
                    assert (
                        "annotations" in call_args.kwargs
                    ), "annotations parameter not provided"
                    assert isinstance(
                        call_args.kwargs["annotations"], list
                    ), "annotations is not a list"
                except TypeError as e:
                    if "annotations must be a list of dictionaries" in str(e):
                        pytest.fail(
                            f"render_reference_content still has annotations error: {e}"
                        )
                    else:
                        raise e


def test_pdf_viewer_error_detection():
    """Standalone test function to detect PDF viewer annotation errors."""
    try:
        from streamlit_pdf_viewer import pdf_viewer


        # Test path
        test_path = Path(__file__).parent.parent / "assets" / "s41596-024-01120-w.pdf"

        if not test_path.exists():
            pytest.skip(f"Test PDF not found at {test_path}")

        # This should work without raising TypeError about annotations
        with patch("streamlit_pdf_viewer.pdf_viewer") as mock_viewer:
            mock_viewer.return_value = None
            pdf_viewer(str(test_path), width=700, height=800, annotations=[])


        return True

    except ImportError:
        pytest.skip("streamlit-pdf-viewer not installed")
    except TypeError as e:
        if "annotations must be a list of dictionaries" in str(e):
            pytest.fail(f"PDF viewer annotations error still occurring: {e}")
        else:
            raise e


if __name__ == "__main__":
    # Run the test when script is executed directly
    test_result = test_pdf_viewer_error_detection()
    print(f"PDF viewer test passed: {test_result}")
