# Multiphoton Microscopy Guide

An interactive application for standardized measurements and protocols in multiphoton microscopy.

## Overview

This application provides interactive guides, data collection tools, and visualizations for key multiphoton microscopy protocols based on the Nature Protocols article by Lees et al. (2024). It helps researchers maintain consistent microscope performance and ensure reproducible results.

## Features

- **Laser Power Measurement**: Tools for measuring and monitoring laser power at the sample
- **Pulse Width Optimization**: Interactive GDD optimization for maximum signal
- **Fluorescence Signal Estimation**: Convert arbitrary units to absolute photon counts
- **System Change Log**: Track all microscope modifications and maintenance
- **Reference Materials**: Access to protocol documentation and guides

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
streamlit run app.py
```

## Project Structure

```
multiphoton_guide/
├── app.py                  # Main application entry point
├── README.md               # This file
├── requirements.txt        # Dependencies
├── data/                   # Data storage directory
│   ├── laser_power_measurements.csv
│   ├── pulse_width_measurements.csv
│   ├── fluorescence_measurements.csv
│   └── rig_log.csv
├── modules/                # Modular components
│   ├── __init__.py
│   ├── theme.py            # Theme configuration
│   ├── data_utils.py       # Data handling utilities
│   ├── ui_components.py    # Reusable UI elements
│   ├── laser_power.py      # Laser power measurement module
│   ├── pulse_width.py      # Pulse width optimization module
│   ├── fluorescence.py     # Fluorescence signal estimation module
│   ├── rig_log.py          # System change log module
│   └── reference.py        # Protocol reference module
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── test_app.py         # Main application tests
│   └── test_data_utils.py  # Data utilities tests
└── assets/                 # Static assets
    └── s41596-024-01120-w.pdf  # Reference protocol document
```

## Usage

1. Set your study parameters in the sidebar
2. Navigate between tabs to access different protocols
3. Record measurements using the interactive tables
4. Save your data using the form submit buttons
5. Track all system changes in the Rig Log tab
6. Access reference materials in the Reference tab

## Testing

Run the test suite to verify application functionality:

```bash
pytest tests/
```

## Dependencies

- streamlit
- streamlit-pdf-viewer
- streamlit-nested-layout
- pandas
- matplotlib
- numpy
- scikit-learn

## Citation

This application is based on protocols from:

Lees, R.M., Bianco, I.H., Campbell, R.A.A. et al. Standardized measurements for monitoring and comparing multiphoton microscope systems. Nat Protoc (2024). https://doi.org/10.1038/s41596-024-01120-w

## License

MIT License
