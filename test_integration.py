#!/usr/bin/env python3
"""
Test script to verify USAF Target Analyzer integration with the main app.
"""

import sys
import traceback


def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")

    try:
        # Test main app imports
        from app import main
        print("✅ Main app import successful")

        # Test USAF analyzer imports
        from modules.usaf_analyzer import run_usaf_analyzer
        print("✅ USAF analyzer import successful")

        # Test page imports
        from modules.pages.usaf_analyzer_page import usaf_analyzer_page
        print("✅ USAF analyzer page import successful")

        # Test that the page function is callable
        if callable(usaf_analyzer_page):
            print("✅ USAF analyzer page function is callable")
        else:
            print("❌ USAF analyzer page function is not callable")
            return False

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        traceback.print_exc()
        return False


def test_dependencies():
    """Test that required dependencies are available."""
    print("\nTesting dependencies...")

    required_packages = [
        'streamlit',
        'numpy',
        'pandas',
        'matplotlib',
        'PIL',
        'cv2',
        'tifffile',
        'skimage',
        'streamlit_image_coordinates',
        'streamlit_nested_layout'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            if package == 'PIL':
                import PIL
            elif package == 'cv2':
                import cv2
            else:
                __import__(package)
            print(f"✅ {package} available")
        except ImportError:
            print(f"❌ {package} missing")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install -r requirements.txt")
        return False

    return True


def main():
    """Run all tests."""
    print("🧪 Testing USAF Target Analyzer Integration\n")

    # Test imports
    imports_ok = test_imports()

    # Test dependencies
    deps_ok = test_dependencies()

    # Summary
    print("\n" + "="*50)
    if imports_ok and deps_ok:
        print("🎉 All tests passed! Integration should work correctly.")
        print("\nTo run the app:")
        print("  streamlit run app.py")
        print("\nThen navigate to 'Analysis Tools' > 'USAF Target Analyzer'")
        return 0
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
