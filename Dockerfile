# Multi-stage Dockerfile for F5-TTS API with CUDA support
# Optimized for fast rebuilds with proper layer caching

# ============================================================================
# BASE STAGE - System dependencies and Python packages (cached)
# ============================================================================
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04 AS base

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV CUDA_VISIBLE_DEVICES=0

# Install system dependencies in a single layer with cleanup
# This layer rarely changes - good for caching
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3.10-dev \
    python3-pip \
    python3.10-venv \
    git \
    curl \
    build-essential \
    cmake \
    pkg-config \
    libsndfile1 \
    ffmpeg \
    sox \
    libsox-fmt-all \
    espeak-ng \
    espeak-ng-data \
    libespeak-ng-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /tmp/* /var/tmp/*

# Create symbolic links for python
RUN ln -sf /usr/bin/python3.10 /usr/bin/python3 && \
    ln -sf /usr/bin/python3.10 /usr/bin/python

# Upgrade pip (cached layer)
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel

# Set working directory
WORKDIR /app

# Create non-root user for security (cached layer)
RUN groupadd -r f5tts && useradd -r -g f5tts -d /app -s /bin/bash f5tts

# ============================================================================
# DEPENDENCIES STAGE - Install Python packages (cached unless requirements change)
# ============================================================================

# Copy ONLY requirements file first - this layer is cached unless requirements change
COPY requirements-api.txt ./

# Install Python dependencies (this is the heavy layer that we want to cache)
RUN pip3 install --no-cache-dir -r requirements-api.txt

# Test PyTorch and CUDA installation (cached with dependencies)
RUN python3 -c "import torch; print('PyTorch version:', torch.__version__); print('CUDA available:', torch.cuda.is_available())"

# ============================================================================
# MODELS STAGE - Copy pre-downloaded models (large but rarely change)
# ============================================================================

# Create necessary directories
RUN mkdir -p /app/models /app/temp /app/outputs /tmp/f5tts /app/.cache/huggingface/hub

# Set environment variables for HuggingFace cache
ENV HF_HOME=/app/.cache/huggingface
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface
ENV HF_DATASETS_CACHE=/app/.cache/huggingface
ENV HF_HUB_CACHE=/app/.cache/huggingface/hub

# Copy pre-downloaded vocos model files directly (3.15GB - large but static)
# This layer is cached unless model files change
COPY vocos_model/ /app/vocos_model/
COPY whisper_model/ /app/whisper_model/

# Set model paths
ENV VOCOS_MODEL_PATH=/app/vocos_model
ENV WHISPER_MODEL_PATH=/app/whisper_model

# ============================================================================
# APPLICATION STAGE - Copy source code (changes frequently, goes LAST)
# ============================================================================

# Copy entrypoint script (rarely changes)
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Copy reference audio files (rarely change)
COPY ref_audio/ ./ref_audio/

# Copy the F5-TTS source code (LAST - changes most frequently)
# Any code change only invalidates layers from here onwards
COPY src/ ./src/
COPY f5_tts_api.py ./

# Set proper permissions
RUN chown -R f5tts:f5tts /app /tmp/f5tts
RUN chmod +x /app/f5_tts_api.py

# Switch to non-root user
USER f5tts

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Default command
CMD ["python3", "-m", "uvicorn", "f5_tts_api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

# ============================================================================
# DEVELOPMENT STAGE - Add dev tools
# ============================================================================
FROM base AS development

USER root

# Install development tools
RUN pip3 install --no-cache-dir \
    jupyter==1.0.0 \
    ipython==8.17.2 \
    notebook==7.0.6 \
    jupyterlab==4.0.8

# Install debugging tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    htop \
    nvtop \
    vim \
    nano \
    tmux \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

USER f5tts

# Expose additional ports for development
EXPOSE 8888 8080

# ============================================================================
# PRODUCTION STAGE - Minimal runtime image (optimized for size)
# ============================================================================
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04 AS production

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV CUDA_VISIBLE_DEVICES=0

# Install only runtime dependencies (no dev packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    curl \
    libsndfile1 \
    ffmpeg \
    sox \
    libsox-fmt-all \
    espeak-ng \
    espeak-ng-data \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /tmp/* /var/tmp/*

# Create symbolic links for python
RUN ln -sf /usr/bin/python3.10 /usr/bin/python3 && \
    ln -sf /usr/bin/python3.10 /usr/bin/python

# Set working directory
WORKDIR /app

# Create non-root user
RUN groupadd -r f5tts && useradd -r -g f5tts -d /app -s /bin/bash f5tts

# Copy only the installed packages from base stage (cached)
COPY --from=base /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
COPY --from=base /usr/local/bin /usr/local/bin

# Copy pre-downloaded models from base stage (large but static - cached)
COPY --from=base /app/vocos_model /app/vocos_model
COPY --from=base /app/whisper_model /app/whisper_model

# Copy entrypoint script (rarely changes - cached)
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Copy reference audio (rarely changes - cached)
COPY --from=base /app/ref_audio ./ref_audio/

# Copy application code (LAST - most frequently changed)
COPY --from=base /app/src ./src/
COPY --from=base /app/f5_tts_api.py ./

# Create necessary directories
RUN mkdir -p /app/models /app/temp /app/outputs /tmp/f5tts

# Set model paths
ENV VOCOS_MODEL_PATH=/app/vocos_model
ENV WHISPER_MODEL_PATH=/app/whisper_model

# Install gunicorn for production
RUN pip3 install --no-cache-dir gunicorn==21.2.0

# Set proper permissions
RUN chown -R f5tts:f5tts /app /tmp/f5tts
RUN chmod +x /app/f5_tts_api.py

# Switch to non-root user
USER f5tts

# Expose port
EXPOSE 8000

# Health check (longer start period for model loading)
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Production command with gunicorn
CMD ["gunicorn", "f5_tts_api:app", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "300", "--keep-alive", "2", "--max-requests", "1000", "--max-requests-jitter", "100"]
