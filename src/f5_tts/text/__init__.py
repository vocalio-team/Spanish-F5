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

from .normalizer import (
    SpanishTextNormalizer,
    normalize_spanish_text,
)

from .prosody import (
    ProsodyType,
    IntensityLevel,
    ProsodyMarker,
    ProsodyAnalysis,
    SpanishProsodyAnalyzer,
    analyze_spanish_prosody,
    format_prosody_report,
)

from .breath_pause import (
    PauseType,
    Pause,
    BreathPattern,
    BreathPauseAnalyzer,
    analyze_breath_pauses,
    format_breath_report,
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
    # Text normalization
    "SpanishTextNormalizer",
    "normalize_spanish_text",
    # Prosody analysis
    "ProsodyType",
    "IntensityLevel",
    "ProsodyMarker",
    "ProsodyAnalysis",
    "SpanishProsodyAnalyzer",
    "analyze_spanish_prosody",
    "format_prosody_report",
    # Breath and pause modeling
    "PauseType",
    "Pause",
    "BreathPattern",
    "BreathPauseAnalyzer",
    "analyze_breath_pauses",
    "format_breath_report",
]
