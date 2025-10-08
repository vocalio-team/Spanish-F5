"""Text chunking strategies for batch processing."""

import re
from typing import List
from abc import ABC, abstractmethod


class BaseTextChunker(ABC):
    """Base class for text chunking strategies."""

    @abstractmethod
    def chunk(self, text: str, max_chars: int) -> List[str]:
        """Split text into chunks."""
        pass


class SentenceBasedChunker(BaseTextChunker):
    """
    Chunks text by sentences, respecting natural language boundaries.
    Improved version of the original chunker with better sentence detection.
    """

    def __init__(self):
        # Improved sentence splitting pattern
        self.sentence_pattern = re.compile(
            r'([.!?;。！？；]+[\s\u200b]*)|'  # Punctuation + optional whitespace
            r'(\n+)',                          # Newlines
            re.UNICODE
        )

    def chunk(self, text: str, max_chars: int) -> List[str]:
        """
        Split text into chunks by sentences.

        Args:
            text: Input text
            max_chars: Maximum characters per chunk

        Returns:
            List of text chunks
        """
        # Split by sentences
        parts = self.sentence_pattern.split(text)
        sentences = []

        # Recombine sentences with their punctuation
        current = ""
        for i, part in enumerate(parts):
            if part:
                current += part
                # If this is punctuation or newline, it ends a sentence
                if i % 3 == 1 or i % 3 == 2:
                    if current.strip():
                        sentences.append(current.strip())
                    current = ""

        # Add any remaining text
        if current.strip():
            sentences.append(current.strip())

        # Combine sentences into chunks
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            # If sentence alone exceeds max_chars, split by words
            if len(sentence.encode("utf-8")) > max_chars:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""

                # Split long sentence by words
                words = sentence.split()
                for word in words:
                    test_chunk = current_chunk + " " + word if current_chunk else word
                    if len(test_chunk.encode("utf-8")) <= max_chars:
                        current_chunk = test_chunk
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = word
                continue

            # Try adding sentence to current chunk
            test_chunk = current_chunk + " " + sentence if current_chunk else sentence
            if len(test_chunk.encode("utf-8")) <= max_chars:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence

        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks if chunks else [text]


class AdaptiveChunker(BaseTextChunker):
    """
    Adaptive chunker that adjusts chunk size based on reference audio duration.
    """

    def __init__(self, ref_audio_duration: float, ref_text_length: int):
        """
        Args:
            ref_audio_duration: Duration of reference audio in seconds
            ref_text_length: Length of reference text in bytes
        """
        self.ref_audio_duration = ref_audio_duration
        self.ref_text_length = ref_text_length
        self.base_chunker = SentenceBasedChunker()

    def calculate_max_chars(self, min_chars: int = 500) -> int:
        """
        Calculate optimal max_chars based on reference audio.

        Args:
            min_chars: Minimum characters per chunk

        Returns:
            Optimal max_chars value
        """
        # Calculate chars per second from reference
        if self.ref_audio_duration > 0:
            chars_per_second = self.ref_text_length / self.ref_audio_duration
            # Target ~30 seconds of audio per chunk for good balance
            calculated = int(chars_per_second * 30)
            return max(calculated, min_chars)
        return min_chars

    def chunk(self, text: str, max_chars: int = None) -> List[str]:
        """
        Chunk text adaptively.

        Args:
            text: Input text
            max_chars: Maximum chars per chunk (calculated if None)

        Returns:
            List of text chunks
        """
        if max_chars is None:
            max_chars = self.calculate_max_chars()

        return self.base_chunker.chunk(text, max_chars)


class FixedLengthChunker(BaseTextChunker):
    """Simple fixed-length chunker (not recommended for TTS)."""

    def chunk(self, text: str, max_chars: int) -> List[str]:
        """Split text into fixed-length chunks."""
        chunks = []
        current_pos = 0

        while current_pos < len(text):
            chunk = text[current_pos:current_pos + max_chars]
            chunks.append(chunk)
            current_pos += max_chars

        return chunks


def get_chunker(
    strategy: str = "sentence",
    ref_audio_duration: float = None,
    ref_text_length: int = None
) -> BaseTextChunker:
    """
    Factory function to get a text chunker.

    Args:
        strategy: Chunking strategy ("sentence", "adaptive", "fixed")
        ref_audio_duration: Reference audio duration for adaptive chunker
        ref_text_length: Reference text length for adaptive chunker

    Returns:
        Text chunker instance
    """
    if strategy == "adaptive":
        if ref_audio_duration is None or ref_text_length is None:
            raise ValueError("Adaptive chunker requires ref_audio_duration and ref_text_length")
        return AdaptiveChunker(ref_audio_duration, ref_text_length)
    elif strategy == "sentence":
        return SentenceBasedChunker()
    elif strategy == "fixed":
        return FixedLengthChunker()
    else:
        raise ValueError(f"Unknown chunking strategy: {strategy}")
