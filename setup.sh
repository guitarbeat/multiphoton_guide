#!/bin/bash

# Multiphoton Guide - Setup and Startup Script
# This script handles all setup and provides options to run the application

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if we're in a virtual environment
check_venv() {
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        return 0  # In virtual environment
    else
        return 1  # Not in virtual environment
    fi
}

# Function to setup the environment
setup_environment() {
    local install_dev=${1:-false}
    
    print_status "Setting up Multiphoton Guide application..."

    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.8 or newer."
        exit 1
    fi

    # Check Python version
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        print_error "Python 3.8 or newer is required. Found Python $PYTHON_VERSION"
        exit 1
    fi

    print_success "Using Python $PYTHON_VERSION"

    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    else
        print_status "Virtual environment already exists"
    fi

    # Activate virtual environment
    print_status "Activating virtual environment..."
    source venv/bin/activate

    # Upgrade pip
    print_status "Upgrading pip..."
    pip install --upgrade pip

    # Install dependencies from pyproject.toml
    if [ "$install_dev" = true ]; then
        print_status "Installing application with development dependencies..."
        pip install -e ".[dev]"
        print_success "Development dependencies installed (pytest, coverage tools, etc.)"
    else
        print_status "Installing application dependencies..."
        pip install -e .
    fi

    print_success "Environment setup complete!"
}

# Function to run the application
run_application() {
    if ! check_venv; then
        print_status "Activating virtual environment..."
        source venv/bin/activate
    fi
    
    print_status "Starting Multiphoton Guide application..."
    print_status "The application will open in your default web browser"
    print_status "Press Ctrl+C to stop the application"
    echo ""
    
    streamlit run app.py
}

# Function to show usage
show_usage() {
    echo "Multiphoton Guide - Setup and Startup Script"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  setup, -s, --setup         Setup the environment (install dependencies)"
    echo "  dev-setup, --dev           Setup with development dependencies (testing, linting)"
    echo "  run, -r, --run             Run the application (setup if needed)"
    echo "  test, -t, --test           Run the test suite"
    echo "  help, -h, --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup                   # Setup environment only"
    echo "  $0 dev-setup               # Setup with development tools"
    echo "  $0 run                     # Setup (if needed) and run application"
    echo "  $0 test                    # Run tests (requires dev setup)"
    echo "  $0                         # Same as 'run' (default behavior)"
}

# Function to run tests
run_tests() {
    if ! check_venv; then
        print_status "Activating virtual environment..."
        source venv/bin/activate
    fi
    
    # Check if pytest is available
    if ! command -v pytest &> /dev/null; then
        print_warning "pytest not found. Installing development dependencies..."
        setup_environment true
    fi
    
    print_status "Running test suite..."
    
    if [ -f "tests/run_tests.py" ]; then
        python tests/run_tests.py
    else
        print_status "Using basic pytest runner..."
        pytest tests/ -v
    fi
}

# Main logic
case "${1:-run}" in
    "setup"|"-s"|"--setup")
        setup_environment false
        echo ""
        print_success "Setup complete! Run the application with:"
        echo "  $0 run"
        echo "or"
        echo "  source venv/bin/activate && streamlit run app.py"
        ;;
    "dev-setup"|"--dev")
        setup_environment true
        echo ""
        print_success "Development setup complete! You can now:"
        echo "  $0 run                    # Run the application"
        echo "  $0 test                   # Run tests"
        echo "  python tests/run_tests.py # Run tests with coverage"
        echo ""
        print_status "All dependencies are managed in pyproject.toml"
        ;;
    "run"|"-r"|"--run")
        # Check if venv exists, if not, run setup first
        if [ ! -d "venv" ]; then
            print_warning "Virtual environment not found. Running setup first..."
            setup_environment false
            echo ""
        fi
        run_application
        ;;
    "test"|"-t"|"--test")
        run_tests
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        print_error "Unknown option: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac 