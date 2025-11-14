# Virgo GUI vs Documentation - Feature Comparison

## 1. COMMAND-LINE ARGUMENTS (CLI -h output)

### Implemented in virgo.py main()
- -da / --dev_args: SDR Device Arguments
- -rf / --rf_gain: SDR RF Gain (dB)
- -if / --if_gain: SDR IF Gain (dB)
- -bb / --bb_gain: SDR BB Gain (dB)
- -f / --frequency: Center Frequency (Hz) [REQUIRED]
- -b / --bandwidth: Bandwidth (Hz) [REQUIRED]
- -c / --channels: Number of Channels/FFT Size [REQUIRED]
- -t / --t_sample: FFT Sample Time (s) [REQUIRED]
- -d / --duration: Observing Duration (s)
- -s / --start_in: Schedule Observation (s)
- -o / --obs_file: Observation Filename
- -C / --cal_file: Calibration Filename
- -db / --db: Use dB-scaled Power values
- -n / --median_frequency: Median Factor (Frequency Domain)
- -m / --median_time: Median Factor (Time Domain)
- -r / --rest_frequency: Spectral Line Rest Frequency (Hz)
- -W / --waterfall_fits: Filename for FITS Waterfall File
- -S / --spectra_csv: Filename for Spectra CSV File
- -P / --power_csv: Filename for Power CSV File
- -p / --plot_file: Plot Filename

### Implemented in virgo_gui.py
GUI form fields available:
- Device Args
- RF Gain (dB)
- IF Gain (dB)
- BB Gain (dB)
- Frequency (Hz)
- Bandwidth (Hz)
- Channels
- Sample Time (s)
- Duration (s)
- Start In (s)
- Observation File
- Waterfall FITS
- Spectra CSV
- Power CSV
- Plot File
- Use dB Scale
- Median Filter (Freq)
- Median Filter (Time)
- Rest Frequency (Hz)

### Missing from GUI CLI-equivalent arguments
- NONE (all main() arguments are accessible via GUI form fields)

---

## 2. observe() PARAMETERS

### Signature:
```python
observe(obs_parameters, spectrometer='wola', obs_file='observation.dat', start_in=0)
```

### obs_parameters dictionary required fields:
| Parameter | Type | Implemented | Notes |
|-----------|------|-------------|-------|
| dev_args | string | YES | Device arguments (gr-osmosdr) |
| rf_gain | float | YES | RF gain |
| if_gain | float | YES | IF gain |
| bb_gain | float | YES | Baseband gain |
| frequency | float | YES | Center frequency [Hz] |
| bandwidth | float | YES | Instantaneous bandwidth [Hz] |
| channels | int | YES | Number of frequency channels (FFT size) |
| t_sample | float | YES | Integration time per FFT sample |
| duration | float | YES | Total observing duration [sec] |
| **loc** | string | **NO** | Latitude, longitude, elevation (space-separated floats) |
| **ra_dec** | string | **NO** | Right ascension, declination (space-separated) |
| **az_alt** | string | **NO** | Azimuth, altitude (space-separated) |

### observe() Options:
| Parameter | Type | Implemented | Notes |
|-----------|------|-------------|-------|
| spectrometer | string | **PARTIAL** | Options: 'wola' or 'ftf'; GUI always uses default 'wola' |
| obs_file | string | YES | Output filename |
| start_in | float | YES | Scheduled start time |

### Missing observe() features in GUI:
- **loc**: Observer location (latitude, longitude, elevation) - CRITICAL
- **ra_dec**: Target RA/Dec coordinates - CRITICAL
- **az_alt**: Target Alt/Az coordinates - CRITICAL
- **spectrometer**: Cannot select FTF vs WOLA pipeline

---

## 3. plot() PARAMETERS

### Signature:
```python
plot(obs_parameters='', n=0, m=0, f_rest=0, slope_correction=False, dB=False, vlsr=False, 
     meta=False, avg_ylim=[0,0], cal_ylim=[0,0], rfi=[], xlim=[0,0], ylim=[0,0], dm=0,
     obs_file='observation.dat', cal_file='', waterfall_fits='', spectra_csv='', 
     power_csv='', plot_file='plot.png')
```

### Implemented in GUI:
| Parameter | Type | Used in GUI |
|-----------|------|------------|
| obs_file | string | YES |
| cal_file | string | YES |
| n | int | YES (Median Filter Freq) |
| m | int | YES (Median Filter Time) |
| f_rest | float | YES (Rest Frequency) |
| dB | bool | YES (Use dB Scale) |
| waterfall_fits | string | YES |
| spectra_csv | string | YES |
| power_csv | string | YES |
| plot_file | string | YES |

### Missing from GUI:
| Parameter | Type | Purpose | Notes |
|-----------|------|---------|-------|
| **slope_correction** | bool | Correct slope in poorly-calibrated spectra using linear regression | NOT ACCESSIBLE |
| **rfi** | list of tuples | Blank frequency channels [(lo_freq, hi_freq)] [Hz] | NOT ACCESSIBLE |
| **xlim** | list [low, high] | X-axis frequency limits [Hz] | NOT ACCESSIBLE |
| **ylim** | list [start_time, end_time] | Y-axis time limits [Hz] | NOT ACCESSIBLE |
| **dm** | float | Dispersion measure for dedispersion [pc/cm^3] | NOT ACCESSIBLE |
| **vlsr** | bool | Display graph in VLSR frame of reference | NOT ACCESSIBLE |
| **meta** | bool | Display header with date, time, and target | NOT ACCESSIBLE |
| **avg_ylim** | list [low, high] | Averaged plot y-axis limits | NOT ACCESSIBLE |
| **cal_ylim** | list [low, high] | Calibrated plot y-axis limits | NOT ACCESSIBLE |
| **obs_parameters** | dict | Could read from header file | PARTIALLY IMPLEMENTED |

