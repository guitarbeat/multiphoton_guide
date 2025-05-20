from setuptools import setup, find_packages

setup(
    name="multiphoton_guide",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "streamlit==1.31.0",
        "streamlit-nested-layout==0.1.1",
        "streamlit-pdf-viewer==0.0.23",
        "pandas==1.5.3",
        "numpy==1.24.3",
        "matplotlib==3.7.0",
        "pillow==9.4.0",
        "scikit-learn==1.2.0",
    ],
    python_requires=">=3.8",
) 