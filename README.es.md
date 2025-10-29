# Spanish-F5 TTS 🗣️🇪🇸

> **Sistema avanzado de Texto-a-Voz con soporte completo para variantes regionales del español**

Spanish-F5 es un sistema de síntesis de voz (TTS) de alta calidad para español basado en F5-TTS, con soporte realista para acentos regionales latinoamericanos, modelado avanzado de prosodia y rendimiento de inferencia optimizado.

[![Tests](https://img.shields.io/badge/tests-287%20passing-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-60%25-yellow)](tests/)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 📖 Tabla de Contenidos

- [Propósito en el Ecosistema Vocalio](#-propósito-en-el-ecosistema-vocalio)
- [Características Principales](#-características-principales)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Componentes Clave](#-componentes-clave)
- [Instalación](#-instalación)
- [Inicio Rápido](#-inicio-rápido)
- [Características Regionales](#-características-regionales-del-español)
- [API REST](#-api-rest)
- [Integración con Backend](#-integración-con-backend-vocalio)
- [Despliegue en Producción](#-despliegue-en-producción)
- [Rendimiento y Optimizaciones](#-rendimiento-y-optimizaciones)
- [Testing](#-testing)
- [Documentación](#-documentación)

---

## 🎯 Propósito en el Ecosistema Vocalio

**Spanish-F5** es el motor de síntesis de voz del ecosistema **Vocalio**, una plataforma distribuida de inteligencia artificial para procesamiento de voz y audio en español.

### Rol en el Ecosistema

```
┌─────────────────────────────────────────────────────────────────┐
│                    ECOSISTEMA VOCALIO                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐         ┌──────────────┐                    │
│  │   Backend    │◄────────┤   Spanish-F5 │  (Motor TTS)       │
│  │  Aithentia   │         │   GPU Worker │                    │
│  └──────┬───────┘         └──────┬───────┘                    │
│         │                         │                             │
│         │                         │                             │
│         │  Gestión de Tareas      │  Inferencia GPU            │
│         │  Coordinación           │  - F5-TTS (síntesis)       │
│         │  Distribución de Carga  │  - Whisper (transcripción) │
│         │                         │                             │
│         ▼                         ▼                             │
│  ┌──────────────┐         ┌──────────────┐                    │
│  │  Worker UI   │         │   Modelos    │                    │
│  │  Dashboard   │         │   Pre-train  │                    │
│  └──────────────┘         └──────────────┘                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Comunicación:
  ↕  REST API + Heartbeat (NAT-friendly)
  →  GPU Inference (CUDA-accelerated)
  ⚡ AWS ECS Spot Instances (60-70% ahorro)
```

### Funcionalidad Principal

Spanish-F5 actúa como **worker GPU especializado** que:

1. **Se registra automáticamente** con el backend de Vocalio
2. **Recibe tareas** de síntesis de voz a través del sistema de heartbeat
3. **Procesa texto en español** con detección automática de variantes regionales
4. **Genera audio de alta calidad** usando modelos Diffusion Transformer
5. **Reporta métricas** de uso de GPU, latencia y calidad al coordinador

### Ventajas Clave

- ✅ **Acentos auténticos**: 6 variantes regionales latinoamericanas
- ✅ **Calidad superior**: Basado en research papers académicos para prosodia
- ✅ **Bajo costo**: Despliegue en AWS Spot instances (~$110-180/mes)
- ✅ **Escalable**: Compatible con NAT/firewalls mediante heartbeat polling
- ✅ **Monitoreable**: Integración completa con sistema de métricas

---

## 🌟 Características Principales

### 🌎 Soporte Regional del Español

- **6 Variantes Regionales**: Rioplatense (🇦🇷🇺🇾), Colombiano (🇨🇴), Mexicano (🇲🇽), Chileno (🇨🇱), Caribeño, Andino
- **Detección Automática de Acento**: Analiza texto en busca de marcadores regionales (jerga, sintaxis)
- **Transformaciones Fonéticas**: Sheísmo, yeísmo, aspiración de /s/, y más
- **Patrones Prosódicos**: Entonación, acentuación y ritmo específicos por región
- **Soporte de Voseo**: Conjugaciones auténticas argentinas/uruguayas (vos sos, tenés, querés)
- **Prosodia Empírica**: Basada en investigación académica (Cuello & Oro Ozán 2024, Guglielmone et al. 2014)

### 🎯 Características TTS Avanzadas

- **Diffusion Transformer (DiT)** y arquitecturas **Flat-UNet**
- **Flow Matching** para síntesis de alta calidad
- **Sway Sampling**: Optimización en tiempo de inferencia
- **Multi-Estilo/Multi-Hablante**: Generación de voces diversas
- **Inferencia por Chunks**: Procesamiento eficiente de textos largos
- **Prosodia a nivel de discurso**: Unidades de declinación y configuraciones de tono nuclear

### 🚀 Optimizaciones de Rendimiento

- **Pasos NFE Adaptativos**: Balance calidad-velocidad basado en complejidad del texto
- **Crossfading Mejorado**: Transiciones suaves (Equal Power, Raised Cosine, Linear)
- **Soporte torch.compile**: Hasta 40% más rápido en GPUs compatibles
- **Detección de Calidad de Audio**: Detección y prevención automática de artefactos
- **Modelado de Respiración y Pausas**: Ritmo de habla natural

### 🛠️ Listo para Producción

- **API REST**: Servidor basado en FastAPI con soporte de streaming
- **Soporte Docker**: Builds multi-etapa para desarrollo y producción
- **Testing Comprensivo**: 287 tests con 60% de cobertura de código
- **Arquitectura Modular**: Separación limpia de responsabilidades
- **Integración AWS**: Despliegue automático en ECS con Spot instances

---

## 🏗️ Arquitectura del Sistema

### Diagrama de Componentes

```
┌────────────────────────────────────────────────────────────────┐
│                      Spanish-F5 TTS System                      │
└────────────────────────────────────────────────────────────────┘

┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│   Entrada de    │────▶│  Procesamiento   │────▶│   Modelo    │
│     Texto       │     │    de Texto      │     │   DiT/UNet  │
└─────────────────┘     └──────────────────┘     └─────────────┘
                                │                        │
                                │                        │
                        ┌───────▼────────┐       ┌──────▼──────┐
                        │   Regional     │       │    Flow     │
                        │   Processor    │       │  Matching   │
                        └────────────────┘       └─────────────┘
                                                         │
                                                         │
┌─────────────────┐     ┌──────────────────┐     ┌─────▼───────┐
│   Audio de      │◀────│  Post-Proceso    │◀────│   Vocoder   │
│    Salida       │     │    de Audio      │     │   (Vocos)   │
└─────────────────┘     └──────────────────┘     └─────────────┘
```

### Flujo de Procesamiento

1. **Entrada de Texto** → Texto en español con marcadores regionales opcionales
2. **Procesamiento Regional** → Detección automática de variante + transformaciones fonéticas
3. **Análisis Prosódico** → Marcadores de entonación, acentuación, pausas
4. **Modelo de Difusión** → DiT/UNetT genera mel-espectrograma
5. **Vocoder** → Vocos convierte espectrograma a forma de onda
6. **Post-Procesamiento** → Normalización, crossfading, control de calidad

---

## 🔧 Componentes Clave

### 1. Procesador Regional de Español (`src/f5_tts/text/spanish_regional.py`)

Motor central para manejo de variantes regionales del español:

```python
from f5_tts.text import process_spanish_text

# Procesar español rioplatense con prosodia empírica
result = process_spanish_text(
    "Che boludo, ¿vos querés tomar unos mates?",
    region="rioplatense",
    apply_phonetics=True
)

# Resultado incluye:
# - detected_region: "rioplatense"
# - slang_markers: ["che", "boludo", "vos", "querés"]
# - phonetic transformations: sheísmo, voseo
# - prosodic_profile: pace=0.75x, F0_range=[75-340Hz]
```

**Componentes:**
- `SpanishRegionalProcessor`: Clase principal de procesamiento
- `RegionalPhonetics`: Reglas de transformación fonética
- `RegionalProsody`: Detección de patrones prosódicos con perfiles validados empíricamente
- `RegionalProsodicProfile`: Perfiles prosódicos completos basados en investigación académica
- `RegionalSlang`: Diccionarios de jerga por región

### 2. Motor de Síntesis (`src/f5_tts/infer/utils_infer.py`)

Lógica de inferencia central con optimizaciones CUDA:

```python
from f5_tts.api import F5TTS

# Inicializar motor TTS
tts = F5TTS(
    model_type="F5-TTS",
    vocoder_name="vocos",
    device="cuda"
)

# Generar audio
wav, sr, spect = tts.infer(
    ref_file="reference.wav",
    ref_text="Audio de referencia",
    gen_text="Texto a sintetizar",
    nfe_step=16,  # Velocidad/calidad ajustable
    seed=42
)
```

**Características:**
- Soporte torch.compile para inferencia acelerada
- Pasos NFE adaptativos (8-64 pasos)
- Procesamiento por chunks para textos largos
- Control de crossfading configurable

### 3. API REST (`src/f5_tts/rest_api/`)

Arquitectura modular refactorizada para servir TTS:

```
src/f5_tts/rest_api/
├── app.py              # Creación de app FastAPI y startup
├── config.py           # Configuración de API
├── state.py            # Gestión de estado global
├── models.py           # Modelos Pydantic request/response
├── enhancements.py     # Procesamiento de mejoras
├── tts_processor.py    # Lógica de generación TTS
└── routes/             # Manejadores de endpoints
    ├── tts.py          # Endpoints principales de TTS
    ├── upload.py       # Endpoints de carga de archivos
    ├── tasks.py        # Gestión de tareas
    └── analysis.py     # Endpoints de análisis
```

**Endpoints Principales:**
- `POST /tts` - Generar voz desde texto
- `POST /analyze` - Analizar texto sin generar audio
- `GET /health` - Health check del servicio
- `GET /audio/{task_id}` - Descargar audio generado

### 4. Pipeline de Audio (`src/f5_tts/audio/`)

Procesamiento profesional de audio con múltiples algoritmos:

```python
from f5_tts.audio import (
    EqualPowerCrossfader,
    AudioProcessingPipeline,
    AudioQualityAnalyzer
)

# Pipeline completo
pipeline = AudioProcessingPipeline([
    remove_dc_offset,
    normalize_rms,
    resample_audio,
    prevent_clipping
])

# Análisis de calidad
analyzer = AudioQualityAnalyzer()
quality = analyzer.analyze("output.wav")
# quality.overall_level: EXCELLENT/GOOD/FAIR/POOR
```

**Componentes:**
- Crossfading: Equal Power (estándar industria), Raised Cosine, Linear
- Normalización: RMS, peak limiting, DC offset removal
- Resampling: Kaiser window para alta calidad
- Quality Analysis: SNR, clipping, dynamic range

### 5. Sistema de Configuración (`src/f5_tts/core/config.py`)

Singleton de configuración global con soporte de variables de entorno:

```python
from f5_tts.core import GlobalConfig

config = GlobalConfig()

# Optimizaciones CUDA
config.enable_torch_compile = True
config.enable_cudnn_benchmark = True
config.torch_matmul_precision = "high"  # TF32 en GPUs Ampere+

# Audio settings
config.target_sample_rate = 24000
config.hop_length = 256
config.n_fft = 1024
```

### 6. Cliente de Integración Backend (`backend_integration.py`)

Cliente Python para comunicación con el backend de Vocalio:

```python
from backend_integration import GPUInferenceClient

# Inicializar cliente
client = GPUInferenceClient(
    f5_tts_url="http://alb-url.amazonaws.com"
)

# Generar voz
audio = await client.generate_speech(
    text="Hola amigo, ¿cómo estás?",
    region="rioplatense",
    nfe_step=16
)

# Analizar texto
analysis = await client.analyze_text(
    "Che boludo, vení acá",
    region="auto"
)
```

---

## 📦 Instalación

### Prerequisitos

- Python 3.10+
- GPU compatible con CUDA (recomendado)
- 8GB+ VRAM de GPU para inferencia

### Opción 1: Instalación Rápida (Pip)

```bash
# Crear ambiente conda
conda create -n f5-tts python=3.10
conda activate f5-tts

# Instalar PyTorch con soporte CUDA
pip install torch==2.3.0+cu118 torchaudio==2.3.0+cu118 --extra-index-url https://download.pytorch.org/whl/cu118

# Instalar Spanish-F5
pip install git+https://github.com/jpgallegoar/Spanish-F5.git
```

### Opción 2: Instalación para Desarrollo

```bash
# Clonar repositorio
git clone https://github.com/jpgallegoar/Spanish-F5.git
cd Spanish-F5

# Crear ambiente
conda create -n f5-tts python=3.10
conda activate f5-tts

# Instalar PyTorch
pip install torch==2.3.0+cu118 torchaudio==2.3.0+cu118 --extra-index-url https://download.pytorch.org/whl/cu118

# Instalar en modo editable
pip install -e .

# Herramientas de desarrollo (opcional)
pip install pre-commit
pre-commit install
```

### Opción 3: Docker

```bash
# Build imagen
docker build -t spanish-f5-tts .

# Ejecutar contenedor con soporte GPU
docker run --gpus all -p 8000:8000 spanish-f5-tts
```

---

## 🚀 Inicio Rápido

### 1. Interfaz Web Gradio

```bash
# Lanzar interfaz web
f5-tts_infer-gradio

# Puerto/host personalizado
f5-tts_infer-gradio --port 7860 --host 0.0.0.0

# Link público para compartir
f5-tts_infer-gradio --share
```

### 2. Inferencia CLI

```bash
# Uso básico
f5-tts_infer-cli \
  --model "F5-TTS" \
  --ref_audio "ref_audio.wav" \
  --ref_text "Texto de referencia" \
  --gen_text "Texto a sintetizar"

# Con archivo de configuración
f5-tts_infer-cli -c config.toml
```

### 3. API Python

```python
from f5_tts.api import F5TTS

# Inicializar motor TTS
tts = F5TTS(model_type="F5-TTS")

# Generar voz
wav, sr, spect = tts.infer(
    ref_file="reference.wav",
    ref_text="Transcripción de audio de referencia",
    gen_text="¡Hola! Esta es una prueba del TTS Spanish F5.",
    file_wave="output.wav",
    seed=42
)
```

---

## 🌎 Características Regionales del Español

Spanish-F5 incluye soporte completo para variantes regionales latinoamericanas con acentos, prosodia y jerga auténticos.

### Regiones Soportadas

| Región | Código | Características | Marcadores de Ejemplo |
|--------|------|----------|-----------------|
| 🇦🇷🇺🇾 **Rioplatense** | `rioplatense` | Sheísmo, voseo, aspiración /s/ | che, boludo, vos, sos |
| 🇨🇴 **Colombiano** | `colombian` | Articulación clara, ritmo paisa | parcero, chimba, ¿sí? |
| 🇲🇽 **Mexicano** | `mexican` | Entonación distintiva, diminutivos | órale, ahorita, -ito |
| 🇨🇱 **Chileno** | `chilean` | Habla rápida, jerga | po', cachai, fome |
| 🌴 **Caribeño** | `caribbean` | Ritmo costero, aspiración | ¿tú sabes?, chévere |
| ⛰️ **Andino** | `andean` | Patrones de tierras altas | pues, nomás |

### Ejemplos de Uso

#### Detección Automática

```python
from f5_tts.text import process_spanish_text

# Detecta automáticamente la región desde la jerga
result = process_spanish_text(
    "Che boludo, ¿vos querés tomar unos mates?",
    auto_detect=True
)
print(result.detected_region)  # "rioplatense"
print(result.slang_markers)    # ["che", "boludo", "vos", "querés"]
```

#### Procesamiento Regional

```python
# Rioplatense (Argentina/Uruguay)
result = process_spanish_text(
    "¿Vos sabés dónde está el colectivo?",
    region="rioplatense",
    apply_phonetics=True
)
# Aplica: sheísmo (ll/y → sh), patrones de acentuación voseo

# Colombiano
result = process_spanish_text(
    "Parcero, eso está muy bacano, ¿sí?",
    region="colombian"
)
# Detecta: parcero, bacano, coletilla ¿sí?

# Mexicano
result = process_spanish_text(
    "Órale güey, ahorita vengo",
    region="mexican"
)
# Detecta: órale, güey, ahorita (sentido diminutivo)
```

### Prosodia Empírica

Todos los perfiles prosódicos están basados en investigación académica:

- **Rioplatense**: Ritmo lento (0.75x), doble acentuación, cualidad quejumbrosa
  - Cuello & Oro Ozán (2024): Mediciones de prosodia T.E.P.HA
  - Rango F0: 75-340Hz (femenino), 75-200Hz (masculino)

- **Colombiano**: Ritmo medio, articulación clara, prosodia neutral

- **Mexicano**: Ritmo medio, contornos melódicos, entonación expresiva

Ver [docs/PROSODY_ANALYSIS_ACADEMIC_PAPERS.md](docs/PROSODY_ANALYSIS_ACADEMIC_PAPERS.md) para detalles completos.

---

## 🌐 API REST

### Iniciar el Servidor

```bash
# Modo desarrollo
python f5_tts_api.py

# Modo producción con gunicorn
gunicorn f5_tts_api:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Docker
docker run --gpus all -p 8000:8000 spanish-f5-tts
```

### Endpoints de API

#### POST `/tts` - Generar Voz

```bash
curl -X POST "http://localhost:8000/tts" \
  -F "gen_text=Hola, esto es una prueba" \
  -F "ref_audio=@reference.wav" \
  -F "ref_text=Texto de referencia" \
  -F "nfe_step=32" \
  -F "normalize_text=true" \
  -F "analyze_prosody=true" \
  --output output.wav
```

```python
import requests

response = requests.post(
    "http://localhost:8000/tts",
    files={"ref_audio": open("reference.wav", "rb")},
    data={
        "gen_text": "¿Cómo estás? ¡Muy bien!",
        "ref_text": "Transcripción de referencia",
        "nfe_step": 32,
        "normalize_text": True,
        "analyze_prosody": True,
        "adaptive_nfe": True,
        "check_audio_quality": True
    }
)

with open("output.wav", "wb") as f:
    f.write(response.content)
```

#### POST `/analyze` - Análisis de Texto

```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Che boludo, ¿vos querés tomar unos mates?",
    "normalize_text": true,
    "analyze_prosody": true,
    "analyze_breath_pauses": true
  }'
```

#### GET `/health` - Health Check

```bash
curl "http://localhost:8000/health"
# {"status": "healthy", "model_loaded": true}
```

Ver [docs/API_REFERENCE.md](docs/API_REFERENCE.md) para documentación completa de endpoints.

---

## 🔌 Integración con Backend Vocalio

Spanish-F5 se integra con el ecosistema Vocalio como worker GPU especializado.

### Cliente de Integración

```python
from backend_integration import GPUInferenceClient

# Inicializar cliente con URL del ALB
client = GPUInferenceClient(
    f5_tts_url="http://gpu-spot-stack-alb-xyz.us-east-1.elb.amazonaws.com"
)

# Health check
health = await client.health_check()
print(f"Estado TTS: {health['status']}")
print(f"Modelos cargados: {health['models_loaded']}")

# Analizar texto (rápido, sin generar audio)
analysis = await client.analyze_text(
    "Che boludo, ¿vos querés tomar unos mates?",
    region="auto"
)
print(f"Región detectada: {analysis['detected_region']}")
print(f"Marcadores de jerga: {analysis['slang_markers']}")

# Generar voz
audio = await client.generate_speech(
    text="Hola amigo, ¿cómo estás hoy?",
    region="rioplatense",
    nfe_step=16,  # Inferencia rápida
    speed=1.0,
    output_path=Path("output.wav")
)
print(f"Audio generado: {len(audio)} bytes")
```

### Integración FastAPI

```python
from fastapi import FastAPI, HTTPException
from backend_integration import GPUInferenceClient

app = FastAPI()

# Inicializar cliente
tts_client = GPUInferenceClient(
    f5_tts_url=os.getenv("F5_TTS_ENDPOINT")
)

@app.post("/api/tts/generate")
async def generate_tts(text: str, region: str = "rioplatense"):
    try:
        audio_bytes = await tts_client.generate_speech(
            text=text,
            region=region,
            nfe_step=16
        )
        return Response(content=audio_bytes, media_type="audio/wav")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"TTS service error: {str(e)}")
```

### Variables de Entorno

```bash
# Agregar a .env del backend
F5_TTS_ENDPOINT=http://<ALB-DNS>
TTS_TIMEOUT=30
TTS_DEFAULT_REGION=rioplatense
TTS_DEFAULT_NFE_STEP=16
```

---

## 🚀 Despliegue en Producción

### AWS ECS con Spot Instances

```bash
# Desplegar stack completo
./deploy-gpu-spot.sh

# Lo que se despliega:
# - CloudFormation stack con instancias g5.xlarge/g4dn.xlarge Spot (2 instancias)
# - Application Load Balancer con health checks
# - ECS Capacity Provider para auto-scaling
# - Costo: ~$0.15-0.25/hora (~$110-180/mes) - 60-70% ahorro vs On-Demand
# - Stack name: gpu-spot-stack
# - Cluster: dev-vocalio-chatterbox
# - Service: f5-tts-spot-service
```

### Monitorear Despliegue

```bash
# Describir servicio
aws ecs describe-services \
  --cluster dev-vocalio-chatterbox \
  --services f5-tts-spot-service \
  --region us-east-1

# Ver logs
aws logs tail /ecs/dev-f5-tts --follow --region us-east-1

# Verificar integración con backend
curl https://api.test.aithentia.com:8000/workers
```

### Build y Push de Docker

```bash
# Imagen de desarrollo
./docker-build.sh latest base

# Imagen de producción (optimizada)
./docker-build.sh latest production

# Build y push a ECR
./docker-build.sh latest production --push
```

Ver [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) y [docs/DOCKER_OPTIMIZATION.md](docs/DOCKER_OPTIMIZATION.md) para guías completas.

---

## ⚡ Rendimiento y Optimizaciones

### Características de Optimización

- **torch.compile**: Habilitar con `ENABLE_TORCH_COMPILE=true`
- **cuDNN Benchmark**: Habilitar con `ENABLE_CUDNN_BENCHMARK=true`
- **Precisión TF32**: Configurar `TORCH_MATMUL_PRECISION=high` (GPUs Ampere+)
- **NFE Adaptativo**: Balance automático calidad-velocidad
- **Audio de Referencia Corto**: Usar clips de 6s para procesamiento más rápido

### Variables de Entorno

```bash
export ENABLE_TORCH_COMPILE=true
export ENABLE_CUDNN_BENCHMARK=true
export TORCH_MATMUL_PRECISION=high
```

### Benchmarks

| Configuración | Pasos NFE | GPU | Tiempo (audio 10s) |
|--------------|-----------|-----|------------------|
| Calidad | 32 | RTX 3090 | ~8s |
| Balanceado | 16 | RTX 3090 | ~4s |
| Rápido | 8 | RTX 3090 | ~2s |

---

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
pytest tests/ -v

# Módulo específico
pytest tests/test_spanish_regional.py -v

# Con cobertura
pytest --cov=src/f5_tts --cov-report=html tests/

# Análisis de cobertura
python analyze_coverage.py
```

### Suite de Tests

- **287 tests** con **60% cobertura de código**
- Español Regional: Fonética, jerga, prosodia
- Procesamiento de Audio: Crossfading, normalización, calidad
- Procesamiento de Texto: Normalización, chunking, análisis de respiración
- API: Inicialización, inferencia, export

---

## 📚 Documentación

### Guías de Usuario (Español)

- **[Documentación Principal (README.es.md)](README.es.md)** - Esta documentación
- **[Guía de Arquitectura del Ecosistema](docs/es/ARQUITECTURA_ECOSISTEMA.md)** - Integración Vocalio
- **[Guía Técnica Detallada](docs/es/GUIA_TECNICA.md)** - Componentes internos

### Guías de Usuario (Inglés)

- **[Regional Spanish Guide](docs/SPANISH_REGIONAL_GUIDE.md)** - Características regionales completas
- **[Quick Reference](docs/REGIONAL_QUICK_REFERENCE.md)** - Patrones comunes
- **[Getting Started](docs/GETTING_STARTED_REGIONAL.md)** - Tutorial

### Documentación Técnica

- **[Architecture](docs/ARCHITECTURE.md)** - Diseño del sistema y módulos
- **[API Documentation](docs/API_REFERENCE.md)** - Referencia REST API
- **[Docker Optimization](docs/DOCKER_OPTIMIZATION.md)** - Optimización de builds
- **[Prosody Guide](docs/PROSODY_GUIDE.md)** - Características prosódicas
- **[Audio Quality Guide](docs/AUDIO_QUALITY_GUIDE.md)** - Análisis de calidad

### Desarrollo

- **[CLAUDE.md](CLAUDE.md)** - Guías de desarrollo para Claude Code
- **[Training Guide](src/f5_tts/train/README.md)** - Entrenamiento y finetuning

---

## 🙏 Agradecimientos

### F5-TTS Original
- **Paper E2-TTS**: [arXiv:2406.18009](https://arxiv.org/abs/2406.18009)
- **Repositorio F5-TTS**: [SWivid/F5-TTS](https://github.com/SWivid/F5-TTS)

### Datasets y Modelos
- **Emilia**: [arXiv:2407.05361](https://arxiv.org/abs/2407.05361)
- **WenetSpeech4TTS**: [arXiv:2406.05763](https://arxiv.org/abs/2406.05763)
- **Modelo Español**: [jpgallegoar/F5-Spanish](https://huggingface.co/jpgallegoar/F5-Spanish/)

### Investigación Prosódica
- **Cuello & Oro Ozán (2024)**: Prosodia rioplatense T.E.P.HA
- **Guglielmone et al. (2014)**: Prosodia a nivel de discurso

---

## 📄 Licencia

Este proyecto está liberado bajo la **Licencia MIT**. Ver [LICENSE](LICENSE) para detalles.

**Modelos pre-entrenados** están licenciados bajo CC-BY-NC debido al dataset de entrenamiento Emilia.

---

<div align="center">

**Hecho con ❤️ para la comunidad TTS de habla hispana**

**Parte del ecosistema Vocalio**

[⬆ Volver Arriba](#spanish-f5-tts-)

</div>
