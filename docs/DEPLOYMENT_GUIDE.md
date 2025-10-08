# Deployment Guide 🚀

Complete guide for deploying Spanish-F5 TTS in production environments.

---

## Table of Contents

- [Deployment Options](#deployment-options)
- [Docker Deployment](#docker-deployment)
- [Production API Server](#production-api-server)
- [Load Balancing & Scaling](#load-balancing--scaling)
- [Monitoring](#monitoring)
- [Security](#security)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)

---

## Deployment Options

### 1. Docker Container (Recommended)
- ✅ Isolated environment
- ✅ Easy deployment
- ✅ Reproducible builds
- ✅ GPU support

### 2. Systemd Service
- ✅ Native Linux integration
- ✅ Auto-restart on failure
- ✅ Resource limits

### 3. Kubernetes
- ✅ Horizontal scaling
- ✅ High availability
- ✅ Auto-healing
- ✅ Load balancing

### 4. Cloud Platforms
- AWS EC2 / ECS
- Google Cloud Run
- Azure Container Instances

---

## Docker Deployment

### Dockerfile

The project includes a multi-stage Dockerfile for optimized builds:

```dockerfile
# Development stage
FROM pytorch/pytorch:2.3.0-cuda11.8-cudnn8-devel AS development

WORKDIR /app
COPY . .
RUN pip install -e .

# Production stage
FROM pytorch/pytorch:2.3.0-cuda11.8-cudnn8-runtime AS production

WORKDIR /app
COPY --from=development /app .
RUN pip install --no-cache-dir -e .

EXPOSE 8000
CMD ["gunicorn", "f5_tts_api:app", \
     "-w", "1", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000"]
```

### Building the Image

```bash
# Build production image
docker build -t spanish-f5-tts:latest .

# Build with specific tag
docker build -t spanish-f5-tts:v1.0.0 .

# Build development image
docker build --target development -t spanish-f5-tts:dev .
```

### Running the Container

#### Basic

```bash
# Run with GPU support
docker run --gpus all -p 8000:8000 spanish-f5-tts:latest

# Run in background
docker run -d --gpus all -p 8000:8000 --name f5-tts spanish-f5-tts:latest

# Run with environment variables
docker run --gpus all -p 8000:8000 \
  -e ENABLE_TORCH_COMPILE=true \
  -e ENABLE_CUDNN_BENCHMARK=true \
  spanish-f5-tts:latest
```

#### With Volume Mounts

```bash
# Mount models directory
docker run --gpus all -p 8000:8000 \
  -v /path/to/models:/app/models \
  -v /path/to/output:/app/output \
  spanish-f5-tts:latest
```

#### Resource Limits

```bash
# Limit GPU and memory
docker run --gpus '"device=0"' \
  -p 8000:8000 \
  --memory="8g" \
  --memory-swap="8g" \
  --cpus="4" \
  spanish-f5-tts:latest
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  f5-tts:
    image: spanish-f5-tts:latest
    container_name: f5-tts-api
    restart: unless-stopped

    ports:
      - "8000:8000"

    environment:
      - ENABLE_TORCH_COMPILE=true
      - ENABLE_CUDNN_BENCHMARK=true
      - TORCH_MATMUL_PRECISION=high

    volumes:
      - ./models:/app/models
      - ./output:/app/output
      - ./logs:/app/logs

    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
        limits:
          memory: 8G

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  # Optional: Nginx reverse proxy
  nginx:
    image: nginx:alpine
    container_name: f5-tts-nginx
    restart: unless-stopped

    ports:
      - "80:80"
      - "443:443"

    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro

    depends_on:
      - f5-tts

  # Optional: Prometheus monitoring
  prometheus:
    image: prom/prometheus:latest
    container_name: f5-tts-prometheus
    restart: unless-stopped

    ports:
      - "9090:9090"

    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus

    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

volumes:
  prometheus-data:
```

Run with Docker Compose:

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f f5-tts

# Stop services
docker-compose down

# Restart services
docker-compose restart f5-tts
```

---

## Production API Server

### Gunicorn Configuration

Create `gunicorn_config.py`:

```python
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = 1  # Single worker for GPU (avoid conflicts)
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "/app/logs/access.log"
errorlog = "/app/logs/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "spanish-f5-tts"

# Server mechanics
daemon = False
pidfile = "/var/run/f5-tts.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = "/path/to/key.pem"
# certfile = "/path/to/cert.pem"
```

Run with Gunicorn:

```bash
# Using config file
gunicorn -c gunicorn_config.py f5_tts_api:app

# Manual configuration
gunicorn f5_tts_api:app \
  -w 1 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

### Systemd Service

Create `/etc/systemd/system/f5-tts.service`:

```ini
[Unit]
Description=Spanish-F5 TTS API Server
After=network.target

[Service]
Type=simple
User=f5-tts
Group=f5-tts
WorkingDirectory=/opt/spanish-f5
Environment="PATH=/opt/spanish-f5/venv/bin"
Environment="CUDA_VISIBLE_DEVICES=0"
Environment="ENABLE_TORCH_COMPILE=true"
ExecStart=/opt/spanish-f5/venv/bin/gunicorn \
  -c /opt/spanish-f5/gunicorn_config.py \
  f5_tts_api:app

# Restart policy
Restart=always
RestartSec=10
StartLimitInterval=200
StartLimitBurst=5

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=f5-tts

[Install]
WantedBy=multi-user.target
```

Manage service:

```bash
# Enable and start
sudo systemctl enable f5-tts
sudo systemctl start f5-tts

# Check status
sudo systemctl status f5-tts

# View logs
sudo journalctl -u f5-tts -f

# Restart
sudo systemctl restart f5-tts

# Stop
sudo systemctl stop f5-tts
```

---

## Load Balancing & Scaling

### Nginx Reverse Proxy

Create `nginx.conf`:

```nginx
upstream f5_tts_backend {
    # Single server
    server localhost:8000 max_fails=3 fail_timeout=30s;

    # Multiple servers for load balancing
    # server 192.168.1.101:8000 weight=1;
    # server 192.168.1.102:8000 weight=1;

    keepalive 32;
}

server {
    listen 80;
    server_name tts.example.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tts.example.com;

    # SSL configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # File upload limits
    client_max_body_size 100M;
    client_body_timeout 300s;

    # Timeouts
    proxy_connect_timeout 120s;
    proxy_send_timeout 120s;
    proxy_read_timeout 120s;

    # Headers
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Main location
    location / {
        proxy_pass http://f5_tts_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check endpoint
    location /health {
        proxy_pass http://f5_tts_backend/health;
        access_log off;
    }

    # Static files (if any)
    location /static {
        alias /opt/spanish-f5/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Logging
    access_log /var/log/nginx/f5-tts-access.log;
    error_log /var/log/nginx/f5-tts-error.log;
}
```

### Kubernetes Deployment

Create `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: f5-tts-deployment
  labels:
    app: f5-tts
spec:
  replicas: 2
  selector:
    matchLabels:
      app: f5-tts
  template:
    metadata:
      labels:
        app: f5-tts
    spec:
      containers:
      - name: f5-tts
        image: spanish-f5-tts:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENABLE_TORCH_COMPILE
          value: "true"
        - name: ENABLE_CUDNN_BENCHMARK
          value: "true"
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
            nvidia.com/gpu: 1
          limits:
            memory: "8Gi"
            cpu: "4"
            nvidia.com/gpu: 1
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: f5-tts-service
spec:
  selector:
    app: f5-tts
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

Deploy to Kubernetes:

```bash
# Apply deployment
kubectl apply -f k8s-deployment.yaml

# Check status
kubectl get pods -l app=f5-tts
kubectl get services

# View logs
kubectl logs -f deployment/f5-tts-deployment

# Scale
kubectl scale deployment/f5-tts-deployment --replicas=4

# Delete
kubectl delete -f k8s-deployment.yaml
```

---

## Monitoring

### Health Checks

The API includes a `/health` endpoint:

```bash
curl http://localhost:8000/health
```

Response:

```json
{
  "status": "healthy",
  "model_loaded": true,
  "gpu_available": true,
  "workers": []
}
```

### Prometheus Metrics

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'f5-tts'
    static_configs:
      - targets: ['f5-tts:8000']
    metrics_path: '/metrics'
```

Add metrics endpoint to `f5_tts_api.py`:

```python
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
tts_requests = Counter('tts_requests_total', 'Total TTS requests')
tts_duration = Histogram('tts_duration_seconds', 'TTS generation duration')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Logging

#### Structured Logging

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

# Configure logging
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

#### Log Aggregation

Use ELK Stack (Elasticsearch, Logstash, Kibana) or alternatives like Loki.

---

## Security

### API Authentication

Add API key authentication:

```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY = os.getenv("API_KEY", "your-secret-key")
api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

@app.post("/tts")
async def tts_endpoint(request: TTSRequest, api_key: str = Depends(verify_api_key)):
    # Protected endpoint
    pass
```

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

@app.post("/tts")
@limiter.limit("10/minute")
async def tts_endpoint(request: Request, tts_request: TTSRequest):
    pass
```

### HTTPS/TLS

```bash
# Generate self-signed certificate (development)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365

# Run with HTTPS
gunicorn f5_tts_api:app \
  --certfile=cert.pem \
  --keyfile=key.pem \
  --bind 0.0.0.0:443
```

For production, use Let's Encrypt:

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d tts.example.com

# Auto-renewal
sudo certbot renew --dry-run
```

---

## Performance Optimization

### Environment Variables

```bash
# PyTorch optimizations
export ENABLE_TORCH_COMPILE=true
export ENABLE_CUDNN_BENCHMARK=true
export TORCH_MATMUL_PRECISION=high

# CUDA optimizations
export CUDA_LAUNCH_BLOCKING=0
export CUDA_VISIBLE_DEVICES=0

# Memory management
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

### Model Optimization

```python
# In f5_tts_api.py startup
import torch

# Compile model
if hasattr(torch, 'compile'):
    model = torch.compile(model, mode="reduce-overhead")

# Use mixed precision
model.half()  # FP16

# Enable cuDNN auto-tuner
torch.backends.cudnn.benchmark = True
```

### Caching

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def preprocess_cached(ref_file: str, ref_text: str):
    """Cache preprocessed reference audio."""
    return preprocess_ref_audio_text(ref_file, ref_text)
```

---

## Troubleshooting

### Common Issues

#### Out of Memory (OOM)

```bash
# Reduce batch size or NFE steps
# Monitor GPU memory
nvidia-smi -l 1

# Clear CUDA cache
import torch
torch.cuda.empty_cache()
```

#### Slow Inference

```bash
# Enable optimizations
export ENABLE_TORCH_COMPILE=true
export ENABLE_CUDNN_BENCHMARK=true

# Use smaller NFE steps (16 instead of 32)
# Use shorter reference audio (6s instead of 30s)
```

#### Model Loading Errors

```bash
# Check model files
ls -lh models/

# Re-download models
rm -rf ~/.cache/huggingface
python -c "from f5_tts.api import F5TTS; F5TTS()"
```

### Debugging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Check container logs
docker logs -f f5-tts

# Check systemd logs
journalctl -u f5-tts -f --since "1 hour ago"

# Test GPU access
nvidia-smi
docker run --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

---

## Best Practices

1. **Use Docker** for consistent deployments
2. **Enable health checks** for monitoring
3. **Implement rate limiting** to prevent abuse
4. **Use HTTPS** in production
5. **Monitor GPU usage** and memory
6. **Set resource limits** to prevent OOM
7. **Use reverse proxy** (Nginx) for load balancing
8. **Implement logging** for debugging
9. **Regular backups** of models and configs
10. **Auto-restart** services on failure

---

## Production Checklist

- [ ] Docker image built and tagged
- [ ] Environment variables configured
- [ ] GPU access tested
- [ ] Health checks working
- [ ] Logging configured
- [ ] Monitoring setup (Prometheus/Grafana)
- [ ] HTTPS/SSL configured
- [ ] Rate limiting enabled
- [ ] API authentication implemented
- [ ] Load balancing configured
- [ ] Auto-restart enabled
- [ ] Backup strategy in place
- [ ] Documentation updated

---

[⬆ Back to Top](#deployment-guide-)
