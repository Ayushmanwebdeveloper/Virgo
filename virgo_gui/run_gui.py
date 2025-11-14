#!/usr/bin/python3
"""
Virgo GUI - Quick launcher that uses system Python
This ensures gnuradio is available
"""

import sys
import os

# Ensure we're using system Python with gnuradio
if sys.executable != '/usr/bin/python3':
    print(f"Warning: Running with {sys.executable} instead of /usr/bin/python3")
    print("Switching to system Python for gnuradio compatibility...")
    os.execv('/usr/bin/python3', ['/usr/bin/python3'] + sys.argv)

# Add Virgo to path if not already there
virgo_path = '/home/user/Virgo'
if virgo_path not in sys.path:
    sys.path.insert(0, virgo_path)

# Now run the actual GUI
import virgo_gui

if __name__ == "__main__":
    virgo_gui.main()
