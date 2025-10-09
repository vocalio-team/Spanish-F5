"""
TTS processing logic for F5-TTS REST API.

This module handles the core TTS generation including parameter adjustments
for short texts and audio file generation.
"""

from typing import Tuple, Optional
import logging

import torch
import torchaudio

from .models import TTSRequest

logger = logging.getLogger(__name__)


class TTSProcessor:
    """Handles TTS generation with adaptive parameter adjustments."""

    def calculate_short_text_adjustments(
        self, text: str, base_speed: float
    ) -> Tuple[float, Optional[float]]:
        """
        Calculate speed and duration adjustments for short texts.

        Short texts need special handling to prevent audio chopping.

        Args:
            text: Input text
            base_speed: Base speed multiplier

        Returns:
            Tuple of (adjusted_speed, fix_duration)
        """
        text_length = len(text)

        if text_length < 15:
            # Slow down speed for better clarity (e.g., "Comida" becomes more natural)
            adjusted_speed = max(0.7, base_speed * 0.85)
            # Pad short text with pauses to get minimum 2 seconds of actual speech
            # Note: F5-TTS trims ref_audio from generated audio, so we need longer duration
            # Reference audio is ~6 seconds, so fix_duration needs to be ref_duration + desired_output
            fix_duration = 8.0  # 6s (ref) + 2s (desired output) = 8s total
            logger.info(
                f"Short text detected ({text_length} chars): adjusted_speed={adjusted_speed:.2f}, "
                f"fix_duration={fix_duration}s"
            )
            return adjusted_speed, fix_duration

        elif text_length < 30:
            # Slightly slower for short texts
            adjusted_speed = max(0.85, base_speed * 0.95)
            # Medium padding
            fix_duration = 7.0  # 6s (ref) + 1s (desired output) = 7s total
            logger.info(
                f"Medium-short text detected ({text_length} chars): adjusted_speed={adjusted_speed:.2f}, "
                f"fix_duration={fix_duration}s"
            )
            return adjusted_speed, fix_duration

        return base_speed, None

    def generate_audio(
        self,
        f5tts_instance,
        ref_audio_path: str,
        processed_text: str,
        request: TTSRequest,
        nfe_step: int,
        crossfade_duration: float,
    ) -> Tuple[torch.Tensor, int, any]:
        """
        Generate audio using F5TTS instance.

        Args:
            f5tts_instance: F5TTS model instance
            ref_audio_path: Path to reference audio
            processed_text: Processed/enhanced text
            request: Original TTS request
            nfe_step: NFE steps to use
            crossfade_duration: Crossfade duration to use

        Returns:
            Tuple of (waveform, sample_rate, spectrogram)
        """
        # Calculate adjustments for short texts
        adjusted_speed, fix_duration = self.calculate_short_text_adjustments(
            processed_text, request.speed
        )

        logger.info("Starting TTS inference...")
        wav, sr, spect = f5tts_instance.infer(
            ref_file=ref_audio_path,
            ref_text=request.ref_text,
            gen_text=processed_text,
            target_rms=0.1,
            cross_fade_duration=crossfade_duration,
            speed=adjusted_speed,
            nfe_step=nfe_step,
            cfg_strength=request.cfg_strength,
            sway_sampling_coef=request.sway_sampling_coef,
            fix_duration=fix_duration,
        )
        logger.info("TTS inference completed")

        return wav, sr, spect

    def save_audio(self, wav, sample_rate: int, output_path: str) -> None:
        """
        Save audio waveform to file.

        Args:
            wav: Waveform (torch.Tensor or numpy array)
            sample_rate: Audio sample rate
            output_path: Output file path
        """
        # Convert numpy array to torch tensor if needed
        if isinstance(wav, torch.Tensor):
            wav_tensor = wav
        else:
            wav_tensor = torch.from_numpy(wav)

        # Ensure proper shape (channels, samples)
        if wav_tensor.dim() == 1:
            wav_tensor = wav_tensor.unsqueeze(0)

        torchaudio.save(output_path, wav_tensor.cpu(), sample_rate)
        logger.info(f"Audio saved to: {output_path}")


# Global TTS processor instance
tts_processor = TTSProcessor()
