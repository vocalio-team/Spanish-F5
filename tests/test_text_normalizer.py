"""Tests for Spanish text normalization."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from f5_tts.text import SpanishTextNormalizer, normalize_spanish_text


def test_number_normalization():
    """Test number to words conversion."""
    normalizer = SpanishTextNormalizer()

    assert normalizer._number_to_words(0) == "cero"
    assert normalizer._number_to_words(1) == "uno"
    assert normalizer._number_to_words(10) == "diez"
    assert normalizer._number_to_words(15) == "quince"
    assert normalizer._number_to_words(21) == "veintiuno"
    assert normalizer._number_to_words(100) == "cien"
    assert normalizer._number_to_words(101) == "ciento uno"
    assert normalizer._number_to_words(500) == "quinientos"
    assert normalizer._number_to_words(1000) == "mil"
    assert normalizer._number_to_words(1234) == "mil doscientos treinta y cuatro"

    print("✓ Number normalization tests passed")


def test_abbreviation_expansion():
    """Test abbreviation expansion."""
    normalizer = SpanishTextNormalizer()

    text = "El Dr. García vive en la Av. Principal."
    expected = "El Doctor García vive en la Avenida Principal."
    result = normalizer._normalize_abbreviations(text)
    assert result == expected

    text = "La Sra. López es Profa. de matemáticas."
    result = normalizer._normalize_abbreviations(text)
    assert "Señora" in result
    assert "Profesora" in result

    print("✓ Abbreviation expansion tests passed")


def test_time_normalization():
    """Test time format conversion."""
    normalizer = SpanishTextNormalizer()

    text = "La reunión es a las 09:00 horas."
    result = normalizer._normalize_time(text)
    assert "nueve en punto" in result

    text = "Nos vemos a las 14:30."
    result = normalizer._normalize_time(text)
    assert "catorce y media" in result

    text = "El tren sale a las 10:15."
    result = normalizer._normalize_time(text)
    assert "diez y cuarto" in result

    print("✓ Time normalization tests passed")


def test_date_normalization():
    """Test date format conversion."""
    normalizer = SpanishTextNormalizer()

    text = "Nací el 15/03/1990."
    result = normalizer._normalize_dates(text)
    assert "quince de marzo" in result
    assert "mil novecientos noventa" in result

    text = "La fecha es 01/01/2024."
    result = normalizer._normalize_dates(text)
    assert "primero de enero" in result
    assert "dos mil veinticuatro" in result

    print("✓ Date normalization tests passed")


def test_currency_normalization():
    """Test currency symbol conversion."""
    normalizer = SpanishTextNormalizer()

    text = "El precio es $50."
    result = normalizer._normalize_currency(text)
    assert "cincuenta dólares" in result

    text = "Cuesta €30."
    result = normalizer._normalize_currency(text)
    assert "treinta euros" in result

    print("✓ Currency normalization tests passed")


def test_ordinal_normalization():
    """Test ordinal number conversion."""
    normalizer = SpanishTextNormalizer()

    text = "Vivo en el 3° piso."
    result = normalizer._normalize_ordinals(text)
    assert "tercero" in result or "tercer" in result

    text = "Es mi 1° día aquí."
    result = normalizer._normalize_ordinals(text)
    assert "primero" in result or "primer" in result

    print("✓ Ordinal normalization tests passed")


def test_decimal_normalization():
    """Test decimal number conversion."""
    normalizer = SpanishTextNormalizer()

    text = "El valor es 3.14."
    result = normalizer._normalize_decimals(text)
    assert "tres punto uno cuatro" in result

    text = "Mide 1.5 metros."
    result = normalizer._normalize_decimals(text)
    assert "uno punto cinco" in result

    print("✓ Decimal normalization tests passed")


def test_full_normalization():
    """Test complete normalization pipeline."""
    text = "El Dr. García cobra $100 por consulta. Llega a las 09:30 el 01/01/2024."
    result = normalize_spanish_text(text)

    # Check all transformations happened
    assert "Doctor" in result
    assert "dólares" in result
    assert "nueve y" in result
    assert "primero de enero" in result
    assert "dos mil veinticuatro" in result

    print("✓ Full normalization test passed")


def test_complex_text():
    """Test normalization with complex, realistic text."""
    text = """
    El Dr. Martínez atenderá el día 15/12/2024 a las 10:30.
    La consulta cuesta $150 y dura 45 minutos.
    Su oficina está en la Av. Principal, 3° piso, oficina núm. 305.
    """

    result = normalize_spanish_text(text)

    # Verify key transformations
    assert "Doctor" in result
    assert "Avenida" in result
    assert "número" in result
    assert "dólares" in result
    assert "diez y media" in result or "diez y treinta" in result

    print("✓ Complex text normalization passed")
    print(f"Original: {text[:100]}...")
    print(f"Normalized: {result[:100]}...")


def test_regional_compatibility():
    """Test that normalization works with regional text."""
    # Rioplatense
    text = "Che, son las 14:00 y necesito $500 para el laburo."
    result = normalize_spanish_text(text)
    assert "catorce en punto" in result
    assert "quinientos dólares" in result

    # Colombian
    text = "Parcero, la reunión es a las 09:15 del 20/06/2024."
    result = normalize_spanish_text(text)
    assert "nueve y cuarto" in result
    assert "veinte de junio" in result

    # Mexican
    text = "Güey, son las 18:30 y cuesta $200."
    result = normalize_spanish_text(text)
    assert "dieciocho y media" in result
    assert "doscientos dólares" in result

    print("✓ Regional compatibility tests passed")


def run_all_tests():
    """Run all normalization tests."""
    print("=" * 60)
    print("SPANISH TEXT NORMALIZER TESTS")
    print("=" * 60)
    print()

    tests = [
        test_number_normalization,
        test_abbreviation_expansion,
        test_time_normalization,
        test_date_normalization,
        test_currency_normalization,
        test_ordinal_normalization,
        test_decimal_normalization,
        test_full_normalization,
        test_complex_text,
        test_regional_compatibility,
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
