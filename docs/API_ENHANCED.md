# Enhanced F5-TTS REST API Documentation

## Overview

The Enhanced F5-TTS REST API provides state-of-the-art Spanish text-to-speech with comprehensive quality improvements:

- **Text Normalization** - Converts numbers, dates, times to spoken Spanish
- **Prosody Analysis** - Detects questions, exclamations, emphasis, pauses
- **Breath & Pause Modeling** - Natural breathing and pause patterns
- **Adaptive NFE** - Automatic quality optimization based on text complexity
- **Adaptive Crossfade** - Dynamic crossfade duration for smoother audio
- **Audio Quality Check** - Reference audio quality validation

All enhancements are **enabled by default** and can be toggled per request.

## Base URL

```
http://localhost:8000
```

## Endpoints

### 1. Health Check

Check API status and loaded models.

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "models_loaded": ["F5-TTS"],
  "timestamp": "2025-10-08T12:00:00"
}
```

### 2. List Models

List available models and vocoders.

```http
GET /models
```

**Response:**
```json
{
  "available_models": ["F5-TTS", "E2-TTS"],
  "loaded_models": ["F5-TTS"],
  "vocoders": ["vocos", "bigvgan"]
}
```

### 3. Generate Speech (Enhanced)

Generate speech with all enhancements enabled.

```http
POST /tts
Content-Type: application/json
```

**Request Body:**
```json
{
  "gen_text": "El 15 de marzo de 2024 a las 14:30 horas",
  "ref_text": "",
  "model": "F5-TTS",
  "speed": 1.0,

  // Enhancement features (all default to true)
  "normalize_text": true,
  "analyze_prosody": true,
  "analyze_breath_pauses": true,
  "adaptive_nfe": true,
  "adaptive_crossfade": true,
  "check_audio_quality": true,

  // Advanced settings
  "nfe_step": 16,
  "cross_fade_duration": 0.8,
  "cfg_strength": 2.0,
  "seed": -1
}
```

**Response:**
- Binary audio file (WAV format)
- Header `X-Enhancement-Metadata` contains JSON with:

```json
{
  "normalized_text": "el quince de marzo de dos mil veinticuatro a las catorce y media",
  "prosody_analysis": {
    "num_questions": 0,
    "num_exclamations": 0,
    "num_pauses": 2,
    "sentence_count": 1,
    "breath_points": 0,
    "marked_text": "el quince de marzo... · a las catorce y media"
  },
  "breath_analysis": {
    "total_pauses": 5,
    "breath_points": 0,
    "avg_pause_interval": 12.5,
    "estimated_duration": 3.2
  },
  "audio_quality": {
    "overall_score": 92,
    "quality_level": "excellent",
    "snr_db": 38.5,
    "issues": [],
    "recommendations": []
  },
  "nfe_step_used": 16,
  "crossfade_duration_used": 0.8
}
```

### 4. Analyze Text (No TTS)

Analyze text without generating speech - useful for preprocessing.

```http
POST /analyze
Content-Type: application/json
```

**Request Body:**
```json
{
  "text": "¿Cuánto cuesta? ¡Son 25 euros!",
  "normalize_text": true,
  "analyze_prosody": true,
  "analyze_breath_pauses": true
}
```

**Response:**
```json
{
  "original_text": "¿Cuánto cuesta? ¡Son 25 euros!",
  "normalized_text": "¿Cuánto cuesta? ¡Son veinticinco euros!",
  "prosody_analysis": {
    "markers": [
      {
        "type": "FALLING_TONE",
        "position": 0,
        "text": "¿Cuánto cuesta?",
        "intensity": null
      },
      {
        "type": "EXCLAMATION_MEDIUM",
        "position": 16,
        "text": "¡Son veinticinco euros!",
        "intensity": "MEDIUM"
      }
    ],
    "marked_text": "¿Cuánto cuesta? ↘ | ¡Son veinticinco euros! ❗",
    "sentence_count": 2,
    "breath_points": 1,
    "stress_points": 2,
    "pitch_contours": ["falling", "rising_exclamation"]
  },
  "breath_analysis": {
    "pauses": [
      {
        "position": 15,
        "type": "long",
        "duration_ms": 600,
        "is_breath_point": true,
        "context": "¿Cuánto cuesta? ¡Son"
      }
    ],
    "breath_points": [15],
    "avg_pause_interval": 0,
    "estimated_duration": 2.5
  }
}
```

### 5. Check Audio Quality (No TTS)

Check audio quality without TTS - useful for validating reference audio.

```http
POST /audio/quality
Content-Type: multipart/form-data
```

**Form Data:**
- `audio_file`: Audio file to analyze

**Response:**
```json
{
  "filename": "reference.wav",
  "overall_score": 85,
  "quality_level": "good",
  "metrics": {
    "snr_db": 32.5,
    "clipping_rate": 0.0005,
    "silence_ratio": 0.12,
    "dynamic_range_db": 48.3,
    "spectral_flatness": 0.15
  },
  "issues": [
    "Moderate background noise (32.5 dB SNR)"
  ],
  "recommendations": [
    "Consider noise reduction processing"
  ]
}
```

### 6. Stream Speech

Stream speech output instead of downloading file.

```http
POST /tts/stream
Content-Type: application/json
```

Same request body as `/tts`, but streams audio instead of returning as download.

### 7. Upload Custom Reference Audio

Upload custom reference audio for TTS.

```http
POST /tts/upload
Content-Type: multipart/form-data
```

**Form Data:**
- `request`: JSON string with TTSRequest fields
- `ref_audio`: Reference audio file

**Response:**
```json
{
  "task_id": "abc123...",
  "status": "processing",
  "message": "TTS generation started"
}
```

Use `/tasks/{task_id}` to check status and `/audio/{task_id}` to download.

## Enhancement Features Explained

### Text Normalization

Converts written text to spoken form:

| Input | Normalized Output |
|-------|------------------|
| `15` | `quince` |
| `2024` | `dos mil veinticuatro` |
| `14:30` | `catorce y media` |
| `15/03/2024` | `quince de marzo de dos mil veinticuatro` |
| `€50` | `cincuenta euros` |
| `Dr.` | `Doctor` |
| `Sra.` | `Señora` |

### Prosody Analysis

Detects and marks prosodic features:

| Feature | Marker | Example |
|---------|--------|---------|
| Rising question | `↗` | `¿Vienes? ↗` |
| Falling question | `↘` | `¿Dónde estás? ↘` |
| Exclamation (high) | `❗❗` | `¡Qué increíble! ❗❗` |
| Exclamation (medium) | `❗` | `¡Genial! ❗` |
| Emphasis | `*palabra*` | `*muy* importante` |
| Long pause | `\|` | `Primero. \| Segundo.` |
| Short pause | `·` | `Hola · ¿cómo estás?` |

### Breath & Pause Modeling

Automatically detects natural breathing points based on:

- **Speaking duration** - Forces breath every 8-15 seconds
- **Punctuation** - Different pause durations:
  - Comma: 200ms
  - Semicolon: 400ms
  - Period: 600ms
  - Exclamation: 650ms
- **Conjunctions** - Micro-pauses (80ms) at "y", "pero", "aunque", etc.
- **Paragraphs** - Long pauses (1000ms) at paragraph breaks

### Adaptive NFE

Automatically adjusts NFE steps based on text complexity:

| Text Complexity | NFE Steps | Quality |
|----------------|-----------|---------|
| Short (< 50 chars) | 12-14 | Fast |
| Simple | 14-16 | Good |
| Medium | 16-20 | Better |
| Complex (questions, multiple sentences) | 20-32 | Best |

### Adaptive Crossfade

Adjusts crossfade duration based on context:

| Context | Duration | Use Case |
|---------|----------|----------|
| Continuous speech | 0.48s | Smooth flow |
| At pause/punctuation | 1.0s | Natural break |
| Default | 0.8s | Balanced |

### Audio Quality Check

Analyzes reference audio across 5 metrics:

| Metric | Excellent | Good | Fair | Poor |
|--------|-----------|------|------|------|
| SNR | > 35 dB | 25-35 dB | 15-25 dB | < 15 dB |
| Clipping | < 0.1% | 0.1-0.5% | 0.5-1% | > 1% |
| Silence | < 15% | 15-30% | 30-50% | > 50% |
| Dynamic Range | > 40 dB | 30-40 dB | 20-30 dB | < 20 dB |

## Python Client Example

```python
import requests

