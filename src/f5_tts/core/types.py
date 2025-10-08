"""Type definitions and protocols for F5-TTS modules."""

from typing import Protocol, Tuple, Optional
import torch
import numpy as np
from dataclasses import dataclass


@dataclass
class AudioData:
    """Represents audio data with metadata."""
    waveform: np.ndarray
    sample_rate: int
    duration: Optional[float] = None

    def __post_init__(self):
        if self.duration is None:
            self.duration = len(self.waveform) / self.sample_rate


@dataclass
class InferenceConfig:
    """Configuration for TTS inference."""
    nfe_step: int = 16
    cfg_strength: float = 2.0
    sway_sampling_coef: float = -1.0
    speed: float = 1.0
    target_rms: float = 0.1
    cross_fade_duration: float = 0.5
    remove_silence: bool = False
    seed: int = -1


@dataclass
class AudioProcessingConfig:
    """Configuration for audio processing."""
    target_sample_rate: int = 24000
    n_mel_channels: int = 100
    hop_length: int = 256
    win_length: int = 1024
    n_fft: int = 1024

    # Resampling config
    resampling_method: str = "kaiser_window"
    lowpass_filter_width: int = 64
    rolloff: float = 0.99

    # Normalization config
    normalize_output: bool = True
    max_amplitude: float = 0.99
    remove_dc_offset: bool = True


class AudioProcessor(Protocol):
    """Protocol for audio processing components."""

    def process(self, audio: AudioData) -> AudioData:
        """Process audio data and return modified audio."""
        ...


class Crossfader(Protocol):
    """Protocol for crossfading algorithms."""

    def crossfade(
        self,
        audio1: np.ndarray,
        audio2: np.ndarray,
        duration: float,
        sample_rate: int
    ) -> np.ndarray:
        """Crossfade two audio segments."""
        ...


class TextChunker(Protocol):
    """Protocol for text chunking strategies."""

    def chunk(self, text: str, max_chars: int) -> list[str]:
        """Split text into chunks."""
        ...


class VocoderInterface(Protocol):
    """Protocol for vocoder implementations."""

    def decode(self, mel_spec: torch.Tensor) -> torch.Tensor:
        """Decode mel-spectrogram to waveform."""
        ...

    def to(self, device: str) -> "VocoderInterface":
        """Move vocoder to device."""
        ...
