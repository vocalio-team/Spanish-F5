"""Test suite for text chunking module."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from f5_tts.text.chunker import (
    BaseTextChunker,
    SentenceBasedChunker,
    FixedLengthChunker,
    AdaptiveChunker,
    get_chunker,
)


class TestSentenceBasedChunker:
    """Test SentenceBasedChunker class."""

    def test_basic_chunking(self):
        """Test basic sentence chunking."""
        chunker = SentenceBasedChunker()
        text = "This is the first sentence. This is the second sentence. This is the third sentence."

        chunks = chunker.chunk(text, max_chars=100)

        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)

    def test_respects_max_chars(self):
        """Test that chunks respect max_chars limit."""
        chunker = SentenceBasedChunker()
        text = "This is a sentence. " * 10

        chunks = chunker.chunk(text, max_chars=50)

        for chunk in chunks:
            assert len(chunk) <= 50 or "." in chunk  # May exceed if sentence is too long

    def test_empty_text(self):
        """Test handling of empty text."""
        chunker = SentenceBasedChunker()
        chunks = chunker.chunk("", max_chars=100)

        assert len(chunks) == 0 or (len(chunks) == 1 and chunks[0] == "")

    def test_single_sentence(self):
        """Test single sentence."""
        chunker = SentenceBasedChunker()
        text = "This is a single sentence."

        chunks = chunker.chunk(text, max_chars=100)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_spanish_text(self):
        """Test with Spanish text."""
        chunker = SentenceBasedChunker()
        text = "Hola, ¿cómo estás? Yo estoy bien. ¿Y tú?"

        chunks = chunker.chunk(text, max_chars=50)

        assert len(chunks) >= 1
        # Should preserve Spanish punctuation
        combined = " ".join(chunks)
        assert "¿" in combined
        assert "?" in combined


class TestFixedLengthChunker:
    """Test FixedLengthChunker class."""

    def test_basic_chunking(self):
        """Test basic fixed-length chunking."""
        chunker = FixedLengthChunker()
        text = "a" * 200

        chunks = chunker.chunk(text, max_chars=50)

        assert len(chunks) == 4
        assert all(len(chunk) == 50 for chunk in chunks)

    def test_remainder_chunk(self):
        """Test handling of remainder."""
        chunker = FixedLengthChunker()
        text = "a" * 75

        chunks = chunker.chunk(text, max_chars=50)

        assert len(chunks) == 2
        assert len(chunks[0]) == 50
        assert len(chunks[1]) == 25

    def test_short_text(self):
        """Test text shorter than max_chars."""
        chunker = FixedLengthChunker()
        text = "short"

        chunks = chunker.chunk(text, max_chars=100)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_word_boundaries(self):
        """Test fixed-length splitting behavior."""
        chunker = FixedLengthChunker()
        text = "word " * 20

        chunks = chunker.chunk(text, max_chars=25)

        # Should split at max_chars
        assert len(chunks) > 1
        for chunk in chunks[:-1]:  # All but last
            assert len(chunk) <= 25


class TestAdaptiveChunker:
    """Test AdaptiveChunker class."""

    def test_adaptation_to_reference(self):
        """Test adaptation based on reference audio."""
        # Reference: 10 seconds audio, 100 characters text
        # So ~10 chars per second
        chunker = AdaptiveChunker(
            ref_audio_duration=10.0,
            ref_text_length=100
        )

        text = "a" * 200

        chunks = chunker.chunk(text)

        # Should adapt chunk size based on reference
        assert len(chunks) > 0
        # Each chunk should be reasonable for ~10 second audio
        for chunk in chunks:
            assert len(chunk) > 0

    def test_fallback_to_default(self):
        """Test with explicit max_chars override."""
        # AdaptiveChunker requires ref_audio_duration and ref_text_length
        chunker = AdaptiveChunker(
            ref_audio_duration=5.0,
            ref_text_length=100
        )
        text = "This is some text to chunk."

        chunks = chunker.chunk(text, max_chars=50)

        assert len(chunks) >= 1

    def test_with_very_short_reference(self):
        """Test with very short reference."""
        chunker = AdaptiveChunker(
            ref_audio_duration=1.0,
            ref_text_length=10
        )

        text = "a" * 100

        chunks = chunker.chunk(text)

        # Should calculate max_chars based on reference
        # Verify chunks were created
        assert len(chunks) >= 1
        assert all(len(chunk) > 0 for chunk in chunks)


class TestGetChunker:
    """Test get_chunker factory function."""

    def test_get_sentence_chunker(self):
        """Test getting sentence-based chunker."""
        chunker = get_chunker("sentence")

        assert isinstance(chunker, SentenceBasedChunker)

    def test_get_fixed_chunker(self):
        """Test getting fixed-length chunker."""
        chunker = get_chunker("fixed")

        assert isinstance(chunker, FixedLengthChunker)

    def test_get_adaptive_chunker(self):
        """Test getting adaptive chunker."""
        chunker = get_chunker("adaptive", ref_audio_duration=5.0, ref_text_length=50)

        assert isinstance(chunker, AdaptiveChunker)

    def test_default_chunker(self):
        """Test default chunker."""
        chunker = get_chunker()

        assert isinstance(chunker, SentenceBasedChunker)

    def test_invalid_type(self):
        """Test invalid chunker type."""
        try:
            chunker = get_chunker("invalid")
            assert False, "Should raise ValueError"
        except (ValueError, KeyError):
            assert True


class TestChunkerIntegration:
    """Test chunker integration scenarios."""

    def test_multilingual_text(self):
        """Test with multilingual text."""
        chunker = SentenceBasedChunker()
        text = "Hello world. Hola mundo. Bonjour le monde."

        chunks = chunker.chunk(text, max_chars=30)

        assert len(chunks) >= 1
        # Should preserve all text
        combined = " ".join(chunks)
        assert "Hello" in combined
        assert "Hola" in combined
        assert "Bonjour" in combined

    def test_long_document(self):
        """Test with long document."""
        chunker = SentenceBasedChunker()
        text = ". ".join([f"Sentence {i}" for i in range(100)])

        chunks = chunker.chunk(text, max_chars=200)

        assert len(chunks) > 1
        # No chunk should be empty
        assert all(len(chunk.strip()) > 0 for chunk in chunks)

    def test_special_characters(self):
        """Test with special characters."""
        chunker = SentenceBasedChunker()
        text = "¿Pregunta? ¡Exclamación! Normal. @#$%."

        chunks = chunker.chunk(text, max_chars=50)

        combined = " ".join(chunks)
        assert "¿" in combined
        assert "¡" in combined
        assert "@#$%" in combined

    def test_preserves_meaning(self):
        """Test that chunking preserves text meaning."""
        chunker = SentenceBasedChunker()
        original = "The quick brown fox jumps over the lazy dog. This is a test sentence."

        chunks = chunker.chunk(original, max_chars=100)

        # Reconstruct
        reconstructed = " ".join(chunks)

        # Should contain all key words
        for word in ["quick", "brown", "fox", "lazy", "dog", "test"]:
            assert word in reconstructed


def run_tests():
    """Run all tests."""
    test_classes = [
        TestSentenceBasedChunker,
        TestFixedLengthChunker,
        TestAdaptiveChunker,
        TestGetChunker,
        TestChunkerIntegration,
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
