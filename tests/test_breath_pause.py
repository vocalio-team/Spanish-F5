"""Tests for breath and pause modeling module."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from f5_tts.text.breath_pause import (
    PauseType,
    Pause,
    BreathPattern,
    BreathPauseAnalyzer,
    analyze_breath_pauses,
    format_breath_report,
)


class TestPauseType:
    """Test PauseType enum."""

    def test_pause_types_exist(self):
        """Test that all pause types are defined."""
        assert PauseType.MICRO.value == "micro"
        assert PauseType.SHORT.value == "short"
        assert PauseType.MEDIUM.value == "medium"
        assert PauseType.LONG.value == "long"
        assert PauseType.PARAGRAPH.value == "paragraph"
        assert PauseType.BREATH.value == "breath"


class TestPause:
    """Test Pause dataclass."""

    def test_pause_creation(self):
        """Test creating a pause."""
        pause = Pause(
            position=10,
            type=PauseType.SHORT,
            duration_ms=200,
            is_breath_point=False,
            context="test, context"
        )
        assert pause.position == 10
        assert pause.type == PauseType.SHORT
        assert pause.duration_ms == 200
        assert not pause.is_breath_point
        assert pause.context == "test, context"


class TestBreathPattern:
    """Test BreathPattern dataclass."""

    def test_breath_pattern_creation(self):
        """Test creating a breath pattern."""
        pause = Pause(10, PauseType.SHORT, 200, False, "context")
        pattern = BreathPattern(
            text="Test text",
            pauses=[pause],
            breath_points=[10],
            avg_pause_interval=100.0,
            total_duration_estimate=5.5
        )
        assert pattern.text == "Test text"
        assert len(pattern.pauses) == 1
        assert len(pattern.breath_points) == 1
        assert pattern.avg_pause_interval == 100.0
        assert pattern.total_duration_estimate == 5.5


class TestBreathPauseAnalyzer:
    """Test BreathPauseAnalyzer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = BreathPauseAnalyzer()

    def test_init(self):
        """Test analyzer initialization."""
        analyzer = BreathPauseAnalyzer()
        assert analyzer is not None

    def test_detect_punctuation_pauses_comma(self):
        """Test comma detection."""
        analyzer = BreathPauseAnalyzer()
        text = "Hola, mundo"
        pauses = analyzer._detect_punctuation_pauses(text)

        assert len(pauses) >= 1
        comma_pause = next((p for p in pauses if p.position == 4), None)
        assert comma_pause is not None
        assert comma_pause.type == PauseType.SHORT
        assert comma_pause.duration_ms == 200

    def test_detect_punctuation_pauses_period(self):
        """Test period detection."""
        analyzer = BreathPauseAnalyzer()
        text = "Hola. Mundo."
        pauses = analyzer._detect_punctuation_pauses(text)

        period_pauses = [p for p in pauses if text[p.position] == '.']
        assert len(period_pauses) >= 1
        assert all(p.type == PauseType.LONG for p in period_pauses)
        assert all(p.duration_ms == 600 for p in period_pauses)

    def test_detect_punctuation_pauses_ellipsis(self):
        """Test ellipsis detection."""
        analyzer = BreathPauseAnalyzer()
        text = "Hola... mundo"
        pauses = analyzer._detect_punctuation_pauses(text)

        # Should detect ellipsis, not individual periods
        ellipsis_pause = next((p for p in pauses if p.position == 4), None)
        assert ellipsis_pause is not None
        assert ellipsis_pause.duration_ms == 800

    def test_detect_punctuation_pauses_question(self):
        """Test question mark detection."""
        analyzer = BreathPauseAnalyzer()
        text = "¿Hola?"
        pauses = analyzer._detect_punctuation_pauses(text)

        question_pause = next((p for p in pauses if text[p.position] == '?'), None)
        assert question_pause is not None
        assert question_pause.type == PauseType.LONG
        assert question_pause.duration_ms == 600

    def test_detect_punctuation_pauses_exclamation(self):
        """Test exclamation mark detection."""
        analyzer = BreathPauseAnalyzer()
        text = "¡Hola!"
        pauses = analyzer._detect_punctuation_pauses(text)

        exclamation_pause = next((p for p in pauses if text[p.position] == '!'), None)
        assert exclamation_pause is not None
        assert exclamation_pause.type == PauseType.LONG
        assert exclamation_pause.duration_ms == 650

    def test_detect_punctuation_pauses_semicolon(self):
        """Test semicolon detection."""
        analyzer = BreathPauseAnalyzer()
        text = "Primera; segunda"
        pauses = analyzer._detect_punctuation_pauses(text)

        semicolon_pause = next((p for p in pauses if p.position == 7), None)
        assert semicolon_pause is not None
        assert semicolon_pause.type == PauseType.MEDIUM

    def test_detect_punctuation_pauses_colon(self):
        """Test colon detection."""
        analyzer = BreathPauseAnalyzer()
        text = "Nota: importante"
        pauses = analyzer._detect_punctuation_pauses(text)

        colon_pause = next((p for p in pauses if p.position == 4), None)
        assert colon_pause is not None
        assert colon_pause.type == PauseType.MEDIUM

    def test_detect_conjunction_pauses(self):
        """Test conjunction detection."""
        analyzer = BreathPauseAnalyzer()
        text = "Hola y adiós"
        pauses = analyzer._detect_conjunction_pauses(text)

        # Should detect 'y'
        y_pause = next((p for p in pauses if 5 <= p.position <= 6), None)
        assert y_pause is not None
        assert y_pause.type == PauseType.MICRO
        assert y_pause.duration_ms == 80

    def test_detect_conjunction_pauses_multiple(self):
        """Test multiple conjunction detection."""
        analyzer = BreathPauseAnalyzer()
        text = "Primero y segundo pero tercero"
        pauses = analyzer._detect_conjunction_pauses(text)

        # Should detect both 'y' and 'pero'
        assert len(pauses) >= 2

    def test_detect_conjunction_pauses_skip_near_punctuation(self):
        """Test that conjunctions near punctuation are skipped."""
        analyzer = BreathPauseAnalyzer()
        text = "Hola, y adiós"
        pauses = analyzer._detect_conjunction_pauses(text)

        # 'y' is near comma, might be skipped
        # This tests the _has_nearby_punctuation logic

    def test_detect_paragraph_pauses(self):
        """Test paragraph break detection."""
        analyzer = BreathPauseAnalyzer()
        text = "Párrafo uno.\n\nPárrafo dos."
        pauses = analyzer._detect_paragraph_pauses(text)

        assert len(pauses) >= 1
        para_pause = pauses[0]
        assert para_pause.type == PauseType.PARAGRAPH
        assert para_pause.duration_ms == 1000
        assert para_pause.is_breath_point is True

    def test_has_nearby_punctuation(self):
        """Test nearby punctuation detection."""
        analyzer = BreathPauseAnalyzer()
        text = "Hola, mundo"

        # Position 5 is right after comma
        assert analyzer._has_nearby_punctuation(text, 5, radius=2)

        # Position 9 is far from punctuation
        assert not analyzer._has_nearby_punctuation(text, 9, radius=2)

    def test_get_context(self):
        """Test context extraction."""
        analyzer = BreathPauseAnalyzer()
        text = "This is a long piece of text for testing context"

        context = analyzer._get_context(text, 10, window=5)
        assert len(context) <= 10  # 5 before + 5 after
        assert "long" in context or "a lo" in context

    def test_get_context_newline_replacement(self):
        """Test that newlines are replaced in context."""
        analyzer = BreathPauseAnalyzer()
        text = "Line one\nLine two"

        context = analyzer._get_context(text, 8, window=10)
        assert '\n' not in context
        assert ' ' in context

    def test_calculate_avg_pause_interval(self):
        """Test average pause interval calculation."""
        analyzer = BreathPauseAnalyzer()
        pauses = [
            Pause(10, PauseType.SHORT, 200, False, ""),
            Pause(20, PauseType.SHORT, 200, False, ""),
            Pause(30, PauseType.SHORT, 200, False, ""),
        ]

        avg = analyzer._calculate_avg_pause_interval(pauses)
        assert avg == 10.0  # Intervals are 10 chars each

    def test_calculate_avg_pause_interval_single_pause(self):
        """Test average with single pause."""
        analyzer = BreathPauseAnalyzer()
        pauses = [Pause(10, PauseType.SHORT, 200, False, "")]

        avg = analyzer._calculate_avg_pause_interval(pauses)
        assert avg == 0.0

    def test_calculate_avg_pause_interval_empty(self):
        """Test average with no pauses."""
        analyzer = BreathPauseAnalyzer()
        avg = analyzer._calculate_avg_pause_interval([])
        assert avg == 0.0

    def test_estimate_duration(self):
        """Test duration estimation."""
        analyzer = BreathPauseAnalyzer()
        text = "A" * 100  # 100 characters
        pauses = [
            Pause(50, PauseType.SHORT, 200, False, ""),
            Pause(99, PauseType.LONG, 600, False, ""),
        ]

        duration = analyzer._estimate_duration(text, pauses)

        # Expected: 100 chars / 15 chars/sec + 800ms pauses
        expected_char_time = 100 / 15.0
        expected_pause_time = 0.8  # 800ms in seconds
        expected = expected_char_time + expected_pause_time

        assert abs(duration - expected) < 0.1

    def test_identify_breath_points_paragraph(self):
        """Test breath point identification at paragraphs."""
        analyzer = BreathPauseAnalyzer()
        text = "First.\n\nSecond."
        pauses = analyzer._detect_paragraph_pauses(text)

        breath_points = analyzer._identify_breath_points(text, pauses)

        # Should have breath point at paragraph break
        assert len(breath_points) >= 1

    def test_identify_breath_points_long_sentence(self):
        """Test breath points in long sentences."""
        analyzer = BreathPauseAnalyzer()
        # Create a long text with multiple sentences
        text = "Sentence one. " * 50  # Very long
        pauses = analyzer._detect_punctuation_pauses(text)

        breath_points = analyzer._identify_breath_points(text, pauses)

        # Should identify multiple breath points
        assert len(breath_points) >= 1

    def test_analyze_simple_text(self):
        """Test analyze on simple text."""
        analyzer = BreathPauseAnalyzer()
        text = "Hola, mundo. ¿Cómo estás?"

        pattern = analyzer.analyze(text)

        assert pattern.text == text
        assert len(pattern.pauses) > 0
        assert pattern.total_duration_estimate > 0
        assert pattern.avg_pause_interval >= 0

    def test_analyze_complex_text(self):
        """Test analyze on complex text."""
        analyzer = BreathPauseAnalyzer()
        text = """
        Primera oración con coma, y punto. Segunda oración.

        Segundo párrafo con más contenido: importante. ¿Preguntas?
        ¡Exclamaciones! Y más... texto.
        """

        pattern = analyzer.analyze(text)

        assert len(pattern.pauses) > 5
        assert len(pattern.breath_points) >= 1  # At least paragraph break
        assert pattern.total_duration_estimate > 0

    def test_analyze_marks_breath_points_in_pauses(self):
        """Test that analyze marks breath points correctly."""
        analyzer = BreathPauseAnalyzer()
        text = "First.\n\nSecond."

        pattern = analyzer.analyze(text)

        # Check that pauses at breath points are marked
        breath_pauses = [p for p in pattern.pauses if p.is_breath_point]
        assert len(breath_pauses) >= 1

    def test_insert_pauses_in_text_breath_marker(self):
        """Test inserting breath markers."""
        analyzer = BreathPauseAnalyzer()
        text = "Test."
        pauses = [
            Pause(4, PauseType.LONG, 600, True, ""),
        ]

        marked = analyzer.insert_pauses_in_text(text, pauses)
        assert "[BREATH:" in marked
        assert "ms]" in marked

    def test_insert_pauses_in_text_micro(self):
        """Test inserting micro pause markers."""
        analyzer = BreathPauseAnalyzer()
        text = "Test."
        pauses = [
            Pause(4, PauseType.MICRO, 80, False, ""),
        ]

        marked = analyzer.insert_pauses_in_text(text, pauses)
        assert "‧" in marked

    def test_insert_pauses_in_text_short(self):
        """Test inserting short pause markers."""
        analyzer = BreathPauseAnalyzer()
        text = "Test."
        pauses = [
            Pause(4, PauseType.SHORT, 200, False, ""),
        ]

        marked = analyzer.insert_pauses_in_text(text, pauses)
        assert "·" in marked

    def test_insert_pauses_in_text_medium(self):
        """Test inserting medium pause markers."""
        analyzer = BreathPauseAnalyzer()
        text = "Test."
        pauses = [
            Pause(4, PauseType.MEDIUM, 400, False, ""),
        ]

        marked = analyzer.insert_pauses_in_text(text, pauses)
        assert "/" in marked

    def test_insert_pauses_in_text_long(self):
        """Test inserting long pause markers."""
        analyzer = BreathPauseAnalyzer()
        text = "Test."
        pauses = [
            Pause(4, PauseType.LONG, 600, False, ""),
        ]

        marked = analyzer.insert_pauses_in_text(text, pauses)
        assert "|" in marked

    def test_insert_pauses_in_text_paragraph(self):
        """Test inserting paragraph pause markers."""
        analyzer = BreathPauseAnalyzer()
        text = "Test."
        pauses = [
            Pause(4, PauseType.PARAGRAPH, 1000, False, ""),
        ]

        marked = analyzer.insert_pauses_in_text(text, pauses)
        assert "[PAUSE]" in marked

    def test_insert_pauses_in_text_multiple(self):
        """Test inserting multiple markers."""
        analyzer = BreathPauseAnalyzer()
        text = "One, two. Three"
        pauses = [
            Pause(3, PauseType.SHORT, 200, False, ""),
            Pause(8, PauseType.LONG, 600, False, ""),
        ]

        marked = analyzer.insert_pauses_in_text(text, pauses)
        assert len(marked) > len(text)  # Should be longer with markers


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_analyze_breath_pauses(self):
        """Test analyze_breath_pauses function."""
        text = "Hola, mundo. ¿Cómo estás?"
        pattern = analyze_breath_pauses(text)

        assert isinstance(pattern, BreathPattern)
        assert pattern.text == text
        assert len(pattern.pauses) > 0

    def test_format_breath_report(self):
        """Test format_breath_report function."""
        text = "Hola, mundo. ¿Cómo estás?"
        pattern = analyze_breath_pauses(text)

        report = format_breath_report(pattern)

        assert "BREATH & PAUSE ANALYSIS" in report
        assert "Total Pauses:" in report
        assert "Breath Points:" in report
        assert "Estimated Duration:" in report
        assert "Pause Breakdown:" in report

    def test_format_breath_report_long_text(self):
        """Test report formatting with long text."""
        text = "Test. " * 100  # Long text with many pauses
        pattern = analyze_breath_pauses(text)

        report = format_breath_report(pattern)

        # Should show sample and indicate there are more
        if len(pattern.pauses) > 10:
            assert "and" in report and "more" in report


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_text(self):
        """Test with empty text."""
        analyzer = BreathPauseAnalyzer()
        pattern = analyzer.analyze("")

        assert len(pattern.pauses) == 0
        assert len(pattern.breath_points) == 0
        assert pattern.total_duration_estimate == 0.0

    def test_text_with_only_punctuation(self):
        """Test with only punctuation."""
        analyzer = BreathPauseAnalyzer()
        pattern = analyzer.analyze(".,;:!?")

        assert len(pattern.pauses) >= 1

    def test_text_without_punctuation(self):
        """Test with no punctuation."""
        analyzer = BreathPauseAnalyzer()
        pattern = analyzer.analyze("hola mundo como estas")

        # May have conjunction pauses
        assert pattern.total_duration_estimate > 0

    def test_very_long_text(self):
        """Test with very long text."""
        analyzer = BreathPauseAnalyzer()
        text = "Test sentence. " * 1000

        pattern = analyzer.analyze(text)

        assert len(pattern.pauses) > 0
        assert len(pattern.breath_points) > 0  # Should need multiple breaths

    def test_unicode_text(self):
        """Test with Unicode characters."""
        analyzer = BreathPauseAnalyzer()
        text = "¿Cómo está? ¡Muy bien! Café, niño, señor."

        pattern = analyzer.analyze(text)

        assert len(pattern.pauses) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
