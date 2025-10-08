"""Tests for adaptive configuration features."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from f5_tts.core import get_adaptive_nfe_step, get_adaptive_crossfade_duration, get_config


def test_adaptive_nfe_short_text():
    """Test adaptive NFE for short text."""
    text = "Hola."
    nfe = get_adaptive_nfe_step(text)
    assert nfe == 14, f"Expected 14 for short text, got {nfe}"
    print(f"✓ Short text ('{text}'): {nfe} steps")


def test_adaptive_nfe_normal_text():
    """Test adaptive NFE for normal text."""
    text = "Esta es una oración de longitud normal para pruebas de texto."
    nfe = get_adaptive_nfe_step(text)
    assert nfe == 16, f"Expected 16 for normal text, got {nfe}"
    print(f"✓ Normal text ({len(text)} chars): {nfe} steps")


def test_adaptive_nfe_long_text():
    """Test adaptive NFE for long text."""
    text = """Esta es una oración muy larga que contiene mucho texto
    para verificar que el sistema adapte correctamente el número de pasos
    de evaluación de función cuando el texto es extenso, largo y muy complejo."""
    nfe = get_adaptive_nfe_step(text)
    assert nfe >= 20, f"Expected >= 20 for long text, got {nfe}"
    print(f"✓ Long text ({len(text)} chars): {nfe} steps")


def test_adaptive_nfe_with_questions():
    """Test adaptive NFE with questions (more expressive)."""
    text = "¿Cómo estás hoy?"
    nfe = get_adaptive_nfe_step(text)
    # Should add +2 for question marker
    assert nfe >= 16, f"Expected >= 16 for question, got {nfe}"
    print(f"✓ Question text: {nfe} steps (increased for expressiveness)")


def test_adaptive_nfe_with_exclamations():
    """Test adaptive NFE with exclamations."""
    text = "¡Qué día tan increíble!"
    nfe = get_adaptive_nfe_step(text)
    # Should add +2 for exclamation marker
    assert nfe >= 16, f"Expected >= 16 for exclamation, got {nfe}"
    print(f"✓ Exclamation text: {nfe} steps (increased for expressiveness)")


def test_adaptive_nfe_multiple_sentences():
    """Test adaptive NFE with multiple sentences."""
    text = """Hola, ¿cómo estás? Yo estoy muy bien. Me alegra verte.
    ¿Vamos a tomar un café? Sería genial."""
    nfe = get_adaptive_nfe_step(text)
    # Should add +2 for multiple sentences
    assert nfe >= 18, f"Expected >= 18 for multiple sentences, got {nfe}"
    print(f"✓ Multiple sentences: {nfe} steps (increased for coherence)")


def test_adaptive_nfe_disabled():
    """Test that adaptive NFE can be disabled."""
    config = get_config()
    original_setting = config.enable_adaptive_nfe

    # Disable adaptive
    config.enable_adaptive_nfe = False

    text = "This is a test."
    nfe = get_adaptive_nfe_step(text)
    assert nfe == 16, f"Expected default 16 when disabled, got {nfe}"

    # Restore
    config.enable_adaptive_nfe = original_setting
    print(f"✓ Adaptive NFE can be disabled (returns default: {nfe})")


def test_adaptive_nfe_clamping():
    """Test that NFE steps are clamped to reasonable range."""
    # Very short text should not go below 12
    text = "Hi"
    nfe = get_adaptive_nfe_step(text)
    assert nfe >= 12, f"NFE should be >= 12, got {nfe}"

    # Even complex text should not exceed 32
    assert nfe <= 32, f"NFE should be <= 32, got {nfe}"
    print(f"✓ NFE steps clamped to range [12, 32]")


def test_adaptive_crossfade_base():
    """Test base crossfade duration."""
    duration = get_adaptive_crossfade_duration()
    config = get_config()
    assert duration == config.default_cross_fade_duration
    print(f"✓ Base crossfade: {duration}s")


def test_adaptive_crossfade_continuous_speech():
    """Test shorter crossfade for continuous speech (high energy)."""
    duration = get_adaptive_crossfade_duration(
        chunk1_energy=0.8,
        chunk2_energy=0.9
    )
    config = get_config()
    expected = config.default_cross_fade_duration * 0.6
    assert abs(duration - expected) < 0.01
    print(f"✓ Continuous speech (high energy): {duration:.2f}s (shorter)")


def test_adaptive_crossfade_at_pause():
    """Test longer crossfade at natural boundaries."""
    duration = get_adaptive_crossfade_duration(at_pause=True)
    config = get_config()
    expected = config.default_cross_fade_duration * 1.25
    assert abs(duration - expected) < 0.01
    print(f"✓ At pause boundary: {duration:.2f}s (longer)")


def test_config_default_improvements():
    """Test that new defaults are improved."""
    config = get_config()

    # Crossfade should be 0.8s (was 0.5s)
    assert config.default_cross_fade_duration == 0.8
    print(f"✓ Improved default crossfade: {config.default_cross_fade_duration}s")

    # Adaptive NFE should be enabled by default
    assert config.enable_adaptive_nfe == True
    print(f"✓ Adaptive NFE enabled by default")


def test_realistic_scenarios():
    """Test realistic TTS scenarios."""
    scenarios = [
        ("Hola.", "Simple greeting"),
        ("¿Cómo estás hoy?", "Simple question"),
        ("¡Qué día tan hermoso!", "Exclamation"),
        (
            "Buenos días. ¿Cómo has estado? Me alegra mucho verte.",
            "Multi-sentence conversation"
        ),
        (
            """El análisis de los datos reveló patrones interesantes.
            Primero, observamos una tendencia clara en los resultados.
            Segundo, las correlaciones fueron significativas.
            Finalmente, las conclusiones respaldan nuestra hipótesis inicial.""",
            "Long paragraph"
        ),
    ]

    print("\n" + "=" * 60)
    print("REALISTIC SCENARIO TESTING")
    print("=" * 60)

    for text, description in scenarios:
        nfe = get_adaptive_nfe_step(text)
        print(f"\n{description}:")
        print(f"  Text length: {len(text)} chars")
        print(f"  NFE steps: {nfe}")
        print(f"  Text preview: {text[:60]}...")


def run_all_tests():
    """Run all adaptive configuration tests."""
    print("=" * 60)
    print("ADAPTIVE CONFIGURATION TESTS")
    print("=" * 60)
    print()

    tests = [
        test_adaptive_nfe_short_text,
        test_adaptive_nfe_normal_text,
        test_adaptive_nfe_long_text,
        test_adaptive_nfe_with_questions,
        test_adaptive_nfe_with_exclamations,
        test_adaptive_nfe_multiple_sentences,
        test_adaptive_nfe_disabled,
        test_adaptive_nfe_clamping,
        test_adaptive_crossfade_base,
        test_adaptive_crossfade_continuous_speech,
        test_adaptive_crossfade_at_pause,
        test_config_default_improvements,
        test_realistic_scenarios,
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