### Missing plot() features in GUI (High Priority):
1. **slope_correction**: RFI/calibration enhancement
2. **rfi**: Frequency blanking (RFI mitigation)
3. **xlim/ylim**: Plot axis customization
4. **dm**: Pulsar dedispersion
5. **vlsr**: VLSR reference frame
6. **meta**: Display metadata header
7. **avg_ylim / cal_ylim**: Axis range customization

---

## 4. MISSING TOOLS

### Fully Implemented but Stub in GUI:
| Tool | Parameters | GUI Status | Notes |
|------|-----------|-----------|-------|
| predict() | lat, lon, height, source, date, plot_sun, plot_file | STUB ONLY | Placeholder window shows "Feature coming soon" |
| simulate() | l, b, beamwidth, v_min, v_max, plot_file | STUB ONLY | Placeholder window shows "Feature coming soon" |
| monitor_rfi() | f_lo, f_hi, obs_parameters, data | NOT IN GUI | No UI at all |
| map_hi() | ra, dec, plot_file | NOT IN GUI | No UI at all |

### predict() - Source Position Prediction
```python
predict(lat, lon, height=0, source='', date='', plot_sun=True, plot_file='')
```
- **Status**: Imported but GUI shows placeholder only
- **Missing parameters in GUI**: All input fields needed
- **Purpose**: Plot source Alt/Az for observer location

### simulate() - HI Profile Simulation
```python
simulate(l, b, beamwidth=0.6, v_min=-400, v_max=400, plot_file='')
```
- **Status**: Imported but GUI shows placeholder only
- **Missing parameters in GUI**: All input fields needed
- **Purpose**: Simulate 21 cm HI profiles from LAB Survey

### monitor_rfi() - RFI Monitoring Survey
```python
monitor_rfi(f_lo, f_hi, obs_parameters, data='rfi_data')
```
- **Status**: Completely missing from GUI
- **Missing**: Entire UI not implemented
- **Purpose**: Wideband RFI survey (multiple frequency observations)

### map_hi() - All-Sky HI Map Viewer
```python
map_hi(ra=None, dec=None, plot_file='')
```
- **Status**: Completely missing from GUI
- **Missing**: Entire UI not implemented
- **Purpose**: Display LAB HI survey all-sky map with pointing indicator

---

## 5. ANTENNA CALCULATION FUNCTIONS (Not in GUI)

| Function | Signature | Status | Purpose |
|----------|-----------|--------|---------|
| **equatorial()** | equatorial(alt, az, lat, lon, height=0) | NOT IN GUI | Convert Alt/Az to RA/Dec |
| **galactic()** | galactic(ra, dec) | NOT IN GUI | Convert RA/Dec to galactic l,b |
| **frequency()** | frequency(wavelength) | NOT IN GUI | Convert wavelength to frequency |
| **wavelength()** | wavelength(frequency) | NOT IN GUI | Convert frequency to wavelength |
| **gain()** | gain(D, f, e=0.7, u='dBi') | NOT IN GUI | Estimate parabolic antenna gain |
| **A_e()** | A_e(gain, f) | NOT IN GUI | Transform gain to effective aperture |
| **beamwidth()** | beamwidth(D, f) | NOT IN GUI | Calculate antenna half-power beamwidth |
| **NF()** | NF(T_noise, T_ref=290) | NOT IN GUI | Convert noise temp to noise figure |
| **T_noise()** | T_noise(NF, T_ref=290) | NOT IN GUI | Convert noise figure to noise temp |
| **G_T()** | G_T(gain, T_sys) | NOT IN GUI | Compute gain-to-noise-temperature |
| **SEFD()** | SEFD(A_e, T_sys) | NOT IN GUI | Compute system equivalent flux density |
| **snr()** | snr(S, sefd, t, bw) | NOT IN GUI | Estimate signal-to-noise ratio |

### Antenna Tool Summary
- **Status**: 0/12 antenna functions implemented
- **Use Case**: Quick antenna/system calculations for observers
- **Missing**: Complete antenna tools submenu

---

## SUMMARY STATISTICS

### Functions in Virgo Library
- **Total Main Functions**: 14
  - Observation: 1 (observe)
  - Plotting: 2 (plot, plot_rfi, map_hi)
  - Prediction/Simulation: 2 (predict, simulate)
  - RFI Monitoring: 1 (monitor_rfi)
  - Antenna Calculations: 8 (equatorial, galactic, frequency, wavelength, gain, A_e, beamwidth, NF, T_noise, G_T, SEFD, snr)

### GUI Implementation Status
| Category | Total | Implemented | Missing | % Complete |
|----------|-------|-------------|---------|-----------|
| **CLI Arguments** | 20 | 20 | 0 | 100% |
| **observe() params** | 12 | 9 | 3 | 75% |
| **plot() params** | 13 | 10 | 3 | 77% |
| **Main Tools** | 4 | 0 (2 stubs) | 2 | 0% |
| **Antenna Functions** | 12 | 0 | 12 | 0% |
| **TOTAL PARAMETERS** | 61 | 49 | 12 | 80% |

### Critical Missing Features (Blocking Functionality)
1. **Observer Location (loc)** - Needed for proper coordinate tracking
2. **Target Coordinates (ra_dec/az_alt)** - Needed for astronomical context
3. **RFI Frequency Blanking** - Needed for RFI mitigation
4. **Slope Correction** - Needed for calibration quality
5. **Dedispersion (dm)** - Needed for pulsar observations
6. **Tools Stubs** - predict() and simulate() need full implementation
7. **Monitor RFI Tool** - Wideband RFI survey not accessible
8. **Map HI Tool** - All-sky map viewer not accessible
