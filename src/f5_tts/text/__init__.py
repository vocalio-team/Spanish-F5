"""Text processing module for F5-TTS."""

from .chunker import (
    BaseTextChunker,
    SentenceBasedChunker,
    AdaptiveChunker,
    FixedLengthChunker,
    get_chunker,
)

from .spanish_regional import (
    SpanishRegion,
    SpanishRegionalProcessor,
    RegionalPhonetics,
    RegionalProsody,
    RegionalSlang,
    get_regional_processor,
    process_spanish_text,
)

__all__ = [
    "BaseTextChunker",
    "SentenceBasedChunker",
    "AdaptiveChunker",
    "FixedLengthChunker",
    "get_chunker",
    # Spanish regional support
    "SpanishRegion",
    "SpanishRegionalProcessor",
    "RegionalPhonetics",
    "RegionalProsody",
    "RegionalSlang",
    "get_regional_processor",
    "process_spanish_text",
]
