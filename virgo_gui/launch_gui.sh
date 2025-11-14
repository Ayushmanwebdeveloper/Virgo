#!/bin/bash
# Virgo GUI Launcher Script

echo "Starting Virgo Radio Telescope GUI..."
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if required packages are available
python3 -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Error: tkinter is not installed"
    echo "Install with: sudo apt-get install python3-tk"
    exit 1
fi

python3 -c "import matplotlib" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Error: matplotlib is not installed"
    echo "Install with: pip3 install matplotlib"
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Launch the GUI
cd "$SCRIPT_DIR"
python3 virgo_gui.py

echo ""
echo "Virgo GUI closed."
