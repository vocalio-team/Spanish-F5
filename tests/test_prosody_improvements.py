"""Tests for improved prosody features based on academic research.

Tests cover:
1. Regional prosodic profiles (Cuello & Oro Ozán, 2024 findings)
2. Discourse-level prosody (Guglielmone et al., 2014 framework)
3. Nuclear tone configurations
4. Declination units
5. F0 range validation
"""

import sys
import pytest

sys.path.append("src")

from f5_tts.text.spanish_regional import (
    SpanishRegion,
    RegionalProsody,
    SpanishRegionalProcessor,
    RegionalProsodicProfile,
)
from f5_tts.text.discourse_prosody import (
    DiscourseProsodia,
    NuclearTone,
    IntonationalPhrase,
    DeclinationUnit,
    analyze_discourse_prosody,
)


class TestRegionalProsodicProfiles:
    """Test regional prosodic profiles based on empirical research."""

    def test_rioplatense_profile_exists(self):
        """Rioplatense should have a complete prosodic profile."""
        profile = RegionalProsody.get_profile(SpanishRegion.RIOPLATENSE)
        assert profile is not None
        assert isinstance(profile, RegionalProsodicProfile)

    def test_rioplatense_pace_correction(self):
        """CRITICAL: Rioplatense pace should be 'slow', not 'fast' (Cuello & Oro Ozán, 2024)."""
        profile = RegionalProsody.get_profile(SpanishRegion.RIOPLATENSE)
        assert profile.pace == "slow", "Rioplatense should be slow, not fast (empirical data)"
        assert profile.pace_multiplier == 0.75, "Should be 25% slower"
        assert profile.reading_pace_multiplier == 0.60, "Reading should be 40% slower"

    def test_rioplatense_double_accentuation(self):
        """Rioplatense should have double accentuation (rhythmic + lexical)."""
        profile = RegionalProsody.get_profile(SpanishRegion.RIOPLATENSE)
        assert profile.stress_pattern == "double_accent"

    def test_rioplatense_plaintive_quality(self):
        """Rioplatense should have plaintive/whining intonation quality."""
        profile = RegionalProsody.get_profile(SpanishRegion.RIOPLATENSE)
        assert profile.intonation_quality == "plaintive"

    def test_rioplatense_f0_ranges(self):
        """Rioplatense F0 ranges should match empirical data (Guglielmone et al., 2014)."""
        profile = RegionalProsody.get_profile(SpanishRegion.RIOPLATENSE)

        # Female range
        assert profile.f0_range_female == (75, 340), "Female F0 range incorrect"

        # Male range
        assert profile.f0_range_male == (75, 200), "Male F0 range incorrect"

    def test_rioplatense_expressive_coloring(self):
        """Rioplatense should be emotionally expressive (Italian influence)."""
        profile = RegionalProsody.get_profile(SpanishRegion.RIOPLATENSE)
        assert profile.emotional_coloring == "expressive"

    def test_colombian_profile(self):
        """Colombian profile should be standard/neutral."""
        profile = RegionalProsody.get_profile(SpanishRegion.COLOMBIAN)
        assert profile is not None
        assert profile.pace == "medium"
        assert profile.pace_multiplier == 1.0
        assert profile.intonation_quality == "neutral"

    def test_mexican_profile(self):
        """Mexican profile should be melodic."""
        profile = RegionalProsody.get_profile(SpanishRegion.MEXICAN)
        assert profile is not None
        assert profile.pace == "medium"
        assert profile.intonation_quality == "melodic"

    def test_neutral_no_profile(self):
        """Neutral region should have no specific profile."""
        profile = RegionalProsody.get_profile(SpanishRegion.NEUTRAL)
        assert profile is None


class TestSpanishRegionalProcessorWithProfiles:
    """Test that processor correctly uses prosodic profiles."""

    def test_processor_loads_profile(self):
        """Processor should load prosodic profile on initialization."""
        processor = SpanishRegionalProcessor(region=SpanishRegion.RIOPLATENSE)
        assert processor.prosodic_profile is not None
        assert processor.prosodic_profile.pace == "slow"

    def test_process_includes_profile_data(self):
        """Processing result should include prosodic profile metadata."""
        processor = SpanishRegionalProcessor(region=SpanishRegion.RIOPLATENSE)
        result = processor.process("Che boludo, ¿cómo andás?")

        assert "prosodic_profile" in result
        profile_data = result["prosodic_profile"]

        assert profile_data["pace"] == "slow"
        assert profile_data["pace_multiplier"] == 0.75
        assert profile_data["stress_pattern"] == "double_accent"
        assert profile_data["intonation_quality"] == "plaintive"
        assert profile_data["f0_range_female"] == (75, 340)
        assert profile_data["f0_range_male"] == (75, 200)

    def test_auto_detect_updates_profile(self):
        """Auto-detection should update prosodic profile."""
        processor = SpanishRegionalProcessor(region=SpanishRegion.NEUTRAL, auto_detect=True)

        # Process Rioplatense text
        result = processor.process("Che boludo, vos tenés razón")

        # Should detect Rioplatense and load its profile
        assert result["region"] == "rioplatense"
        assert "prosodic_profile" in result
        assert result["prosodic_profile"]["pace"] == "slow"


