# Virgo Radio Telescope GUI

A comprehensive graphical user interface for the Virgo spectrometer and radiometer, designed for radio astronomy observations using software-defined radios (SDRs).

## Features

### 📡 Observation Control
- **Complete parameter configuration** for all Virgo command-line arguments
- **Live spectrum visualization** during observations
- **Real-time power monitoring** with time-series plots
- **Preset configurations** for common observations (HI line, continuum, etc.)
- **Scheduled observations** with configurable start delays

### 🔬 Calibration Support
- **Dedicated calibration tab** with step-by-step instructions
- **Easy calibration file management**
- **Quick preset loading** for calibration observations
- **Side-by-side comparison** of calibrated and uncalibrated data

### 📊 Analysis & Plotting
- **Advanced data processing** with RFI mitigation options
- **Flexible output formats**: FITS, CSV, PNG
- **Interactive plot viewer** with zoom and pan
- **Median filtering** for frequency and time domain
- **Velocity axis** for spectral line analysis
- **Multi-panel visualization** of spectrum, waterfall, and time series

### 🛠️ Additional Tools
- Source position prediction
- HI profile simulation
- RFI monitoring
- Data import/export

## Installation

### Prerequisites

The GUI requires Python 3 with the following packages:

```bash
# System packages (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install python3 python3-tk python3-pip

# Python packages
pip3 install numpy matplotlib astropy pillow

# Virgo and GNU Radio (if not already installed)
pip3 install virgo
# OR from source:
# cd /home/user/Virgo
# pip3 install -e .
```

### Installing GNU Radio and SDR Drivers

For hardware support, you'll need GNU Radio and appropriate SDR drivers:

```bash
# GNU Radio
sudo apt-get install gnuradio gr-osmosdr

# For RTL-SDR
sudo apt-get install rtl-sdr

# For other SDRs (HackRF, USRP, etc.)
# Follow manufacturer's instructions
```

## Usage

### Quick Start

1. **Launch the GUI:**
   ```bash
   cd /home/user/Virgo
   ./launch_gui.sh
   ```

   Or directly with Python:
   ```bash
   python3 virgo_gui.py
   ```

2. **Configure your observation:**
   - Go to the **Observation** tab
   - Click "Load Preset: HI Line" for hydrogen line observations
   - Or manually configure parameters:
     - **Frequency**: Center frequency in Hz (e.g., 1420405752 for HI line)
     - **Bandwidth**: Observation bandwidth in Hz (e.g., 2400000 for 2.4 MHz)
     - **Channels**: Number of FFT channels (e.g., 2048)
     - **Sample Time**: Integration time per spectrum in seconds (e.g., 1.0)
     - **Duration**: Total observation time in seconds (e.g., 60)

3. **Start observing:**
   - Click "Start Observation"
   - Watch the live spectrum display update in real-time
   - Data is automatically saved to the specified output files

4. **Analyze your data:**
   - Switch to the **Analysis & Plotting** tab
   - Load your observation file
   - Optionally load a calibration file
   - Configure RFI mitigation and processing options
   - Click "Generate Plot" to create publication-quality plots

### Parameter Guide

#### SDR Configuration
- **Device Args**: SDR device identifier (e.g., "rtl=0" for first RTL-SDR)
- **RF Gain**: RF amplifier gain in dB (typical: 20-40 dB)
- **IF Gain**: IF amplifier gain in dB (typical: 20-30 dB)
- **BB Gain**: Baseband gain in dB (typical: 15-25 dB)

#### Frequency Configuration
- **Frequency**: Center frequency in Hz
  - HI line: 1420405752 Hz
  - Continuum: varies by target
- **Bandwidth**: Observation bandwidth in Hz
  - Typical: 2.4 MHz (2400000 Hz)
  - Maximum depends on SDR capabilities
- **Channels**: Number of frequency channels (FFT size)
  - More channels = better frequency resolution
  - Typical: 1024, 2048, or 4096

#### Timing Configuration
- **Sample Time**: Integration time per spectrum (seconds)
  - Shorter = better time resolution but noisier
  - Longer = better sensitivity but slower
  - Typical: 0.5 - 2.0 seconds
- **Duration**: Total observation length (seconds)
  - Minimum: ~10 seconds
  - Typical: 60-3600 seconds (1 minute to 1 hour)
