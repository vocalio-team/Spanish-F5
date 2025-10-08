#!/bin/bash

# This script should be run on the EC2 debug instance to manually test the F5-TTS container

echo "🧪 Manual F5-TTS Container Testing Script"
echo "========================================="
echo ""

# Check if we're running as root or with sudo
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script should be run as root or with sudo"
   echo "Usage: sudo ./test_container_manual.sh"
   exit 1
fi

echo "📊 System Information:"
echo "CPU: $(nproc) cores"
echo "Memory: $(free -h | grep ^Mem | awk '{print $2}')"
echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'No GPU detected')"
echo ""

echo "🔍 Checking Docker status..."
systemctl status docker --no-pager || {
    echo "❌ Docker is not running. Starting Docker..."
    systemctl start docker || {
        echo "❌ Failed to start Docker!"
        exit 1
    }
}
echo "✅ Docker is running"
echo ""

echo "🔍 Checking EFS mount..."
if mountpoint -q /mnt/efs; then
    echo "✅ EFS is mounted"
    echo "📁 EFS contents:"
    ls -la /mnt/efs/
    echo ""
    echo "📁 Models directory:"
    ls -la /mnt/efs/models/ || echo "⚠️ No models directory found"
    echo ""
    if [ -d "/mnt/efs/models/F5TTS_Base" ]; then
        echo "📁 F5TTS_Base model files:"
        ls -la /mnt/efs/models/F5TTS_Base/
        echo ""
    fi
    if [ -d "/mnt/efs/models/E2TTS_Base" ]; then
        echo "📁 E2TTS_Base model files:"
        ls -la /mnt/efs/models/E2TTS_Base/
        echo ""
    fi
else
    echo "❌ EFS is not mounted"
    echo "🔧 Attempting to mount EFS..."
    mkdir -p /mnt/efs
    mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,intr,timeo=600,retrans=2 fs-00c1631283c0bd7e1.efs.us-east-1.amazonaws.com:/ /mnt/efs && {
        echo "✅ EFS mounted successfully"
    } || {
        echo "❌ Failed to mount EFS"
        echo "🔍 Testing DNS resolution..."
        nslookup fs-00c1631283c0bd7e1.efs.us-east-1.amazonaws.com
        exit 1
    }
fi

echo "🔐 Testing ECR login..."
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 475302692635.dkr.ecr.us-east-1.amazonaws.com && {
    echo "✅ ECR login successful"
} || {
    echo "❌ ECR login failed"
    echo "🔍 Checking AWS credentials..."
    aws sts get-caller-identity || echo "❌ AWS credentials not configured"
    exit 1
}
echo ""

echo "📥 Pulling F5-TTS Docker image..."
docker pull 475302692635.dkr.ecr.us-east-1.amazonaws.com/f5-tts-api:latest && {
    echo "✅ Docker image pulled successfully"
} || {
    echo "❌ Failed to pull Docker image"
    exit 1
}
echo ""

echo "🧹 Cleaning up any existing containers..."
docker stop f5-tts-api 2>/dev/null || true
docker rm f5-tts-api 2>/dev/null || true

echo "🚀 Starting F5-TTS container..."
docker run --gpus all -d --restart unless-stopped \
  -p 8000:8000 \
  --name f5-tts-api \
  -v /mnt/efs/models:/app/models \
  --health-cmd="curl -f http://localhost:8000/health || exit 1" \
  --health-interval=30s \
  --health-timeout=10s \
  --health-retries=3 \
  475302692635.dkr.ecr.us-east-1.amazonaws.com/f5-tts-api:latest && {
    echo "✅ Container started successfully"
} || {
    echo "❌ Failed to start container"
    exit 1
}

echo ""
echo "🔍 Monitoring container startup..."
echo "Container ID: $(docker ps -q -f name=f5-tts-api)"

# Wait for container to be running
for i in {1..10}; do
    if docker ps | grep -q f5-tts-api; then
        echo "✅ Container is running!"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "❌ Container failed to start after 10 attempts"
        echo "📋 Container logs:"
        docker logs f5-tts-api
        exit 1
    fi
    echo "⏳ Waiting for container to start... ($i/10)"
    sleep 5
done

echo ""
echo "📋 Container status:"
docker ps -f name=f5-tts-api

echo ""
echo "📋 Live container logs (last 20 lines):"
docker logs --tail 20 f5-tts-api

echo ""
echo "🔍 Waiting for health check..."
for i in {1..20}; do
    HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' f5-tts-api 2>/dev/null || echo "no-health")
    echo "[$i/20] Health status: $HEALTH_STATUS"
    
    if [ "$HEALTH_STATUS" = "healthy" ]; then
        echo "✅ Container is healthy!"
        break
    elif [ "$HEALTH_STATUS" = "unhealthy" ]; then
        echo "❌ Container is unhealthy"
        echo "📋 Recent container logs:"
        docker logs --tail 50 f5-tts-api
        break
    fi
    
    if [ $i -eq 20 ]; then
        echo "⚠️ Health check timeout after 20 attempts"
        echo "📋 Final container logs:"
        docker logs --tail 50 f5-tts-api
    fi
    
    sleep 15
done

echo ""
echo "🌐 Testing API endpoints:"
echo "Health endpoint:"
curl -s http://localhost:8000/health | jq . 2>/dev/null || curl -s http://localhost:8000/health

echo ""
echo "Models endpoint:"
curl -s http://localhost:8000/models | jq . 2>/dev/null || curl -s http://localhost:8000/models

echo ""
echo "📊 Container resource usage:"
docker stats --no-stream f5-tts-api

echo ""
echo "🎉 Testing completed!"
echo ""
echo "📋 Container Management Commands:"
echo "  View logs:           docker logs -f f5-tts-api"
echo "  Stop container:      docker stop f5-tts-api"
echo "  Restart container:   docker restart f5-tts-api"
echo "  Remove container:    docker rm -f f5-tts-api"
echo ""
echo "🌐 API Access:"
echo "  Health check: curl http://localhost:8000/health"
echo "  List models:  curl http://localhost:8000/models"
echo "  External API: curl http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000/health"
