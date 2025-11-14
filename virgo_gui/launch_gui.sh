#!/bin/bash
# Virgo GUI Launcher Script - Smart Python Finder

echo "Starting Virgo Radio Telescope GUI..."
echo ""

# Try to find Python with working Virgo installation
PYTHON=""

# Option 1: Try the alias Python
if [ -f "/usr/bin/python3" ]; then
    echo "Checking /usr/bin/python3..."
    if /usr/bin/python3 -c "import sys; sys.path.insert(0, '/home/user/Virgo'); from virgo import observe" 2>/dev/null; then
        PYTHON="/usr/bin/python3"
        echo "✓ Found working Virgo at /usr/bin/python3"
    fi
fi

# Option 2: Try python3 in PATH
if [ -z "$PYTHON" ]; then
    echo "Checking python3 in PATH..."
    if python3 -c "import sys; sys.path.insert(0, '/home/user/Virgo'); from virgo import observe" 2>/dev/null; then
        PYTHON="python3"
        echo "✓ Found working Virgo with python3"
    fi
fi

# Option 3: Try python in PATH
if [ -z "$PYTHON" ]; then
    if command -v python &> /dev/null; then
        echo "Checking python in PATH..."
        if python -c "import sys; sys.path.insert(0, '/home/user/Virgo'); from virgo import observe" 2>/dev/null; then
            PYTHON="python"
            echo "✓ Found working Virgo with python"
        fi
    fi
fi

# If still not found, error out
if [ -z "$PYTHON" ]; then
    echo "❌ Error: Could not find Python with working Virgo installation"
    echo ""
    echo "Please make sure Virgo is installed:"
    echo "  cd /home/user/Virgo"
    echo "  pip install -e ."
    echo ""
    echo "Or check your Python setup."
    exit 1
fi

echo "Using Python: $PYTHON"
$PYTHON --version
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set PYTHONPATH to include Virgo
export PYTHONPATH="/home/user/Virgo:$PYTHONPATH"

# Launch the GUI
cd "$SCRIPT_DIR"
$PYTHON virgo_gui.py

echo ""
echo "Virgo GUI closed."