- **Start In**: Delay before starting (seconds)
  - Useful for scheduling observations

#### Output Configuration
- **Observation File**: Raw data output (.dat file)
- **Waterfall FITS**: Waterfall plot in FITS format
- **Spectra CSV**: Spectrum data in CSV format
- **Power CSV**: Time series power data in CSV format
- **Plot File**: Generated plot image (.png)

#### Advanced Settings
- **Use dB Scale**: Display power in decibels
- **Median Filter (Freq)**: RFI mitigation in frequency domain
  - Higher values = more aggressive filtering
  - Typical: 5-15
- **Median Filter (Time)**: RFI mitigation in time domain
  - Higher values = more aggressive filtering
  - Typical: 3-10
- **Rest Frequency**: Spectral line rest frequency for velocity axis
  - HI line: 1420405752 Hz

## Calibration Procedure

### Why Calibrate?

Calibration removes instrumental effects and converts raw power measurements to meaningful astronomical units (signal-to-noise ratio or temperature).

### How to Calibrate

1. **Record a calibration observation:**
   - Go to the **Calibration** tab
   - Click "Start Calibration Observation"
   - Point your antenna at a "cold sky" region:
     - High galactic latitude (away from Milky Way)
     - No strong radio sources nearby
     - Use stellarium or online tools to find suitable regions
   - Let the observation complete

2. **Record your target observation:**
   - Return to the **Observation** tab
   - Point your antenna at your target
   - Use the SAME parameters as the calibration
   - Start the observation

3. **Analyze calibrated data:**
   - Go to the **Analysis & Plotting** tab
   - Load your target observation file
   - Load your calibration file
   - Generate the plot
   - The GUI will automatically:
     - Divide target by calibration
     - Compute signal-to-noise ratio
     - Display calibrated spectrum

### Calibration Tips

- ✅ **DO**: Use identical parameters for calibration and target
- ✅ **DO**: Calibrate regularly (daily is best)
- ✅ **DO**: Choose calibration regions carefully
- ❌ **DON'T**: Use different bandwidths or frequencies
- ❌ **DON'T**: Use very old calibration files
- ❌ **DON'T**: Point calibration at strong sources

## Common Observation Scenarios

### 1. Hydrogen Line (HI) Observation

**Goal**: Detect the 21 cm neutral hydrogen emission line

**Configuration**:
```
Frequency: 1420405752 Hz (HI line)
Bandwidth: 2400000 Hz (2.4 MHz)
Channels: 2048
Sample Time: 1.0 s
Duration: 300 s (5 minutes)
Rest Frequency: 1420405752 Hz
```

**Steps**:
1. Click "Load Preset: HI Line"
2. Adjust duration as needed
3. Point antenna at Milky Way or specific HI region
4. Start observation
5. Analyze with velocity axis enabled

### 2. Radio Continuum Observation

**Goal**: Measure broadband radio emission from a source

**Configuration**:
```
Frequency: 1400000000 Hz (1.4 GHz)
Bandwidth: 2400000 Hz
Channels: 1024
Sample Time: 0.5 s
Duration: 600 s (10 minutes)
```

**Steps**:
1. Load continuum preset or configure manually
2. Point at radio source (e.g., Cygnus A, Cas A, Sun)
3. Perform calibration observation first (cold sky)
4. Perform target observation
5. Analyze with calibration file

### 3. RFI Survey

**Goal**: Identify radio frequency interference in your environment

**Configuration**:
```
Frequency: Variable (scan range)
Bandwidth: 2400000 Hz
Channels: 2048
Sample Time: 0.1 s
Duration: 30 s
```

**Steps**:
1. Use Tools > Monitor RFI
2. Scan different frequency ranges
3. Identify interference patterns
4. Avoid RFI-heavy frequencies for science observations

## Live Spectrum Display

The live display shows:

1. **Top Panel**: Average Spectrum
   - Frequency (MHz) vs Power
   - Updates every 2 seconds during observation
   - Shows cumulative average

2. **Bottom Panel**: Power vs Time
   - Sample number vs Average Power
   - Useful for detecting transients
   - Monitors system stability

## Troubleshooting

### GUI won't start

**Error**: `ModuleNotFoundError: No module named 'tkinter'`
```bash
sudo apt-get install python3-tk
```

