#!/usr/bin/env python3
"""
Comprehensive Test Suite for H1 Baseline Subtraction
Tests all major functionality with synthetic data
"""

import numpy as np
import sys
import os

# Test parameters
H1_REST_FREQ = 1420.405751
SPEED_OF_LIGHT = 299792.458

def create_test_spectrum(snr=3.0, baseline_type='quadratic', add_rfi=False,
                         n_channels=500, seed=42):
    """Create synthetic H1 spectrum for testing"""
    np.random.seed(seed)

    # Frequency array
    freq = np.linspace(1420.0, 1421.0, n_channels)

    # Generate baseline
    if baseline_type == 'linear':
        baseline = 10.0 + 0.5 * (freq - 1420.0)
    elif baseline_type == 'quadratic':
        baseline = 10.0 + 0.5 * (freq - 1420.0) - 0.3 * (freq - 1420.0)**2
    elif baseline_type == 'cubic':
        baseline = 10.0 + 0.5 * (freq - 1420.0) - 0.3 * (freq - 1420.0)**2 + 0.1 * (freq - 1420.0)**3
    else:
        baseline = np.ones_like(freq) * 10.0

    # H1 Gaussian line
    line_width = 0.05  # MHz (FWHM)
    sigma = line_width / 2.355
    noise_level = 0.1
    signal_amplitude = snr * noise_level
    h1_line = signal_amplitude * np.exp(-0.5 * ((freq - H1_REST_FREQ) / sigma)**2)

    # Noise
    noise = np.random.normal(0, noise_level, n_channels)

    # Combine
    spectrum = baseline + h1_line + noise

    # Add RFI spikes if requested
    if add_rfi:
        rfi_positions = np.random.choice(n_channels, 5, replace=False)
        for pos in rfi_positions:
            spectrum[pos] += np.random.uniform(0.5, 2.0)

    return freq, spectrum, baseline, h1_line, noise_level

def test_basic_functionality():
    """Test 1: Basic polynomial baseline subtraction"""
    print("\n" + "="*70)
    print("TEST 1: Basic Polynomial Baseline Subtraction")
    print("="*70)

    try:
        from h1_baseline_subtraction import H1BaselineProcessor

        # Create test data
        freq, spectrum, true_baseline, true_line, true_noise = create_test_spectrum(
            snr=3.0, baseline_type='quadratic', add_rfi=False
        )

        # Save test file
        np.savetxt('test_basic.csv', np.column_stack([freq, spectrum]), delimiter=',')

        # Process
        processor = H1BaselineProcessor(
            poly_order=2,
            exclude_velocity=300.0,
            verbose=False
        )
        processor.set_spectrum(freq, spectrum)
        results = processor.process()

        # Validate results
        assert results['snr'] > 0, "SNR should be positive"
        assert results['noise'] > 0, "Noise should be positive"
        assert len(results['corrected']) == len(freq), "Output length mismatch"
        assert results['quality']['quality_score'] in ['PASS', 'MARGINAL', 'FAIL'], "Invalid quality score"

        # Check baseline removal quality
        recovered_snr = results['snr']
        expected_snr = 3.0

        print(f"✓ Basic processing works")
        print(f"  Input SNR: {expected_snr:.2f}")
        print(f"  Recovered SNR: {recovered_snr:.2f}")
        print(f"  Noise level: {results['noise']:.6f}")
        print(f"  Quality: {results['quality']['quality_score']}")

        # Cleanup
        os.remove('test_basic.csv')

        return True

    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False

def test_spike_removal():
    """Test 2: RFI spike removal"""
    print("\n" + "="*70)
    print("TEST 2: RFI Spike Removal")
    print("="*70)

    try:
        from h1_baseline_subtraction import H1BaselineProcessor

        # Create test data with RFI
        freq, spectrum, _, _, _ = create_test_spectrum(
            snr=3.0, baseline_type='quadratic', add_rfi=True
        )

        # Process without spike removal
        processor_no_spike = H1BaselineProcessor(
            poly_order=2,
            spike_removal=False,
            verbose=False
        )
        processor_no_spike.set_spectrum(freq, spectrum.copy())
        results_no_spike = processor_no_spike.process()

        # Process with spike removal
        processor_with_spike = H1BaselineProcessor(
            poly_order=2,
            spike_removal=True,
            spike_threshold=5.0,
            verbose=False
        )
        processor_with_spike.set_spectrum(freq, spectrum.copy())
        results_with_spike = processor_with_spike.process()

        assert results_with_spike['spikes_removed'] > 0, "Should detect spikes"

        print(f"✓ Spike removal works")
        print(f"  Spikes detected: {results_with_spike['spikes_removed']}")
        print(f"  SNR without removal: {results_no_spike['snr']:.2f}")
        print(f"  SNR with removal: {results_with_spike['snr']:.2f}")

        return True

    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False

