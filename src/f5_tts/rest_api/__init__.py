"""
F5-TTS REST API module.

This module provides a modular REST API for F5-TTS text-to-speech generation
with comprehensive Spanish language enhancements.

Main Components:
    - app: FastAPI application factory
    - models: Pydantic request/response models
    - state: Global state management
    - config: API configuration
    - enhancements: Text and audio enhancement processors
    - tts_processor: Core TTS generation logic
    - routes: API endpoint handlers

Usage:
    from f5_tts.rest_api import create_app

    app = create_app()
"""

from .app import create_app
from .models import TTSRequest, TTSResponse, TaskStatus, MultiStyleRequest, AnalysisRequest
from .state import api_state
from .config import (
    ENABLE_TORCH_COMPILE,
    ENABLE_CUDNN_BENCHMARK,
    TORCH_MATMUL_PRECISION,
    DEFAULT_REF_AUDIO_PATH,
)

__all__ = [
    "create_app",
    "TTSRequest",
    "TTSResponse",
    "TaskStatus",
    "MultiStyleRequest",
    "AnalysisRequest",
    "api_state",
    "ENABLE_TORCH_COMPILE",
    "ENABLE_CUDNN_BENCHMARK",
    "TORCH_MATMUL_PRECISION",
    "DEFAULT_REF_AUDIO_PATH",
]
