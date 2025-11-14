#!/bin/bash
# Virgo GUI Launcher Script

echo "Starting Virgo Radio Telescope GUI..."
echo ""

# Use system Python3 (same as Virgo command-line)
PYTHON="/usr/bin/python3"

# Check if Python 3 is available
if [ ! -f "$PYTHON" ]; then
    echo "Error: System Python 3 not found at $PYTHON"
    echo "Trying alternative python3..."
    PYTHON=$(which python3)
    if [ -z "$PYTHON" ]; then
        echo "Error: Python 3 is not installed"
        exit 1
    fi
fi

echo "Using Python: $PYTHON"
$PYTHON --version

# Check if required packages are available
$PYTHON -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Error: tkinter is not installed"
    echo "Install with: sudo apt-get install python3-tk"
    exit 1
fi

$PYTHON -c "import matplotlib" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Error: matplotlib is not installed"
    echo "Install with: sudo apt-get install matplotlib"
    exit 1
fi

$PYTHON -c "import gnuradio" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Warning: gnuradio not found in system Python"
    echo "Observations will fail without GNU Radio installed"
    echo "Install with: sudo apt-get install gnuradio"
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Launch the GUI with system Python
cd "$SCRIPT_DIR"
$PYTHON virgo_gui.py

echo ""
echo "Virgo GUI closed."