# Basic TTS with all enhancements
response = requests.post(
    "http://localhost:8000/tts",
    json={
        "gen_text": "¿Tienes 15 euros? ¡Necesito comprar algo!",
        "ref_text": "",
        # All enhancements enabled by default
    }
)

# Save audio
with open("output.wav", "wb") as f:
    f.write(response.content)

# Get enhancement metadata
import json
metadata = json.loads(response.headers["X-Enhancement-Metadata"])
print(f"Normalized: {metadata['normalized_text']}")
print(f"NFE steps used: {metadata['nfe_step_used']}")
```

## Using the Enhanced CLI Client

```bash
# Install client
chmod +x examples/api_client_enhanced.py

# Check health
python examples/api_client_enhanced.py health

# Analyze text
python examples/api_client_enhanced.py analyze "¿Cuánto cuesta? ¡25 euros!"

# Check audio quality
python examples/api_client_enhanced.py quality reference.wav

# Generate speech with all enhancements
python examples/api_client_enhanced.py tts \
  "El 15 de marzo a las 14:30 tengo una reunión" \
  -o output.wav

# Generate with custom settings
python examples/api_client_enhanced.py tts \
  "Texto complejo con múltiples oraciones y preguntas" \
  --nfe-step 20 \
  --speed 0.9 \
  -o output.wav
