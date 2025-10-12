"""
FastAPI application setup for F5-TTS REST API.

This module creates and configures the FastAPI application including:
- Model loading on startup
- Route registration
- CUDA optimizations
"""

import logging
from datetime import datetime

import torch
from fastapi import FastAPI
from f5_tts.api import F5TTS

from .config import (
    ENABLE_TORCH_COMPILE,
    ENABLE_CUDNN_BENCHMARK,
    TORCH_MATMUL_PRECISION,
    DEFAULT_F5TTS_MODEL_PATH,
    DEFAULT_F5TTS_VOCAB_PATH,
    DEFAULT_REF_AUDIO_PATH,
    DEFAULT_REF_TEXT,
)
from .state import api_state
from .routes import create_router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI app instance
    """
    app = FastAPI(
        title="F5-TTS REST API",
        description="REST API for F5-TTS Text-to-Speech inference operations",
        version="2.0.0",
    )

    # Register startup event
    @app.on_event("startup")
    async def startup_event():
        """Load default models and apply optimizations on startup."""
        await load_models()

    # Register root endpoint
    @app.get("/")
    async def root():
        """API root endpoint with service information."""
        return {
            "message": "F5-TTS REST API - Enhanced with Spanish Quality Improvements",
            "version": "2.0.0",
            "enhancements": {
                "text_normalization": "Convert numbers, dates, times to spoken Spanish",
                "prosody_analysis": "Detect questions, exclamations, emphasis, pauses",
                "breath_pause_modeling": "Natural breathing and pause patterns",
                "adaptive_nfe": "Automatic quality optimization based on text complexity",
                "adaptive_crossfade": "Dynamic crossfade duration for smoother audio",
                "audio_quality_check": "Reference audio quality validation",
            },
            "endpoints": {
                "tts": {"path": "/tts", "description": "Generate speech with all enhancements enabled by default"},
                "tts_stream": {"path": "/tts/stream", "description": "Stream speech output"},
                "tts_upload": {"path": "/tts/upload", "description": "Upload custom reference audio"},
                "tts_file": {"path": "/tts/file", "description": "Generate from text file"},
                "analyze": {"path": "/analyze", "description": "Analyze text without generating speech"},
                "audio_quality": {"path": "/audio/quality", "description": "Check audio quality without TTS"},
                "status": {"path": "/tasks/{task_id}", "description": "Get task status"},
                "models": {"path": "/models", "description": "List available models"},
                "health": {"path": "/health", "description": "Health check"},
            },
        }

    # Register health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "models_loaded": api_state.loaded_models,
            "timestamp": datetime.now().isoformat(),
        }

    # Register models list endpoint
    @app.get("/models")
    async def list_models():
        """List available models."""
        return {
            "available_models": ["F5-TTS", "E2-TTS"],
            "loaded_models": api_state.loaded_models,
            "vocoders": ["vocos", "bigvgan"],
        }

    # Include all route modules
    router = create_router()
    app.include_router(router)

    return app


async def load_models():
    """
    Load TTS models on startup with CUDA optimizations.

    This function:
    1. Detects available device (CUDA/CPU)
    2. Applies CUDA optimizations if available
    3. Loads F5-TTS model
    4. Runs warmup inference
    """
    try:
        api_state.model_loading_status["loading"] = True
        logger.info("Loading default F5-TTS model...")

        # Detect the best available device
        if torch.cuda.is_available():
            device = "cuda"
            logger.info("CUDA is available, using GPU")

            # Apply CUDA optimizations
            if ENABLE_CUDNN_BENCHMARK:
                torch.backends.cudnn.benchmark = True
                logger.info("Enabled cuDNN benchmark mode for optimal kernel selection")

            # Set matmul precision for faster computation
            torch.set_float32_matmul_precision(TORCH_MATMUL_PRECISION)
            logger.info(f"Set matmul precision to: {TORCH_MATMUL_PRECISION}")

            # Enable TF32 on Ampere+ GPUs for faster matmul
            if torch.cuda.get_device_properties(0).major >= 8:
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True
                logger.info("Enabled TF32 for Ampere+ GPU")
        else:
            device = "cpu"
            logger.info("CUDA not available, using CPU")

        # Load F5-TTS model
        f5tts = F5TTS(
            model_type="F5-TTS",
            ckpt_file=DEFAULT_F5TTS_MODEL_PATH,
            vocab_file=DEFAULT_F5TTS_VOCAB_PATH,
            ode_method="euler",
            use_ema=True,
            vocoder_name="vocos",
            local_path=None,  # Let vocoder download from HF
            device=device,
        )
        api_state.add_model("F5-TTS", f5tts)

        # Warmup inference disabled to avoid ASR model download
        # The first inference request will be slower, but subsequent requests will be fast
        logger.info("Warmup inference disabled - first request will initialize ASR if needed")

        # E2-TTS model loading disabled (model architecture mismatch)
        # Can be enabled when compatible checkpoint is available

        api_state.model_loading_status["loading"] = False
        api_state.model_loading_status["loaded"] = True
        logger.info(f"Models loaded successfully: {api_state.loaded_models}")

    except Exception as e:
        api_state.model_loading_status["loading"] = False
        api_state.model_loading_status["error"] = str(e)
        logger.error(f"Failed to load models: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
