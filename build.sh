#!/bin/bash

# Build script for F5-TTS API Docker image

set -e

echo "Building F5-TTS API Docker image..."

# Build production image
docker build -t f5-tts-api:latest --target production .

# Build development image
docker build -t f5-tts-api:dev --target development .

echo "Build completed successfully!"
echo ""
echo "Available images:"
echo "  f5-tts-api:latest (production)"
echo "  f5-tts-api:dev (development)"
echo ""
echo "To run production: docker-compose up f5-tts-api"
echo "To run development: docker-compose --profile dev up f5-tts-api-dev"

