# Arquitectura del Ecosistema Vocalio

**Versión**: 1.0
**Fecha**: 2025-10-29
**Componente**: Spanish-F5 TTS Worker

---

## 📋 Tabla de Contenidos

- [Visión General del Ecosistema](#-visión-general-del-ecosistema)
- [Componentes del Sistema](#-componentes-del-sistema)
- [Flujo de Comunicación](#-flujo-de-comunicación)
- [Protocolo de Integración](#-protocolo-de-integración)
- [Gestión de Ciclo de Vida](#-gestión-de-ciclo-de-vida)
- [Infraestructura y Despliegue](#-infraestructura-y-despliegue)
- [Monitoreo y Métricas](#-monitoreo-y-métricas)
- [Escalabilidad y Resiliencia](#-escalabilidad-y-resiliencia)

---

## 🌐 Visión General del Ecosistema

**Vocalio** es una plataforma distribuida de inteligencia artificial para procesamiento de voz y audio en español. El ecosistema está diseñado como una arquitectura de microservicios con workers especializados que proveen capacidades de GPU bajo demanda.

### Diagrama de Alto Nivel

```
┌──────────────────────────────────────────────────────────────────────┐
│                        ECOSISTEMA VOCALIO                             │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                    CAPA DE APLICACIÓN                           │ │
│  │                                                                 │ │
│  │  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐ │ │
│  │  │   Web App    │      │  Mobile App  │      │   Admin UI   │ │ │
│  │  └──────┬───────┘      └──────┬───────┘      └──────┬───────┘ │ │
│  │         │                     │                      │         │ │
│  └─────────┼─────────────────────┼──────────────────────┼─────────┘ │
│            │                     │                      │            │
│            └─────────────────────┴──────────────────────┘            │
│                                  │                                   │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                     BACKEND AITHENTIA                           │ │
│  │                  (Coordinador Central)                          │ │
│  │                                                                 │ │
│  │  • Gestión de workers                                          │ │
│  │  • Cola de tareas distribuida                                  │ │
│  │  • Balanceo de carga                                           │ │
│  │  • Monitoreo y métricas                                        │ │
│  │  • Autenticación y autorización                                │ │
│  │                                                                 │ │
│  │  API: https://api.test.aithentia.com:8000                      │ │
│  │  Endpoints: /api/v1/workers, /api/v1/jobs                      │ │
│  └────────────────────────┬───────────────────────────────────────┘ │
│                           │                                          │
│            ┌──────────────┼──────────────┐                          │
│            │              │              │                          │
│  ┌─────────▼─────┐ ┌─────▼──────┐ ┌────▼──────────┐               │
│  │               │ │            │ │               │                │
│  │  Spanish-F5   │ │  Whisper   │ │ Other Workers │                │
│  │  TTS Worker   │ │   Worker   │ │  (Futuro)     │                │
│  │               │ │            │ │               │                │
│  │  • GPU Spot   │ │ • GPU Spot │ │ • GPU Spot    │                │
│  │  • F5-TTS     │ │ • ASR      │ │ • Training    │                │
│  │  • Regional   │ │ • Spanish  │ │ • etc.        │                │
│  │                                                                  │ │
│  └──────────────┘ └────────────┘ └───────────────┘                │ │
│                                                                     │ │
│  CAPA DE WORKERS GPU (ECS Fargate + EC2 Spot)                      │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘

Almacenamiento:
  • S3: Modelos, datasets, resultados
  • EFS: Checkpoints compartidos (opcional)
  • CloudWatch: Logs y métricas
```

### Principios de Diseño

1. **Desacoplamiento**: Workers independientes que pueden desplegarse/escalarse sin afectar otros componentes
2. **Especialización**: Cada worker tiene un propósito específico (TTS, ASR, training, etc.)
3. **Elasticidad**: Uso de Spot instances para reducir costos (60-70% ahorro)
4. **Resiliencia**: Heartbeat polling para compatibilidad NAT/firewall, circuit breakers, retry con backoff
5. **Observabilidad**: Métricas detalladas, logs centralizados, trazabilidad de tareas

---

## 🔧 Componentes del Sistema

### 1. Backend Aithentia (Coordinador Central)

**Responsabilidades:**
- Registro y gestión de workers
- Distribución de tareas entre workers disponibles
- Monitoreo de salud y métricas de workers
- Gestión de cola de tareas
- Autenticación y autorización

**Tecnología:**
- FastAPI
- PostgreSQL (estado persistente)
- Redis (cola de tareas, cache)
- Deployed en ECS/EC2

**Endpoints Clave:**
```
POST   /api/v1/workers          - Registrar worker
GET    /api/v1/workers          - Listar workers activos
POST   /api/v1/workers/{id}/heartbeat - Heartbeat + polling de tareas
DELETE /api/v1/workers/{id}     - Desregistrar worker
POST   /api/v1/jobs             - Enviar nueva tarea
GET    /api/v1/jobs/{id}        - Obtener estado de tarea
```

### 2. Spanish-F5 TTS Worker (Este Proyecto)

**Responsabilidades:**
- Síntesis de voz en español de alta calidad
- Procesamiento de variantes regionales
- Inferencia GPU con modelos DiT/UNetT
- Reportar métricas de uso y calidad

**Tecnología:**
- PyTorch 2.3+ con CUDA 11.8
- FastAPI para API REST
- F5-TTS + Vocos vocoder
- Procesador regional de español personalizado

**Capacidades Reportadas:**
```json
{
  "worker_type": "tts",
  "models": ["F5-TTS", "E2-TTS"],
  "languages": ["es"],
  "regional_variants": [
    "rioplatense", "colombian", "mexican",
    "chilean", "caribbean", "andean"
  ],
  "gpu_info": {
    "name": "NVIDIA A10G",
    "memory_total": 24576,
    "cuda_version": "11.8"
  },
  "max_concurrent_jobs": 2,
  "average_latency_ms": 4000
}
```

**Endpoints:**
```
POST /tts                - Generar voz
POST /analyze            - Analizar texto
GET  /health             - Health check
GET  /metrics            - Métricas Prometheus
```

### 3. Worker UI Dashboard

**Responsabilidades:**
- Visualización de workers activos
- Monitoreo de tareas en ejecución
- Métricas en tiempo real
- Control manual de workers

**Tecnología:**
- React + TypeScript
- TailwindCSS
- Recharts para gráficos
- WebSocket para updates en tiempo real

### 4. Cliente de Integración Backend

**Archivo:** `backend_integration.py`

**Responsabilidades:**
- Abstracción de comunicación con backend
- Manejo de autenticación
- Retry automático con backoff
- Serialización de requests/responses

**Uso:**
```python
from backend_integration import GPUInferenceClient

client = GPUInferenceClient(
    f5_tts_url="http://alb-url.amazonaws.com"
)

# Generar voz
audio = await client.generate_speech(
    text="Hola mundo",
    region="rioplatense",
    nfe_step=16
)

# Health check
health = await client.health_check()
```

---

## 🔄 Flujo de Comunicación

### Registro de Worker

```
┌──────────┐                                    ┌──────────┐
│ Spanish  │                                    │ Backend  │
│ F5 Worker│                                    │Aithentia │
└────┬─────┘                                    └────┬─────┘
     │                                                │
     │ 1. POST /api/v1/workers                       │
     │    {                                           │
     │      worker_id: "f5-tts-worker-abc123"        │
     │      worker_type: "tts"                        │
     │      capabilities: {...}                       │
     │      host: "10.0.1.50"                         │
     │      port: 8000                                │
     │    }                                           │
     ├───────────────────────────────────────────────►│
     │                                                │
     │                    2. Validar worker           │
     │                       Asignar ID único         │
     │                       Registrar en DB          │
     │                                                │
     │ 3. 200 OK                                     │
     │    {                                           │
     │      worker_id: "f5-tts-worker-abc123"        │
     │      status: "registered"                      │
     │      heartbeat_interval: 30                    │
     │    }                                           │
     │◄───────────────────────────────────────────────┤
     │                                                │
     │ 4. Iniciar heartbeat loop                     │
     │    cada 30 segundos                            │
     │                                                │
```

### Heartbeat y Polling de Tareas

**Flujo NAT-Friendly:**

El worker inicia todas las conexiones (backend nunca llama al worker directamente):

```
┌──────────┐                                    ┌──────────┐
│ Worker   │                                    │ Backend  │
└────┬─────┘                                    └────┬─────┘
     │                                                │
     │ Cada 30s: POST /workers/{id}/heartbeat        │
     │    {                                           │
     │      status: "idle",                           │
     │      metrics: {                                │
     │        gpu_utilization: 45,                    │
     │        memory_usage: 8192,                     │
     │        active_jobs: 0                          │
     │      }                                          │
     │    }                                           │
     ├───────────────────────────────────────────────►│
     │                                                │
     │              Si hay tarea pendiente:           │
     │ 200 OK                                         │
     │    {                                           │
     │      status: "ok",                             │
     │      pending_job: {                            │
     │        job_id: "job-xyz",                      │
     │        type: "tts",                            │
     │        params: {...}                           │
     │      }                                          │
     │    }                                           │
     │◄───────────────────────────────────────────────┤
     │                                                │
     │ Worker procesa tarea                           │
     │                                                │
     │ POST /jobs/{job_id}/status                    │
     │    { status: "completed", result_url: "..." } │
     ├───────────────────────────────────────────────►│
     │                                                │
```

**Ventajas:**
- ✅ Funciona detrás de NAT/firewalls
- ✅ No requiere IP pública en worker
- ✅ No requiere configuración de puertos entrantes
- ✅ Compatible con containers efímeros

### Ejecución de Tarea

```
┌──────────┐                                    ┌──────────┐
│ Worker   │                                    │ Backend  │
└────┬─────┘                                    └────┬─────┘
     │                                                │
     │ 1. Recibir tarea en heartbeat                 │
     │    job = { job_id, type: "tts", params }      │
     │                                                │
     │ 2. POST /jobs/{job_id}/status                │
     │    { status: "running", progress: 0 }         │
     ├───────────────────────────────────────────────►│
     │                                                │
     │ 3. Procesar texto regional                     │
     │    - Detectar variante                         │
     │    - Aplicar transformaciones fonéticas        │
     │    - Generar marcadores prosódicos             │
     │                                                │
     │ 4. POST /jobs/{job_id}/status                │
     │    { status: "running", progress: 30 }        │
     ├───────────────────────────────────────────────►│
     │                                                │
     │ 5. Inferencia GPU                              │
     │    - Cargar modelo F5-TTS                      │
     │    - Generar mel-espectrograma                 │
     │    - Vocodrr a waveform                        │
     │                                                │
     │ 6. POST /jobs/{job_id}/status                │
     │    { status: "running", progress: 70 }        │
     ├───────────────────────────────────────────────►│
     │                                                │
     │ 7. Post-procesamiento                          │
     │    - Normalizar audio                          │
     │    - Aplicar crossfading                       │
     │    - Verificar calidad                         │
     │                                                │
     │ 8. Subir resultado a S3                        │
     │    s3://vocalio-results/job-xyz.wav            │
     │                                                │
     │ 9. POST /jobs/{job_id}/status                │
     │    {                                           │
     │      status: "completed",                      │
     │      progress: 100,                            │
     │      result_url: "s3://...",                   │
     │      metrics: {                                │
     │        latency_ms: 4250,                       │
     │        audio_quality: 96.5,                    │
     │        detected_region: "rioplatense"          │
     │      }                                          │
     │    }                                           │
     ├───────────────────────────────────────────────►│
     │                                                │
```

---

## 🔌 Protocolo de Integración

### Formato de Mensajes

#### WorkerRegistration

```json
{
  "worker_id": "f5-tts-worker-i-0abc123",
  "worker_type": "tts",
  "capabilities": {
    "models": ["F5-TTS", "E2-TTS"],
    "languages": ["es"],
    "regional_variants": [
      "rioplatense", "colombian", "mexican",
      "chilean", "caribbean", "andean"
    ],
    "gpu_info": {
      "name": "NVIDIA A10G",
      "memory_total_mb": 24576,
      "memory_available_mb": 22000,
      "cuda_version": "11.8",
      "compute_capability": "8.6"
    },
    "max_concurrent_jobs": 2,
    "supported_sample_rates": [16000, 22050, 24000, 44100, 48000]
  },
  "host": "10.0.1.50",
  "port": 8000,
  "status": "idle",
  "version": "1.0.0"
}
```

#### HeartbeatRequest

```json
{
  "worker_id": "f5-tts-worker-i-0abc123",
  "status": "busy",
  "metrics": {
    "timestamp": "2025-10-29T12:34:56Z",
    "cpu_usage_percent": 45.2,
    "memory_usage_mb": 8192,
    "memory_total_mb": 16384,
    "gpu_utilization_percent": 85,
    "gpu_memory_used_mb": 12000,
    "gpu_memory_total_mb": 24576,
    "active_jobs": 1,
    "completed_jobs_total": 142,
    "failed_jobs_total": 3,
    "average_latency_ms": 4250
  },
  "active_job_ids": ["job-xyz-123"]
}
```

#### HeartbeatResponse (con tarea)

```json
{
  "status": "ok",
  "next_heartbeat_interval": 30,
  "pending_job": {
    "job_id": "job-abc-456",
    "type": "tts",
    "priority": "normal",
    "created_at": "2025-10-29T12:35:00Z",
    "params": {
      "text": "Che boludo, ¿cómo andás?",
      "region": "auto",
      "nfe_step": 16,
      "speed": 1.0,
      "output_format": "wav",
      "sample_rate": 24000
    },
    "callback_url": "https://api.test.aithentia.com:8000/api/v1/jobs/job-abc-456/status"
  }
}
```

#### JobStatusUpdate

```json
{
  "job_id": "job-abc-456",
  "worker_id": "f5-tts-worker-i-0abc123",
  "status": "completed",
  "progress": 100,
  "started_at": "2025-10-29T12:35:05Z",
  "completed_at": "2025-10-29T12:35:10Z",
  "result": {
    "output_url": "s3://vocalio-results/2025/10/29/job-abc-456.wav",
    "duration_seconds": 3.5,
    "sample_rate": 24000,
    "channels": 1,
    "format": "wav"
  },
  "metrics": {
    "latency_ms": 4250,
    "processing_time_ms": 3800,
    "upload_time_ms": 450,
    "audio_quality_score": 96.5,
    "detected_region": "rioplatense",
    "slang_markers": ["che", "boludo", "andás"],
    "nfe_steps_used": 16
  },
  "error": null
}
```

### Manejo de Errores

```json
{
  "job_id": "job-abc-456",
  "worker_id": "f5-tts-worker-i-0abc123",
  "status": "failed",
  "progress": 45,
  "started_at": "2025-10-29T12:35:05Z",
  "failed_at": "2025-10-29T12:35:08Z",
  "error": {
    "code": "GPU_OOM",
    "message": "GPU out of memory during inference",
    "category": "RESOURCE",
    "severity": "HIGH",
    "recoverable": true,
    "retry_suggested": true,
    "context": {
      "gpu_memory_required_mb": 14000,
      "gpu_memory_available_mb": 12000,
      "text_length": 5000
    }
  }
}
```

---

## 🔄 Gestión de Ciclo de Vida

### Estados del Worker

```
                    ┌──────────────┐
                    │ INITIALIZING │
                    └──────┬───────┘
                           │
                           │ Carga modelos
                           │ Detecta GPU
                           ▼
                    ┌──────────────┐
              ┌────►│     IDLE     │◄────┐
              │     └──────┬───────┘     │
              │            │              │
              │            │ Tarea nueva  │
              │            ▼              │
              │     ┌──────────────┐     │
              │     │     BUSY     │     │
              │     └──────┬───────┘     │
              │            │              │
              │            │ Tarea       │
              │            │ completada   │
              └────────────┴──────────────┘
                           │
                           │ Señal shutdown
                           ▼
                    ┌──────────────┐
                    │  DRAINING    │
                    └──────┬───────┘
                           │
                           │ Todas las tareas
                           │ completadas
                           ▼
                    ┌──────────────┐
                    │  SHUTDOWN    │
                    └──────────────┘
```

### Graceful Shutdown

1. **Recibir señal SIGTERM** (ej. Spot interruption)
2. **Cambiar estado a DRAINING**
3. **Dejar de aceptar nuevas tareas**
4. **Esperar a que tareas activas terminen** (máx 120s)
5. **Hacer checkpoint de tareas largas** (si aplica)
6. **Desregistrar worker del backend**
7. **Cerrar conexiones GPU**
8. **EXIT 0**

```python
async def graceful_shutdown(worker_service, timeout=120):
    logger.info("Iniciando graceful shutdown")

    # Cambiar a modo draining
    worker_service.set_status("draining")

    # Esperar tareas activas
    await worker_service.wait_for_active_jobs(timeout)

    # Desregistrar
    await worker_service.deregister()

    # Cleanup
    await worker_service.cleanup()

    logger.info("Shutdown completado")
```

---

## 🏗️ Infraestructura y Despliegue

### AWS Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                      VPC (10.0.0.0/16)                         │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Public Subnet (10.0.1.0/24)                      │  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │  Application Load Balancer (ALB)                    │ │  │
│  │  │  - Health checks                                     │ │  │
│  │  │  - SSL termination                                   │ │  │
│  │  │  - Target group: GPU workers                         │ │  │
│  │  └─────────────────┬───────────────────────────────────┘ │  │
│  └────────────────────┼───────────────────────────────────── │  │
│                       │                                         │
│  ┌────────────────────▼─────────────────────────────────────┐  │
│  │         Private Subnet (10.0.2.0/24)                     │  │
│  │                                                           │  │
│  │  ┌──────────────────────────────────────────────────┐   │  │
│  │  │  ECS Cluster: dev-vocalio-chatterbox             │   │  │
│  │  │                                                   │   │  │
│  │  │  ┌────────────────┐      ┌────────────────┐     │   │  │
│  │  │  │ EC2 Spot       │      │ EC2 Spot       │     │   │  │
│  │  │  │ g5.xlarge      │      │ g4dn.xlarge    │     │   │  │
│  │  │  │                │      │                │     │   │  │
│  │  │  │ F5-TTS Task    │      │ F5-TTS Task    │     │   │  │
│  │  │  │ - 1 vCPU       │      │ - 1 vCPU       │     │   │  │
│  │  │  │ - 4 GB RAM     │      │ - 4 GB RAM     │     │   │  │
│  │  │  │ - 1 GPU        │      │ - 1 GPU        │     │   │  │
│  │  │  └────────────────┘      └────────────────┘     │   │  │
│  │  │                                                   │   │  │
│  │  │  Capacity Provider: gpu-spot-stack-cp            │   │  │
│  │  │  Auto Scaling Group: 1-4 instances               │   │  │
│  │  └──────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Servicios Auxiliares:
  • S3: Modelos, resultados de audio
  • CloudWatch: Logs y métricas
  • ECR: Docker images
  • Secrets Manager: Tokens, API keys
```

### Configuración de Despliegue

**CloudFormation Stack:** `gpu-spot-stack`

**Recursos Principales:**
- ALB con health checks
- ECS Cluster
- Capacity Provider (Spot)
- Auto Scaling Group (1-4 instances)
- Target Group
- Security Groups
- IAM Roles

**Tipos de Instancia:**
- `g5.xlarge`: NVIDIA A10G, 24GB VRAM, ~$0.27/hr Spot
- `g4dn.xlarge`: NVIDIA T4, 16GB VRAM, ~$0.16/hr Spot

**Costos Estimados:**
- 2 instancias g4dn.xlarge Spot: ~$110-140/mes
- 2 instancias g5.xlarge Spot: ~$150-180/mes
- **Ahorro vs On-Demand: 60-70%**

### Script de Despliegue

```bash
#!/bin/bash
# deploy-gpu-spot.sh

# Desplegar stack completo
./deploy-gpu-spot.sh

# Lo que hace:
# 1. Build Docker image
# 2. Push to ECR
# 3. Deploy/update CloudFormation stack
# 4. Wait for stack creation
# 5. Register tasks in ECS
# 6. Configure ALB target group
# 7. Verificar health checks
```

---

## 📊 Monitoreo y Métricas

### Métricas del Worker

**Categorías:**

1. **Sistema:**
   - CPU usage %
   - Memory usage (MB)
   - Disk I/O
   - Network I/O

2. **GPU:**
   - GPU utilization %
   - GPU memory used/total (MB)
   - GPU temperature (°C)
   - CUDA version

3. **Tareas:**
   - Active jobs count
   - Completed jobs (total, últimas 24h)
   - Failed jobs (total, últimas 24h)
   - Average latency (ms)
   - P50/P95/P99 latency

4. **Calidad:**
   - Audio quality score (promedio)
   - SNR (dB)
   - Clipping rate %
   - Regional detection accuracy %

### Endpoint de Métricas

```
GET /metrics

# Formato Prometheus
# TYPE gpu_utilization_percent gauge
gpu_utilization_percent{worker_id="f5-tts-worker-abc"} 85.0

# TYPE memory_usage_mb gauge
memory_usage_mb{worker_id="f5-tts-worker-abc"} 8192

# TYPE jobs_completed_total counter
jobs_completed_total{worker_id="f5-tts-worker-abc",status="success"} 142

# TYPE inference_latency_seconds histogram
inference_latency_seconds_bucket{le="1.0"} 5
inference_latency_seconds_bucket{le="5.0"} 120
inference_latency_seconds_bucket{le="10.0"} 140
inference_latency_seconds_sum 567.5
inference_latency_seconds_count 142
```

### CloudWatch Integration

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

# Publicar métrica
cloudwatch.put_metric_data(
    Namespace='Vocalio/Workers',
    MetricData=[
        {
            'MetricName': 'InferenceLatency',
            'Value': latency_ms,
            'Unit': 'Milliseconds',
            'Dimensions': [
                {'Name': 'WorkerID', 'Value': worker_id},
                {'Name': 'Region', 'Value': 'rioplatense'}
            ]
        }
    ]
)
```

---

## 🚀 Escalabilidad y Resiliencia

### Auto-Scaling

**Políticas:**

1. **Target Tracking** (CPU):
   ```
   Si CPU > 70% durante 3 min → Scale out (+1 instancia)
   Si CPU < 30% durante 10 min → Scale in (-1 instancia)
   ```

2. **Target Tracking** (GPU):
   ```
   Si GPU util > 80% durante 5 min → Scale out
   Si GPU util < 20% durante 15 min → Scale in
   ```

3. **Basado en Cola**:
   ```
   Si pending_jobs > workers * 2 → Scale out
   Si pending_jobs == 0 durante 10 min → Scale in (hasta min)
   ```

### Manejo de Spot Interruptions

```python
async def monitor_spot_interruption():
    """Monitorear avisos de interrupción de Spot instance."""

    while True:
        # Consultar metadata endpoint
        try:
            response = await client.get(
                "http://169.254.169.254/latest/meta-data/spot/instance-action"
            )

            if response.status_code == 200:
                # Recibido aviso de terminación (2 min warning)
                logger.warning("Spot interruption inminente")

                # Iniciar graceful shutdown
                await graceful_shutdown(worker_service, timeout=120)
                break

        except Exception:
            pass  # No interruption

        await asyncio.sleep(5)  # Check cada 5s
```

### Circuit Breaker

```python
from resilience import CircuitBreaker

# Circuit breaker para backend
backend_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=30.0,
    half_open_max_calls=3
)

@backend_breaker.call
async def send_heartbeat():
    return await backend_client.post('/heartbeat', data=...)
```

### Retry con Backoff

```python
from resilience import retry_with_backoff

@retry_with_backoff(
    max_attempts=3,
    base_delay=1.0,
    max_delay=10.0,
    exponential_base=2.0
)
async def upload_result_to_s3(file_path, s3_key):
    await s3_client.upload_file(file_path, bucket, s3_key)
```

---

## 📚 Documentación Relacionada

- **[README.es.md](../../README.es.md)** - Documentación principal
- **[GUIA_TECNICA.md](GUIA_TECNICA.md)** - Componentes técnicos detallados
- **[../ARCHITECTURE.md](../ARCHITECTURE.md)** - Arquitectura interna (inglés)
- **[../DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)** - Guía de despliegue (inglés)
- **[../DOCKER_OPTIMIZATION.md](../DOCKER_OPTIMIZATION.md)** - Optimización Docker (inglés)

---

<div align="center">

**Parte del Ecosistema Vocalio**

**Spanish-F5 TTS Worker v1.0**

</div>
