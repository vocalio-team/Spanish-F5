"""Centralized configuration management for F5-TTS."""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GlobalConfig:
    """Global configuration for F5-TTS system."""

    # Device configuration
    device: str = "auto"  # "auto", "cuda", "cpu", "mps"

    # Performance optimizations
    enable_torch_compile: bool = True
    enable_cudnn_benchmark: bool = True
    torch_matmul_precision: str = "high"  # "high" or "highest"
    enable_tf32: bool = True  # For Ampere+ GPUs

    # Audio settings
    target_sample_rate: int = 24000
    n_mel_channels: int = 100
    hop_length: int = 256
    win_length: int = 1024
    n_fft: int = 1024

    # Inference defaults
    default_nfe_step: int = 16
    default_cfg_strength: float = 2.0
    default_speed: float = 1.0
    default_cross_fade_duration: float = 0.8  # Increased for smoother transitions

    # Adaptive inference settings
    enable_adaptive_nfe: bool = True  # Adjust NFE steps based on text complexity
    nfe_step_short: int = 14  # For simple, short text (< 50 chars)
    nfe_step_normal: int = 16  # For normal text (50-200 chars)
    nfe_step_complex: int = 20  # For complex, long text (> 200 chars)

    # Chunking configuration
    min_chunk_chars: int = 500
    max_chunk_chars: int = 2000

    # Vocoder settings
    default_vocoder: str = "vocos"  # "vocos" or "bigvgan"

    # Cache settings
    enable_ref_audio_cache: bool = True
    cache_size_mb: int = 100

    # Regional Spanish settings
    spanish_region: str = "neutral"  # "neutral", "rioplatense", "colombian", "mexican", "chilean", "caribbean", "andean"
    auto_detect_region: bool = False  # Auto-detect region from text slang markers
    apply_regional_phonetics: bool = True  # Apply regional phonetic transformations

    @classmethod
    def from_env(cls) -> "GlobalConfig":
        """Load configuration from environment variables."""
        return cls(
            enable_torch_compile=os.getenv("ENABLE_TORCH_COMPILE", "true").lower() == "true",
            enable_cudnn_benchmark=os.getenv("ENABLE_CUDNN_BENCHMARK", "true").lower() == "true",
            torch_matmul_precision=os.getenv("TORCH_MATMUL_PRECISION", "high"),
            device=os.getenv("DEVICE", "auto"),
            default_nfe_step=int(os.getenv("DEFAULT_NFE_STEP", "16")),
            min_chunk_chars=int(os.getenv("MIN_CHUNK_CHARS", "500")),
            spanish_region=os.getenv("SPANISH_REGION", "neutral"),
            auto_detect_region=os.getenv("AUTO_DETECT_REGION", "false").lower() == "true",
            apply_regional_phonetics=os.getenv("APPLY_REGIONAL_PHONETICS", "true").lower() == "true",
        )

    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            k: v for k, v in self.__dict__.items()
        }


# Singleton instance
_global_config: Optional[GlobalConfig] = None


def get_config() -> GlobalConfig:
    """Get the global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = GlobalConfig.from_env()
    return _global_config


def set_config(config: GlobalConfig):
    """Set the global configuration instance."""
    global _global_config
    _global_config = config


def reset_config():
    """Reset configuration to defaults."""
    global _global_config
    _global_config = GlobalConfig.from_env()


def get_adaptive_nfe_step(text: str, base_nfe_step: int = None) -> int:
    """
    Calculate optimal NFE steps based on text complexity.

    Args:
        text: Input text to analyze
        base_nfe_step: Override base NFE step (uses config default if None)

    Returns:
        Optimal number of NFE steps for the given text
    """
    config = get_config()

    if not config.enable_adaptive_nfe:
        return base_nfe_step or config.default_nfe_step

    text_length = len(text.strip())

    # Count complexity indicators
    has_questions = "?" in text or "¿" in text
    has_exclamations = "!" in text or "¡" in text
    has_multiple_sentences = text.count(".") + text.count("?") + text.count("!") > 2

    # Base selection on length
    if text_length < 50:
        nfe_step = config.nfe_step_short
    elif text_length < 200:
        nfe_step = config.nfe_step_normal
    else:
        nfe_step = config.nfe_step_complex

    # Adjust for complexity indicators
    if has_questions or has_exclamations:
        nfe_step += 2  # More steps for expressive speech

    if has_multiple_sentences and text_length > 100:
        nfe_step += 2  # More steps for paragraph coherence

    # Use provided base or clamp to reasonable range
    if base_nfe_step:
        nfe_step = base_nfe_step

    return max(12, min(32, nfe_step))  # Clamp between 12 and 32


def get_adaptive_crossfade_duration(
    chunk1_energy: float = None,
    chunk2_energy: float = None,
    at_pause: bool = False
) -> float:
    """
    Calculate optimal crossfade duration based on audio characteristics.

    Args:
        chunk1_energy: Energy level of first chunk (0-1)
        chunk2_energy: Energy level of second chunk (0-1)
        at_pause: Whether crossfade is at a natural pause/boundary

    Returns:
        Optimal crossfade duration in seconds
    """
    config = get_config()
    base_duration = config.default_cross_fade_duration

    # Shorter crossfade for continuous speech
    if chunk1_energy is not None and chunk2_energy is not None:
        avg_energy = (chunk1_energy + chunk2_energy) / 2
        if avg_energy > 0.7:  # High energy = continuous speech
            return base_duration * 0.6  # ~0.48s with default 0.8s

    # Longer crossfade at natural boundaries
    if at_pause:
        return base_duration * 1.25  # ~1.0s with default 0.8s

    return base_duration
