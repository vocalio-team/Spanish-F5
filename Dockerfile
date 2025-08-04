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

# Install PyTorch with CUDA support (use --no-cache-dir to save space)
RUN pip3 install --no-cache-dir torch==2.7.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu126

# Copy requirements and install Python dependencies
COPY pyproject.toml ./
RUN pip3 install --no-cache-dir -e .[dev]

# Install additional dependencies in one layer with compatible versions
RUN pip3 install --no-cache-dir \
    librosa==0.10.1 \
    soundfile==0.12.1 \
    scipy==1.11.4 \
    numpy==1.24.3 \
    transformers==4.35.2 \
    accelerate==0.24.1 \
    pyarrow==12.0.1 \
    datasets==2.14.6

# Copy the F5-TTS source code
COPY src/ ./src/
COPY f5_tts_api.py ./
COPY ref_audio/ ./ref_audio/

# Create necessary directories
RUN mkdir -p /app/models /app/temp /app/outputs /tmp/f5tts

# Copy pre-downloaded models
COPY models/ ./models/

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

# Copy application files
COPY --from=base /app/src ./src/
COPY --from=base /app/f5_tts_api.py ./
COPY --from=base /app/models ./models/
COPY --from=base /app/ref_audio ./ref_audio/

# Create necessary directories
RUN mkdir -p /app/temp /app/outputs /tmp/f5tts

# Install only gunicorn for production
RUN pip3 install --no-cache-dir gunicorn==21.2.0

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

# Production command with gunicorn
CMD ["gunicorn", "f5_tts_api:app", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "300", "--keep-alive", "2", "--max-requests", "1000", "--max-requests-jitter", "100"]
