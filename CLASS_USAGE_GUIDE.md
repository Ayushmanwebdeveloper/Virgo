# GILDAS/CLASS Scripts for H1 Baseline Subtraction

## Quick Start

### Method 1: Simple Script (Recommended for Beginners)

```bash
# Edit the script to set your input filename
vi h1_baseline_simple.class

# Run in CLASS
class
@ h1_baseline_simple.class
```

### Method 2: Full Featured Script

```bash
# Edit configuration parameters at the top
vi h1_baseline_class.class

# Run in CLASS
class
@ h1_baseline_class.class
```

### Method 3: Interactive Commands

Launch CLASS and type commands directly:

```class
! Load your data
file in your_spectrum.30m
find /line HI
get first

! Setup for H1
set unit v f
set line HI " " 1420.405751

! Define line-free windows (±300 km/s exclusion)
clear window
set window -1000 -300 /velocity
set window 300 1000 /velocity

! Fit 2nd order polynomial with iteration
base 2 /iterate

! Subtract baseline
subtract

! Calculate SNR
compute maximum
compute rms

! Save
file out corrected.30m single
put
```

---

## Available Scripts

### 1. `h1_baseline_simple.class`

**Quick processing with standard parameters**

- 2nd order polynomial (observatory standard)
- ±300 km/s exclusion
- Iterative fitting for RFI rejection
- Hanning smoothing (11 channels)
- Minimal output

**Edit these lines:**
```class
define character infile "your_spectrum.30m"
define character outfile "corrected.30m"
define integer order 2
define real exclude_vel 300.0
```

**Run:**
```bash
class
@ h1_baseline_simple.class
```

---

### 2. `h1_baseline_class.class`

**Full-featured professional pipeline**

Features:
- ✅ Configurable polynomial order (0-9)
- ✅ Custom line-free window definition
- ✅ Iterative sigma clipping
- ✅ Optional RFI spike removal
- ✅ Multiple smoothing methods (Hanning, Box, Gaussian)
- ✅ Quality assessment
- ✅ Comprehensive statistics
- ✅ Automatic plot generation
- ✅ Extensions for batch processing and stacking

**Configuration parameters** (edit at top of script):

```class
! Input/Output
define character input_file "your_spectrum.30m"
define character output_file "corrected_spectrum.30m"

! Baseline
define integer poly_order 2
define real exclude_velocity 300.0

! Iterative fitting
define integer max_iterations 5
define real sigma_clip 3.0

! Smoothing
define logical do_smoothing .true.
define character smooth_method "HANNING"
define integer smooth_width 11

! RFI removal
define logical remove_spikes .false.
define real spike_threshold 5.0
```

**Run:**
```bash
class
@ h1_baseline_class.class
```

---

## Parameter Guide

### Polynomial Order

| Order | Use Case | CLASS Command |
|-------|----------|---------------|
| 1 | Linear baseline, narrow BW | `base 1` |
| **2** | **Standard (60% of cases)** | `base 2` |
| 3 | Complex baseline, wide BW | `base 3` |
| 4+ | Very wide BW, stacked data | `base 4` |

### Line-Free Windows

Standard exclusion: **±300 km/s** around H1 rest frequency

```class
! Clear existing windows
clear window

! Define windows (velocity in km/s)
set window -1000 -300 /velocity    ! Left window
set window 300 1000 /velocity      ! Right window
```

**For broader H1 lines** (e.g., ±500 km/s):
```class
set window -1000 -500 /velocity
set window 500 1000 /velocity
```

**For narrower lines** (e.g., ±200 km/s):
```class
set window -1000 -200 /velocity
set window 200 1000 /velocity
```

### Baseline Fitting Methods

**Standard polynomial (most common):**
```class
base 2
```

**With iteration** (recommended for RFI rejection):
```class
base 2 /iterate
```

**Chebyshev polynomial** (alternative):
```class
base cheby 2
```

### Smoothing Methods

