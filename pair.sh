#!/bin/bash
# Razer Nari Pairing Tool - Quick Runner
# This script handles the Python environment and runs with sudo

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_CMD="python3"

# Check if PyUSB is installed
if ! $PYTHON_CMD -c "import usb.core" 2>/dev/null; then
    echo "Error: PyUSB not installed"
    echo "Please install with: pip install pyusb"
    echo "Or run: pip install -r requirements.txt"
    exit 1
fi

# Check for sudo
if [ "$EUID" -ne 0 ]; then
    echo "This tool requires root privileges"
    echo "Running with sudo..."
    echo
    # Preserve PYTHONPATH for user-installed packages
    PYTHONPATH="${PYTHONPATH}" exec sudo -E "$PYTHON_CMD" "$SCRIPT_DIR/razer_nari_pair.py" "$@"
else
    exec "$PYTHON_CMD" "$SCRIPT_DIR/razer_nari_pair.py" "$@"
fi
