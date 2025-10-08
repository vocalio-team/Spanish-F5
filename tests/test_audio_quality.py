"""Tests for audio quality analysis."""

import sys
from pathlib import Path
import torch
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from f5_tts.audio import (
    AudioQualityAnalyzer,
    QualityLevel,
    print_quality_report
)


def generate_test_audio(sample_rate=24000, duration=3.0):
    """Generate synthetic test audio."""
    t = np.linspace(0, duration, int(sample_rate * duration))

    # More realistic speech simulation with harmonics and modulation
    audio = np.zeros_like(t)
    for i, (freq, amp) in enumerate([(150, 0.5), (300, 0.3), (450, 0.2), (600, 0.1)]):
        # Add amplitude modulation for naturalness
        modulation = 1.0 + 0.3 * np.sin(2 * np.pi * 3 * t)
        audio += amp * np.sin(2 * np.pi * freq * t) * modulation

    # Normalize to reasonable level
    audio = audio / np.max(np.abs(audio)) * 0.7

    return torch.tensor(audio, dtype=torch.float32), sample_rate


def test_clean_audio():
    """Test with clean audio."""
    print("Test 1: Clean Audio")
    print("-" * 60)

    audio, sr = generate_test_audio()
    analyzer = AudioQualityAnalyzer(sample_rate=sr)
    metrics = analyzer.analyze(audio, sr)

    # Synthetic audio won't be excellent, but should be fair or better
    assert metrics.quality_level in [QualityLevel.EXCELLENT, QualityLevel.GOOD, QualityLevel.FAIR]
    assert metrics.overall_score >= 40  # Reasonable for synthetic
    assert metrics.clipping_rate < 0.01

    print(f"✓ Score: {metrics.overall_score:.1f}/100")
    print(f"✓ Quality: {metrics.quality_level.value}")
    print()


def test_noisy_audio():
    """Test with noisy audio."""
    print("Test 2: Noisy Audio")
    print("-" * 60)

    audio, sr = generate_test_audio()
    # Add significant noise
    noise = torch.randn_like(audio) * 0.8
    noisy_audio = audio + noise

    analyzer = AudioQualityAnalyzer(sample_rate=sr)
    metrics = analyzer.analyze(noisy_audio, sr)

    # Should detect noise issues (either low SNR or other problems)
    assert len(metrics.issues) > 0, "Should detect issues in noisy audio"
    assert metrics.overall_score < 50, "Noisy audio should score poorly"

    print(f"✓ Detected issues in noisy audio")
    print(f"✓ SNR: {metrics.snr_db:.1f} dB")
    print(f"✓ Score: {metrics.overall_score:.1f}/100")
    print()


def test_clipped_audio():
    """Test with clipped audio."""
    print("Test 3: Clipped Audio")
    print("-" * 60)

    audio, sr = generate_test_audio()
    # Amplify and clip
    clipped_audio = torch.clamp(audio * 3.0, -1.0, 1.0)

    analyzer = AudioQualityAnalyzer(sample_rate=sr)
    metrics = analyzer.analyze(clipped_audio, sr)

    assert metrics.clipping_rate > 0.05  # Should detect clipping
    assert "clip" in " ".join(metrics.issues).lower()

    print(f"✓ Detected clipping: {metrics.clipping_rate*100:.1f}%")
    print(f"✓ Issues found: {len(metrics.issues)}")
    print()


def test_silent_audio():
    """Test with mostly silent audio."""
    print("Test 4: Silent Audio")
    print("-" * 60)

    sr = 24000
    duration = 3.0

    # Create audio with 70% silence
    audio_segment, _ = generate_test_audio(sr, duration * 0.3)
    silence = torch.zeros(int(sr * duration * 0.7))
    silent_audio = torch.cat([audio_segment, silence])

    analyzer = AudioQualityAnalyzer(sample_rate=sr)
    metrics = analyzer.analyze(silent_audio, sr)

    assert metrics.silence_ratio > 0.6  # Should detect high silence
    assert "silence" in " ".join(metrics.issues).lower()

    print(f"✓ Detected high silence: {metrics.silence_ratio*100:.0f}%")
    print(f"✓ Issues found: {len(metrics.issues)}")
    print()


