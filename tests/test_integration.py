#!/usr/bin/env python3
"""
Integration tests for the Multiphoton Microscopy Guide application.
Tests that all components work together correctly.
"""

import importlib
import os
import sys
from pathlib import Path

import pytest

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.mark.integration
class TestImports:
    """Test that all required modules can be imported successfully."""

    def test_main_app_import(self):
        """Test that the main app module imports correctly."""
        try:
            import app

            assert hasattr(app, "main"), "App should have a main function"
        except ImportError as e:
            pytest.fail(f"Failed to import main app: {e}")

    def test_core_modules_import(self):
        """Test that core modules import correctly."""
        core_modules = [
            "modules.core.data_utils",
            "modules.ui.components",
            "modules.ui.theme",
        ]

        for module_name in core_modules:
            try:
                module = importlib.import_module(module_name)
                assert module is not None, f"{module_name} should not be None"
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")

    def test_page_modules_import(self):
        """Test that page modules import correctly."""
        page_modules = [
            "modules.measurements.laser_power",
            "modules.measurements.pulse_width",
            "modules.measurements.fluorescence",
            "modules.measurements.rig_log",
        ]

        for module_name in page_modules:
            try:
                module = importlib.import_module(module_name)
                assert module is not None, f"{module_name} should not be None"
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")

    def test_analyzer_modules_import(self):
        """Test that analyzer modules import correctly."""
        try:
            from modules.analysis.usaf_analyzer import run_usaf_analyzer

            assert callable(run_usaf_analyzer), "run_usaf_analyzer should be callable"
        except ImportError as e:
            pytest.fail(f"Failed to import USAF analyzer: {e}")


@pytest.mark.integration
class TestDependencies:
    """Test that all required dependencies are available."""

    @pytest.mark.parametrize(
        "package_name,import_name",
        [
            ("streamlit", "streamlit"),
            ("numpy", "numpy"),
            ("pandas", "pandas"),
            ("matplotlib", "matplotlib"),
            ("PIL", "PIL"),
            ("opencv-python", "cv2"),
            ("tifffile", "tifffile"),
            ("scikit-image", "skimage"),
            ("streamlit-image-coordinates", "streamlit_image_coordinates"),
            ("streamlit-nested-layout", "streamlit_nested_layout"),
        ],
    )
    def test_required_package_available(self, package_name, import_name):
        """Test that each required package can be imported."""
        try:
            __import__(import_name)
        except ImportError:
            pytest.fail(
                f"Required package '{package_name}' (import as '{import_name}') is not available"
            )


@pytest.mark.integration
class TestFileStructure:
    """Test that required files and directories exist."""

    def test_main_files_exist(self):
        """Test that main application files exist."""
        required_files = ["app.py", "pyproject.toml", "setup.sh"]

        for filename in required_files:
            assert Path(filename).exists(), f"Required file '{filename}' does not exist"

    def test_modules_directory_exists(self):
        """Test that modules directory and key files exist."""
        modules_dir = Path("modules")
        assert modules_dir.exists(), "modules directory should exist"
        assert modules_dir.is_dir(), "modules should be a directory"

        # Check for key module files
        key_modules = [
            "modules/__init__.py",
            "modules/core/data_utils.py",
            "modules/ui/components.py",
            "modules/ui/theme.py",
        ]

        for module_file in key_modules:
            assert Path(
                module_file
            ).exists(), f"Key module file '{module_file}' should exist"

    def test_data_directory_creation(self):
        """Test that data directory can be created."""
        from modules.core.data_utils import ensure_data_dir

        # This should not raise an exception
        try:
            ensure_data_dir()
        except Exception as e:
            pytest.fail(f"Failed to ensure data directory: {e}")


@pytest.mark.integration
class TestModuleFunctionality:
    """Test that key module functions work correctly."""

    def test_data_utils_functions(self):
        """Test that data utilities functions are working."""
        import pandas as pd

        from modules.core.data_utils import ensure_columns, safe_numeric_conversion

        # Test ensure_columns
        test_df = pd.DataFrame({"A": [1, 2, 3]})
        result = ensure_columns(test_df, ["A", "B"], {"B": "default"})
        assert "B" in result.columns, "ensure_columns should add missing columns"
        assert result["B"].iloc[0] == "default", "Should use default value"

        # Test safe_numeric_conversion
        test_df = pd.DataFrame({"nums": ["1", "2", "3"]})
        result = safe_numeric_conversion(test_df, ["nums"])
        assert result["nums"].dtype.kind in "iuf", "Should convert to numeric type"

    def test_ui_components_functions(self):
        """Test that UI components can be imported and are callable."""
        from modules.ui.components import create_header, create_info_box

        assert callable(create_header), "create_header should be callable"
        assert callable(create_info_box), "create_info_box should be callable"

    def test_theme_functions(self):
        """Test that theme functions work correctly."""
        from modules.ui.theme import apply_theme, get_colors

        assert callable(get_colors), "get_colors should be callable"
        assert callable(apply_theme), "apply_theme should be callable"

        # Test that get_colors returns a dictionary
        colors = get_colors()
        assert isinstance(colors, dict), "get_colors should return a dictionary"


@pytest.mark.integration
class TestEndToEndWorkflow:
    """Test end-to-end workflows to ensure integration works."""

    def test_data_workflow(self):
        """Test a complete data workflow using the DB utilities."""
        
        import pandas as pd
        from sqlalchemy import create_engine

        from modules.core.data_utils import load_dataframe, save_dataframe
        from modules.core import database_utils

        # Create test data
        test_data = pd.DataFrame(
            {
                "Study Name": ["Test Study"],
                "Wavelength (nm)": [920],
                "Power (mW)": [10.5],
            }
        )

        engine = create_engine("sqlite:///:memory:")
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(database_utils, "get_connection", lambda url=None: engine)
        monkeypatch.setattr(database_utils, "get_gsheets_connection", lambda: None)

        table_name = "workflow_table"

        # Save data
        save_dataframe(test_data, table_name)

        # Load data back
        loaded_data = load_dataframe(table_name)

        # Verify data integrity
        assert len(loaded_data) == len(test_data), "Loaded data should have same length"
        assert list(loaded_data.columns) == list(test_data.columns), "Columns should match"
        
        monkeypatch.undo()


if __name__ == "__main__":
    # Run with pytest
    pytest.main(["-v", __file__])
