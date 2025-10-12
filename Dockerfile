# Multi-stage Dockerfile for F5-TTS API with CUDA support - Optimized
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04 AS base

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV CUDA_VISIBLE_DEVICES=0

# Install system dependencies in a single layer with cleanup
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

# Upgrade pip
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN groupadd -r f5tts && useradd -r -g f5tts -d /app -s /bin/bash f5tts

# Copy minimal API requirements (no dev/training dependencies)
COPY requirements-api.txt ./

# Install minimal dependencies for API (no gradio, wandb, matplotlib, etc.)
RUN pip3 install --no-cache-dir -r requirements-api.txt

# Copy the F5-TTS source code
COPY src/ ./src/
COPY f5_tts_api.py ./
COPY ref_audio/ ./ref_audio/

# Create necessary directories
RUN mkdir -p /app/models /app/temp /app/outputs /tmp/f5tts /app/.cache/huggingface/hub

# Set environment variables for HuggingFace cache BEFORE downloading
ENV HF_HOME=/app/.cache/huggingface
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface
ENV HF_DATASETS_CACHE=/app/.cache/huggingface
ENV HF_HUB_CACHE=/app/.cache/huggingface/hub

# Copy pre-downloaded vocos model files directly
COPY vocos_model/ /app/vocos_model/

# Copy pre-downloaded Whisper ASR model files
COPY whisper_model/ /app/whisper_model/

# Copy entrypoint script for S3 model download
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Test PyTorch and CUDA installation
RUN python3 -c "import torch; print('PyTorch version:', torch.__version__); print('CUDA available:', torch.cuda.is_available())"

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

# Development stage
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

# Production stage - Heavily optimized
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

# Copy only the installed packages from base stage
COPY --from=base /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
COPY --from=base /usr/local/bin /usr/local/bin

# Copy application files (NO MODELS - download from S3 at runtime)
COPY --from=base /app/src ./src/
COPY --from=base /app/f5_tts_api.py ./
COPY --from=base /app/ref_audio ./ref_audio/

# Copy pre-downloaded vocos model from base stage
COPY --from=base /app/vocos_model /app/vocos_model

# Copy pre-downloaded Whisper ASR model from base stage
COPY --from=base /app/whisper_model /app/whisper_model

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create necessary directories
RUN mkdir -p /app/models /app/temp /app/outputs /tmp/f5tts

# Set vocos and whisper model paths
ENV VOCOS_MODEL_PATH=/app/vocos_model
ENV WHISPER_MODEL_PATH=/app/whisper_model

# Install gunicorn for production (AWS CLI already included from base stage)
RUN pip3 install --no-cache-dir gunicorn==21.2.0

# Set proper permissions
RUN chown -R f5tts:f5tts /app /tmp/f5tts
RUN chmod +x /app/f5_tts_api.py

# Switch to non-root user
USER f5tts

# Expose port
EXPOSE 8000

# Health check (longer start period for model download)
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set entrypoint for S3 model download
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Production command with gunicorn
CMD ["gunicorn", "f5_tts_api:app", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "300", "--keep-alive", "2", "--max-requests", "1000", "--max-requests-jitter", "100"]
