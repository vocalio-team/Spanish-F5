"""Test suite for model utility helper functions (non-torch dependent)."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestHelperFunctions:
    """Test helper functions from model.utils."""

    def test_exists_with_none(self):
        """Test exists() with None value."""
        from f5_tts.model.utils import exists
        assert exists(None) == False

    def test_exists_with_value(self):
        """Test exists() with actual value."""
        from f5_tts.model.utils import exists
        assert exists(0) == True
        assert exists("") == True
        assert exists([]) == True
        assert exists(42) == True

    def test_default_returns_value(self):
        """Test default() returns value when exists."""
        from f5_tts.model.utils import default
        assert default(42, 100) == 42
        assert default("hello", "default") == "hello"
        assert default([], [1, 2, 3]) == []

    def test_default_returns_default(self):
        """Test default() returns default when value is None."""
        from f5_tts.model.utils import default
        assert default(None, 100) == 100
        assert default(None, "default") == "default"
        assert default(None, [1, 2, 3]) == [1, 2, 3]

    def test_repetition_found_basic(self):
        """Test repetition_found() basic functionality."""
        from f5_tts.model.utils import repetition_found

        # No repetitions
        text = "abcdefghij"
        assert repetition_found(text, length=2, tolerance=2) == False

        # Clear repetitions
        text = "aaaaaaaaaa"
        assert repetition_found(text, length=2, tolerance=2) == True

    def test_repetition_found_with_tolerance(self):
        """Test repetition_found() respects tolerance."""
        from f5_tts.model.utils import repetition_found

        # Within tolerance
        text = "abcabcabc"  # "abc" repeated 3 times
        assert repetition_found(text, length=3, tolerance=5) == False

        # Exceeds tolerance
        text = "abcabcabcabcabcabc"  # "abc" repeated 6 times
        assert repetition_found(text, length=3, tolerance=3) == True

    def test_repetition_found_different_lengths(self):
        """Test repetition_found() with different pattern lengths."""
        from f5_tts.model.utils import repetition_found

        text = "lalalala"

        # Length 2 pattern
        assert repetition_found(text, length=2, tolerance=2) == True

        # Length 4 pattern
        assert repetition_found(text, length=4, tolerance=5) == False


class TestConvertCharToPinyin:
    """Test convert_char_to_pinyin function."""

    def test_basic_conversion(self):
        """Test basic Chinese to pinyin conversion."""
        from f5_tts.model.utils import convert_char_to_pinyin

        text_list = ["你好"]
        result = convert_char_to_pinyin(text_list, polyphone=False)

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], list)

    def test_english_passthrough(self):
        """Test that English text passes through."""
        from f5_tts.model.utils import convert_char_to_pinyin

        text_list = ["hello world"]
        result = convert_char_to_pinyin(text_list, polyphone=False)

        # Should contain English characters
        result_str = ''.join(result[0])
        assert 'h' in result_str or 'e' in result_str

    def test_mixed_content(self):
        """Test mixed Chinese and English."""
        from f5_tts.model.utils import convert_char_to_pinyin

        text_list = ["你好 hello"]
        result = convert_char_to_pinyin(text_list, polyphone=False)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_empty_input(self):
        """Test empty input."""
        from f5_tts.model.utils import convert_char_to_pinyin

        text_list = [""]
        result = convert_char_to_pinyin(text_list, polyphone=False)

        assert isinstance(result, list)

    def test_polyphone_parameter(self):
        """Test polyphone parameter affects output."""
        from f5_tts.model.utils import convert_char_to_pinyin

        text_list = ["中国"]

        result_no_poly = convert_char_to_pinyin(text_list, polyphone=False)
        result_with_poly = convert_char_to_pinyin(text_list, polyphone=True)

        # Both should work
        assert isinstance(result_no_poly, list)
        assert isinstance(result_with_poly, list)


class TestGetTokenizer:
    """Test get_tokenizer function."""

    def test_get_tokenizer_byte(self):
        """Test byte tokenizer."""
        from f5_tts.model.utils import get_tokenizer

        vocab_map, vocab_size = get_tokenizer("test", tokenizer="byte")

        assert vocab_map is None  # Byte tokenizer doesn't use vocab map
        assert vocab_size == 256

    def test_vocab_size_byte(self):
        """Test byte tokenizer vocab size."""
        from f5_tts.model.utils import get_tokenizer

        _, vocab_size = get_tokenizer("any_name", tokenizer="byte")

        assert vocab_size == 256  # UTF-8 byte range


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_exists_with_false(self):
        """Test exists() with False value."""
        from f5_tts.model.utils import exists

        # False is a value, not None
        assert exists(False) == True

    def test_exists_with_zero(self):
        """Test exists() with zero."""
        from f5_tts.model.utils import exists

        assert exists(0) == True
        assert exists(0.0) == True

    def test_default_with_false(self):
        """Test default() with False value."""
        from f5_tts.model.utils import default

        # False is a value, should return False not default
        assert default(False, True) == False

    def test_repetition_empty_string(self):
        """Test repetition_found() with empty string."""
        from f5_tts.model.utils import repetition_found

        text = ""
        result = repetition_found(text, length=2, tolerance=10)

        # Empty string has no repetitions
        assert result == False

    def test_repetition_short_string(self):
        """Test repetition_found() with string shorter than pattern."""
        from f5_tts.model.utils import repetition_found

        text = "a"
        result = repetition_found(text, length=5, tolerance=10)

        # Can't find pattern longer than string
        assert result == False


def run_tests():
    """Run all tests."""
    test_classes = [
        TestHelperFunctions,
        TestConvertCharToPinyin,
        TestGetTokenizer,
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