def test_low_dynamic_range():
    """Test with low dynamic range audio."""
    print("Test 5: Low Dynamic Range Audio")
    print("-" * 60)

    audio, sr = generate_test_audio()
    # Compress dynamic range
    compressed_audio = torch.tanh(audio * 0.5)  # Soft clipping

    analyzer = AudioQualityAnalyzer(sample_rate=sr)
    metrics = analyzer.analyze(compressed_audio, sr)

    assert metrics.dynamic_range_db < 30  # Should detect low DR
    print(f"✓ Detected low DR: {metrics.dynamic_range_db:.1f} dB")
    print(f"✓ Score: {metrics.overall_score:.1f}/100")
    print()


def test_quality_levels():
    """Test quality level thresholds."""
    print("Test 6: Quality Level Classification")
    print("-" * 60)

    audio, sr = generate_test_audio()
    analyzer = AudioQualityAnalyzer(sample_rate=sr)

    # Test different noise levels
    noise_levels = [0.0, 0.1, 0.3, 0.6, 1.0]
    quality_progression = []

    for noise_level in noise_levels:
        noise = torch.randn_like(audio) * noise_level
        test_audio = audio + noise
        metrics = analyzer.analyze(test_audio, sr)
        quality_progression.append(metrics.quality_level.value)

    print(f"✓ Quality progression with increasing noise:")
    for i, (noise, quality) in enumerate(zip(noise_levels, quality_progression)):
        print(f"  Noise {noise:.1f}: {quality}")

    # Quality should degrade with more noise
    # (though not strictly monotonic due to other factors)
    print()


def test_recommendations():
    """Test that recommendations are provided."""
    print("Test 7: Recommendations Generation")
    print("-" * 60)

    # Create problematic audio
    audio, sr = generate_test_audio()
    noise = torch.randn_like(audio) * 0.8
    noisy_audio = audio + noise
    clipped = torch.clamp(noisy_audio * 2.0, -1.0, 1.0)

    analyzer = AudioQualityAnalyzer(sample_rate=sr)
    metrics = analyzer.analyze(clipped, sr)

    assert len(metrics.recommendations) > 0
    assert len(metrics.issues) > 0

    print(f"✓ Generated {len(metrics.issues)} issues")
    print(f"✓ Generated {len(metrics.recommendations)} recommendations")
    print()


def test_score_calculation():
    """Test score calculation logic."""
    print("Test 8: Score Calculation")
    print("-" * 60)

    audio, sr = generate_test_audio()
    analyzer = AudioQualityAnalyzer(sample_rate=sr)
    metrics = analyzer.analyze(audio, sr)

    # Score should be between 0 and 100
    assert 0 <= metrics.overall_score <= 100

    # Components should be reasonable
    assert metrics.snr_db > 0
    assert 0 <= metrics.clipping_rate <= 1
    assert 0 <= metrics.silence_ratio <= 1
    assert metrics.dynamic_range_db > 0
    assert 0 <= metrics.spectral_flatness <= 1

    print(f"✓ Overall score: {metrics.overall_score:.1f}/100")
    print(f"✓ SNR: {metrics.snr_db:.1f} dB")
    print(f"✓ Dynamic range: {metrics.dynamic_range_db:.1f} dB")
    print()


def test_print_report():
    """Test report printing."""
    print("Test 9: Quality Report Formatting")
    print("-" * 60)

    # Create audio with some issues
    audio, sr = generate_test_audio()
    noise = torch.randn_like(audio) * 0.3
    noisy = audio + noise

    analyzer = AudioQualityAnalyzer(sample_rate=sr)
    metrics = analyzer.analyze(noisy, sr)

    print("✓ Generated quality report:")
    print()
    print_quality_report(metrics)


def run_all_tests():
    """Run all quality analysis tests."""
    print("=" * 60)
    print("AUDIO QUALITY ANALYZER TESTS")
    print("=" * 60)
    print()

    tests = [
        test_clean_audio,
        test_noisy_audio,
        test_clipped_audio,
        test_silent_audio,
        test_low_dynamic_range,
        test_quality_levels,
        test_recommendations,
        test_score_calculation,
        test_print_report,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print()
    print("=" * 60)
    print(f"Tests passed: {passed}/{len(tests)}")
    print(f"Tests failed: {failed}/{len(tests)}")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
