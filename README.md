# Multiphoton Microscopy Guide

A comprehensive application for standardized measurements, monitoring, and comparing multiphoton microscope systems.

## Quick Start

### Local Development (Recommended)

The easiest way to get started is using the provided setup script:

```bash
# Clone or download the repository
# Navigate to the project directory

# Run the setup script (handles everything automatically)
./setup.sh

# Or run with specific options:
./setup.sh setup    # Setup environment only
./setup.sh run      # Setup (if needed) and run application
./setup.sh help     # Show all options
```

The script will:
 - Check Python version (3.9+ required, 3.10 recommended; 3.9.7 not supported)
- Create a virtual environment
- Install all dependencies
- Launch the application

### Development Setup

For developers who want to contribute or run tests:

```bash
# Setup with development dependencies (testing, linting, etc.)
./setup.sh dev-setup

# Run tests
./setup.sh test

# Or run tests with coverage reporting
python tests/run_tests.py
```

**Development dependencies include:**
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `black` - Code formatting
- `flake8` - Code linting
- `isort` - Import sorting

**All dependencies are managed in `pyproject.toml`** for simplified project configuration.

### Manual Installation

If you prefer manual setup:

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -e .

# For development (optional)
pip install -e ".[dev]"

# Run the application
streamlit run app.py
```

## Dependency Management

**All dependencies are managed in `pyproject.toml`** for simplified project configuration.

### Local Development
- Production dependencies: `pip install -e .`
- Development dependencies: `pip install -e ".[dev]"`
- Building with `poetry build` produces a wheel containing both the
  `multiphoton_guide` and `modules` packages.

### Using Poetry
Poetry is an all-in-one tool for dependency management and packaging.  The
repository includes a `poetry.lock` file so you can recreate the exact
environment used during development.  If you prefer to use Poetry instead of the
`pip` commands above:

```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies and create a virtual environment
poetry install

# If you change dependencies in `pyproject.toml`, update the lock file
poetry lock --regenerate

# Run the Streamlit application
poetry run streamlit run app.py

# Build a distributable wheel
poetry build
```

Using Poetry is optional, but it provides reproducible installs and simplifies
publishing packages from the `pyproject.toml` configuration.

### For Deployment Platforms
Some platforms still require `requirements.txt`. Generate one if needed:

```bash
# Option 1: Using pip-tools (recommended)
pip install pip-tools
pip-compile pyproject.toml

# Option 2: Using our utility script
pip install tomli
python scripts/generate_requirements.py
```

**Benefits of pyproject.toml approach:**
- Single source of truth for all project metadata
- Modern Python packaging standard
- Optional dependency groups for development tools
- No need to maintain multiple requirements files

### Streamlit Community Cloud

This application is optimized for Streamlit Community Cloud deployment:

1. Push your code to a GitHub repository
2. Visit [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub and deploy

**Required files for Streamlit Cloud:**
- `packages.txt` - System dependencies  
 - `runtime.txt` - Python version (3.11 recommended; Python 3.9.7 is unsupported)

**Note:** Streamlit Cloud requires a `requirements.txt` file. If needed, generate one from pyproject.toml:
```bash
pip install pip-tools
pip-compile pyproject.toml
```

All dependencies are defined in `pyproject.toml` but can be exported to `requirements.txt` for deployment platforms that require it.

## Database Setup

Measurement data is stored in a public Google Sheet. Configure a
`[connections.gsheets]` section in `.streamlit/secrets.toml` as shown below and
the application will read and write data to that spreadsheet (see
`docs/public_google_sheets.md`). If the connection is not configured the
application will raise an error.

```toml
[connections.gsheets]
spreadsheet = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
```

Place these credentials in `.streamlit/secrets.toml` so the application can
establish the Google Sheets connection.

The app uses the
[`st-gsheets-connection`](https://pypi.org/project/st-gsheets-connection/)
package. Create the connection in your code with

```python
from streamlit_gsheets import GSheetsConnection
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(worksheet="Sheet1")
```

If the connection fails, the app will display an error in the sidebar.

### Docker Deployment

For containerized deployment:

```bash
# Build and run with Docker
docker build -t multiphoton-guide .
docker run -p 8501:8501 multiphoton-guide
```

Then visit http://localhost:8501

## System Requirements

- **Python**: 3.9+ (3.10 recommended; 3.9.7 not supported)
- **System Dependencies** (auto-installed on Streamlit Cloud/Docker):
  - libgl1, libglib2.0-0, poppler-utils
  - libgtk2.0-0, libx11-xcb1, libnss3

## Features

### Microscope Tools
- **Laser Power at the Sample**: Calculate and measure laser power delivery
- **Pulse Width Control**: Optimize temporal pulse characteristics
- **Fluorescence Signal Estimation**: Calculate expected signal levels

### Analysis Tools
- **USAF Target Analyzer**: Comprehensive analysis tool for USAF 1951 resolution targets
  - Automated line pair detection and measurement
  - Pixel size calibration from known targets
  - Image processing with contrast enhancement
  - ROI selection and rotation capabilities
  - Export analysis results to CSV

### Documentation
- **Rig Log**: Track maintenance, calibration, and modifications
- **Reference**: View standardized measurement procedures

## Contributing

1. Fork the repository
2. Set up development environment: `./setup.sh dev-setup`
3. Run tests to ensure everything works: `./setup.sh test`
4. Make your changes
5. Run tests again to ensure nothing breaks
6. Submit a pull request

## Troubleshooting

### Local Development Issues
- Ensure Python 3.9+ is installed (except 3.9.7)
- Use the provided `./setup.sh` script for automated setup
- Try manual installation if the script fails

### Streamlit Cloud Issues
- Check build logs for specific errors
- All dependencies are in `pyproject.toml` (generate `requirements.txt` if needed)
- System dependencies should be in `packages.txt`
- Python version is specified in `runtime.txt`

### Common Solutions
- Update pip: `pip install --upgrade pip`
- Clear cache: Delete `venv` folder and re-run setup
- Check Python version: `python3 --version`

## License

[Your license information here]

## Testing

The project includes a comprehensive test suite:

```bash
# Quick test run
./setup.sh test

# Detailed test run with coverage
python tests/run_tests.py

# Run specific test files
pytest tests/test_data_utils.py -v
pytest tests/test_integration.py -v
```

**Test Coverage:**
- Unit tests for data utilities
- Integration tests for module imports
- Streamlit app testing
- End-to-end workflow testing

## Deployment Options

### Streamlit Community Cloud

Deploying this project on Streamlit Community Cloud is straightforward:

1. Ensure `packages.txt` lists any required system packages and `runtime.txt` specifies the Python version.
2. If your deployment platform requires a `requirements.txt` file, generate it from `pyproject.toml` using:
   ```bash
   pip install pip-tools
   pip-compile pyproject.toml
   ```
3. Push the repository to GitHub.
4. Visit [share.streamlit.io](https://share.streamlit.io) and sign in with your GitHub account.
5. Select this repository, choose `app.py` as the entry point, and click **Deploy**.

Streamlit Cloud will build the environment, install dependencies, and host the app automatically.
