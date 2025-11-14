# Virgo GUI Installation Guide

## Quick Installation (Ubuntu/Debian)

Run these commands in order:

```bash
# 1. Update package list
sudo apt-get update

# 2. Install system packages
sudo apt-get install -y python3 python3-tk python3-pip

# 3. Install Python dependencies
cd /home/user/Virgo
pip3 install -r gui-requirements.txt

# 4. Install Virgo (if not already installed)
pip3 install -e .

# 5. Launch the GUI
./launch_gui.sh
```

## Detailed Installation Steps

### Step 1: System Packages

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install python3 python3-tk python3-pip
```

**Fedora:**
```bash
sudo dnf install python3 python3-tkinter python3-pip
```

**Arch Linux:**
```bash
sudo pacman -S python python-pip tk
```

### Step 2: Python Dependencies

```bash
cd /home/user/Virgo
pip3 install -r gui-requirements.txt
```

Or install individually:
```bash
pip3 install numpy matplotlib astropy pillow
```

### Step 3: Virgo Installation

If Virgo is not already installed:

```bash
cd /home/user/Virgo
pip3 install -e .
```

### Step 4: SDR Hardware Support (Optional)

For actual radio observations, you'll need SDR hardware and drivers.

**GNU Radio and gr-osmosdr:**
```bash
sudo apt-get install gnuradio gr-osmosdr
```

**RTL-SDR Support:**
```bash
sudo apt-get install rtl-sdr
```

**HackRF Support:**
```bash
sudo apt-get install hackrf
```

**USRP Support:**
```bash
sudo apt-get install libuhd-dev uhd-host
```

### Step 5: Permissions (RTL-SDR)

To use RTL-SDR without sudo:

```bash
# Create udev rule
sudo bash -c 'cat > /etc/udev/rules.d/20-rtlsdr.rules << EOF
SUBSYSTEM=="usb", ATTRS{idVendor}=="0bda", ATTRS{idProduct}=="2838", GROUP="plugdev", MODE="0666"
EOF'

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Add user to plugdev group
sudo usermod -a -G plugdev $USER

# Log out and log back in for group changes to take effect
```

## Running the GUI

### Method 1: Launch Script

```bash
cd /home/user/Virgo
./launch_gui.sh
```

### Method 2: Direct Python

```bash
cd /home/user/Virgo
python3 virgo_gui.py
```

### Method 3: Desktop Launcher

1. Copy the desktop file to your applications directory:
   ```bash
   mkdir -p ~/.local/share/applications
   cp /home/user/Virgo/virgo-gui.desktop ~/.local/share/applications/
   ```

2. Update desktop database:
   ```bash
   update-desktop-database ~/.local/share/applications
   ```

3. Launch from your application menu (search for "Virgo")

## Troubleshooting

### "No module named 'tkinter'"

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-tk
```

**Fedora:**
```bash
sudo dnf install python3-tkinter
```

### "ModuleNotFoundError: No module named 'matplotlib'"

```bash
pip3 install matplotlib
```

### "ModuleNotFoundError: No module named 'virgo'"

```bash
cd /home/user/Virgo
pip3 install -e .
```

### GUI opens but observation fails

1. **Check SDR connection:**
   ```bash
   lsusb | grep -i rtl  # For RTL-SDR
   ```

2. **Test RTL-SDR:**
   ```bash
   rtl_test -t
   ```

3. **Check permissions:**
   ```bash
   ls -l /dev/bus/usb/XXX/YYY
   ```
   Should show read/write permissions

### Display issues on Wayland

If you're using Wayland and experience display issues:

```bash
# Run with X11 backend
GDK_BACKEND=x11 python3 virgo_gui.py
```

### High DPI displays

If GUI elements are too small:

```bash
# Set scaling factor
export GDK_SCALE=2
python3 virgo_gui.py
```

## Verify Installation

Run this test to verify all components:

```bash
cd /home/user/Virgo
python3 -c "
import tkinter as tk
import matplotlib
import numpy
import virgo
print('✓ All dependencies installed correctly!')
print('✓ Virgo GUI is ready to use')
"
```

If this runs without errors, you're all set!

## Next Steps

1. Read `GUI_README.md` for usage instructions
2. Connect your SDR hardware
3. Launch the GUI: `./launch_gui.sh`
4. Try the HI Line preset for your first observation

## Getting Help

- **Documentation**: `GUI_README.md`
- **Virgo Docs**: https://virgo.readthedocs.io
- **Issues**: https://github.com/0xCoto/Virgo/issues

Happy observing! 🔭
