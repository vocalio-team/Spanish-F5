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

        CRITICAL: F5-TTS removes ref_audio_len from the beginning of generated audio.
        For a 6s reference, fix_duration=12s yields ~6s of actual output.
        With silence removal and crossfading, this becomes ~3-4s.

        Args:
            text: Input text
            base_speed: Base speed multiplier

        Returns:
            Tuple of (adjusted_speed, fix_duration)
        """
        text_length = len(text)

        if text_length < 15:
            # Very short text (1-2 words): needs aggressive padding
            # Slow down significantly for clarity
            adjusted_speed = max(0.6, base_speed * 0.75)
            # Generate much longer audio to compensate for:
            # 1. ref_audio removal (~6s lost)
            # 2. silence removal at edges (~1-2s lost)
            # 3. crossfading overlap (~0.15s lost per chunk)
            # Target: 3-4s of final audible speech
            fix_duration = 12.0  # 12s total - 6s (ref) - 2s (silence) = 4s output
            logger.info(
                f"Very short text detected ({text_length} chars): adjusted_speed={adjusted_speed:.2f}, "
                f"fix_duration={fix_duration}s (target: ~4s output)"
            )
            return adjusted_speed, fix_duration

        elif text_length < 30:
            # Short text: moderate padding
            adjusted_speed = max(0.75, base_speed * 0.90)
            # Less aggressive padding needed
            fix_duration = 9.0  # 9s total - 6s (ref) - 1s (silence) = 2s output
            logger.info(
                f"Short text detected ({text_length} chars): adjusted_speed={adjusted_speed:.2f}, "
                f"fix_duration={fix_duration}s (target: ~2s output)"
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
