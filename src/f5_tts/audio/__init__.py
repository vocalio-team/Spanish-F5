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
]
