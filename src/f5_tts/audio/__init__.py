"""Audio processing module for F5-TTS."""

from .crossfading import (
    CrossfadeType,
    EqualPowerCrossfader,
    RaisedCosineCrossfader,
    LinearCrossfader,
    get_crossfader,
    apply_edge_fades,
)
from .processors import (
    AudioNormalizer,
    AudioResampler,
    StereoToMono,
    AudioClipping,
    AudioProcessingPipeline,
)
from .quality import (
    QualityLevel,
    QualityMetrics,
    AudioQualityAnalyzer,
    analyze_audio_quality,
    print_quality_report,
)

__all__ = [
    "CrossfadeType",
    "EqualPowerCrossfader",
    "RaisedCosineCrossfader",
    "LinearCrossfader",
    "get_crossfader",
    "apply_edge_fades",
    "AudioNormalizer",
    "AudioResampler",
    "StereoToMono",
    "AudioClipping",
    "AudioProcessingPipeline",
    "QualityLevel",
    "QualityMetrics",
    "AudioQualityAnalyzer",
    "analyze_audio_quality",
    "print_quality_report",
]