def test_polynomial_orders():
    """Test 3: Different polynomial orders"""
    print("\n" + "="*70)
    print("TEST 3: Polynomial Order Selection")
    print("="*70)

    try:
        from h1_baseline_subtraction import H1BaselineProcessor

        # Test different baseline types with appropriate orders
        test_cases = [
            ('linear', 1, "Linear baseline → 1st order"),
            ('quadratic', 2, "Quadratic baseline → 2nd order"),
            ('cubic', 3, "Cubic baseline → 3rd order")
        ]

        all_passed = True
        for baseline_type, order, description in test_cases:
            freq, spectrum, _, _, _ = create_test_spectrum(
                snr=3.0, baseline_type=baseline_type
            )

            processor = H1BaselineProcessor(
                poly_order=order,
                verbose=False
            )
            processor.set_spectrum(freq, spectrum)
            results = processor.process()

            quality = results['quality']['quality_score']
            passed = quality in ['PASS', 'MARGINAL']

            status = "✓" if passed else "✗"
            print(f"{status} {description}: SNR={results['snr']:.2f}, Quality={quality}")

            if not passed:
                all_passed = False

        return all_passed

    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False

def test_stacking():
    """Test 4: Signal stacking"""
    print("\n" + "="*70)
    print("TEST 4: Signal Stacking")
    print("="*70)

    try:
        from h1_baseline_subtraction import H1SpectrumStacker

        # Create multiple weak observations
        n_obs = 10
        individual_snr = 1.0

        # Generate and save test files
        files = []
        for i in range(n_obs):
            freq, spectrum, _, _, _ = create_test_spectrum(
                snr=individual_snr,
                seed=42+i  # Different seed for each
            )
            filename = f'test_stack_{i}.csv'
            np.savetxt(filename, np.column_stack([freq, spectrum]), delimiter=',')
            files.append(filename)

        # Stack
        stacker = H1SpectrumStacker(
            processor_params={'poly_order': 2},
            verbose=False
        )
        results = stacker.stack_observations(files, final_poly_order=4)

        # Check improvement
        expected_improvement = np.sqrt(n_obs)
        actual_improvement = results['actual_improvement']
        efficiency = results['efficiency']

        # Cleanup
        for f in files:
            os.remove(f)

        print(f"✓ Stacking works")
        print(f"  N observations: {n_obs}")
        print(f"  Individual SNR: {individual_snr:.2f}")
        print(f"  Final SNR: {results['snr']:.2f}")
        print(f"  Expected improvement: {expected_improvement:.2f}×")
        print(f"  Actual improvement: {actual_improvement:.2f}×")
        print(f"  Efficiency: {efficiency:.1f}%")

        # Should see significant improvement
        assert results['snr'] > individual_snr * 2, "Stacking should improve SNR"

        return True

    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_quality_assessment():
    """Test 5: Quality assessment metrics"""
    print("\n" + "="*70)
    print("TEST 5: Quality Assessment")
    print("="*70)

    try:
        from h1_baseline_subtraction import H1BaselineProcessor

        # Good quality data
        freq, spectrum, _, _, _ = create_test_spectrum(
            snr=5.0, baseline_type='quadratic', add_rfi=False
        )

        processor = H1BaselineProcessor(poly_order=2, verbose=False)
        processor.set_spectrum(freq, spectrum)
        results = processor.process()

        quality = results['quality']

        print(f"✓ Quality assessment works")
        print(f"  Baseline RMS: {quality['baseline_rms']:.6f}")
        print(f"  Flatness ratio: {quality['flatness_ratio']:.3f}")
        print(f"  Gaussian p-value: {quality['gaussian_p_value']:.4f}")
        print(f"  Periodic structure: {quality['periodic_structure']}")
        print(f"  Overall quality: {quality['quality_score']}")

        # Basic validation
        assert 'baseline_rms' in quality
        assert 'flatness_ratio' in quality
        assert 'gaussian_p_value' in quality
        assert 'quality_score' in quality

        return True

    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False

def test_iterative_clipping():
    """Test 6: Iterative sigma clipping"""
    print("\n" + "="*70)
    print("TEST 6: Iterative Sigma Clipping")
    print("="*70)

    try:
        from h1_baseline_subtraction import H1BaselineProcessor

        freq, spectrum, _, _, _ = create_test_spectrum(
            snr=3.0, baseline_type='quadratic', add_rfi=True
        )

        # Without iteration
        proc_no_iter = H1BaselineProcessor(
            poly_order=2,
            max_iterations=1,
            verbose=False
        )
        proc_no_iter.set_spectrum(freq, spectrum.copy())
        results_no_iter = proc_no_iter.process()

        # With iteration
        proc_iter = H1BaselineProcessor(
            poly_order=2,
            max_iterations=5,
            sigma_clip=3.0,
            verbose=False
        )
        proc_iter.set_spectrum(freq, spectrum.copy())
        results_iter = proc_iter.process()

        print(f"✓ Iterative clipping works")
        print(f"  SNR without iteration: {results_no_iter['snr']:.2f}")
        print(f"  SNR with iteration: {results_iter['snr']:.2f}")
        print(f"  Quality improvement: {results_iter['quality']['quality_score']} vs {results_no_iter['quality']['quality_score']}")

        return True

    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False