class TestDiscourseProsodia:
    """Test discourse-level prosody processor (Guglielmone et al., 2014)."""

    def test_initialization(self):
        """Discourse processor should initialize with correct F0 ranges."""
        # Female voice
        processor_f = DiscourseProsodia(voice_type="female")
        assert processor_f.f0_range["min"] == 75
        assert processor_f.f0_range["max"] == 340
        assert processor_f.f0_range["mid"] == 200

        # Male voice
        processor_m = DiscourseProsodia(voice_type="male")
        assert processor_m.f0_range["min"] == 75
        assert processor_m.f0_range["max"] == 200
        assert processor_m.f0_range["mid"] == 140

    def test_segmentation_basic(self):
        """Should segment text into intonational phrases."""
        processor = DiscourseProsodia()
        text = "Hola amigo. ¿Cómo estás? Muy bien, gracias."

        phrases = processor.segment_into_phrases(text)

        assert len(phrases) > 0
        assert any("Hola" in p for p in phrases)
        assert any("Cómo" in p for p in phrases)

    def test_segmentation_with_commas(self):
        """Should split on commas and conjunctions."""
        processor = DiscourseProsodia()
        text = "Vine, vi, vencí."

        phrases = processor.segment_into_phrases(text)

        assert len(phrases) >= 3  # At least 3 phrases

    def test_nuclear_tone_last_phrase(self):
        """Last phrase should be DESCENDING (assertion/foreground)."""
        processor = DiscourseProsodia()

        tone = processor.determine_nuclear_tone(
            phrase="Es verdad.",
            phrase_index=2,
            total_phrases=3,  # Last phrase
            is_topic_start=False
        )

        assert tone == NuclearTone.DESCENDING

    def test_nuclear_tone_question(self):
        """Questions should be ASCENDING."""
        processor = DiscourseProsodia()

        tone = processor.determine_nuclear_tone(
            phrase="¿Cómo estás?",
            phrase_index=0,
            total_phrases=2
        )

        assert tone == NuclearTone.ASCENDING

    def test_nuclear_tone_given_info(self):
        """Given information should be ASCENDING."""
        processor = DiscourseProsodia()

        tone = processor.determine_nuclear_tone(
            phrase="Mi familia es grande.",  # "Mi" is possessive (given)
            phrase_index=0,
            total_phrases=2,
            contains_given_info=True
        )

        assert tone == NuclearTone.ASCENDING

    def test_nuclear_tone_continuation(self):
        """Middle phrases should be SUSPENSIVE (continuation)."""
        processor = DiscourseProsodia()

        tone = processor.determine_nuclear_tone(
            phrase="Fui al mercado",
            phrase_index=0,
            total_phrases=3,  # Middle phrase
            is_topic_start=False
        )

        assert tone == NuclearTone.SUSPENSIVE

    def test_topic_boundaries_first_phrase(self):
        """First phrase should always be a topic boundary."""
        processor = DiscourseProsodia()
        phrases = ["Primera frase.", "Segunda frase."]

        boundaries = processor.identify_topic_boundaries(phrases)

        assert boundaries[0] is True  # First phrase

    def test_topic_boundaries_discourse_markers(self):
        """Discourse markers should indicate topic boundaries."""
        processor = DiscourseProsodia()
        phrases = ["Hola.", "Entonces vamos.", "Llegamos."]

        boundaries = processor.identify_topic_boundaries(phrases)

        assert boundaries[1] is True  # "Entonces" is a discourse marker

    def test_process_text_complete(self):
        """Full processing should produce complete discourse structure."""
        processor = DiscourseProsodia(voice_type="female")
        text = "Hola amigo. ¿Cómo estás? Estoy bien."

        result = processor.process_text(text)

        assert "original_text" in result
        assert "phrases" in result
        assert "declination_units" in result
        assert "f0_range" in result
        assert result["voice_type"] == "female"
        assert len(result["phrases"]) > 0

        # Check first phrase structure
        first_phrase = result["phrases"][0]
        assert "text" in first_phrase
        assert "nuclear_tone" in first_phrase
        assert "f0_pattern" in first_phrase
        assert "discourse_role" in first_phrase

    def test_nuclear_tone_configurations(self):
        """All three nuclear tones should have proper configurations."""
        # Descending
        desc_config = DiscourseProsodia.NUCLEAR_TONES[NuclearTone.DESCENDING]
        assert desc_config.symbol == "↘"
        assert desc_config.discourse_role == "foreground"
        assert desc_config.processing == "immediate_evaluation"

        # Suspensive
        susp_config = DiscourseProsodia.NUCLEAR_TONES[NuclearTone.SUSPENSIVE]
        assert susp_config.symbol == "→"
        assert susp_config.discourse_role == "background"
        assert susp_config.processing == "suspend_judgment"

        # Ascending
        asc_config = DiscourseProsodia.NUCLEAR_TONES[NuclearTone.ASCENDING]
        assert asc_config.symbol == "↗"
        assert asc_config.discourse_role == "background"
        assert asc_config.processing == "context_reminder"

    def test_declination_units_creation(self):
        """Should create declination units with high start and low end."""
        processor = DiscourseProsodia(voice_type="female")

        phrases = [
            IntonationalPhrase(
                text="Primera frase.",
                nuclear_tone=NuclearTone.DESCENDING,
                f0_start="high",
                f0_end="low",
                is_topic_boundary=True,
                discourse_role="foreground"
            ),
            IntonationalPhrase(
                text="Segunda frase.",
                nuclear_tone=NuclearTone.DESCENDING,
                f0_start="high",
                f0_end="low",
                is_topic_boundary=True,
                discourse_role="foreground"
            ),
        ]

        units = processor.create_declination_units(phrases)

        assert len(units) > 0
        # Each unit should have high start and low end
        for unit in units:
            assert unit.f0_start_hz == 340  # Female max
            assert unit.f0_end_hz == 75  # Female min

    def test_generate_ssml_markup(self):
        """Should generate SSML markup with prosodic annotations."""
        processor = DiscourseProsodia()
        text = "Hola. Adiós."

        ssml = processor.generate_ssml_markup(text)

        assert "<speak>" in ssml
        assert "</speak>" in ssml
        assert "<prosody" in ssml
        assert "Hola" in ssml or "Adiós" in ssml

    def test_convenience_function_analyze(self):
        """Convenience function should work."""
        result = analyze_discourse_prosody("Hola mundo.", voice_type="male")

        assert result["voice_type"] == "male"
        assert "phrases" in result
        assert result["f0_range"]["max"] == 200  # Male range


