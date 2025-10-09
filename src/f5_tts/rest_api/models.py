"""
Pydantic models for F5-TTS REST API.

This module contains all request/response models used by the API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


# Request Models


class TTSRequest(BaseModel):
    """Request model for text-to-speech generation."""

    model: str = Field(default="F5-TTS", description="Model to use: F5-TTS or E2-TTS")
    ref_text: str = Field(description="Reference text (leave empty for auto-transcription)")
    gen_text: str = Field(description="Text to generate speech for")
    remove_silence: bool = Field(default=False, description="Remove silence from output")
    speed: float = Field(default=1.0, description="Speech speed multiplier")
    cross_fade_duration: float = Field(
        default=0.8, description="Cross-fade duration for chunks (0.8s for smoother audio)"
    )
    nfe_step: int = Field(
        default=16, description="Number of function evaluations (lower = faster, default was 32)"
    )
    cfg_strength: float = Field(default=2.0, description="Classifier-free guidance strength")
    sway_sampling_coef: float = Field(default=-1.0, description="Sway sampling coefficient")
    seed: int = Field(default=-1, description="Random seed (-1 for random)")
    vocoder_name: str = Field(default="vocos", description="Vocoder to use")
    output_format: str = Field(default="wav", description="Output audio format")
    use_fp16: bool = Field(default=True, description="Use FP16/BF16 for faster inference (recommended)")

    # Enhancement features (Phase 1-4 improvements)
    normalize_text: bool = Field(
        default=True, description="Apply Spanish text normalization (numbers, dates, etc.)"
    )
    analyze_prosody: bool = Field(
        default=True, description="Analyze and enhance prosody (questions, exclamations, etc.)"
    )
    analyze_breath_pauses: bool = Field(
        default=True, description="Analyze breath and pause patterns"
    )
    adaptive_nfe: bool = Field(
        default=True, description="Automatically adjust NFE steps based on text complexity"
    )
    adaptive_crossfade: bool = Field(
        default=True, description="Automatically adjust crossfade duration based on audio characteristics"
    )
    check_audio_quality: bool = Field(
        default=True, description="Check reference audio quality and provide warnings"
    )


class MultiStyleRequest(BaseModel):
    """Request model for multi-style TTS with different voices."""

    model: str = Field(default="F5-TTS", description="Model to use")
    gen_text: str = Field(description="Text with voice markers like [main], [voice1], etc.")
    voices: Dict[str, Dict[str, str]] = Field(description="Voice configurations")
    remove_silence: bool = Field(default=True, description="Remove silence from output")
    output_format: str = Field(default="wav", description="Output audio format")


class AnalysisRequest(BaseModel):
    """Request model for text analysis without TTS generation."""

    text: str = Field(description="Text to analyze")
    normalize_text: bool = Field(default=True, description="Apply text normalization")
    analyze_prosody: bool = Field(default=True, description="Analyze prosody")
    analyze_breath_pauses: bool = Field(default=True, description="Analyze breath and pauses")


# Response Models


class TTSResponse(BaseModel):
    """Response model for TTS generation requests."""

    task_id: str
    status: str
    message: str
    audio_url: Optional[str] = None
    duration: Optional[float] = None

    # Enhancement metadata
    normalized_text: Optional[str] = None
    prosody_analysis: Optional[Dict[str, Any]] = None
    breath_analysis: Optional[Dict[str, Any]] = None
    audio_quality: Optional[Dict[str, Any]] = None
    nfe_step_used: Optional[int] = None
    crossfade_duration_used: Optional[float] = None


class TaskStatus(BaseModel):
    """Model representing the status of a background task."""

    task_id: str
    status: str
    progress: Optional[float] = None
    message: str
    result: Optional[Dict[str, Any]] = None
    created_at: str
    completed_at: Optional[str] = None
