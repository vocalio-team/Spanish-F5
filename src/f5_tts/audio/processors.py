"""Audio processing components."""

import numpy as np
import torch
import torchaudio
from typing import Optional

from f5_tts.core import AudioData, AudioProcessingConfig


class AudioNormalizer:
    """Handles audio normalization operations."""

    def __init__(self, config: Optional[AudioProcessingConfig] = None):
        self.config = config or AudioProcessingConfig()

    def remove_dc_offset(self, audio: np.ndarray) -> np.ndarray:
        """Remove DC offset (mean) from audio signal."""
        return audio - np.mean(audio)

    def normalize_amplitude(
        self,
        audio: np.ndarray,
        max_amplitude: float = 0.99
    ) -> np.ndarray:
        """Normalize audio to prevent clipping while preserving dynamics."""
        max_abs = np.abs(audio).max()
        if max_abs > max_amplitude:
            return audio * max_amplitude / max_abs
        return audio

    def normalize_rms(
        self,
        audio: torch.Tensor,
        target_rms: float = 0.1
    ) -> torch.Tensor:
        """Normalize audio to target RMS level."""
        rms = torch.sqrt(torch.mean(torch.square(audio)))
        if rms < target_rms:
            return audio * target_rms / rms
        return audio

    def process(self, audio_data: AudioData) -> AudioData:
        """Apply all normalization steps."""
        waveform = audio_data.waveform

        if self.config.remove_dc_offset:
            waveform = self.remove_dc_offset(waveform)

        if self.config.normalize_output:
            waveform = self.normalize_amplitude(
                waveform,
                self.config.max_amplitude
            )

        return AudioData(
            waveform=waveform,
            sample_rate=audio_data.sample_rate
        )


class AudioResampler:
    """Handles audio resampling with high quality."""

    def __init__(self, config: Optional[AudioProcessingConfig] = None):
        self.config = config or AudioProcessingConfig()

    def resample(
        self,
        audio: torch.Tensor,
        orig_sr: int,
        target_sr: Optional[int] = None
    ) -> torch.Tensor:
        """
        Resample audio using high-quality Kaiser window method.

        Args:
            audio: Input audio tensor
            orig_sr: Original sample rate
            target_sr: Target sample rate (uses config if not provided)

        Returns:
            Resampled audio tensor
        """
        if target_sr is None:
            target_sr = self.config.target_sample_rate

        if orig_sr == target_sr:
            return audio

        resampler = torchaudio.transforms.Resample(
            orig_sr,
            target_sr,
            resampling_method=self.config.resampling_method,
            lowpass_filter_width=self.config.lowpass_filter_width,
            rolloff=self.config.rolloff
        )

        return resampler(audio)


class StereoToMono:
    """Convert stereo audio to mono."""

    @staticmethod
    def convert(audio: torch.Tensor) -> torch.Tensor:
        """Convert stereo to mono by averaging channels."""
        if audio.shape[0] > 1:
            return torch.mean(audio, dim=0, keepdim=True)
        return audio


class AudioClipping:
    """Prevent audio clipping."""

    @staticmethod
    def clamp(
        audio: torch.Tensor,
        min_val: float = -1.0,
        max_val: float = 1.0
    ) -> torch.Tensor:
        """Clamp audio values to prevent clipping."""
        return torch.clamp(audio, min_val, max_val)


class AudioProcessingPipeline:
    """
    Complete audio processing pipeline combining multiple processors.
    """

    def __init__(self, config: Optional[AudioProcessingConfig] = None):
        self.config = config or AudioProcessingConfig()
        self.normalizer = AudioNormalizer(config)
        self.resampler = AudioResampler(config)

    def prepare_reference_audio(
        self,
        audio: torch.Tensor,
        sample_rate: int,
        target_rms: float = 0.1,
        device: str = "cuda"
    ) -> torch.Tensor:
        """
        Prepare reference audio for TTS inference.

        Args:
            audio: Input audio tensor
            sample_rate: Input sample rate
            target_rms: Target RMS level
            device: Target device

        Returns:
            Processed audio tensor on device
        """
        # Convert stereo to mono
        audio = StereoToMono.convert(audio)

        # Normalize RMS
        audio = self.normalizer.normalize_rms(audio, target_rms)

        # Resample if needed
        audio = self.resampler.resample(audio, sample_rate)

        # Move to device
        return audio.to(device)

    def finalize_output_audio(
        self,
        audio: np.ndarray
    ) -> np.ndarray:
        """
        Finalize output audio with post-processing.

        Args:
            audio: Generated audio waveform

        Returns:
            Processed audio ready for output
        """
        # Remove DC offset
        if self.config.remove_dc_offset:
            audio = self.normalizer.remove_dc_offset(audio)

        # Normalize amplitude
        if self.config.normalize_output:
            audio = self.normalizer.normalize_amplitude(
                audio,
                self.config.max_amplitude
            )

        return audio
