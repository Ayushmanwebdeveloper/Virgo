# Virgo GUI - Quick Start Guide

## Installation (One-time setup)

```bash
# Install dependencies
sudo apt-get update && sudo apt-get install -y python3-tk python3-pip
pip3 install -r gui-requirements.txt

# Make scripts executable
chmod +x launch_gui.sh virgo_gui.py
```

## Launching the GUI

```bash
./launch_gui.sh
```

## First Observation - HI Line (21 cm Hydrogen)

1. **Click "Load Preset: HI Line"** in the Observation tab
   - This sets frequency to 1420.405752 MHz (21 cm line)
   - Bandwidth: 2.4 MHz
   - Channels: 2048
   - Sample time: 1 second

2. **Adjust duration** (default: 60 seconds)
   - Longer = better sensitivity
   - Typical: 5-30 minutes for good results

3. **Click "Start Observation"**
   - Watch the live spectrum display
   - Status panel shows progress

4. **View results**
   - Plot is auto-generated when complete
   - Files saved: observation.dat, plot.png, spectra.csv, etc.

## Calibration (Recommended for best results)

### Step 1: Calibration Observation
1. Go to **Calibration** tab
2. Click **"Start Calibration Observation"**
3. **Point antenna at cold sky**:
   - High latitude (away from Milky Way)
   - No strong sources
   - Empty region of sky
4. Wait for completion
5. File saved as: `calibration_YYYYMMDD_HHMMSS.dat`

### Step 2: Target Observation
1. Go to **Observation** tab
2. **Use same settings as calibration**
3. Point antenna at your target
4. Start observation

### Step 3: Analyze
1. Go to **Analysis & Plotting** tab
2. Load observation file (target)
3. Load calibration file
4. Click **"Generate Plot"**
5. Result shows calibrated spectrum with SNR!

## Common Tasks

### Change Frequency
- **HI Line**: 1420405752 Hz (1420.405752 MHz)
- **Continuum**: 1400000000 Hz (1400 MHz)
- **Custom**: Enter frequency in Hz

### Adjust Gain (if signal too weak/strong)
- **Too weak**: Increase RF/IF/BB gain
- **Too strong**: Decrease gains
- **Typical**: RF=30, IF=25, BB=18

### Remove RFI (Radio Interference)
In Analysis tab:
- **Median Filter (Freq)**: 5-15 (removes narrow-band RFI)
- **Median Filter (Time)**: 3-10 (removes transient RFI)

### Export Data
In Analysis tab:
- **Export FITS**: For professional analysis (ds9, CASA)
- **Export CSV**: For Excel, Python, MATLAB

## GUI Layout

### Observation Tab
- **Left**: Parameter controls
- **Right**: Live spectrum + status log
- **Bottom**: Start/Stop buttons

### Calibration Tab
- Instructions for calibration procedure
- Quick presets
- File browser for calibration files

### Analysis & Plotting Tab
- Load observation and calibration files
- Set processing options (RFI mitigation, dB scale)
- Generate publication-quality plots
- Export to FITS/CSV

## Files Created

After an observation, you'll find:
- `observation.dat` - Raw binary data
- `observation.dat.header` - Metadata (frequency, time, gains)
- `plot.png` - Auto-generated plot
- `waterfall.fits` - Waterfall plot (if enabled)
- `spectra.csv` - Spectrum data (if enabled)
- `power.csv` - Time series (if enabled)

## Keyboard Shortcuts

- **Ctrl+O**: Load observation file
- **Ctrl+C**: Load calibration file
- **Ctrl+Q**: Quit application

## Tips for Success

✅ **DO**:
- Use HI Line preset for your first observation
- Point at Milky Way for easy HI detection
- Let observation run for at least 5 minutes
- Calibrate regularly
- Use same settings for calibration and target

❌ **DON'T**:
- Use very short durations (<10 sec)
- Point at Sun (can damage SDR!)
- Use different settings between cal and target
- Forget to connect SDR hardware 😊

## Troubleshooting

| Problem | Solution |
|---------|----------|
| GUI won't start | Install tkinter: `sudo apt-get install python3-tk` |
| No SDR detected | Check connection: `lsusb` |
| Observation fails | Check device args (e.g., "rtl=0") |
| No live updates | Wait 2 seconds, check disk space |
| Plot is empty | Verify observation completed, check file exists |

## Example Observation Parameters

### Strong Source (Sun, Cas A) - **NEVER POINT AT SUN**
```
Duration: 30-60 seconds
Sample Time: 0.5 s
Gain: Medium (RF=25, IF=20, BB=15)
```

### Weak Source (Distant HI clouds)
```
Duration: 300-1800 seconds (5-30 min)
Sample Time: 1-2 s
Gain: High (RF=40, IF=30, BB=20)
```

### RFI Survey
```
Duration: 30 seconds
Sample Time: 0.1 s
Bandwidth: Wide
Scan multiple frequencies
```

## Getting Help

- Full manual: `GUI_README.md`
- Installation: `INSTALL_GUI.md`
- Virgo docs: https://virgo.readthedocs.io

---

**Ready to observe? Click that green "Start Observation" button! 🚀**
