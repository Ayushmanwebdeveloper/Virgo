#!/usr/bin/env python3
"""
Example Usage of H1 Baseline Subtraction Script

Demonstrates various use cases and parameter combinations
Based on observatory-standard practices
"""

import numpy as np
import matplotlib.pyplot as plt
from h1_baseline_subtraction import H1BaselineProcessor, H1SpectrumStacker


def generate_synthetic_h1_spectrum(snr=3.0, baseline_type='quadratic',
                                   add_rfi=False, freq_range=(1420.0, 1421.0),
                                   n_channels=500):
    """
    Generate synthetic H1 spectrum for testing

    Parameters:
    -----------
    snr : float
        Signal-to-noise ratio for H1 line
    baseline_type : str
        Type of baseline: 'linear', 'quadratic', 'cubic'
    add_rfi : bool
        Add RFI spikes
    freq_range : tuple
        (min, max) frequency in MHz
    n_channels : int
        Number of spectral channels
    """
    # Frequency array
    freq = np.linspace(freq_range[0], freq_range[1], n_channels)

    # Generate baseline
    if baseline_type == 'linear':
        baseline = 10.0 + 0.5 * (freq - 1420.0)
    elif baseline_type == 'quadratic':
        baseline = 10.0 + 0.5 * (freq - 1420.0) - 0.3 * (freq - 1420.0)**2
    elif baseline_type == 'cubic':
        baseline = 10.0 + 0.5 * (freq - 1420.0) - 0.3 * (freq - 1420.0)**2 + 0.1 * (freq - 1420.0)**3
    else:
        baseline = np.ones_like(freq) * 10.0

    # Generate H1 Gaussian line
    h1_freq = 1420.405751  # MHz
    line_width = 0.05  # MHz (FWHM)
    sigma = line_width / 2.355

    # Noise level
    noise_level = 0.1

    # Signal amplitude from desired SNR
    signal_amplitude = snr * noise_level

    h1_line = signal_amplitude * np.exp(-0.5 * ((freq - h1_freq) / sigma)**2)

    # Add noise
    noise = np.random.normal(0, noise_level, n_channels)

    # Combine
    spectrum = baseline + h1_line + noise

    # Add RFI if requested
    if add_rfi:
        # Add a few strong spikes
        rfi_positions = np.random.choice(n_channels, 5, replace=False)
        for pos in rfi_positions:
            spectrum[pos] += np.random.uniform(0.5, 2.0)

    return freq, spectrum


def example_1_basic_usage():
    """
    Example 1: Basic usage with default parameters (2nd order polynomial)

    Most common case: Standard H1 observation with clean data
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Usage - 2nd Order Polynomial (Standard)")
    print("="*70)

    # Generate synthetic data
    freq, power = generate_synthetic_h1_spectrum(snr=3.0, baseline_type='quadratic')

    # Save to file for demonstration
    np.savetxt('synthetic_spectrum.csv', np.column_stack([freq, power]),
               delimiter=',', header='Frequency(MHz),Power')

    # Initialize processor with default parameters
    processor = H1BaselineProcessor(
        poly_order=2,           # 2nd order (60% of observations use this)
        exclude_velocity=300.0,  # Standard ±300 km/s exclusion
        sigma_clip=3.0,         # 3-sigma clipping
        max_iterations=5,       # Up to 5 iterations
        smoothing_method='savgol',
        smoothing_param=11,
        verbose=True
    )

    # Load and process
    processor.set_spectrum(freq, power)
    results = processor.process()

    # Create plot
    processor.plot_results(save_path='example1_result.png', show=False)

    print("\nResult saved to: example1_result.png")
    print(f"SNR achieved: {results['snr']:.2f}")
    print(f"Detection: {results['status']}")


def example_2_observatory_presets():
    """
    Example 2: Using observatory-specific presets

    Demonstrates standard parameters from major observatories
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Observatory Presets")
    print("="*70)

    freq, power = generate_synthetic_h1_spectrum(snr=2.5, baseline_type='quadratic')

    # Compare different observatory methods
    presets = {
        'Parkes (HIPASS)': {
            'poly_order': 2,
            'exclude_velocity': 300,
            'smoothing_method': 'tukey',
            'smoothing_param': 0.25,
            'max_iterations': 1
        },
        'Green Bank Telescope': {
            'poly_order': 2,
            'exclude_velocity': 300,
            'smoothing_method': 'hanning',
            'smoothing_param': 11,
            'max_iterations': 5,
            'sigma_clip': 3.0
        },
        'FAST': {
            'poly_order': 2,
            'exclude_velocity': 300,
            'smoothing_method': 'savgol',
            'smoothing_param': 21,
            'max_iterations': 5
        },
        'VLA/ALMA (CASA)': {
            'poly_order': 2,
            'exclude_velocity': 300,
            'smoothing_method': 'hanning',
            'smoothing_param': 5,
            'max_iterations': 5,
            'sigma_clip': 3.0
        }
    }

    for name, params in presets.items():
        print(f"\n--- {name} ---")
        processor = H1BaselineProcessor(verbose=False, **params)
        processor.set_spectrum(freq, power)
        results = processor.process()
        print(f"SNR: {results['snr']:.2f} | Status: {results['status']}")


