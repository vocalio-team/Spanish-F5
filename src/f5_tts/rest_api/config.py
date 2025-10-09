"""
Configuration management for F5-TTS REST API.

This module contains API-specific configuration settings loaded from environment variables.
"""

import os


# Performance optimization flags
ENABLE_TORCH_COMPILE = os.getenv("ENABLE_TORCH_COMPILE", "true").lower() == "true"
ENABLE_CUDNN_BENCHMARK = os.getenv("ENABLE_CUDNN_BENCHMARK", "true").lower() == "true"
TORCH_MATMUL_PRECISION = os.getenv("TORCH_MATMUL_PRECISION", "high")  # "high" or "highest"

# Model paths
DEFAULT_F5TTS_MODEL_PATH = os.getenv(
    "F5TTS_MODEL_PATH", "/app/models/Spanish/model_1200000.safetensors"
)
DEFAULT_F5TTS_VOCAB_PATH = os.getenv("F5TTS_VOCAB_PATH", "/app/models/Spanish/vocab.txt")
DEFAULT_E2TTS_MODEL_PATH = os.getenv(
    "E2TTS_MODEL_PATH", "/app/models/E2TTS_Base/model_1200000.safetensors"
)

# Reference audio
DEFAULT_REF_AUDIO_PATH = os.getenv("DEFAULT_REF_AUDIO_PATH", "ref_audio/short.wav")

# Temporary file storage
TEMP_DIR = os.getenv("TEMP_DIR", "/tmp")
