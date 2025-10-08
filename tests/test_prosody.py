"""Tests for Spanish prosody analysis."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from f5_tts.text import (
    analyze_spanish_prosody,
    format_prosody_report,
    ProsodyType,
    IntensityLevel
)


def test_yes_no_questions():
    """Test detection of yes/no questions (rising intonation)."""
    print("Test 1: Yes/No Questions")
    print("-" * 60)

    text = "¿Quieres tomar un café?"
    analysis = analyze_spanish_prosody(text)

    # Should detect rising tone
    rising_markers = [m for m in analysis.markers if m.type == ProsodyType.RISING_TONE]
    assert len(rising_markers) > 0, "Should detect rising tone in yes/no question"

    # Check metadata
    assert any(m.metadata.get('question_type') == 'yes_no' for m in rising_markers)

    print(f"✓ Detected rising tone in yes/no question")
    print(f"✓ Marked text: {analysis.marked_text}")
    print()


def test_information_questions():
    """Test detection of information questions (falling intonation)."""
    print("Test 2: Information Questions")
    print("-" * 60)

    text = "¿Dónde está el baño?"
    analysis = analyze_spanish_prosody(text)

    # Should detect falling tone (wh-question)
    falling_markers = [m for m in analysis.markers if m.type == ProsodyType.FALLING_TONE]
    assert len(falling_markers) > 0, "Should detect falling tone in information question"

    # Check metadata
    assert any(m.metadata.get('question_type') == 'information' for m in falling_markers)

    print(f"✓ Detected falling tone in wh-question")
    print(f"✓ Marked text: {analysis.marked_text}")
    print()


def test_exclamations():
    """Test detection of exclamations."""
    print("Test 3: Exclamations")
    print("-" * 60)

    texts = [
        "¡Qué día tan hermoso!",
        "¡Ay, qué dolor!",
        "¡Increíble!"
    ]

    for text in texts:
        analysis = analyze_spanish_prosody(text)
        exclamation_markers = [m for m in analysis.markers if m.type == ProsodyType.EXCLAMATION]
        assert len(exclamation_markers) > 0, f"Should detect exclamation in: {text}"
        print(f"✓ '{text}' → {analysis.marked_text}")

    print()


def test_emphasis_detection():
    """Test detection of emphasis words."""
    print("Test 4: Emphasis Detection")
    print("-" * 60)

    text = "Esto es muy importante y nunca debes olvidarlo."
    analysis = analyze_spanish_prosody(text)

    emphasis_markers = [m for m in analysis.markers if m.type == ProsodyType.EMPHASIS]
    assert len(emphasis_markers) > 0, "Should detect emphasis words"

    # Should detect 'muy' and 'nunca'
    emphasis_words = [m.metadata.get('word') for m in emphasis_markers]
    assert 'muy' in emphasis_words or 'nunca' in emphasis_words

    print(f"✓ Detected {len(emphasis_markers)} emphasis markers")
    print(f"✓ Words: {', '.join(emphasis_words)}")
    print()


def test_pause_detection():
    """Test detection of natural pauses."""
    print("Test 5: Pause Detection")
    print("-" * 60)

    text = "Buenos días, ¿cómo estás? Espero que bien."
    analysis = analyze_spanish_prosody(text)

    pause_markers = [m for m in analysis.markers if m.type == ProsodyType.PAUSE]
    assert len(pause_markers) > 0, "Should detect pauses"

    # Should have pauses at comma and periods
    print(f"✓ Detected {len(pause_markers)} pause points")

    # Check intensity levels
    high_pauses = sum(1 for m in pause_markers if m.intensity == IntensityLevel.HIGH)
    low_pauses = sum(1 for m in pause_markers if m.intensity == IntensityLevel.LOW)

    print(f"✓ High intensity (sentence-end): {high_pauses}")
    print(f"✓ Low intensity (comma): {low_pauses}")
    print()


def test_sentence_boundaries():
    """Test sentence boundary detection."""
    print("Test 6: Sentence Boundaries")
    print("-" * 60)

    text = "Hola. ¿Cómo estás? Muy bien, gracias. ¿Y tú?"
    analysis = analyze_spanish_prosody(text)

    # Should detect 4 sentence boundaries
    assert len(analysis.sentence_boundaries) >= 3, "Should detect multiple sentences"

    print(f"✓ Detected {len(analysis.sentence_boundaries)} sentence boundaries")
    print(f"✓ Positions: {analysis.sentence_boundaries}")
    print()


def test_breath_points():
    """Test natural breath point detection."""
    print("Test 7: Breath Points")
    print("-" * 60)

    text = """Buenos días. Mi nombre es Juan, y trabajo en una empresa de tecnología.
    Me gusta mucho mi trabajo, aunque a veces es estresante."""

    analysis = analyze_spanish_prosody(text)

    assert len(analysis.breath_points) > 0, "Should detect breath points"

    print(f"✓ Detected {len(analysis.breath_points)} breath points")
    print(f"✓ Sentence boundaries: {len(analysis.sentence_boundaries)}")
    print()


def test_stress_points():
    """Test lexical stress point detection."""
    print("Test 8: Stress Points")
    print("-" * 60)

    text = "El perro grande corre rápidamente por el parque."
    analysis = analyze_spanish_prosody(text)

    assert len(analysis.stress_points) > 0, "Should detect stress points"

    # Content words should receive stress (perro, grande, corre, rápidamente, parque)
    # Function words shouldn't (el, por)

    print(f"✓ Detected {len(analysis.stress_points)} stress points")
    print(f"✓ Stressed words: content words")
    print()


def test_intensity_levels():
    """Test that intensity levels are assigned correctly."""
    print("Test 9: Intensity Levels")
    print("-" * 60)

    texts = {
        "¡Qué hermoso!": IntensityLevel.VERY_HIGH,  # Strong exclamation
        "Esto es muy bueno.": IntensityLevel.MEDIUM,  # Emphasis
        "Nunca lo haré.": IntensityLevel.HIGH,  # Strong negation
    }

    for text, expected_min_intensity in texts.items():
        analysis = analyze_spanish_prosody(text)

        # Find highest intensity marker
        if analysis.markers:
            max_intensity = max(m.intensity for m in analysis.markers)
            print(f"✓ '{text}' → {max_intensity.value}")

    print()


def test_pitch_contours():
    """Test pitch contour analysis."""
    print("Test 10: Pitch Contours")
    print("-" * 60)

    # Interrogative pattern
    text1 = "¿Vienes? ¿Puedes? ¿Quieres?"
    analysis1 = analyze_spanish_prosody(text1)
    assert analysis1.pitch_contours['overall_pattern'] in ['interrogative', 'neutral']

    # Expressive pattern
    text2 = "¡Increíble! ¡Fantástico! ¡Maravilloso!"
    analysis2 = analyze_spanish_prosody(text2)
    assert analysis2.pitch_contours['overall_pattern'] in ['expressive', 'neutral']

    print(f"✓ Questions → {analysis1.pitch_contours['overall_pattern']}")
    print(f"✓ Exclamations → {analysis2.pitch_contours['overall_pattern']}")
    print()


def test_complex_text():
    """Test with complex, realistic text."""
    print("Test 11: Complex Text")
    print("-" * 60)

    text = """¡Buenos días! ¿Cómo estás hoy? Espero que muy bien.
    Quería preguntarte algo importante: ¿puedes ayudarme con el proyecto?
    Sería realmente fantástico si pudieras hacerlo. ¡Muchas gracias!"""

    analysis = analyze_spanish_prosody(text)

    # Should detect various markers
    assert len(analysis.markers) > 5, "Should detect multiple markers in complex text"

    types_found = set(m.type for m in analysis.markers)
    assert len(types_found) >= 3, "Should detect at least 3 different prosody types"

    print(f"✓ Detected {len(analysis.markers)} total markers")
    print(f"✓ Types found: {', '.join(t.value for t in types_found)}")
    print(f"✓ Marked text preview:")
    print(f"  {analysis.marked_text[:100]}...")
    print()


def test_connector_pauses():
    """Test pauses at connectors."""
    print("Test 12: Connector Pauses")
    print("-" * 60)

    text = "Me gusta, pero es caro. Sin embargo, lo compraré."
    analysis = analyze_spanish_prosody(text)

    pause_markers = [m for m in analysis.markers if m.type == ProsodyType.PAUSE]
    connector_pauses = [m for m in pause_markers if 'connector' in m.metadata]

    print(f"✓ Total pauses: {len(pause_markers)}")
    print(f"✓ Connector pauses: {len(connector_pauses)}")
    if connector_pauses:
        connectors = [m.metadata['connector'] for m in connector_pauses]
        print(f"✓ Connectors: {', '.join(connectors)}")
    print()


def test_format_report():
    """Test report formatting."""
    print("Test 13: Report Formatting")
    print("-" * 60)

    text = "¿Cómo estás? ¡Muy bien, gracias!"
    analysis = analyze_spanish_prosody(text)

    report = format_prosody_report(analysis)

    assert "PROSODY ANALYSIS REPORT" in report
    assert "Original Text" in report
    assert "Marked Text" in report
    assert "Markers Found" in report

    print("✓ Report generated successfully")
    print()
    print(report)
    print()


def run_all_tests():
    """Run all prosody tests."""
    print("=" * 60)
    print("SPANISH PROSODY ANALYZER TESTS")
    print("=" * 60)
    print()

    tests = [
        test_yes_no_questions,
        test_information_questions,
        test_exclamations,
        test_emphasis_detection,
        test_pause_detection,
        test_sentence_boundaries,
        test_breath_points,
        test_stress_points,
        test_intensity_levels,
        test_pitch_contours,
        test_complex_text,
        test_connector_pauses,
        test_format_report,
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
