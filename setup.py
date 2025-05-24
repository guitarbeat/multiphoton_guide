from setuptools import setup, find_packages
import os
import re

def get_version():
    # Assuming __init__.py is in the same directory as setup.py
    # and it's the correct one for the package's version.
    # If the package 'multiphoton_guide' has its __init__.py in a subdirectory,
    # this path needs to be adjusted (e.g., 'multiphoton_guide/__init__.py').
    # Based on the file listing, __init__.py is in the root.
    init_py_path = os.path.join(os.path.dirname(__file__), "__init__.py")
    with open(init_py_path, "r") as f:
        for line in f:
            match = re.search(r"^__version__\s*=\s*['"]([^'"]*)['"]", line)
            if match:
                return match.group(1)
    raise RuntimeError("Unable to find version string.")

setup(
    name="multiphoton_guide",
    version=get_version(), # Use the function here
    packages=find_packages(),
    install_requires=[
        "streamlit==1.31.0",
        "streamlit-nested-layout==0.1.1",
        "streamlit-pdf-viewer==0.0.23",
        "pandas==1.5.3",
        "numpy>=1.26.0",
        "matplotlib==3.7.0",
        "pillow==9.4.0",
        "scikit-learn==1.2.0",
    ],
    python_requires=">=3.8",
) 