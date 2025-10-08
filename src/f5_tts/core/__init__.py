"""Core module for F5-TTS."""

from .config import GlobalConfig, get_config, set_config, reset_config
from .types import (
    AudioData,
    InferenceConfig,
    AudioProcessingConfig,
    AudioProcessor,
    Crossfader,
    TextChunker,
    VocoderInterface,
)

__all__ = [
    "GlobalConfig",
    "get_config",
    "set_config",
    "reset_config",
    "AudioData",
    "InferenceConfig",
    "AudioProcessingConfig",
    "AudioProcessor",
    "Crossfader",
    "TextChunker",
    "VocoderInterface",
]
