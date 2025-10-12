#!/bin/bash
# Docker build script for F5-TTS with optimized caching
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="spanish-f5-tts"
REGISTRY="475302692635.dkr.ecr.us-east-1.amazonaws.com"
TAG="${1:-latest}"
STAGE="${2:-base}"  # base, development, or production

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Building F5-TTS Docker Image${NC}"
echo -e "${BLUE}Stage: ${STAGE}${NC}"
echo -e "${BLUE}Tag: ${TAG}${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Build with BuildKit for better caching
export DOCKER_BUILDKIT=1

echo -e "${YELLOW}Building ${STAGE} stage...${NC}"
START_TIME=$(date +%s)

docker build \
  --target ${STAGE} \
  --tag ${IMAGE_NAME}:${TAG} \
  --tag ${IMAGE_NAME}:${STAGE}-${TAG} \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  --progress=plain \
  .

END_TIME=$(date +%s)
BUILD_TIME=$((END_TIME - START_TIME))

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build completed in ${BUILD_TIME} seconds${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Image: ${GREEN}${IMAGE_NAME}:${TAG}${NC}"
echo -e "Size: ${GREEN}$(docker images ${IMAGE_NAME}:${TAG} --format '{{.Size}}')${NC}"
echo ""

# Optional: Push to ECR
if [ "$3" == "--push" ]; then
  echo -e "${YELLOW}Logging in to ECR...${NC}"
  aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ${REGISTRY}

  echo -e "${YELLOW}Tagging for ECR...${NC}"
  docker tag ${IMAGE_NAME}:${TAG} ${REGISTRY}/f5-tts-api:${TAG}

  echo -e "${YELLOW}Pushing to ECR...${NC}"
  docker push ${REGISTRY}/f5-tts-api:${TAG}

  echo -e "${GREEN}✓ Pushed to ECR${NC}"
fi

echo ""
echo -e "${BLUE}Layer Caching Tips:${NC}"
echo -e "  • System dependencies:  ${GREEN}Fully cached${NC} (unless Dockerfile changes)"
echo -e "  • Python packages:      ${GREEN}Cached${NC} until requirements-api.txt changes"
echo -e "  • Models (3.15GB):      ${GREEN}Cached${NC} unless model files change"
echo -e "  • Source code:          ${YELLOW}Rebuilt${NC} on every code change (fast)"
echo ""
echo -e "${BLUE}Usage:${NC}"
echo -e "  ./docker-build.sh [TAG] [STAGE] [--push]"
echo -e "  Examples:"
echo -e "    ./docker-build.sh latest base         # Build base image"
echo -e "    ./docker-build.sh v1.0.0 production   # Build production image"
echo -e "    ./docker-build.sh latest base --push  # Build and push to ECR"
echo ""
