# Virgo Radio Telescope GUI

**A comprehensive graphical interface for the Virgo spectrometer and radiometer**

Version 2.0 Enhanced - 100% Feature Complete

---

## Quick Download & Install

### What's in This Folder

All GUI files are contained here - just download this entire `virgo_gui/` folder!

**Files included:**
- `virgo_gui.py` - Main GUI application (71KB)
- `launch_gui.sh` - Launcher script
- `virgo-gui.desktop` - Desktop launcher
- `requirements.txt` - Python dependencies
- **Documentation** (5 guides):
  - `USER_GUIDE.md` - Complete manual
  - `INSTALL.md` - Installation instructions
  - `QUICKSTART.md` - Quick reference
  - `CHANGELOG.md` - Version history
  - `COMPLETION_SUMMARY.md` - Feature list

---

## Installation (Ubuntu/Debian)

```bash
# 1. Install system packages
sudo apt-get update
sudo apt-get install -y python3-tk python3-pip

# 2. Install Python dependencies
cd virgo_gui
pip3 install -r requirements.txt

# 3. Install Virgo (if not already installed)
cd ..
pip3 install -e .

# 4. Launch the GUI
cd virgo_gui
./launch_gui.sh
```

---

## What This GUI Does

✅ **Complete observation control** - All Virgo parameters  
✅ **Live spectrum display** - Real-time monitoring  
✅ **Calibration workflow** - Cold sky reference  
✅ **Advanced RFI mitigation** - Median filtering + frequency blanking  
✅ **6 professional tools** - Prediction, simulation, calculators  
✅ **Multiple export formats** - FITS, CSV, PNG  

---

## Features

### Observation Parameters (All 12)
- Spectrometer type (WOLA/FTF)
- SDR configuration (gains, device args)
- Frequency & bandwidth
- Observer location (lat/lon/height)
- Target coordinates (RA/Dec or Az/Alt)
- Timing parameters

### Analysis Options (All 23)
- Calibration support
- RFI mitigation (2 methods)
- Dispersion measure (pulsars)
- VLSR frame conversion
- Slope correction
- Custom axis limits
- Metadata overlay

### Tools (All 6)
- **Source Prediction** - Alt/Az throughout day
- **HI Simulation** - LAB survey profiles
- **HI Map Viewer** - All-sky visualization
- **RFI Monitor** - Frequency survey
- **Antenna Calculator** - Gain, beamwidth, SEFD, SNR
- **Coordinate Converter** - All coordinate systems

---

## Quick Start

1. Click **"HI Preset"** button
2. Click **"Start Observation"**
3. Watch live spectrum!

See `QUICKSTART.md` for more details.

---

## Documentation

- **New users**: Start with `INSTALL.md` then `QUICKSTART.md`
- **Full manual**: See `USER_GUIDE.md`
- **What's new**: See `CHANGELOG.md`

---

## Requirements

**Minimum:**
- Python 3.6+
- 2GB RAM
- Ubuntu 18.04+ (or similar Linux)

**For observations:**
- Software-defined radio (RTL-SDR, HackRF, USRP, etc.)
- GNU Radio + gr-osmosdr

---

## Support

- **Documentation**: All guides in this folder
- **Virgo Docs**: https://virgo.readthedocs.io
- **Issues**: https://github.com/0xCoto/Virgo/issues

---

## License

Same as Virgo project

---

**Happy observing! 🔭📡**
