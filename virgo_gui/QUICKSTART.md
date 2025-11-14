# Virgo GUI - Quick Start Guide (v2.0 Enhanced)

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

## What's New in v2.0
- ✅ **100% Feature Complete** - All Virgo functions now available
- ✅ Observer location & target coordinates
- ✅ Spectrometer type selection (WOLA/FTF)
- ✅ Advanced RFI blanking with frequency ranges
- ✅ All plot options: slope correction, dispersion, VLSR, metadata
- ✅ Fully functional tools: predict, simulate, HI map, RFI monitor
- ✅ Antenna calculators: gain, beamwidth, SEFD, SNR
- ✅ Coordinate converter

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

### Select Spectrometer Type
- **WOLA** (default): 4-tap weighted overlap-add, lower sidelobes, better for spectral observations
- **FTF**: Plain FFT, lighter weight, faster for resource-constrained systems

### Add Observer Location & Target
1. Enter your **Latitude, Longitude, Height** (optional but recommended)
2. Select **Coordinate Type**:
   - **None**: No target tracking
   - **Equatorial (RA/Dec)**: For celestial coordinates
   - **Horizontal (Az/Alt)**: For local coordinates
3. Enter coordinates - GUI adapts to show relevant fields

### Adjust Gain (if signal too weak/strong)
- **Too weak**: Increase RF/IF/BB gain
- **Too strong**: Decrease gains
- **Typical**: RF=30, IF=25, BB=18

### Remove RFI (Radio Interference)

**Method 1: Median Filtering** (In Analysis tab)
- **Median Filter (Freq)**: 5-15 (removes narrow-band RFI)
- **Median Filter (Time)**: 3-10 (removes transient RFI)

**Method 2: Frequency Blanking** (NEW!)
1. Click **"Manage RFI Ranges"** in Analysis tab
2. Add frequency ranges to blank out (e.g., FM radio, cell towers)
3. Specify low and high frequency for each range
4. Blanked ranges will be excluded from analysis

### Export Data
In Analysis tab:
- **Export FITS**: For professional analysis (ds9, CASA)
- **Export CSV**: For Excel, Python, MATLAB

## GUI Layout

### Observation Tab
- **Spectrometer Type**: WOLA or FTF selection
- **SDR Settings**: Device args, gains
- **Frequency/Timing**: All observation parameters
- **Observer Location**: NEW - Lat/Lon/Height
- **Target Coordinates**: NEW - RA/Dec or Az/Alt
- **Live Display**: Real-time spectrum and time series

### Calibration Tab
- Instructions for calibration procedure
- Quick presets
- File browser for calibration files

### Analysis & Plotting Tab
- Load observation and calibration files
- **RFI Mitigation**: Median filters + NEW frequency blanking
- **Display Options**: NEW - dB, VLSR, metadata, slope correction
- **Spectral Line**: Rest frequency, NEW - dispersion measure
- **Axis Limits**: NEW - Full control over all plot axes
- Export to FITS/CSV

### Tools Menu
- **Predict Source Position**: NEW - Full implementation with Alt/Az prediction
- **Simulate HI Profile**: NEW - LAB survey-based simulation
- **View HI Map**: NEW - All-sky hydrogen map
- **Monitor RFI**: NEW - Wideband frequency survey
- **Antenna Calculator**: NEW - Gain, beamwidth, SEFD, SNR
- **Coordinate Converter**: NEW - Alt/Az ↔ RA/Dec ↔ Galactic

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
