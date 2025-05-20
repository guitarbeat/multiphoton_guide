# Multiphoton Microscopy Guide

A comprehensive application for standardized measurements, monitoring, and comparing multiphoton microscope systems.

## Installation Options

### Option 1: Using the Setup Script (Recommended for Local Development)

The easiest way to install locally is using the provided setup script:

```bash
# Make the script executable
chmod +x setup.sh

# Run the setup script
./setup.sh

# Run the application
source venv/bin/activate
streamlit run app.py
```

### Option 2: Manual Installation

If you prefer to install manually:

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

### Option 3: Using Docker

If you have Docker installed, you can build and run the application in a container:

```bash
# Build the Docker image
docker build -t multiphoton-guide .

# Run the container
docker run -p 8501:8501 multiphoton-guide
```

Then visit http://localhost:8501 in your web browser.

### Option 4: Deploying to Streamlit Community Cloud

To deploy this application on Streamlit Community Cloud:

1. Push your code to a GitHub repository
2. Visit [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub
4. Click "New app" and select your repository
5. Choose the branch and main file path (app.py)
6. Click "Deploy"

The application includes the necessary configuration files:
- `requirements.txt` - Python dependencies
- `packages.txt` - System dependencies
- `.streamlit/config.toml` - Streamlit configuration
- `runtime.txt` - Python version specification

## System Requirements

- Python 3.8 or newer (Python 3.10 recommended)
- System dependencies (automatically installed with Docker or Streamlit Cloud):
  - libgl1
  - libglib2.0-0
  - poppler-utils
  - libgtk2.0-0
  - libx11-xcb1
  - libnss3

## Troubleshooting

If you encounter installation issues:

1. Make sure you're using Python 3.8 or newer
2. Try using a virtual environment
3. Update pip before installing requirements: `pip install --upgrade pip`
4. If specific packages fail, try installing them individually
5. Consider using the Docker option which handles all dependencies

### Streamlit Cloud Deployment Issues

If you encounter issues deploying to Streamlit Cloud:

1. Check the build logs for specific error messages
2. Ensure all dependencies are properly listed in requirements.txt
3. Make sure system dependencies are listed in packages.txt
4. Try specifying an older Python version in runtime.txt if compatibility issues arise
5. Consider removing or simplifying complex dependencies

## Features

- Microscope Log: Track maintenance, calibration, and modifications
- Protocol Reference: View standardized measurement procedures
- Fluorescence Signal Estimation: Calculate expected signal levels
- And more...

## License

[Your license information here]
