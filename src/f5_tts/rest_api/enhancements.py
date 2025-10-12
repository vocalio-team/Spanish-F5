"""
Text and audio enhancement processing for F5-TTS REST API.

This module provides centralized enhancement processing including:
- Spanish text normalization
- Prosody analysis
- Breath and pause analysis
- Adaptive NFE step calculation
- Adaptive crossfade duration
- Audio quality checking
"""

from typing import Dict, Any, Tuple, Optional
import logging

import torch
import torchaudio

from f5_tts.text import normalize_spanish_text, analyze_spanish_prosody, analyze_breath_pauses
from f5_tts.audio import AudioQualityAnalyzer, QualityLevel
from f5_tts.core import get_adaptive_nfe_step, get_adaptive_crossfade_duration

from .models import TTSRequest

logger = logging.getLogger(__name__)


class EnhancementProcessor:
    """Processes text and audio enhancements for TTS generation."""

    def __init__(self):
        """Initialize enhancement processor."""
        self.quality_analyzer = AudioQualityAnalyzer()

    def process_enhancements(
        self, request: TTSRequest, ref_audio_path: str
    ) -> Tuple[str, Dict[str, Any], int, float]:
        """
        Apply all enabled enhancements to the request.

        Args:
            request: TTS request with enhancement flags
            ref_audio_path: Path to reference audio file

        Returns:
            Tuple of (processed_text, enhancement_metadata, nfe_step, crossfade_duration)
        """
        enhancement_metadata = {}
        processed_text = request.gen_text
        nfe_step = request.nfe_step
        crossfade_duration = request.cross_fade_duration

        # 1. Check reference audio quality
        if request.check_audio_quality:
            quality_metrics = self._check_audio_quality(ref_audio_path)
            if quality_metrics:
                enhancement_metadata["audio_quality"] = quality_metrics

        # 2. Apply text normalization
        if request.normalize_text:
            processed_text = self._normalize_text(processed_text)
            if processed_text != request.gen_text:
                enhancement_metadata["normalized_text"] = processed_text

        # 3. Analyze prosody
        if request.analyze_prosody:
            prosody_data = self._analyze_prosody(processed_text)
            if prosody_data:
                enhancement_metadata["prosody_analysis"] = prosody_data

        # 4. Analyze breath and pauses
        if request.analyze_breath_pauses:
            breath_data = self._analyze_breath_pauses(processed_text)
            if breath_data:
                enhancement_metadata["breath_analysis"] = breath_data

        # 5. Adaptive NFE steps
        if request.adaptive_nfe:
            nfe_step = self._get_adaptive_nfe(processed_text, request.nfe_step)
            enhancement_metadata["nfe_step_used"] = nfe_step

        # 6. Adaptive crossfade duration
        if request.adaptive_crossfade:
            crossfade_duration = self._get_adaptive_crossfade(request.cross_fade_duration, processed_text)
            enhancement_metadata["crossfade_duration_used"] = crossfade_duration

        logger.info(
            f"Enhancements applied: nfe_step={nfe_step}, crossfade={crossfade_duration:.2f}s, "
            f"text_len={len(processed_text)}"
        )

        return processed_text, enhancement_metadata, nfe_step, crossfade_duration

    def _check_audio_quality(self, audio_path: str) -> Optional[Dict[str, Any]]:
        """
        Check audio quality and return metrics.

        Args:
            audio_path: Path to audio file

        Returns:
            Dictionary with quality metrics or None if check fails
        """
        try:
            audio, sr = torchaudio.load(audio_path)
            quality_metrics = self.quality_analyzer.analyze(audio, sr)

            result = {
                "overall_score": quality_metrics.overall_score,
                "quality_level": quality_metrics.quality_level.value,
                "snr_db": quality_metrics.snr_db,
                "issues": quality_metrics.issues,
                "recommendations": quality_metrics.recommendations,
            }

            # Warn if quality is poor
            if quality_metrics.quality_level in [QualityLevel.POOR, QualityLevel.UNACCEPTABLE]:
                logger.warning(
                    f"Reference audio quality is {quality_metrics.quality_level.value}: "
                    f"{quality_metrics.issues}"
                )

            return result
        except Exception as e:
            logger.warning(f"Audio quality check failed: {e}")
            return None

    def _normalize_text(self, text: str) -> str:
        """
        Normalize Spanish text.

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        try:
            normalized = normalize_spanish_text(text)
            if normalized != text:
                logger.info(f"Text normalized: {text[:50]}... -> {normalized[:50]}...")
            return normalized
        except Exception as e:
            logger.warning(f"Text normalization failed: {e}")
            return text

    def _analyze_prosody(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Analyze prosody patterns in text.

        Args:
            text: Input text

        Returns:
            Dictionary with prosody analysis or None if analysis fails
        """
        try:
            prosody_analysis = analyze_spanish_prosody(text)
            result = {
                "num_questions": sum(1 for m in prosody_analysis.markers if "QUESTION" in str(m.type)),
                "num_exclamations": sum(
                    1 for m in prosody_analysis.markers if "EXCLAMATION" in str(m.type)
                ),
                "num_pauses": sum(1 for m in prosody_analysis.markers if "PAUSE" in str(m.type)),
                "sentence_count": len(prosody_analysis.sentence_boundaries),
                "breath_points": len(prosody_analysis.breath_points),
                "marked_text": prosody_analysis.marked_text,
            }
            logger.info(f"Prosody analyzed: {len(prosody_analysis.markers)} markers detected")
            return result
        except Exception as e:
            logger.warning(f"Prosody analysis failed: {e}")
            return None

    def _analyze_breath_pauses(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Analyze breath and pause patterns.

        Args:
            text: Input text

        Returns:
            Dictionary with breath analysis or None if analysis fails
        """
        try:
            breath_analysis = analyze_breath_pauses(text)
            result = {
                "total_pauses": len(breath_analysis.pauses),
                "breath_points": len(breath_analysis.breath_points),
                "avg_pause_interval": breath_analysis.avg_pause_interval,
                "estimated_duration": breath_analysis.total_duration_estimate,
            }
            logger.info(
                f"Breath analysis: {len(breath_analysis.pauses)} pauses, "
                f"{len(breath_analysis.breath_points)} breath points"
            )
            return result
        except Exception as e:
            logger.warning(f"Breath analysis failed: {e}")
            return None

    def _get_adaptive_nfe(self, text: str, default_nfe: int) -> int:
        """
        Calculate adaptive NFE steps based on text complexity.

        Args:
            text: Input text
            default_nfe: Default NFE value

        Returns:
            Adaptive NFE step value
        """
        try:
            nfe_step = get_adaptive_nfe_step(text, default_nfe)
            if nfe_step != default_nfe:
                logger.info(f"Adaptive NFE: {default_nfe} -> {nfe_step}")
            return nfe_step
        except Exception as e:
            logger.warning(f"Adaptive NFE failed: {e}")
            return default_nfe

    def _get_adaptive_crossfade(self, default_duration: float, text: str) -> float:
        """
        Calculate adaptive crossfade duration based on text length.

        For very short texts, use shorter crossfade to preserve more audio.

        Args:
            default_duration: Default crossfade duration
            text: Input text

        Returns:
            Adaptive crossfade duration
        """
        try:
            text_length = len(text)

            # For very short texts, use much shorter crossfade to avoid chopping
            if text_length < 15:
                # Very short: minimal crossfade (50ms)
                duration = 0.05
                logger.info(
                    f"Very short text ({text_length} chars): reducing crossfade "
                    f"{default_duration:.2f}s -> {duration:.2f}s"
                )
                return duration
            elif text_length < 30:
                # Short: reduced crossfade (80ms)
                duration = 0.08
                logger.info(
                    f"Short text ({text_length} chars): reducing crossfade "
                    f"{default_duration:.2f}s -> {duration:.2f}s"
                )
                return duration

            # For normal/long texts, use adaptive crossfade
            duration = get_adaptive_crossfade_duration()
            if duration != default_duration:
                logger.info(f"Adaptive crossfade: {default_duration:.2f}s -> {duration:.2f}s")
            return duration
        except Exception as e:
            logger.warning(f"Adaptive crossfade failed: {e}")
            return default_duration


# Global enhancement processor instance
enhancement_processor = EnhancementProcessor()
