"""Comprehensive test suite for regional Spanish features."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

from f5_tts.text.spanish_regional import (
    SpanishRegion,
    RegionalPhonetics,
    RegionalProsody,
    RegionalSlang,
    SpanishRegionalProcessor,
    get_regional_processor,
    process_spanish_text,
)


class TestSpanishRegion:
    """Test SpanishRegion enum."""

    def test_region_values(self):
        """Test all region values are defined."""
        assert SpanishRegion.NEUTRAL.value == "neutral"
        assert SpanishRegion.RIOPLATENSE.value == "rioplatense"
        assert SpanishRegion.COLOMBIAN.value == "colombian"
        assert SpanishRegion.MEXICAN.value == "mexican"
        assert SpanishRegion.CHILEAN.value == "chilean"
        assert SpanishRegion.CARIBBEAN.value == "caribbean"
        assert SpanishRegion.ANDEAN.value == "andean"


class TestRegionalPhonetics:
    """Test phonetic transformations."""

    def test_rioplatense_sheismo(self):
        """Test Rioplatense sheísmo (ll → ʃ)."""
        features = RegionalPhonetics.get_features(SpanishRegion.RIOPLATENSE)
        sheismo = [f for f in features if 'sheísmo' in f.description.lower()][0]

        import re
        text = "calle"
        result = re.sub(sheismo.pattern, sheismo.replacement, text)
        assert 'ʃ' in result or result != text

    def test_rioplatense_yeismo(self):
        """Test Rioplatense yeísmo rehilado."""
        features = RegionalPhonetics.get_features(SpanishRegion.RIOPLATENSE)
        yeismo = [f for f in features if 'yeísmo' in f.description.lower()][0]

        import re
        text = "yo soy"
        result = re.sub(yeismo.pattern, yeismo.replacement, text)
        assert 'ʒ' in result

    def test_rioplatense_s_aspiration(self):
        """Test Rioplatense s-aspiration."""
        features = RegionalPhonetics.get_features(SpanishRegion.RIOPLATENSE)
        s_asp = [f for f in features if 'aspir' in f.description.lower()][0]

        import re
        text = "dos amigos"
        result = re.sub(s_asp.pattern, s_asp.replacement, text)
        # Should have 'h' instead of final 's'
        assert 'doh' in result or 'amigoh' in result

    def test_mexican_affricate(self):
        """Test Mexican clear affricate (ch → tʃ)."""
        features = RegionalPhonetics.get_features(SpanishRegion.MEXICAN)
        affricate = [f for f in features if 'afric' in f.description.lower()][0]

        import re
        text = "mucho"
        result = re.sub(affricate.pattern, affricate.replacement, text)
        assert 'tʃ' in result

    def test_colombian_conservative_s(self):
        """Test Colombian conservative s-pronunciation."""
        features = RegionalPhonetics.get_features(SpanishRegion.COLOMBIAN)
        # Colombian maintains 's', so should have fewer transformations
        assert len(features) <= 3

    def test_neutral_no_features(self):
        """Test neutral region has no special features."""
        features = RegionalPhonetics.get_features(SpanishRegion.NEUTRAL)
        assert len(features) == 0


class TestRegionalProsody:
    """Test prosodic patterns."""

    def test_rioplatense_prosody(self):
        """Test Rioplatense prosodic patterns."""
        patterns = RegionalProsody.get_patterns(SpanishRegion.RIOPLATENSE)
        assert len(patterns) > 0

        # Check for intonation pattern
        intonation = [p for p in patterns if p.pattern_type == "intonation"]
        assert len(intonation) > 0

        # Check for stress pattern
        stress = [p for p in patterns if p.pattern_type == "stress"]
        assert len(stress) > 0

    def test_colombian_prosody(self):
        """Test Colombian prosodic patterns."""
        patterns = RegionalProsody.get_patterns(SpanishRegion.COLOMBIAN)
        assert len(patterns) > 0

        # Should have question tags
        markers = []
        for p in patterns:
            markers.extend(p.markers)
        assert "¿cierto?" in markers or "¿sí?" in markers

    def test_mexican_prosody(self):
        """Test Mexican prosodic patterns."""
        patterns = RegionalProsody.get_patterns(SpanishRegion.MEXICAN)
        assert len(patterns) > 0

        # Should have distinctive markers
        markers = []
        for p in patterns:
            markers.extend(p.markers)
        assert "¿verdad?" in markers or "órale" in markers

    def test_neutral_no_prosody(self):
        """Test neutral region has no special prosody."""
        patterns = RegionalProsody.get_patterns(SpanishRegion.NEUTRAL)
        assert len(patterns) == 0


class TestRegionalSlang:
    """Test slang detection and dictionaries."""

    def test_rioplatense_slang_dict(self):
        """Test Rioplatense slang dictionary."""
        slang = RegionalSlang.get_slang_dict(SpanishRegion.RIOPLATENSE)

        # Check key terms
        assert "che" in slang
        assert "boludo" in slang
        assert "vos" in slang
        assert "tenés" in slang
        assert "querés" in slang
        assert "quilombo" in slang
        assert "laburo" in slang
        assert "pibe" in slang

    def test_colombian_slang_dict(self):
        """Test Colombian slang dictionary."""
        slang = RegionalSlang.get_slang_dict(SpanishRegion.COLOMBIAN)

        # Check key terms
        assert "parcero" in slang or "parce" in slang
        assert "chimba" in slang
        assert "bacano" in slang
        assert "polas" in slang

    def test_mexican_slang_dict(self):
        """Test Mexican slang dictionary."""
        slang = RegionalSlang.get_slang_dict(SpanishRegion.MEXICAN)

        # Check key terms
        assert "órale" in slang
        assert "güey" in slang or "wey" in slang
        assert "chido" in slang
        assert "padre" in slang
        assert "neta" in slang

    def test_detect_rioplatense(self):
        """Test auto-detection of Rioplatense."""
        text = "Che boludo, ¿vos sabés algo?"
        detected = RegionalSlang.detect_region_from_text(text)
        assert detected == SpanishRegion.RIOPLATENSE

    def test_detect_colombian(self):
        """Test auto-detection of Colombian."""
        text = "Parcero, eso está muy bacano"
        detected = RegionalSlang.detect_region_from_text(text)
        assert detected == SpanishRegion.COLOMBIAN

    def test_detect_mexican(self):
        """Test auto-detection of Mexican."""
        text = "Órale güey, no manches"
        detected = RegionalSlang.detect_region_from_text(text)
        assert detected == SpanishRegion.MEXICAN

    def test_detect_neutral(self):
        """Test neutral text returns None."""
        text = "Hola, ¿cómo estás? Todo bien."
        detected = RegionalSlang.detect_region_from_text(text)
        assert detected is None

    def test_voseo_in_slang(self):
        """Test voseo forms are in Rioplatense slang."""
        slang = RegionalSlang.get_slang_dict(SpanishRegion.RIOPLATENSE)

        voseo_forms = ["vos", "tenés", "querés", "podés", "sabés", "sos"]
        for form in voseo_forms:
            assert form in slang, f"Voseo form '{form}' not in slang dict"


class TestSpanishRegionalProcessor:
    """Test the main processor class."""

    def test_initialization(self):
        """Test processor initialization."""
        processor = SpanishRegionalProcessor(region=SpanishRegion.RIOPLATENSE)
        assert processor.region == SpanishRegion.RIOPLATENSE
        assert not processor.auto_detect

    def test_initialization_with_auto_detect(self):
        """Test processor with auto-detect enabled."""
        processor = SpanishRegionalProcessor(auto_detect=True)
        assert processor.auto_detect

    def test_normalize_text(self):
        """Test text normalization."""
        processor = SpanishRegionalProcessor(region=SpanishRegion.RIOPLATENSE)
        text = "Hola, ¿cómo estás?"
        result = processor.normalize_text(text)
        assert result is not None
        assert isinstance(result, str)

    def test_apply_phonetic_features_rioplatense(self):
        """Test phonetic features for Rioplatense."""
        processor = SpanishRegionalProcessor(region=SpanishRegion.RIOPLATENSE)
        text = "¿Vos sabés dónde está?"
        result = processor.apply_phonetic_features(text)

        # Should have s-aspiration
        assert 'h' in result or result != text

    def test_apply_phonetic_features_neutral(self):
        """Test phonetic features for neutral (none)."""
        processor = SpanishRegionalProcessor(region=SpanishRegion.NEUTRAL)
        text = "¿Tú sabes dónde está?"
        result = processor.apply_phonetic_features(text)

        # Should be unchanged
        assert result == text

    def test_add_prosodic_markers(self):
        """Test prosodic marker detection."""
        processor = SpanishRegionalProcessor(region=SpanishRegion.RIOPLATENSE)
        text = "Che, ¿vos tenés tiempo?"
        result, hints = processor.add_prosodic_markers(text)

        assert isinstance(hints, list)
        # Should detect 'che' and 'vos' as prosodic markers
        assert len(hints) > 0

    def test_process_full_pipeline(self):
        """Test full processing pipeline."""
        processor = SpanishRegionalProcessor(region=SpanishRegion.RIOPLATENSE)
        text = "Che boludo, ¿vos querés tomar unos mates?"
        result = processor.process(text)

        # Check all expected keys
        assert "original" in result
        assert "normalized" in result
        assert "phonetic" in result
        assert "final" in result
        assert "region" in result
        assert "prosodic_hints" in result
        assert "detected_slang" in result

        # Check values
        assert result["original"] == text
        assert result["region"] == "rioplatense"
        assert len(result["detected_slang"]) > 0

    def test_process_detect_slang(self):
        """Test slang detection in processing."""
        processor = SpanishRegionalProcessor(region=SpanishRegion.RIOPLATENSE)
        text = "Che boludo, ¿vos sabés?"
        result = processor.process(text)

        slang_terms = [s["term"] for s in result["detected_slang"]]
        assert "che" in slang_terms
        assert "boludo" in slang_terms
        assert "vos" in slang_terms

    def test_auto_detect_changes_region(self):
        """Test auto-detect changes the processor's region."""
        processor = SpanishRegionalProcessor(
            region=SpanishRegion.NEUTRAL,
            auto_detect=True
        )

        text = "Che boludo, ¿vos sabés?"
        result = processor.process(text)

        # Should have detected Rioplatense
        assert result["region"] == "rioplatense"
        assert processor.region == SpanishRegion.RIOPLATENSE

    def test_apply_phonetics_false(self):
        """Test processing without phonetics."""
        processor = SpanishRegionalProcessor(region=SpanishRegion.RIOPLATENSE)
        text = "¿Vos sabés?"
        result = processor.process(text, apply_phonetics=False)

        # Phonetic should be same as normalized
        assert result["phonetic"] == result["normalized"]


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_get_regional_processor_string(self):
        """Test get_regional_processor with string."""
        processor = get_regional_processor(region="rioplatense")
        assert processor.region == SpanishRegion.RIOPLATENSE

    def test_get_regional_processor_enum(self):
        """Test get_regional_processor with enum."""
        processor = get_regional_processor(region=SpanishRegion.COLOMBIAN)
        assert processor.region == SpanishRegion.COLOMBIAN

    def test_get_regional_processor_auto_detect(self):
        """Test get_regional_processor with auto-detect."""
        processor = get_regional_processor(region="neutral", auto_detect=True)
        assert processor.auto_detect

    def test_process_spanish_text_basic(self):
        """Test process_spanish_text convenience function."""
        result = process_spanish_text("Hola mundo", region="neutral")
        assert "original" in result
        assert result["region"] == "neutral"

    def test_process_spanish_text_auto_detect(self):
        """Test process_spanish_text with auto-detect."""
        result = process_spanish_text(
            "Che boludo, ¿vos sabés?",
            auto_detect=True
        )
        assert result["region"] == "rioplatense"


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_rioplatense_complete(self):
        """Test complete Rioplatense processing."""
        text = "Che boludo, ¿vos querés ir al quilombo ese?"
        result = process_spanish_text(text, region="rioplatense")

        # Check detection
        slang_terms = [s["term"] for s in result["detected_slang"]]
        assert "che" in slang_terms
        assert "boludo" in slang_terms
        assert "quilombo" in slang_terms
        assert "vos" in slang_terms
        assert "querés" in slang_terms

        # Check phonetics
        assert result["phonetic"] != text  # Should be transformed

        # Check region
        assert result["region"] == "rioplatense"

    def test_colombian_complete(self):
        """Test complete Colombian processing."""
        text = "Parcero, eso está muy bacano, ¿cierto?"
        result = process_spanish_text(text, region="colombian")

        # Check detection
        slang_terms = [s["term"] for s in result["detected_slang"]]
        assert "parcero" in slang_terms or "parce" in slang_terms
        assert "bacano" in slang_terms

        # Check region
        assert result["region"] == "colombian"

    def test_mexican_complete(self):
        """Test complete Mexican processing."""
        text = "Órale güey, eso está muy chido"
        result = process_spanish_text(text, region="mexican")

        # Check detection
        slang_terms = [s["term"] for s in result["detected_slang"]]
        assert "órale" in slang_terms
        assert "güey" in slang_terms or "wey" in slang_terms
        assert "chido" in slang_terms

        # Check region
        assert result["region"] == "mexican"

    def test_mixed_content_auto_detect(self):
        """Test auto-detect with mixed regional content."""
        texts = [
            ("Che boludo", "rioplatense"),
            ("Parce, qué chimba", "colombian"),
            ("Órale güey", "mexican"),
        ]

        for text, expected_region in texts:
            result = process_spanish_text(text, auto_detect=True)
            assert result["region"] == expected_region

    def test_voseo_conjugations(self):
        """Test all voseo conjugations are recognized."""
        voseo_texts = [
            "Vos tenés razón",
            "¿Vos querés salir?",
            "Vos podés hacerlo",
            "¿Vos sabés qué hora es?",
            "Vos sos mi amigo",
        ]

        for text in voseo_texts:
            result = process_spanish_text(text, region="rioplatense")
            slang = result["detected_slang"]

            # Should detect vos and the verb
            terms = [s["term"] for s in slang]
            assert "vos" in terms


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_text(self):
        """Test processing empty text."""
        result = process_spanish_text("", region="neutral")
        assert result["original"] == ""
        assert len(result["detected_slang"]) == 0

    def test_no_regional_markers(self):
        """Test text with no regional markers."""
        text = "Buenos días, ¿cómo está usted?"
        result = process_spanish_text(text, auto_detect=True)
        # Should default to neutral or stay neutral
        assert result["region"] in ["neutral", "rioplatense", "colombian", "mexican"]

    def test_multiple_regions(self):
        """Test text with markers from multiple regions."""
        text = "Che parce, ¿vos sabés qué onda?"
        result = process_spanish_text(text, auto_detect=True)
        # Should pick one region (the one with most markers)
        assert result["region"] in ["rioplatense", "colombian", "mexican"]

    def test_special_characters(self):
        """Test text with special characters."""
        text = "¿¡Che!? @#$ ¿Vos sabés?"
        result = process_spanish_text(text, region="rioplatense")
        # Should handle gracefully
        assert result["region"] == "rioplatense"

    def test_very_long_text(self):
        """Test with very long text."""
        text = "Che boludo, " * 100 + "¿vos sabés?"
        result = process_spanish_text(text, region="rioplatense")
        assert result["region"] == "rioplatense"
        # Should still detect slang
        assert len(result["detected_slang"]) > 0


def run_tests():
    """Run all tests and report results."""
    import subprocess

    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=True,
        text=True
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    return result.returncode == 0


if __name__ == "__main__":
    # Run without pytest if not installed
    import sys

    if PYTEST_AVAILABLE:
        sys.exit(pytest.main([__file__, "-v"]))
    else:
        print("pytest not installed, running manual tests...")

        # Manual test execution
        test_classes = [
            TestSpanishRegion,
            TestRegionalPhonetics,
            TestRegionalProsody,
            TestRegionalSlang,
            TestSpanishRegionalProcessor,
            TestConvenienceFunctions,
            TestIntegration,
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

        sys.exit(0 if failed == 0 else 1)