**Error**: `ModuleNotFoundError: No module named 'matplotlib'`
```bash
pip3 install matplotlib
```

**Error**: `ModuleNotFoundError: No module named 'virgo'`
```bash
cd /home/user/Virgo
pip3 install -e .
```

### Observation fails to start

**Error**: `No devices found`
- Check SDR is connected: `lsusb`
- Check SDR permissions: `sudo chmod 666 /dev/bus/usb/XXX/YYY`
- Install SDR drivers (rtl-sdr, hackrf, etc.)

**Error**: `Invalid parameter value`
- Check all required fields are filled
- Ensure numeric fields contain valid numbers
- Frequency, bandwidth, channels, and sample time are required

### No live updates

- Check that observation file is being created
- Verify disk space is available
- Look for errors in status panel
- Increase sample time for slower systems

### Plot generation fails

**Error**: `File not found`
- Verify observation file exists
- Check file path is correct
- Ensure observation completed successfully

**Error**: `Invalid calibration file`
- Verify calibration file format matches observation
- Check that calibration was done with same parameters
- Ensure calibration file has associated .header file

## Advanced Features

### Median Filtering for RFI Mitigation

Radio Frequency Interference (RFI) can contaminate observations. The GUI provides two types of median filtering:

1. **Frequency Domain Filtering**:
   - Removes narrow-band RFI (broadcast stations, satellites)
   - Higher values = more aggressive
   - Set in "Median Filter (Freq)" field
   - Typical values: 5-15

2. **Time Domain Filtering**:
   - Removes transient RFI (radar, aircraft)
   - Higher values = more aggressive
   - Set in "Median Filter (Time)" field
   - Typical values: 3-10

### Custom Gain Settings

Different SDRs have different gain ranges:

**RTL-SDR**:
- RF Gain: 0-50 dB
- Typical: 30-40 dB

**HackRF**:
- LNA Gain: 0-40 dB (RF Gain)
- VGA Gain: 0-62 dB (IF Gain)
- Typical: LNA=24, VGA=20

**USRP**:
- Total Gain: 0-76 dB
- Set in RF Gain field
- Typical: 40-60 dB

### Output File Formats

**DAT File** (observation.dat):
- Binary file with float32 values
- Each spectrum stored sequentially
- Accompanied by .header file with metadata

**FITS File** (waterfall.fits):
- Standard astronomical format
- 2D array: frequency × time
- Contains WCS headers for coordinates
- Can be opened in ds9, TOPCAT, or astropy

**CSV Files**:
- Human-readable text format
- Spectra CSV: frequency, power, calibrated power, SNR
- Power CSV: time, integrated power
- Easy to import into Excel, MATLAB, Python

## Tips for Best Results

1. **Minimize RFI**:
   - Observe from quiet locations
   - Turn off nearby electronics
   - Use shielded cables
   - Enable median filtering

2. **Optimize Gain**:
   - Start with moderate gain (30 dB)
   - Increase if signal is weak
   - Decrease if signal saturates
   - Monitor power levels during observation

3. **Choose Integration Time**:
   - Longer integration = better sensitivity
   - Shorter integration = better time resolution
   - For weak sources: 1-5 seconds
   - For strong sources: 0.1-1 second

4. **Calibrate Regularly**:
   - Daily calibration is best
   - Calibrate in same conditions as target
   - Save calibration files with timestamps
   - Use consistent calibration regions

5. **Monitor System**:
   - Watch live display for issues
   - Check power stability
   - Look for saturation or dropouts
   - Verify spectrum shape makes sense

## Keyboard Shortcuts

- **Ctrl+O**: Load Observation
- **Ctrl+C**: Load Calibration
- **Ctrl+Q**: Quit

## Support and Documentation

- **Virgo Documentation**: https://virgo.readthedocs.io
- **GitHub Repository**: https://github.com/0xCoto/Virgo
- **Issues**: Report bugs on GitHub Issues

## License

This GUI is part of the Virgo project and follows the same license.

## Credits

- **Virgo**: Apostolos Spanakis-Misirlis (@0xCoto)
- **GUI**: Created for enhanced usability
- **GNU Radio**: Signal processing framework
- **Matplotlib**: Plotting library
- **Tkinter**: GUI framework

---

**Happy Observing! 🔭📡**