def example_3_polynomial_order_comparison():
    """
    Example 3: Comparing different polynomial orders

    Shows when to use 1st, 2nd, 3rd order polynomials
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: Polynomial Order Comparison")
    print("="*70)

    # Test different baseline types
    baseline_types = [
        ('linear', 1, "Linear baseline → 1st order"),
        ('quadratic', 2, "Quadratic baseline → 2nd order"),
        ('cubic', 3, "Cubic baseline → 3rd order")
    ]

    fig, axes = plt.subplots(3, 1, figsize=(12, 10))

    for idx, (baseline_type, best_order, title) in enumerate(baseline_types):
        freq, power = generate_synthetic_h1_spectrum(
            snr=3.0,
            baseline_type=baseline_type
        )

        print(f"\n{title}")

        # Try different orders
        orders = [1, 2, 3]
        for order in orders:
            processor = H1BaselineProcessor(
                poly_order=order,
                verbose=False
            )
            processor.set_spectrum(freq, power)
            results = processor.process()

            quality = results['quality']['quality_score']
            print(f"  Order {order}: SNR={results['snr']:.2f}, Quality={quality}")

            # Plot best order
            if order == best_order:
                axes[idx].plot(freq, results['corrected'], 'b-', linewidth=1,
                             label=f'Corrected (order {order})')
                axes[idx].plot(freq, results['smoothed'], 'r-', linewidth=2,
                             label='Smoothed')
                axes[idx].axhline(0, color='gray', linestyle='--', alpha=0.5)
                axes[idx].axhline(3*results['noise'], color='red', linestyle=':', alpha=0.5)
                axes[idx].set_title(title)
                axes[idx].legend()
                axes[idx].grid(True, alpha=0.3)
                axes[idx].set_ylabel('Corrected Power')

    axes[2].set_xlabel('Frequency (MHz)')
    plt.tight_layout()
    plt.savefig('example3_order_comparison.png', dpi=300, bbox_inches='tight')
    print("\nComparison plot saved to: example3_order_comparison.png")
    plt.close()


def example_4_rfi_handling():
    """
    Example 4: Handling RFI with iterative sigma clipping

    Demonstrates robustness of iterative fitting
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: RFI Handling with Sigma Clipping")
    print("="*70)

    # Generate spectrum with RFI
    freq, power = generate_synthetic_h1_spectrum(
        snr=3.0,
        baseline_type='quadratic',
        add_rfi=True
    )

    print("\nWithout iterative clipping:")
    processor_no_iter = H1BaselineProcessor(
        poly_order=2,
        max_iterations=1,  # No iteration
        verbose=False
    )
    processor_no_iter.set_spectrum(freq, power)
    results_no_iter = processor_no_iter.process()
    print(f"SNR: {results_no_iter['snr']:.2f}")
    print(f"Quality: {results_no_iter['quality']['quality_score']}")

    print("\nWith iterative sigma clipping (5 iterations):")
    processor_iter = H1BaselineProcessor(
        poly_order=2,
        max_iterations=5,  # 5 iterations
        sigma_clip=3.0,
        verbose=False
    )
    processor_iter.set_spectrum(freq, power)
    results_iter = processor_iter.process()
    print(f"SNR: {results_iter['snr']:.2f}")
    print(f"Quality: {results_iter['quality']['quality_score']}")

    # Plot comparison
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

    ax1.plot(freq, power, 'k-', linewidth=0.5, alpha=0.5, label='Original')
    ax1.plot(freq, results_no_iter['corrected'], 'b-', linewidth=1,
            label='No iteration')
    ax1.plot(freq, results_no_iter['smoothed'], 'r-', linewidth=2)
    ax1.axhline(3*results_no_iter['noise'], color='red', linestyle=':', alpha=0.5)
    ax1.set_title('Without Iterative Clipping')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.plot(freq, power, 'k-', linewidth=0.5, alpha=0.5, label='Original')
    ax2.plot(freq, results_iter['corrected'], 'b-', linewidth=1,
            label='With 5 iterations')
    ax2.plot(freq, results_iter['smoothed'], 'r-', linewidth=2)
    ax2.axhline(3*results_iter['noise'], color='red', linestyle=':', alpha=0.5)
    ax2.set_title('With Iterative Sigma Clipping (Standard)')
    ax2.set_xlabel('Frequency (MHz)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('example4_rfi_handling.png', dpi=300, bbox_inches='tight')
    print("\nComparison saved to: example4_rfi_handling.png")
    plt.close()


def example_5_signal_stacking():
    """
    Example 5: Stacking multiple observations

    Standard method for weak signal detection
    Expected SNR improvement: √N
    """
    print("\n" + "="*70)
    print("EXAMPLE 5: Signal Stacking for Weak Signals")
    print("="*70)

    # Generate multiple weak observations
    n_observations = 15
    individual_snr = 0.5  # Very weak individual detection

    print(f"\nGenerating {n_observations} observations with SNR={individual_snr}")

    observation_files = []
    for i in range(n_observations):
        freq, power = generate_synthetic_h1_spectrum(
            snr=individual_snr,
            baseline_type='quadratic'
        )
        filename = f'weak_obs_{i+1}.csv'
        np.savetxt(filename, np.column_stack([freq, power]), delimiter=',')
        observation_files.append(filename)

    # Stack observations
    stacker = H1SpectrumStacker(
        processor_params={
            'poly_order': 2,
            'exclude_velocity': 300,
            'smoothing_method': 'savgol',
            'smoothing_param': 11
        },
        verbose=True
    )

    results = stacker.stack_observations(
        observation_files,
        final_poly_order=4  # Use higher order for final stack
    )

    print(f"\nTheoretical SNR improvement: {results['theoretical_improvement']:.2f}×")
    print(f"Actual SNR improvement: {results['actual_improvement']:.2f}×")
    print(f"Stacking efficiency: {results['efficiency']:.1f}%")
    print(f"Final SNR: {results['snr']:.2f}")
    print(f"Detection: {results['status']}")

    # Clean up temporary files
    import os
    for f in observation_files:
        os.remove(f)


def example_6_alternative_pls_method():
    """
    Example 6: Alternative AsLS baseline method for severe RFI

    Penalized Least Squares method used by FAST for difficult cases
    """
    print("\n" + "="*70)
    print("EXAMPLE 6: Alternative AsLS Method (FAST)")
    print("="*70)

    # Generate spectrum with complex baseline ripples
    freq = np.linspace(1420.0, 1421.0, 500)

    # Complex baseline with ripples (simulating standing waves)
    baseline = 10.0 + 0.5 * (freq - 1420.0) - 0.3 * (freq - 1420.0)**2
    baseline += 0.2 * np.sin(2 * np.pi * 5 * (freq - 1420.0))  # Standing wave

    # H1 line
    h1_freq = 1420.405751
    h1_line = 0.3 * np.exp(-0.5 * ((freq - h1_freq) / 0.02)**2)

    # Noise
    noise = np.random.normal(0, 0.1, 500)

    # Strong RFI
    rfi_positions = np.random.choice(500, 10, replace=False)
    for pos in rfi_positions:
        noise[pos] += np.random.uniform(0.5, 1.5)

    spectrum = baseline + h1_line + noise

    print("\nStandard polynomial method:")
    processor_poly = H1BaselineProcessor(
        poly_order=3,
        verbose=False
    )
    processor_poly.set_spectrum(freq, spectrum)
    results_poly = processor_poly.process(use_pls=False)
    print(f"SNR: {results_poly['snr']:.2f}")
    print(f"Quality: {results_poly['quality']['quality_score']}")

    print("\nAsLS method (better for complex baselines):")
    processor_pls = H1BaselineProcessor(
        poly_order=3,
        verbose=False
    )
    processor_pls.set_spectrum(freq, spectrum)
    results_pls = processor_pls.process(use_pls=True)
    print(f"SNR: {results_pls['snr']:.2f}")
    print(f"Quality: {results_pls['quality']['quality_score']}")

    # Plot comparison
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

    ax1.plot(freq, results_poly['corrected'], 'b-', linewidth=1, label='Polynomial')
    ax1.plot(freq, results_poly['smoothed'], 'r-', linewidth=2)
    ax1.axhline(3*results_poly['noise'], color='red', linestyle=':', alpha=0.5)
    ax1.set_title('Standard Polynomial Method')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.plot(freq, results_pls['corrected'], 'b-', linewidth=1, label='AsLS')
    ax2.plot(freq, results_pls['smoothed'], 'r-', linewidth=2)
    ax2.axhline(3*results_pls['noise'], color='red', linestyle=':', alpha=0.5)
    ax2.set_title('AsLS Method (FAST)')
    ax2.set_xlabel('Frequency (MHz)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('example6_pls_comparison.png', dpi=300, bbox_inches='tight')
    print("\nComparison saved to: example6_pls_comparison.png")
    plt.close()


def example_7_quality_assessment():
    """
    Example 7: Professional quality assessment metrics
    """
    print("\n" + "="*70)
    print("EXAMPLE 7: Quality Assessment")
    print("="*70)

    # Good quality data
    freq_good, power_good = generate_synthetic_h1_spectrum(
        snr=5.0,
        baseline_type='quadratic',
        add_rfi=False
    )

    processor_good = H1BaselineProcessor(poly_order=2, verbose=False)
    processor_good.set_spectrum(freq_good, power_good)
    results_good = processor_good.process()

    print("\nGood Quality Data:")
    quality = results_good['quality']
    print(f"  Baseline RMS: {quality['baseline_rms']:.6f}")
    print(f"  Flatness ratio: {quality['flatness_ratio']:.3f} (should be ~1.0)")
    print(f"  Gaussian p-value: {quality['gaussian_p_value']:.4f} (>0.05 is good)")
    print(f"  Periodic structure: {quality['periodic_structure']}")
    print(f"  Overall quality: {quality['quality_score']}")

    # Poor quality data (wrong polynomial order)
    freq_poor, power_poor = generate_synthetic_h1_spectrum(
        snr=3.0,
        baseline_type='cubic',  # Cubic baseline
        add_rfi=True
    )

    processor_poor = H1BaselineProcessor(
        poly_order=1,  # Too low order for cubic baseline!
        verbose=False
    )
    processor_poor.set_spectrum(freq_poor, power_poor)
    results_poor = processor_poor.process()

    print("\nPoor Quality Data (wrong polynomial order):")
    quality_poor = results_poor['quality']
    print(f"  Baseline RMS: {quality_poor['baseline_rms']:.6f}")
    print(f"  Flatness ratio: {quality_poor['flatness_ratio']:.3f} (>1.2 indicates problem)")
    print(f"  Gaussian p-value: {quality_poor['gaussian_p_value']:.4f}")
    print(f"  Periodic structure: {quality_poor['periodic_structure']}")
    print(f"  Overall quality: {quality_poor['quality_score']}")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("H1 21cm BASELINE SUBTRACTION - EXAMPLE DEMONSTRATIONS")
    print("Professional Observatory-Level Implementation")
    print("="*70)

    # Run all examples
    example_1_basic_usage()
    example_2_observatory_presets()
    example_3_polynomial_order_comparison()
    example_4_rfi_handling()
    example_5_signal_stacking()
    example_6_alternative_pls_method()
    example_7_quality_assessment()

    print("\n" + "="*70)
    print("ALL EXAMPLES COMPLETED")
    print("="*70)
    print("\nGenerated files:")
    print("  - example1_result.png")
    print("  - example3_order_comparison.png")
    print("  - example4_rfi_handling.png")
    print("  - example6_pls_comparison.png")
    print("  - synthetic_spectrum.csv")
    print("\nFor real data, use: python h1_baseline_subtraction.py your_spectrum.csv")
    print("="*70 + "\n")
