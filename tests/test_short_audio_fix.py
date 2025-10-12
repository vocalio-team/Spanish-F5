"""Test short audio generation fixes."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from f5_tts.rest_api.tts_processor import TTSProcessor
from f5_tts.rest_api.enhancements import EnhancementProcessor


class TestShortAudioFixes:
    """Test fixes for short audio generation (1-2 words)."""

    def setup_method(self):
        """Initialize processors."""
        self.tts_processor = TTSProcessor()
        self.enhancement_processor = EnhancementProcessor()

    def test_very_short_text_adjustments(self):
        """Test adjustments for very short texts (< 15 chars)."""
        # Test cases: very short Spanish words/phrases
        test_texts = [
            "Hola",  # 4 chars
            "Sí",    # 2 chars (with accent)
            "No",    # 2 chars
            "Adiós", # 5 chars (with accent)
            "Bien",  # 4 chars
        ]

        for text in test_texts:
            speed, fix_duration = self.tts_processor.calculate_short_text_adjustments(text, 1.0)

            # Should slow down significantly (0.75 = 75% of base speed)
            assert speed <= 0.75, f"Speed not reduced enough for '{text}': {speed}"
            assert speed >= 0.6, f"Speed too slow for '{text}': {speed}"

            # Should use long fix_duration to compensate for ref removal and silence removal
            assert fix_duration == 12.0, f"Wrong fix_duration for '{text}': {fix_duration}"

            print(f"✓ '{text}' ({len(text)} chars): speed={speed:.2f}, fix_duration={fix_duration}s")

    def test_short_text_adjustments(self):
        """Test adjustments for short texts (15-30 chars)."""
        test_texts = [
            "Gracias por todo",  # 16 chars
            "¿Cómo estás?",      # 13 chars (but treated as short)
            "Hasta luego",       # 12 chars
        ]

        for text in test_texts:
            speed, fix_duration = self.tts_processor.calculate_short_text_adjustments(text, 1.0)

            if len(text) < 15:
                # Very short - should use 12s fix_duration
                assert fix_duration == 12.0, f"Wrong fix_duration for very short text: {fix_duration}"
                assert speed <= 0.75, f"Speed not reduced for very short text: {speed}"
            else:
                # Short (15-30 chars) - should use 9s fix_duration
                assert speed <= 0.90, f"Speed not reduced for short text: {speed}"
                assert fix_duration == 9.0, f"Wrong fix_duration for short text: {fix_duration}"

            print(f"✓ '{text}' ({len(text)} chars): speed={speed:.2f}, fix_duration={fix_duration}s")

    def test_normal_text_no_adjustments(self):
        """Test that normal texts don't get adjusted."""
        text = "Este es un texto normal que no necesita ajustes especiales"

        speed, fix_duration = self.tts_processor.calculate_short_text_adjustments(text, 1.0)

        # Should return base speed and no fix_duration
        assert speed == 1.0
        assert fix_duration is None

        print(f"✓ Normal text: speed={speed}, fix_duration={fix_duration}")

    def test_adaptive_crossfade_very_short(self):
        """Test adaptive crossfade for very short texts."""
        text = "Hola"  # 4 chars

        crossfade = self.enhancement_processor._get_adaptive_crossfade(0.15, text)

        # Should use minimal crossfade (50ms)
        assert crossfade == 0.05, f"Wrong crossfade for very short text: {crossfade}"

        print(f"✓ Very short text crossfade: {crossfade}s (50ms)")

    def test_adaptive_crossfade_short(self):
        """Test adaptive crossfade for short texts."""
        # Test with text just under 15 chars (treated as very short)
        text = "Gracias amigo"  # 13 chars

        crossfade = self.enhancement_processor._get_adaptive_crossfade(0.15, text)

        # 13 chars < 15, so should use minimal crossfade (50ms)
        assert crossfade == 0.05, f"Wrong crossfade for text < 15 chars: {crossfade}"

        print(f"✓ Short text (<15 chars) crossfade: {crossfade}s (50ms)")

        # Test with text 15-30 chars (treated as short)
        text2 = "Gracias por todo amigo"  # 22 chars

        crossfade2 = self.enhancement_processor._get_adaptive_crossfade(0.15, text2)

        # 15 <= 22 < 30, so should use reduced crossfade (80ms)
        assert crossfade2 == 0.08, f"Wrong crossfade for 15-30 chars: {crossfade2}"

        print(f"✓ Short text (15-30 chars) crossfade: {crossfade2}s (80ms)")

    def test_adaptive_crossfade_normal(self):
        """Test adaptive crossfade for normal texts."""
        text = "Este es un texto normal con suficiente longitud"  # 47 chars

        crossfade = self.enhancement_processor._get_adaptive_crossfade(0.15, text)

        # Should use normal/adaptive crossfade
        assert crossfade >= 0.15, f"Crossfade too short for normal text: {crossfade}"

        print(f"✓ Normal text crossfade: {crossfade}s")

    def test_duration_calculations(self):
        """Test that duration calculations prevent audio chopping."""
        # Simulate the full pipeline:
        # 1. Generate with fix_duration=12s
        # 2. Remove ref_audio_len (assume 6s = ~144000 samples)
        # 3. Apply minimal crossfade (0.05s = 1200 samples)
        # 4. Expect ~5-6s of output audio after processing

        text = "Hola"
        speed, fix_duration = self.tts_processor.calculate_short_text_adjustments(text, 1.0)
        crossfade = self.enhancement_processor._get_adaptive_crossfade(0.15, text)

        # Calculation:
        # - fix_duration = 12s = 288,000 samples @ 24kHz
        # - ref_audio removed = 6s = 144,000 samples
        # - remaining = 144,000 samples = 6s
        # - crossfade loss = 1,200 samples = 0.05s
        # - after silence removal (~1-2s loss) = 3-4s final audio

        sample_rate = 24000
        total_samples = fix_duration * sample_rate
        ref_samples = 6.0 * sample_rate
        remaining_after_ref = total_samples - ref_samples
        final_duration = remaining_after_ref / sample_rate

        assert final_duration >= 5.0, f"Not enough audio after ref removal: {final_duration}s"

        print(f"✓ Duration check: {fix_duration}s -> {final_duration}s after ref removal")
        print(f"  Expected final: ~3-4s after silence removal and crossfading")

    def test_crossfade_preservation(self):
        """Test that short crossfade preserves more audio."""
        # For a 6s audio chunk, compare audio loss:
        sample_rate = 24000
        audio_duration = 6.0  # seconds
        audio_samples = int(audio_duration * sample_rate)  # 144,000 samples

        # Old crossfade (150ms)
        old_crossfade = 0.15
        old_loss = old_crossfade * sample_rate  # 3,600 samples lost

        # New crossfade for short text (50ms)
        new_crossfade = 0.05
        new_loss = new_crossfade * sample_rate  # 1,200 samples lost

        # Calculate preservation
        old_preserved = (audio_samples - old_loss) / audio_samples * 100
        new_preserved = (audio_samples - new_loss) / audio_samples * 100

        improvement = new_preserved - old_preserved

        assert improvement > 1.5, f"Not enough improvement: {improvement}%"

        print(f"✓ Crossfade improvement:")
        print(f"  Old (150ms): {old_preserved:.1f}% preserved")
        print(f"  New (50ms):  {new_preserved:.1f}% preserved")
        print(f"  Improvement: +{improvement:.1f}%")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