class TestIntegration:
    """Integration tests combining regional and discourse prosody."""

    def test_rioplatense_with_discourse_prosody(self):
        """Rioplatense text should work with discourse prosody analysis."""
        # Step 1: Regional processing
        regional_processor = SpanishRegionalProcessor(region=SpanishRegion.RIOPLATENSE)
        regional_result = regional_processor.process("Che boludo, ¿vos querés ir al parque?")

        # Verify regional profile
        assert regional_result["prosodic_profile"]["pace"] == "slow"
        assert regional_result["prosodic_profile"]["pace_multiplier"] == 0.75

        # Step 2: Discourse prosody analysis
        discourse_processor = DiscourseProsodia(voice_type="female")
        discourse_result = discourse_processor.process_text(regional_result["final"])

        # Verify discourse structure
        assert len(discourse_result["phrases"]) > 0
        assert discourse_result["f0_range"]["max"] == 340  # Female Rioplatense range

    def test_combined_prosody_metadata(self):
        """Combined processing should provide complete prosodic metadata."""
        # Regional profile
        regional_processor = SpanishRegionalProcessor(region=SpanishRegion.RIOPLATENSE)
        regional_result = regional_processor.process("Hola amigo.")

        # Discourse prosody
        discourse_processor = DiscourseProsodia(voice_type="female")
        discourse_result = discourse_processor.process_text("Hola amigo.")

        # Both should provide complementary information
        assert "prosodic_profile" in regional_result  # Pace, stress, quality
        assert "phrases" in discourse_result  # Nuclear tones, declination
        assert "f0_range" in discourse_result  # Empirical F0 ranges

        # F0 ranges should match
        profile_f0 = regional_result["prosodic_profile"]["f0_range_female"]
        discourse_f0 = (discourse_result["f0_range"]["min"], discourse_result["f0_range"]["max"])
        assert profile_f0 == discourse_f0


class TestRegressionPrevention:
    """Tests to prevent regression of the pace error."""

    def test_no_fast_pace_in_rioplatense(self):
        """REGRESSION TEST: Ensure Rioplatense is never marked as 'fast' again."""
        profile = RegionalProsody.get_profile(SpanishRegion.RIOPLATENSE)

        # Explicitly check it's NOT fast
        assert profile.pace != "fast", "REGRESSION: Rioplatense marked as fast again!"
        assert profile.pace == "slow", "Rioplatense must be slow"

    def test_pace_multiplier_less_than_one(self):
        """REGRESSION TEST: Rioplatense pace multiplier must be < 1.0 (slower)."""
        profile = RegionalProsody.get_profile(SpanishRegion.RIOPLATENSE)

        assert profile.pace_multiplier < 1.0, "Pace multiplier must be < 1.0 for slower speech"
        assert profile.pace_multiplier == 0.75, "Empirical value is 0.75x"

    def test_reading_pace_even_slower(self):
        """REGRESSION TEST: Reading pace should be even slower than conversational."""
        profile = RegionalProsody.get_profile(SpanishRegion.RIOPLATENSE)

        assert profile.reading_pace_multiplier < profile.pace_multiplier
        assert profile.reading_pace_multiplier == 0.60


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
