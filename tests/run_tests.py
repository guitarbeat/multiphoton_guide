#!/usr/bin/env python3
"""
Test runner for the Multiphoton Microscopy Guide application.
Runs all tests with proper configuration and reporting.
"""

import pytest
import sys
from pathlib import Path

def main():
    """Run all tests with appropriate configuration."""
    
    # Add parent directory to path
    parent_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(parent_dir))
    
    print("🧪 Running Multiphoton Microscopy Guide Test Suite\n")
    
    # Parse command line arguments for test selection
    test_type = sys.argv[1] if len(sys.argv) > 1 else "fast"
    
    # Configure pytest arguments based on test type
    if test_type == "all":
        print("🔍 Running ALL tests (including slow Streamlit tests)")
        pytest_args = [
            "-v",
            "--tb=short", 
            "--strict-markers",
            str(Path(__file__).parent),
        ]
    elif test_type == "streamlit":
        print("🔍 Running only Streamlit tests")
        pytest_args = [
            "-v",
            "--tb=short",
            "--strict-markers", 
            "-m", "streamlit",
            str(Path(__file__).parent),
        ]
    elif test_type == "unit":
        print("🔍 Running only unit tests")
        pytest_args = [
            "-v",
            "--tb=short",
            "--strict-markers",
            "-m", "unit",
            str(Path(__file__).parent),
        ]
    elif test_type == "integration":
        print("🔍 Running only integration tests")
        pytest_args = [
            "-v",
            "--tb=short",
            "--strict-markers",
            "-m", "integration", 
            str(Path(__file__).parent),
        ]
    else:  # fast (default)
        print("🔍 Running fast tests (excluding slow Streamlit tests)")
        pytest_args = [
            "-v",
            "--tb=short",
            "--strict-markers",
            "-m", "not slow",
            str(Path(__file__).parent),
        ]
    
    # Add coverage if available
    try:
        pytest_args.extend([
            "--cov=modules",
            "--cov-report=term-missing",
            "--cov-report=html:tests/coverage_html"
        ])
        print("📊 Coverage reporting enabled")
    except ImportError:
        print("ℹ️  Install pytest-cov for coverage reporting: pip install pytest-cov")
    
    print(f"🔍 Running tests from: {Path(__file__).parent}")
    print("-" * 50)
    
    # Run tests
    exit_code = pytest.main(pytest_args)
    
    print("\n" + "=" * 50)
    if exit_code == 0:
        print("🎉 All tests passed!")
        print("\nTo run the application:")
        print("  ./setup.sh run")
        print("\nOther test options:")
        print("  python tests/run_tests.py fast        # Fast tests (default)")
        print("  python tests/run_tests.py unit        # Unit tests only") 
        print("  python tests/run_tests.py integration # Integration tests only")
        print("  python tests/run_tests.py all         # All tests (including slow)")
        print("  python tests/run_tests.py streamlit   # Streamlit tests only")
    else:
        print("❌ Some tests failed.")
        print("Check the output above for details.")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main()) 