```

## curl Examples

### Basic TTS
```bash
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{
    "gen_text": "Hola, ¿cómo estás?",
    "ref_text": ""
  }' \
  -o output.wav
```

### Text Analysis Only
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "¿Tienes 25 euros?",
    "normalize_text": true,
    "analyze_prosody": true,
    "analyze_breath_pauses": true
  }' | jq
```

### Audio Quality Check
```bash
curl -X POST http://localhost:8000/audio/quality \
  -F "audio_file=@reference.wav" | jq
```

### TTS with Custom Settings
```bash
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{
    "gen_text": "El 15/03/2024 a las 14:30",
    "ref_text": "",
    "normalize_text": true,
    "adaptive_nfe": true,
    "adaptive_crossfade": true,
    "nfe_step": 16,
    "speed": 1.0
  }' \
  -o output.wav -D headers.txt

# View enhancement metadata
cat headers.txt | grep X-Enhancement-Metadata
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK` - Success
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

Error responses include details:
```json
{
  "detail": "Model F5-TTS not loaded"
}
```

## Performance Tips

1. **Use adaptive features** - Let the system optimize NFE and crossfade
2. **Check audio quality first** - Validate reference audio before processing large batches
3. **Analyze text separately** - Use `/analyze` to preview normalization and prosody
4. **Disable unused features** - Set feature flags to `false` if not needed
5. **Adjust NFE for speed** - Lower NFE (12-14) for faster, higher (20-32) for better quality

## Docker Deployment

The enhanced API is fully compatible with the existing Docker setup:

```bash
# Build with production target
docker build --target production -t f5-tts-enhanced .

# Run with GPU
docker run --gpus all -p 8000:8000 f5-tts-enhanced

# Test
curl http://localhost:8000/health
```

## Limitations

- Maximum text length: ~5000 characters (will be chunked)
- Supported audio formats: WAV, MP3, FLAC
- Reference audio: 24kHz recommended, will be resampled if different
- Concurrent requests: Limited by GPU memory

## See Also

- [Audio Quality Guide](AUDIO_QUALITY_GUIDE.md) - Detailed quality metrics
- [Prosody Guide](PROSODY_GUIDE.md) - Prosodic features explained
- [Spanish Regional Guide](SPANISH_REGIONAL_GUIDE.md) - Regional accent support
- [Architecture](../ARCHITECTURE.md) - System architecture
