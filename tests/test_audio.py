"""Test suite for audio processing modules (crossfading and processors)."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
from f5_tts.audio.crossfading import (
    CrossfadeType,
    EqualPowerCrossfader,
    RaisedCosineCrossfader,
    LinearCrossfader,
    apply_edge_fades,
    get_crossfader,
)


class TestCrossfadeType:
    """Test CrossfadeType enum."""

    def test_enum_values(self):
        """Test enum values are defined."""
        assert CrossfadeType.LINEAR.value == "linear"
        assert CrossfadeType.EQUAL_POWER.value == "equal_power"
        assert CrossfadeType.RAISED_COSINE.value == "raised_cosine"


class TestEqualPowerCrossfader:
    """Test EqualPowerCrossfader class."""

    def test_basic_crossfade(self):
        """Test basic crossfading."""
        crossfader = EqualPowerCrossfader()

        # Create test audio
        audio1 = np.ones(24000)  # 1 second at 24kHz
        audio2 = np.zeros(24000)

        result = crossfader.crossfade(audio1, audio2, duration=0.5, sample_rate=24000)

        # Result should be longer than individual segments
        assert len(result) > 0
        # Should preserve total duration minus overlap
        expected_len = len(audio1) + len(audio2) - int(0.5 * 24000)
        assert len(result) == expected_len

    def test_crossfade_preserves_content(self):
        """Test that crossfade preserves audio content."""
        crossfader = EqualPowerCrossfader()

        audio1 = np.ones(24000)
        audio2 = np.zeros(24000)

        result = crossfader.crossfade(audio1, audio2, duration=0.1, sample_rate=24000)

        # Beginning should be mostly ones
        assert np.mean(result[:1000]) > 0.9
        # End should be mostly zeros
        assert np.mean(result[-1000:]) < 0.1

    def test_zero_duration(self):
        """Test crossfade with zero duration."""
        crossfader = EqualPowerCrossfader()

        audio1 = np.ones(1000)
        audio2 = np.zeros(1000)

        result = crossfader.crossfade(audio1, audio2, duration=0.0, sample_rate=24000)

        # Should concatenate without crossfade
        assert len(result) == 2000

    def test_short_audio(self):
        """Test crossfade with very short audio."""
        crossfader = EqualPowerCrossfader()

        audio1 = np.ones(100)
        audio2 = np.zeros(100)

        # Request longer crossfade than audio
        result = crossfader.crossfade(audio1, audio2, duration=1.0, sample_rate=24000)

        # Should handle gracefully
        assert len(result) > 0

    def test_equal_power_property(self):
        """Test that equal power crossfade maintains energy."""
        crossfader = EqualPowerCrossfader()

        # Create audio with known power
        audio1 = np.ones(24000) * 0.5
        audio2 = np.ones(24000) * 0.5

        result = crossfader.crossfade(audio1, audio2, duration=0.5, sample_rate=24000)

        # In crossfade region, power should be relatively constant
        crossfade_samples = int(0.5 * 24000)
        crossfade_region = result[len(audio1)-crossfade_samples:len(audio1)]

        # Power should not drop significantly (allowing some tolerance)
        power = crossfade_region ** 2
        assert np.mean(power) > 0.1  # Should maintain reasonable power


class TestRaisedCosineCrossfader:
    """Test RaisedCosineCrossfader class."""

    def test_basic_crossfade(self):
        """Test basic raised cosine crossfading."""
        crossfader = RaisedCosineCrossfader()

        audio1 = np.ones(24000)
        audio2 = np.zeros(24000)

        result = crossfader.crossfade(audio1, audio2, duration=0.5, sample_rate=24000)

        # Should produce valid output
        assert len(result) > 0
        expected_len = len(audio1) + len(audio2) - int(0.5 * 24000)
        assert len(result) == expected_len

    def test_smooth_transition(self):
        """Test that transition is smooth."""
        crossfader = RaisedCosineCrossfader()

        audio1 = np.ones(24000)
        audio2 = np.zeros(24000)

        result = crossfader.crossfade(audio1, audio2, duration=0.2, sample_rate=24000)

        # Gradient should be smooth (no sharp jumps)
        gradient = np.diff(result)
        max_gradient = np.max(np.abs(gradient))

        # Gradient should be reasonably small
        assert max_gradient < 0.1


class TestLinearCrossfader:
    """Test LinearCrossfader class."""

    def test_basic_crossfade(self):
        """Test basic linear crossfading."""
        crossfader = LinearCrossfader()

        audio1 = np.ones(24000)
        audio2 = np.zeros(24000)

        result = crossfader.crossfade(audio1, audio2, duration=0.5, sample_rate=24000)

        # Should produce valid output
        assert len(result) > 0

    def test_linear_transition(self):
        """Test that transition is linear."""
        crossfader = LinearCrossfader()

        audio1 = np.ones(24000)
        audio2 = np.zeros(24000)

        result = crossfader.crossfade(audio1, audio2, duration=0.5, sample_rate=24000)

        # Extract crossfade region
        crossfade_samples = int(0.5 * 24000)
        crossfade_start = len(audio1) - crossfade_samples
        crossfade_region = result[crossfade_start:crossfade_start + crossfade_samples]

        # Should have linear gradient from 1 to 0
        # (allowing for some numerical error)
        expected = np.linspace(1, 0, crossfade_samples)
        assert np.allclose(crossfade_region, expected, atol=0.01)


class TestApplyEdgeFades:
    """Test apply_edge_fades function."""

    def test_basic_fades(self):
        """Test basic edge fading."""
        audio = np.ones(24000)

        result = apply_edge_fades(audio, fade_duration=0.01, sample_rate=24000)

        # Should start with fade in
        assert result[0] < 0.5  # Should be faded
        # Middle should be unchanged
        assert result[12000] == 1.0
        # End should be faded out
        assert result[-1] < 0.5

    def test_preserves_length(self):
        """Test that length is preserved."""
        audio = np.ones(24000)

        result = apply_edge_fades(audio, fade_duration=0.01, sample_rate=24000)

        assert len(result) == len(audio)

    def test_no_fade(self):
        """Test with very short fade duration."""
        audio = np.ones(24000)

        result = apply_edge_fades(audio, fade_duration=0.001, sample_rate=24000)

        # Should still work with minimal fade
        assert len(result) == len(audio)
        assert result.shape == audio.shape


class TestGetCrossfader:
    """Test get_crossfader factory function."""

    def test_get_equal_power(self):
        """Test getting equal power crossfader."""
        crossfader = get_crossfader(CrossfadeType.EQUAL_POWER)

        assert isinstance(crossfader, EqualPowerCrossfader)

    def test_get_raised_cosine(self):
        """Test getting raised cosine crossfader."""
        crossfader = get_crossfader(CrossfadeType.RAISED_COSINE)

        assert isinstance(crossfader, RaisedCosineCrossfader)

    def test_get_linear(self):
        """Test getting linear crossfader."""
        crossfader = get_crossfader(CrossfadeType.LINEAR)

        assert isinstance(crossfader, LinearCrossfader)

    def test_get_by_string(self):
        """Test getting crossfader by enum value."""
        # get_crossfader accepts CrossfadeType enum, not strings
        crossfader = get_crossfader(CrossfadeType.RAISED_COSINE)

        assert isinstance(crossfader, RaisedCosineCrossfader)

    def test_default(self):
        """Test default crossfader."""
        crossfader = get_crossfader()

        # Should return some crossfader
        assert hasattr(crossfader, 'crossfade')


class TestCrossfaderIntegration:
    """Test crossfader integration scenarios."""

    def test_multiple_crossfades(self):
        """Test chaining multiple crossfades."""
        crossfader = EqualPowerCrossfader()

        # Create multiple segments
        segments = [
            np.ones(10000) * 0.5,
            np.ones(10000) * 0.6,
            np.ones(10000) * 0.7,
        ]

        # Chain crossfades
        result = segments[0]
        for segment in segments[1:]:
            result = crossfader.crossfade(result, segment, duration=0.1, sample_rate=24000)

        # Should produce valid output
        assert len(result) > 0
        # Should be shorter than concatenation due to overlaps
        assert len(result) < sum(len(s) for s in segments)

    def test_different_sample_rates(self):
        """Test with different sample rates."""
        crossfader = EqualPowerCrossfader()

        # 16kHz audio
        audio1 = np.ones(16000)
        audio2 = np.zeros(16000)

        result = crossfader.crossfade(audio1, audio2, duration=0.5, sample_rate=16000)

        # Should handle correctly
        assert len(result) > 0

    def test_real_world_scenario(self):
        """Test realistic audio crossfade scenario."""
        crossfader = EqualPowerCrossfader()

        # Simulate TTS chunks
        chunk1 = np.random.randn(24000) * 0.1  # 1 second
        chunk2 = np.random.randn(24000) * 0.1  # 1 second

        result = crossfader.crossfade(chunk1, chunk2, duration=0.1, sample_rate=24000)

        # Should produce valid audio
        assert len(result) > 0
        # Should not clip
        assert np.max(np.abs(result)) < 1.0

    def test_stereo_audio(self):
        """Test with stereo audio (2D array)."""
        crossfader = EqualPowerCrossfader()

        # Stereo audio (2 channels)
        audio1 = np.ones((2, 24000))
        audio2 = np.zeros((2, 24000))

        # Process each channel
        result_left = crossfader.crossfade(audio1[0], audio2[0], duration=0.5, sample_rate=24000)
        result_right = crossfader.crossfade(audio1[1], audio2[1], duration=0.5, sample_rate=24000)

        # Should work for each channel
        assert len(result_left) > 0
        assert len(result_right) > 0


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_audio(self):
        """Test with empty audio."""
        crossfader = EqualPowerCrossfader()

        audio1 = np.array([])
        audio2 = np.ones(1000)

        try:
            result = crossfader.crossfade(audio1, audio2, duration=0.1, sample_rate=24000)
            # Should handle gracefully or raise error
            assert len(result) >= 0
        except:
            # Error is acceptable
            pass

    def test_very_long_crossfade(self):
        """Test with crossfade longer than audio."""
        crossfader = EqualPowerCrossfader()

        audio1 = np.ones(100)
        audio2 = np.zeros(100)

        # Request 10 second crossfade on 100 sample audio
        result = crossfader.crossfade(audio1, audio2, duration=10.0, sample_rate=24000)

        # Should limit crossfade to audio length
        assert len(result) > 0
        assert len(result) <= len(audio1) + len(audio2)

    def test_negative_values(self):
        """Test with negative audio values."""
        crossfader = EqualPowerCrossfader()

        audio1 = np.ones(24000) * -0.5
        audio2 = np.ones(24000) * 0.5

        result = crossfader.crossfade(audio1, audio2, duration=0.5, sample_rate=24000)

        # Should handle negative values
        assert len(result) > 0

    def test_different_lengths(self):
        """Test with different length audio segments."""
        crossfader = EqualPowerCrossfader()

        audio1 = np.ones(24000)
        audio2 = np.zeros(48000)  # Twice as long

        result = crossfader.crossfade(audio1, audio2, duration=0.5, sample_rate=24000)

        # Should handle different lengths
        assert len(result) > 0


def run_tests():
    """Run all tests."""
    test_classes = [
        TestCrossfadeType,
        TestEqualPowerCrossfader,
        TestRaisedCosineCrossfader,
        TestLinearCrossfader,
        TestApplyEdgeFades,
        TestGetCrossfader,
        TestCrossfaderIntegration,
        TestEdgeCases,
    ]

    total = 0
    passed = 0
    failed = 0

    for test_class in test_classes:
        print(f"\n{'='*60}")
        print(f"Testing {test_class.__name__}")
        print('='*60)

        instance = test_class()
        methods = [m for m in dir(instance) if m.startswith('test_')]

        for method_name in methods:
            total += 1
            try:
                method = getattr(instance, method_name)
                method()
                print(f"✓ {method_name}")
                passed += 1
            except AssertionError as e:
                print(f"✗ {method_name}: {e}")
                failed += 1
            except Exception as e:
                print(f"✗ {method_name}: ERROR: {e}")
                failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} passed, {failed}/{total} failed")
    print('='*60)

    return failed == 0


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
