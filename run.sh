#!/bin/bash

# Run script for F5-TTS API

set -e

# Check if NVIDIA Docker runtime is available
if ! docker info | grep -q nvidia; then
    echo "Warning: NVIDIA Docker runtime not detected. GPU acceleration may not work."
    echo "Please install nvidia-docker2 and restart Docker daemon."
fi

# Create necessary directories
mkdir -p models outputs

# Check command line arguments
if [ "$1" = "dev" ]; then
    echo "Starting F5-TTS API in development mode..."
    docker-compose --profile dev up f5-tts-api-dev
elif [ "$1" = "build" ]; then
    echo "Building and starting F5-TTS API..."
    docker-compose up --build f5-tts-api
else
    echo "Starting F5-TTS API in production mode..."
    docker-compose up f5-tts-api
fi