**Hanning (GBT/VLA standard):**
```class
smooth hann 11
```

**Boxcar:**
```class
smooth box 11
```

**Gaussian:**
```class
smooth gaus 11
```

Width values:
- 5-11: Light smoothing (publication quality)
- 11-21: Medium smoothing (standard)
- 21+: Heavy smoothing (weak signals)

---

## Detection Thresholds

CLASS calculates SNR automatically. Professional thresholds:

| SNR | Detection Status | CLASS Check |
|-----|------------------|-------------|
| >5σ | Strong detection | `if (snr .gt. 5.0)` |
| >3σ | Confirmed detection | `if (snr .gt. 3.0)` |
| 2-3σ | Marginal | `if (snr .gt. 2.0)` |
| <2σ | No detection | `if (snr .lt. 2.0)` |

---

## Batch Processing

Process multiple spectra in a loop:

```class
! Load file with multiple spectra
file in observations.30m
find /line HI

! Count spectra
define integer nspec found
say "Found " nspec " spectra"

! Process each one
for scan_num 1 to nspec
  ! Get spectrum
  get next

  ! Setup
  set unit v f
  set line HI " " 1420.405751

  ! Windows
  clear window
  set window -1000 -300 /velocity
  set window 300 1000 /velocity

  ! Baseline
  base 2 /iterate
  subtract

  ! Smooth
  smooth hann 11

  ! Save with unique name
  define character outname
  write outname "corrected_" scan_num ".30m"
  file out outname single
  put

  say "Processed spectrum " scan_num "/" nspec
next

say "Batch processing complete!"
```

---

## Stacking Multiple Observations

Improve SNR by stacking (expected improvement: √N):

```class
! Initialize accumulator
file in obs1.30m
get first
base 2 /iterate
subtract
define spectrum stack_sum /like
stack_sum = spectrum

! Add more observations
file in obs2.30m
get first
base 2 /iterate
subtract
stack_sum = stack_sum + spectrum

file in obs3.30m
get first
base 2 /iterate
subtract
stack_sum = stack_sum + spectrum

! Average
define real n_obs 3.0
stack_sum = stack_sum / n_obs

! Apply final baseline (higher order for stacks)
base 4
subtract

! Calculate final SNR
compute rms
define real noise rms
compute maximum
define real signal maximum
define real snr signal / noise

! Expected improvement
define real expected sqrt(n_obs)

say "Stacked " n_obs " observations"
say "Final SNR: " snr
say "Expected improvement: " expected "×"
say "Actual improvement: " snr / (snr / expected) "×"
```

---

## Quality Assessment

After baseline subtraction, check quality:

```class
! Calculate RMS in line-free regions
compute rms
define real final_rms rms

! Should be close to noise level
! If too high, try higher polynomial order
```

**Quality indicators:**
- **Good:** RMS ≈ noise level (flatness ratio ~1.0)
- **Marginal:** RMS 1.2-1.5× noise level
- **Poor:** RMS >1.5× noise level → increase polynomial order

---

## File Formats

### Input

CLASS supports:
- **30m format** (.30m) - Standard IRAM 30m telescope
- **SDFITS** (.fits) - Single-dish FITS
- **GILDAS** (.gdf) - GILDAS data format
- **CLASS** (.class) - CLASS native format

Load with:
```class
file in filename.30m
```

### Output

**CLASS format** (preserves all metadata):
```class
file out corrected.30m single
put
```

**ASCII format** (for other programs):
```class
write corrected.dat /formatted
```

**FITS format:**
```class
fits write corrected.fits /style sdfits
```

---

## Troubleshooting

### Problem: "No data found"

**Solution:**
```class
! Check file format
file in your_file.30m
find          ! Show all lines
find /line HI ! Find only HI
```

### Problem: Low SNR despite strong signal

**Cause:** Wrong polynomial order

**Solution:** Increase order:
```class
base 3 /iterate
```

### Problem: "Too few channels in window"

**Cause:** Line-free windows too narrow

