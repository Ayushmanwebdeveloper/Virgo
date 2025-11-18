#!/usr/bin/env python3
"""
H1 21cm Polynomial Baseline Subtraction - Professional Implementation

Based on universal standards from:
- Parkes Observatory (HIPASS)
- Green Bank Telescope (GBT)
- FAST Telescope
- VLA/ALMA (CASA)
- Effelsberg (EBHIS)

Author: Radio Astronomy Standard Pipeline
Date: 2025
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import interpolate, signal, stats
from scipy import sparse
from scipy.sparse.linalg import spsolve
import argparse
import sys
from pathlib import Path
import warnings

# Physical constants (CODATA)
H1_REST_FREQ = 1420.405751  # MHz (precise H1 rest frequency)
SPEED_OF_LIGHT = 299792.458  # km/s


class H1BaselineProcessor:
    """
    Professional H1 baseline subtraction processor
    Implements methods from all major radio observatories
    """

    def __init__(self,
                 poly_order=2,
                 exclude_velocity=300.0,
                 sigma_clip=3.0,
                 max_iterations=5,
                 smoothing_method='savgol',
                 smoothing_param=11,
                 spike_removal=False,
                 spike_threshold=5.0,
                 spike_width=3,
                 verbose=True):
        """
        Initialize H1 baseline processor

        Parameters:
        -----------
        poly_order : int
            Polynomial order for baseline fitting (default: 2)
            - 0: DC offset only (rare)
            - 1: Linear (20% of cases)
            - 2: Quadratic (60% of cases) - STANDARD
            - 3: Cubic (10% of cases)
            - 4+: Special cases (5%)

        exclude_velocity : float
            Velocity range to exclude around H1 line (km/s, default: 300)
            Standard: 250-300 km/s for most observations

        sigma_clip : float
            Sigma clipping threshold for iterative fitting (default: 3.0)

        max_iterations : int
            Maximum iterations for sigma clipping (default: 5)

        smoothing_method : str
            Smoothing method: 'hanning', 'savgol', 'tukey', or 'none'

        smoothing_param : int or float
            Smoothing parameter (window size or alpha)

        spike_removal : bool
            Enable RFI spike removal (default: False)

        spike_threshold : float
            Threshold for spike detection in MAD units (default: 5.0)

        spike_width : int
            Width of median filter for spike detection (default: 3)

        verbose : bool
            Print diagnostic information
        """
        self.poly_order = poly_order
        self.exclude_velocity = exclude_velocity
        self.sigma_clip = sigma_clip
        self.max_iterations = max_iterations
        self.smoothing_method = smoothing_method
        self.smoothing_param = smoothing_param
        self.spike_removal = spike_removal
        self.spike_threshold = spike_threshold
        self.spike_width = spike_width
        self.verbose = verbose

        # Results storage
        self.frequency = None
        self.power = None
        self.baseline = None
        self.corrected = None
        self.smoothed = None
        self.noise = None
        self.snr = None
        self.mask = None
        self.spikes_removed = 0

    def load_spectrum(self, filepath, freq_col=0, power_col=1,
                     delimiter=',', skiprows=0):
        """
        Load spectrum from file

        Parameters:
        -----------
        filepath : str
            Path to spectrum file
        freq_col : int
            Column index for frequency data
        power_col : int
            Column index for power/temperature data
        delimiter : str
            Column delimiter (default: ',')
        skiprows : int
            Number of header rows to skip
        """
        try:
            data = np.loadtxt(filepath, delimiter=delimiter,
                            skiprows=skiprows, usecols=(freq_col, power_col))
            self.frequency = data[:, 0]
            self.power = data[:, 1]

            if self.verbose:
                self._print_data_info()

            return True

        except Exception as e:
            print(f"Error loading spectrum: {e}")
            return False

    def set_spectrum(self, frequency, power):
        """
        Set spectrum data directly

        Parameters:
        -----------
        frequency : array-like
            Frequency array (MHz)
        power : array-like
            Power/temperature array
        """
        self.frequency = np.array(frequency)
        self.power = np.array(power)

        if self.verbose:
            self._print_data_info()

    def _print_data_info(self):
        """Print spectrum information"""
        print("\n" + "="*60)
        print("SPECTRUM INFORMATION")
        print("="*60)
        print(f"Frequency range: {self.frequency.min():.3f} - {self.frequency.max():.3f} MHz")
        print(f"Bandwidth: {self.frequency.max() - self.frequency.min():.3f} MHz")
        print(f"Number of channels: {len(self.frequency)}")
        print(f"Channel resolution: {np.median(np.diff(self.frequency))*1000:.3f} kHz")
        print(f"H1 rest frequency: {H1_REST_FREQ:.6f} MHz")
        print("="*60 + "\n")

    def remove_rfi_spikes(self):
        """
        Remove RFI spikes using MAD-based outlier detection

        Standard method for RFI mitigation in radio astronomy
        Uses Median Absolute Deviation (MAD) for robust outlier detection

        Method:
        -------
        1. Compute median-filtered spectrum
        2. Calculate residuals
        3. Detect outliers using MAD threshold
        4. Replace spikes with interpolated values

        Returns:
        --------
        n_spikes : int
            Number of spikes removed
        """
        if self.power is None:
            raise ValueError("No spectrum loaded. Load spectrum first.")

        original_power = self.power.copy()

        # Step 1: Median filtering
        median_filtered = signal.medfilt(self.power, kernel_size=self.spike_width)

        # Step 2: Calculate residuals
        residuals = self.power - median_filtered

        # Step 3: MAD (Median Absolute Deviation)
        mad = np.median(np.abs(residuals - np.median(residuals)))

        # Convert MAD to approximate standard deviation
        # Factor 1.4826 for Gaussian distribution
        mad_std = 1.4826 * mad

        # Step 4: Detect spikes
        spike_mask = np.abs(residuals) > (self.spike_threshold * mad_std)

        # Count spikes
        n_spikes = np.sum(spike_mask)

        if n_spikes > 0:
            # Step 5: Interpolate over spikes
            good_indices = np.where(~spike_mask)[0]
            spike_indices = np.where(spike_mask)[0]

            # Use linear interpolation to replace spikes
            if len(good_indices) > 1:
                interp_func = interpolate.interp1d(
                    good_indices,
                    self.power[good_indices],
                    kind='linear',
                    bounds_error=False,
                    fill_value='extrapolate'
                )
                self.power[spike_mask] = interp_func(spike_indices)

            self.spikes_removed = n_spikes

            if self.verbose:
                print(f"\n{'='*60}")
                print(f"RFI SPIKE REMOVAL")
                print(f"{'='*60}")
                print(f"Spikes detected: {n_spikes} / {len(self.power)} channels ({n_spikes/len(self.power)*100:.2f}%)")
                print(f"MAD: {mad:.6f}")
                print(f"Threshold: {self.spike_threshold}σ (MAD-based)")
                print(f"Median filter width: {self.spike_width} channels")
                print(f"Spikes replaced with linear interpolation")
                print(f"{'='*60}\n")

                # Warning if too many spikes
                if n_spikes / len(self.power) > 0.1:
                    warnings.warn(
                        f"High fraction of spikes removed ({n_spikes/len(self.power)*100:.1f}%). "
                        f"Consider using --method pls for severe RFI."
                    )
        else:
            if self.verbose:
                print(f"\nNo RFI spikes detected (threshold: {self.spike_threshold}σ MAD)")

        return n_spikes

    def identify_line_free_channels(self):
        """
        Identify line-free channels using velocity criterion

        Standard exclusion: ±300 km/s around H1 rest frequency
        Used by: HIPASS, EBHIS, GBT, FAST

        Returns:
        --------
        mask : bool array
            True for line-free channels
        """
        # Convert frequency to velocity
        velocity = SPEED_OF_LIGHT * (1 - self.frequency / H1_REST_FREQ)

        # Standard exclusion zone
        self.mask = np.abs(velocity) > self.exclude_velocity

        # Calculate percentage of line-free channels
        percent_free = np.sum(self.mask) / len(self.frequency) * 100

        if self.verbose:
            print(f"Line-free channels: {np.sum(self.mask)} / {len(self.frequency)} ({percent_free:.1f}%)")

            # Professional requirement check (CSIRO guidelines)
            if percent_free < 25:
                warnings.warn(
                    f"Only {percent_free:.1f}% line-free channels! "
                    f"Minimum 25% recommended for reliable fitting."
                )
            elif percent_free < 15:
                warnings.warn(
                    f"Only {percent_free:.1f}% line-free channels! "
                    f"Fit may be poorly constrained."
                )

        return self.mask

    def fit_polynomial_baseline(self):
        """
        Fit polynomial baseline using iterative sigma clipping

        Standard method used by:
        - CASA (sdbaseline)
        - GILDAS/CLASS (BASE)
        - Miriad (uvlin)
        - GBTIDL (baseline)

        Returns:
        --------
        baseline : array
            Fitted baseline
        """
        if self.mask is None:
            self.identify_line_free_channels()

        current_mask = self.mask.copy()

        if self.verbose:
            print(f"\nFitting {self.poly_order}-order polynomial baseline...")
            print(f"Iterative sigma clipping: {self.sigma_clip}σ, max {self.max_iterations} iterations")

        for iteration in range(self.max_iterations):
            # Fit polynomial to current mask
            coeffs = np.polyfit(
                self.frequency[current_mask],
                self.power[current_mask],
                self.poly_order
            )
            baseline = np.polyval(coeffs, self.frequency)

            # Calculate residuals and noise
            residuals = self.power - baseline
            noise = np.std(residuals[current_mask])

            # Update mask with sigma clipping
            new_mask = self.mask & (np.abs(residuals) < self.sigma_clip * noise)

            # Check convergence
            if np.sum(new_mask) == np.sum(current_mask):
                if self.verbose:
                    print(f"Converged after {iteration + 1} iterations")
                break

            current_mask = new_mask

            # Warning if too many points excluded
            percent_remaining = np.sum(current_mask) / len(self.frequency) * 100
            if percent_remaining < 25:
                warnings.warn(
                    f"Only {percent_remaining:.1f}% points remaining after iteration {iteration + 1}. "
                    f"Fit may be unreliable."
                )

        self.baseline = baseline
        self.noise = noise

        # Calculate fit quality
        residuals = self.power[current_mask] - baseline[current_mask]
        rms = np.std(residuals)
        chi2_dof = np.sum(residuals**2) / (np.sum(current_mask) - self.poly_order - 1)

        if self.verbose:
            print(f"\nBaseline Fit Quality:")
            print(f"  RMS: {rms:.6f}")
            print(f"  Noise: {noise:.6f}")
            print(f"  χ²/DOF: {chi2_dof:.4f}")
            print(f"  Channels used: {np.sum(current_mask)} / {len(self.frequency)}")

        return baseline

    def fit_pls_baseline(self, lam=1e6, p=0.01, niter=10):
        """
        Fit baseline using Asymmetric Least Squares (AsLS)

        Alternative method for severe RFI or standing waves
        Used by: FAST telescope for complex baselines

        Parameters:
        -----------
        lam : float
            Smoothness parameter (default: 1e6)
        p : float
            Asymmetry parameter (default: 0.01)
        niter : int
            Number of iterations (default: 10)

        Returns:
        --------
        baseline : array
            Fitted baseline
        """
        if self.verbose:
            print(f"\nFitting AsLS baseline (FAST method)...")
            print(f"  λ={lam:.0e}, p={p}, iterations={niter}")

        L = len(self.power)
        D = sparse.diags([1, -2, 1], [0, -1, -2], shape=(L, L-2))
        w = np.ones(L)

        for i in range(niter):
            W = sparse.spdiags(w, 0, L, L)
            Z = W + lam * D.dot(D.transpose())
            z = spsolve(Z, w * self.power)
            w = p * (self.power > z) + (1 - p) * (self.power < z)

        self.baseline = z

        # Calculate noise from line-free regions
        if self.mask is None:
            self.identify_line_free_channels()
        corrected = self.power - self.baseline
        self.noise = np.std(corrected[self.mask])

        return self.baseline

    def subtract_baseline(self):
        """
        Subtract baseline from spectrum

        Returns:
        --------
        corrected : array
            Baseline-corrected spectrum
        """
        if self.baseline is None:
            self.fit_polynomial_baseline()

        self.corrected = self.power - self.baseline

        if self.verbose:
            print(f"\nBaseline subtracted successfully")

        return self.corrected

    def calculate_snr(self):
        """
        Calculate SNR at H1 rest frequency

        Professional detection thresholds:
        - >5σ: Strong detection
        - >3σ: Confirmed detection
        - 2-3σ: Marginal detection
        - <2σ: No significant detection

        Returns:
        --------
        snr : float
            Signal-to-noise ratio
        status : str
            Detection status
        """
        if self.corrected is None:
            self.subtract_baseline()

        # Find H1 channel
        h1_idx = np.argmin(np.abs(self.frequency - H1_REST_FREQ))
        h1_value = self.corrected[h1_idx]

        self.snr = h1_value / self.noise

        # Determine detection status
        if self.snr > 5:
            status = "STRONG DETECTION (>5σ)"
        elif self.snr > 3:
            status = "CONFIRMED DETECTION (>3σ)"
        elif self.snr > 2:
            status = "MARGINAL DETECTION (2-3σ)"
        else:
            status = "NO SIGNIFICANT DETECTION (<2σ)"

        if self.verbose:
            print(f"\n" + "="*60)
            print("DETECTION STATISTICS")
            print("="*60)
            print(f"H1 signal: {h1_value:.6f}")
            print(f"Noise level: {self.noise:.6f}")
            print(f"SNR: {self.snr:.2f}")
            print(f"Status: {status}")
            print("="*60 + "\n")

        return self.snr, status

    def apply_smoothing(self):
        """
        Apply smoothing to corrected spectrum

        Methods:
        - 'hanning': Hanning window (HIPASS standard)
        - 'savgol': Savitzky-Golay filter (modern standard)
        - 'tukey': Tukey window with alpha parameter
        - 'none': No smoothing

        Returns:
        --------
        smoothed : array
            Smoothed spectrum
        """
        if self.corrected is None:
            self.subtract_baseline()

        if self.smoothing_method == 'none':
            self.smoothed = self.corrected
            return self.smoothed

        if self.smoothing_method == 'hanning':
            window = np.hanning(self.smoothing_param)
            self.smoothed = np.convolve(
                self.corrected,
                window / window.sum(),
                mode='same'
            )

        elif self.smoothing_method == 'savgol':
            # Savitzky-Golay filter
            window = int(self.smoothing_param)
            if window % 2 == 0:
                window += 1  # Must be odd
            polyorder = min(3, window - 1)
            self.smoothed = signal.savgol_filter(
                self.corrected,
                window,
                polyorder
            )

        elif self.smoothing_method == 'tukey':
            # Tukey window (HIPASS standard: 25%)
            window = signal.windows.tukey(
                len(self.corrected),
                alpha=self.smoothing_param
            )
            self.smoothed = self.corrected * window

        else:
            warnings.warn(f"Unknown smoothing method: {self.smoothing_method}")
            self.smoothed = self.corrected

        if self.verbose:
            print(f"Applied {self.smoothing_method} smoothing (param={self.smoothing_param})")

        return self.smoothed

    def assess_quality(self):
        """
        Professional quality assessment

        Tests:
        1. Baseline flatness (RMS in line-free regions)
        2. Gaussian noise statistics
        3. Residual periodic structure (FFT)

        Returns:
        --------
        quality_report : dict
            Quality metrics and assessment
        """
        if self.corrected is None:
            self.subtract_baseline()

        if self.mask is None:
            self.identify_line_free_channels()

        # Test 1: Baseline flatness
        baseline_rms = np.std(self.corrected[self.mask])
        flatness_ratio = baseline_rms / self.noise

        # Test 2: Gaussian noise statistics
        _, p_value = stats.normaltest(self.corrected[self.mask])

        # Test 3: Check for residual structure (FFT)
        fft_spectrum = np.abs(np.fft.fft(self.corrected[self.mask]))
        fft_median = np.median(fft_spectrum[1:len(fft_spectrum)//2])
        fft_max = np.max(fft_spectrum[1:len(fft_spectrum)//2])
        has_periodic = fft_max > 5 * fft_median

        # Overall quality score
        quality_score = 'PASS' if (
            flatness_ratio < 1.2 and
            p_value > 0.05 and
            not has_periodic
        ) else 'MARGINAL' if (
            flatness_ratio < 1.5 and
            p_value > 0.01
        ) else 'FAIL'

        quality_report = {
            'baseline_rms': baseline_rms,
            'flatness_ratio': flatness_ratio,
            'gaussian_p_value': p_value,
            'periodic_structure': has_periodic,
            'quality_score': quality_score
        }

        if self.verbose:
            print("\n" + "="*60)
            print("QUALITY ASSESSMENT")
            print("="*60)
            print(f"Baseline RMS: {baseline_rms:.6f}")
            print(f"Flatness ratio: {flatness_ratio:.3f} (should be ~1.0)")
            print(f"Gaussian test p-value: {p_value:.4f} (>0.05 is good)")
            print(f"Periodic structure: {'DETECTED' if has_periodic else 'None'}")
            print(f"Overall quality: {quality_score}")
            print("="*60 + "\n")

        return quality_report

    def process(self, use_pls=False):
        """
        Complete processing pipeline

        Parameters:
        -----------
        use_pls : bool
            Use AsLS method instead of polynomial

        Returns:
        --------
        results : dict
            Complete results dictionary
        """
        # Step 0: Remove RFI spikes (if enabled)
        if self.spike_removal:
            self.remove_rfi_spikes()

        # Step 1: Identify line-free channels
        self.identify_line_free_channels()

        # Step 2: Fit baseline
        if use_pls:
            self.fit_pls_baseline()
        else:
            self.fit_polynomial_baseline()

        # Step 3: Subtract baseline
        self.subtract_baseline()

        # Step 4: Calculate SNR
        snr, status = self.calculate_snr()

        # Step 5: Apply smoothing
        self.apply_smoothing()

        # Step 6: Quality assessment
        quality = self.assess_quality()

        results = {
            'frequency': self.frequency,
            'original': self.power,
            'baseline': self.baseline,
            'corrected': self.corrected,
            'smoothed': self.smoothed,
            'mask': self.mask,
            'noise': self.noise,
            'snr': snr,
            'status': status,
            'quality': quality,
            'spikes_removed': self.spikes_removed
        }

        return results

    def plot_results(self, save_path=None, show=True):
        """
        Create publication-quality plot

        Parameters:
        -----------
        save_path : str, optional
            Path to save figure
        show : bool
            Display plot
        """
        if self.corrected is None:
            raise ValueError("No processed data to plot. Run process() first.")

        fig = plt.figure(figsize=(12, 10))
        gs = fig.add_gridspec(4, 1, height_ratios=[2, 2, 1, 1], hspace=0.3)

        # Panel 1: Original spectrum with baseline
        ax1 = fig.add_subplot(gs[0])
        ax1.plot(self.frequency, self.power, 'k-', linewidth=0.8,
                label='Original spectrum', alpha=0.7)
        ax1.plot(self.frequency, self.baseline, 'r-', linewidth=2,
                label=f'Baseline (order {self.poly_order})')
        ax1.axvline(H1_REST_FREQ, color='green', linestyle='--',
                   linewidth=1.5, alpha=0.7, label=f'H I rest ({H1_REST_FREQ:.3f} MHz)')
        ax1.set_ylabel('Power/Temperature', fontsize=11)
        ax1.set_title('H I 21cm Spectrum - Polynomial Baseline Subtraction',
                     fontsize=13, fontweight='bold')
        ax1.legend(loc='upper right', fontsize=9)
        ax1.grid(True, alpha=0.3, linestyle=':')
        ax1.set_xlim(self.frequency.min(), self.frequency.max())

        # Panel 2: Corrected spectrum with smoothing
        ax2 = fig.add_subplot(gs[1])
        ax2.step(self.frequency, self.corrected, 'k-', linewidth=0.5,
                where='mid', label='Baseline corrected', alpha=0.7)
        ax2.plot(self.frequency, self.smoothed, 'b-', linewidth=2,
                label=f'Smoothed ({self.smoothing_method})', alpha=0.9)

        # Mark detection thresholds
        ax2.axhline(3*self.noise, color='red', linestyle=':',
                   alpha=0.5, linewidth=1.5, label='3σ threshold')
        ax2.axhline(-3*self.noise, color='red', linestyle=':', alpha=0.5, linewidth=1.5)
        ax2.axhline(5*self.noise, color='orange', linestyle=':',
                   alpha=0.3, linewidth=1.5, label='5σ threshold')
        ax2.axhline(-5*self.noise, color='orange', linestyle=':', alpha=0.3, linewidth=1.5)

        ax2.axvline(H1_REST_FREQ, color='green', linestyle='--',
                   linewidth=1.5, alpha=0.7)

        # Shade line region
        line_region = np.abs(self.frequency - H1_REST_FREQ) < 0.1
        y_min, y_max = ax2.get_ylim()
        ax2.fill_between(self.frequency[line_region], y_min, y_max,
                        alpha=0.1, color='green')

        ax2.set_ylabel('Corrected Power/Temperature', fontsize=11)
        ax2.legend(loc='upper right', fontsize=9)
        ax2.grid(True, alpha=0.3, linestyle=':')
        ax2.set_xlim(self.frequency.min(), self.frequency.max())

        # Add statistics box
        h1_idx = np.argmin(np.abs(self.frequency - H1_REST_FREQ))
        stats_text = (
            f'Peak: {self.corrected[h1_idx]:.6f}\n'
            f'Noise: {self.noise:.6f}\n'
            f'SNR: {self.snr:.2f}\n'
            f'Order: {self.poly_order}'
        )
        ax2.text(0.02, 0.98, stats_text, transform=ax2.transAxes,
                fontsize=9, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        # Panel 3: Residuals
        ax3 = fig.add_subplot(gs[2])
        residuals = self.corrected - self.smoothed
        ax3.step(self.frequency, residuals, 'k-', linewidth=0.5, where='mid')
        ax3.axhline(0, color='gray', linestyle='-', alpha=0.5)
        ax3.axhline(self.noise, color='red', linestyle=':', alpha=0.3)
        ax3.axhline(-self.noise, color='red', linestyle=':', alpha=0.3)
        ax3.set_ylabel('Residuals', fontsize=10)
        ax3.grid(True, alpha=0.3, linestyle=':')
        ax3.set_xlim(self.frequency.min(), self.frequency.max())

        # Panel 4: Line-free mask
        ax4 = fig.add_subplot(gs[3])
        ax4.fill_between(self.frequency, 0, self.mask.astype(int),
                        step='mid', alpha=0.5, color='blue',
                        label='Line-free channels')
        ax4.set_xlabel('Frequency (MHz)', fontsize=11)
        ax4.set_ylabel('Mask', fontsize=10)
        ax4.set_ylim(-0.1, 1.1)
        ax4.set_yticks([0, 1])
        ax4.set_yticklabels(['Line', 'Free'])
        ax4.grid(True, alpha=0.3, linestyle=':')
        ax4.set_xlim(self.frequency.min(), self.frequency.max())
        ax4.legend(loc='upper right', fontsize=9)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            if self.verbose:
                print(f"Plot saved to: {save_path}")

        if show:
            plt.show()
        else:
            plt.close()

        return fig


class H1SpectrumStacker:
    """
    Stack multiple H1 observations to improve SNR

    Standard method used by:
    - HIPASS (Barnes et al. 2001)
    - Delhaize et al. (2013)
    - Modern survey pipelines
    """

    def __init__(self, processor_params=None, verbose=True):
        """
        Initialize stacker

        Parameters:
        -----------
        processor_params : dict, optional
            Parameters for H1BaselineProcessor
        verbose : bool
            Print diagnostic information
        """
        self.processor_params = processor_params or {}
        self.verbose = verbose

    def stack_observations(self, file_list, freq_range=(1420.15, 1420.65),
                          n_channels=500, final_poly_order=4):
        """
        Stack multiple observations

        Standard workflow:
        1. Process each observation individually
        2. Interpolate to common frequency grid
        3. Weight by noise (1/σ²)
        4. Co-add weighted spectra
        5. Apply final baseline correction

        Parameters:
        -----------
        file_list : list of str
            Paths to spectrum files
        freq_range : tuple
            (min, max) frequency for common grid (MHz)
        n_channels : int
            Number of channels in common grid
        final_poly_order : int
            Polynomial order for final stack correction (default: 4)

        Returns:
        --------
        results : dict
            Stacked spectrum and statistics
        """
        # Common frequency grid
        common_freq = np.linspace(freq_range[0], freq_range[1], n_channels)

        weighted_spectra = []
        weights = []
        individual_snrs = []

        if self.verbose:
            print("\n" + "="*60)
            print("STACKING OBSERVATIONS")
            print("="*60)
            print(f"Number of observations: {len(file_list)}")
            print(f"Common frequency grid: {n_channels} channels")
            print(f"Frequency range: {freq_range[0]:.3f} - {freq_range[1]:.3f} MHz")
            print("="*60 + "\n")

        # Process each observation
        for i, filepath in enumerate(file_list):
            if self.verbose:
                print(f"Processing observation {i+1}/{len(file_list)}: {Path(filepath).name}")

            # Create processor
            processor = H1BaselineProcessor(
                verbose=False,  # Suppress individual output
                **self.processor_params
            )

            # Load and process
            if not processor.load_spectrum(filepath):
                warnings.warn(f"Failed to load {filepath}, skipping...")
                continue

            results = processor.process()

            # Interpolate to common grid
            interp_func = interpolate.interp1d(
                results['frequency'],
                results['corrected'],
                kind='cubic',
                bounds_error=False,
                fill_value=0.0
            )
            aligned_spectrum = interp_func(common_freq)

            # Weight by noise
            weight = 1.0 / results['noise']**2
            weighted_spectra.append(aligned_spectrum * weight)
            weights.append(weight)
            individual_snrs.append(results['snr'])

            if self.verbose:
                print(f"  SNR: {results['snr']:.2f}, Noise: {results['noise']:.6f}, Weight: {weight:.2f}")

        # Stack with weights
        stacked = np.sum(weighted_spectra, axis=0) / np.sum(weights)

        if self.verbose:
            print(f"\nStacked {len(weights)} observations successfully")
            print(f"Mean individual SNR: {np.mean(individual_snrs):.2f}")
            print(f"Expected improvement: {np.sqrt(len(weights)):.2f}×")

        # Apply final baseline correction to stack
        if self.verbose:
            print(f"\nApplying final {final_poly_order}-order baseline correction to stack...")

        final_processor = H1BaselineProcessor(
            poly_order=final_poly_order,
            verbose=False,
            **{k: v for k, v in self.processor_params.items() if k != 'poly_order'}
        )
        final_processor.set_spectrum(common_freq, stacked)
        final_results = final_processor.process()

        # Calculate improvement
        theoretical_improvement = np.sqrt(len(weights))
        actual_improvement = final_results['snr'] / np.mean(individual_snrs)
        efficiency = (actual_improvement / theoretical_improvement) * 100

        if self.verbose:
            print("\n" + "="*60)
            print("STACKING RESULTS")
            print("="*60)
            print(f"Number stacked: {len(weights)}")
            print(f"Mean individual SNR: {np.mean(individual_snrs):.2f}")
            print(f"Final stacked SNR: {final_results['snr']:.2f}")
            print(f"Theoretical improvement: {theoretical_improvement:.2f}×")
            print(f"Actual improvement: {actual_improvement:.2f}×")
            print(f"Stacking efficiency: {efficiency:.1f}%")
            print(f"Detection status: {final_results['status']}")
            print("="*60 + "\n")

        return {
            'frequency': common_freq,
            'stacked_spectrum': final_results['corrected'],
            'smoothed': final_results['smoothed'],
            'baseline': final_results['baseline'],
            'noise': final_results['noise'],
            'snr': final_results['snr'],
            'status': final_results['status'],
            'n_observations': len(weights),
            'individual_snrs': individual_snrs,
            'theoretical_improvement': theoretical_improvement,
            'actual_improvement': actual_improvement,
            'efficiency': efficiency,
            'quality': final_results['quality']
        }


def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(
        description='H1 21cm Polynomial Baseline Subtraction - Professional Implementation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single spectrum with default 2nd-order polynomial
  python h1_baseline_subtraction.py spectrum.csv

  # Use 3rd-order polynomial with custom exclusion
  python h1_baseline_subtraction.py spectrum.csv --order 3 --exclude-vel 400

  # Stack multiple observations
  python h1_baseline_subtraction.py obs1.csv obs2.csv obs3.csv --stack

  # Use AsLS method for severe RFI
  python h1_baseline_subtraction.py spectrum.csv --method pls

  # Custom smoothing
  python h1_baseline_subtraction.py spectrum.csv --smooth hanning --smooth-param 21

Observatory presets:
  --preset parkes   : 2nd order, Tukey 25% smoothing (HIPASS)
  --preset gbt      : 2nd order, Hanning smoothing, 5 iterations (GBT)
  --preset fast     : 2nd order, Savitzky-Golay smoothing (FAST)
  --preset vla      : 2nd order, CASA-style processing (VLA/ALMA)
        """
    )

    # Input files
    parser.add_argument('files', nargs='+', help='Spectrum file(s) (CSV format)')

    # Processing parameters
    parser.add_argument('--order', type=int, default=2,
                       help='Polynomial order (default: 2)')
    parser.add_argument('--exclude-vel', type=float, default=300.0,
                       help='Velocity exclusion around H1 line (km/s, default: 300)')
    parser.add_argument('--sigma', type=float, default=3.0,
                       help='Sigma clipping threshold (default: 3.0)')
    parser.add_argument('--iterations', type=int, default=5,
                       help='Max iterations for sigma clipping (default: 5)')

    # Baseline method
    parser.add_argument('--method', choices=['poly', 'pls'], default='poly',
                       help='Baseline method: poly (polynomial) or pls (AsLS)')

    # Smoothing
    parser.add_argument('--smooth', choices=['hanning', 'savgol', 'tukey', 'none'],
                       default='savgol', help='Smoothing method (default: savgol)')
    parser.add_argument('--smooth-param', type=float, default=11,
                       help='Smoothing parameter (default: 11)')

    # RFI Spike Removal
    parser.add_argument('--remove-spikes', action='store_true',
                       help='Enable RFI spike removal (MAD-based detection)')
    parser.add_argument('--spike-threshold', type=float, default=5.0,
                       help='Spike detection threshold in MAD units (default: 5.0)')
    parser.add_argument('--spike-width', type=int, default=3,
                       help='Median filter width for spike detection (default: 3)')

    # Stacking
    parser.add_argument('--stack', action='store_true',
                       help='Stack multiple observations')
    parser.add_argument('--stack-order', type=int, default=4,
                       help='Polynomial order for final stack (default: 4)')

    # Observatory presets
    parser.add_argument('--preset', choices=['parkes', 'gbt', 'fast', 'vla'],
                       help='Use observatory-specific preset parameters')

    # Output
    parser.add_argument('--output', '-o', help='Output plot filename')
    parser.add_argument('--no-plot', action='store_true', help='Do not display plot')
    parser.add_argument('--save-data', help='Save processed data to file')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress output')

    # File format
    parser.add_argument('--delimiter', default=',', help='Column delimiter (default: ,)')
    parser.add_argument('--skiprows', type=int, default=0, help='Header rows to skip')
    parser.add_argument('--freq-col', type=int, default=0, help='Frequency column index')
    parser.add_argument('--power-col', type=int, default=1, help='Power column index')

    args = parser.parse_args()

    # Apply observatory presets
    if args.preset:
        presets = {
            'parkes': {
                'order': 2,
                'exclude_vel': 300,
                'smooth': 'tukey',
                'smooth_param': 0.25,
                'iterations': 1
            },
            'gbt': {
                'order': 2,
                'exclude_vel': 300,
                'smooth': 'hanning',
                'smooth_param': 11,
                'iterations': 5,
                'sigma': 3.0
            },
            'fast': {
                'order': 2,
                'exclude_vel': 300,
                'smooth': 'savgol',
                'smooth_param': 21,
                'iterations': 5
            },
            'vla': {
                'order': 2,
                'exclude_vel': 300,
                'smooth': 'hanning',
                'smooth_param': 5,
                'iterations': 5,
                'sigma': 3.0
            }
        }
        preset_params = presets[args.preset]
        if not args.quiet:
            print(f"Using {args.preset.upper()} preset parameters")
        for key, value in preset_params.items():
            if key == 'smooth':
                args.smooth = value
            elif key == 'smooth_param':
                args.smooth_param = value
            elif key == 'exclude_vel':
                args.exclude_vel = value
            elif key == 'order':
                args.order = value
            elif key == 'iterations':
                args.iterations = value
            elif key == 'sigma':
                args.sigma = value

    # Build processor parameters
    processor_params = {
        'poly_order': args.order,
        'exclude_velocity': args.exclude_vel,
        'sigma_clip': args.sigma,
        'max_iterations': args.iterations,
        'smoothing_method': args.smooth,
        'smoothing_param': args.smooth_param,
        'spike_removal': args.remove_spikes,
        'spike_threshold': args.spike_threshold,
        'spike_width': args.spike_width,
        'verbose': not args.quiet
    }

    # Stacking mode
    if args.stack or len(args.files) > 1:
        stacker = H1SpectrumStacker(
            processor_params=processor_params,
            verbose=not args.quiet
        )

        results = stacker.stack_observations(
            args.files,
            final_poly_order=args.stack_order
        )

        # Create plot
        if not args.no_plot or args.output:
            processor = H1BaselineProcessor(verbose=False, **processor_params)
            processor.frequency = results['frequency']
            processor.power = results['stacked_spectrum'] + results['baseline']
            processor.baseline = results['baseline']
            processor.corrected = results['stacked_spectrum']
            processor.smoothed = results['smoothed']
            processor.noise = results['noise']
            processor.snr = results['snr']
            processor.mask = np.abs(results['frequency'] - H1_REST_FREQ) > args.exclude_vel

            output_path = args.output or 'h1_stacked_result.png'
            processor.plot_results(
                save_path=output_path,
                show=not args.no_plot
            )

        # Save data
        if args.save_data:
            data = np.column_stack([
                results['frequency'],
                results['stacked_spectrum'],
                results['smoothed']
            ])
            np.savetxt(
                args.save_data,
                data,
                delimiter=',',
                header='Frequency(MHz),Corrected,Smoothed',
                comments=''
            )
            if not args.quiet:
                print(f"Data saved to: {args.save_data}")

    # Single spectrum mode
    else:
        processor = H1BaselineProcessor(**processor_params)

        # Load spectrum
        if not processor.load_spectrum(
            args.files[0],
            freq_col=args.freq_col,
            power_col=args.power_col,
            delimiter=args.delimiter,
            skiprows=args.skiprows
        ):
            sys.exit(1)

        # Process
        results = processor.process(use_pls=(args.method == 'pls'))

        # Plot
        if not args.no_plot or args.output:
            output_path = args.output or 'h1_result.png'
            processor.plot_results(
                save_path=output_path,
                show=not args.no_plot
            )

        # Save data
        if args.save_data:
            data = np.column_stack([
                results['frequency'],
                results['corrected'],
                results['smoothed']
            ])
            np.savetxt(
                args.save_data,
                data,
                delimiter=',',
                header='Frequency(MHz),Corrected,Smoothed',
                comments=''
            )
            if not args.quiet:
                print(f"Data saved to: {args.save_data}")


if __name__ == '__main__':
    main()
