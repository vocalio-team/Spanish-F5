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
    default_cross_fade_duration: float = 0.5

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