**Solution:** Widen windows:
```class
set window -1500 -300 /velocity
set window 300 1500 /velocity
```

### Problem: Baseline looks wavy after subtraction

**Cause:** Polynomial order too low or standing waves

**Solutions:**
1. Increase order: `base 3` or `base 4`
2. Use Chebyshev: `base cheby 3`
3. Use sinusoidal fit for standing waves

### Problem: RFI spikes remain

**Solution:** Use iterative fitting:
```class
base 2 /iterate
```

---

## Observatory-Specific Presets

### Effelsberg (EBHIS Standard)

```class
file in spectrum.30m
find /line HI
get first
set unit v f
set line HI " " 1420.405751
clear window
set window -1000 -300 /velocity
set window 300 1000 /velocity
base 2
subtract
smooth hann 11
```

### IRAM 30m Standard

```class
file in spectrum.30m
find /line HI
get first
set unit v f
base cheby 2
subtract
smooth gaus 15
```

### Generic European Standard

```class
! Same as simple script
@ h1_baseline_simple.class
```

---

## Integration with Python Pipeline

Export CLASS results for Python analysis:

```class
! After baseline subtraction
write corrected.dat /formatted

! Creates ASCII file:
! Column 1: Velocity (km/s)
! Column 2: Frequency (MHz)
! Column 3: Intensity (K)
```

Then load in Python:
```python
import numpy as np
from h1_baseline_subtraction import H1BaselineProcessor

# Load CLASS output
data = np.loadtxt('corrected.dat', skiprows=1)
velocity = data[:, 0]
frequency = data[:, 1]
intensity = data[:, 2]

# Further processing if needed
# Or just use for comparison
```

---

## Best Practices

1. **Always use /iterate** for iterative sigma clipping (RFI rejection)

2. **Check line-free percentage** - Need >25% for reliable fitting

3. **Start with 2nd order** - It works for 60% of cases

4. **Smooth for visualization** - But keep unsmoothed version for analysis

5. **Save intermediate steps** - For debugging and quality checks

6. **Document your parameters** - For reproducibility

7. **Stack weak signals** - Even 3-5 observations help significantly

---

## Example Workflow

Complete workflow from raw data to final result:

```class
! 1. Load
file in my_h1_obs.30m
find /line HI
get first

! 2. Setup
set unit v f
set align frequency velocity
set line HI " " 1420.405751

! 3. Define windows (±300 km/s)
clear window
set window -1000 -300 /velocity
set window 300 1000 /velocity

! 4. Baseline (2nd order with iteration)
base 2 /iterate

! 5. Check fit quality
compute rms
say "Baseline RMS: " rms

! 6. Subtract
subtract

! 7. Calculate SNR
compute maximum
define real signal maximum
compute rms
define real noise rms
define real snr signal / noise

say "H1 Signal: " signal
say "Noise: " noise
say "SNR: " snr

! 8. Detection check
if (snr .gt. 3.0) then
  say "H1 DETECTED!"
else
  say "No significant detection"
endif

! 9. Smooth for display
smooth hann 11

! 10. Save
file out h1_corrected.30m single
put
write h1_corrected.dat /formatted

! 11. Plot
draw

say "Complete!"
```

---

## References

- **GILDAS/CLASS Documentation:** http://iram.fr/IRAMFR/GILDAS/
- **Effelsberg EBHIS:** Kerp et al. (2011)
- **HIPASS Methods:** Barnes et al. (2001, MNRAS 322, 486)
- **H1 Baseline Standards:** Liu et al. (2022, PASA 39, e029)

---

## Support

For CLASS-specific help:
```class
help base      ! Baseline fitting help
help smooth    ! Smoothing help
help window    ! Window definition help
```

For this pipeline:
- Read `H1_BASELINE_README.md` for theory and background
- Read `QUICK_REFERENCE.md` for Python version quick reference
- Compare Python and CLASS results for validation

---

Last updated: 2025-01-18
Compatible with: GILDAS nov25a and later