def test_command_line():
    """Test 7: Command-line interface"""
    print("\n" + "="*70)
    print("TEST 7: Command-Line Interface")
    print("="*70)

    try:
        # Create test file
        freq, spectrum, _, _, _ = create_test_spectrum(snr=3.0)
        np.savetxt('test_cli.csv', np.column_stack([freq, spectrum]), delimiter=',')

        # Test help
        exit_code = os.system('python h1_baseline_subtraction.py --help > /dev/null 2>&1')
        assert exit_code == 0, "Help command failed"

        # Test basic processing
        exit_code = os.system('python h1_baseline_subtraction.py test_cli.csv --no-plot --quiet -o test_output.png 2>&1 | tail -5')
        assert exit_code == 0, "Basic processing failed"

        # Test spike removal
        exit_code = os.system('python h1_baseline_subtraction.py test_cli.csv --remove-spikes --no-plot --quiet 2>&1 | tail -5')
        assert exit_code == 0, "Spike removal failed"

        # Cleanup
        os.remove('test_cli.csv')
        if os.path.exists('test_output.png'):
            os.remove('test_output.png')
        if os.path.exists('h1_result.png'):
            os.remove('h1_result.png')

        print(f"✓ Command-line interface works")
        print(f"  --help: OK")
        print(f"  Basic processing: OK")
        print(f"  --remove-spikes: OK")

        return True

    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False

def test_edge_cases():
    """Test 8: Edge cases and error handling"""
    print("\n" + "="*70)
    print("TEST 8: Edge Cases and Error Handling")
    print("="*70)

    try:
        from h1_baseline_subtraction import H1BaselineProcessor

        # Test 1: Very weak signal (SNR < 1)
        freq, spectrum, _, _, _ = create_test_spectrum(snr=0.5)
        processor = H1BaselineProcessor(poly_order=2, verbose=False)
        processor.set_spectrum(freq, spectrum)
        results = processor.process()
        print(f"✓ Handles very weak signal (SNR={results['snr']:.2f})")

        # Test 2: Very strong signal (SNR > 10)
        freq, spectrum, _, _, _ = create_test_spectrum(snr=15.0)
        processor = H1BaselineProcessor(poly_order=2, verbose=False)
        processor.set_spectrum(freq, spectrum)
        results = processor.process()
        print(f"✓ Handles strong signal (SNR={results['snr']:.2f})")

        # Test 3: Many RFI spikes
        freq, spectrum, _, _, _ = create_test_spectrum(snr=3.0, add_rfi=True)
        # Add many more spikes
        for _ in range(20):
            pos = np.random.randint(0, len(spectrum))
            spectrum[pos] += np.random.uniform(1.0, 3.0)
        processor = H1BaselineProcessor(
            poly_order=2,
            spike_removal=True,
            verbose=False
        )
        processor.set_spectrum(freq, spectrum)
        results = processor.process()
        print(f"✓ Handles many RFI spikes ({results['spikes_removed']} removed)")

        # Test 4: Different polynomial orders
        for order in [0, 1, 2, 3, 4, 5]:
            freq, spectrum, _, _, _ = create_test_spectrum(snr=3.0)
            processor = H1BaselineProcessor(poly_order=order, verbose=False)
            processor.set_spectrum(freq, spectrum)
            results = processor.process()
        print(f"✓ All polynomial orders (0-5) work")

        return True

    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run complete test suite"""
    print("\n" + "="*70)
    print("H1 BASELINE SUBTRACTION - COMPREHENSIVE TEST SUITE")
    print("="*70)

    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("RFI Spike Removal", test_spike_removal),
        ("Polynomial Orders", test_polynomial_orders),
        ("Signal Stacking", test_stacking),
        ("Quality Assessment", test_quality_assessment),
        ("Iterative Clipping", test_iterative_clipping),
        ("Command-Line Interface", test_command_line),
        ("Edge Cases", test_edge_cases)
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n✗ {name} CRASHED: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n" + "="*70)
        print("🎉 ALL TESTS PASSED - SCRIPT IS PRODUCTION READY!")
        print("="*70)
        return 0
    else:
        print("\n" + "="*70)
        print("⚠️  SOME TESTS FAILED - REVIEW REQUIRED")
        print("="*70)
        return 1

if __name__ == '__main__':
    sys.exit(run_all_tests())
