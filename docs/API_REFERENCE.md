# Spanish-F5 TTS API Reference 📚

Complete API documentation for Spanish-F5 TTS system, including Python API, REST API, and CLI tools.

---

## Table of Contents

- [Python API](#python-api)
  - [F5TTS Class](#f5tts-class)
  - [Text Processing](#text-processing)
  - [Audio Processing](#audio-processing)
  - [Quality Analysis](#quality-analysis)
- [REST API](#rest-api)
  - [Endpoints](#endpoints)
  - [Request/Response Models](#requestresponse-models)
  - [Error Handling](#error-handling)
- [CLI Tools](#cli-tools)

---

## Python API

### F5TTS Class

Main interface for TTS inference.

#### Initialization

```python
from f5_tts.api import F5TTS

tts = F5TTS(
    model_type="F5-TTS",      # Model architecture
    ckpt_file="",             # Custom checkpoint (optional)
    vocab_file="",            # Custom vocabulary (optional)
    ode_method="euler",       # ODE solver method
    use_ema=True,             # Use EMA weights
    vocoder_name="vocos",     # Vocoder type
    local_path=None,          # Local vocoder path
    device=None               # Device (auto-detect if None)
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_type` | `str` | `"F5-TTS"` | Model architecture: `"F5-TTS"` (DiT) or `"E2-TTS"` (UNetT) |
| `ckpt_file` | `str` | `""` | Path to custom checkpoint (auto-downloads if empty) |
| `vocab_file` | `str` | `""` | Path to custom vocabulary file |
| `ode_method` | `str` | `"euler"` | ODE solver: `"euler"`, `"midpoint"`, `"rk4"` |
| `use_ema` | `bool` | `True` | Use exponential moving average weights |
| `vocoder_name` | `str` | `"vocos"` | Vocoder type: `"vocos"` or `"bigvgan"` |
| `local_path` | `str\|None` | `None` | Local path for vocoder files |
| `device` | `str\|None` | `None` | Device: `"cuda"`, `"cpu"`, `"mps"` (auto-detect if None) |

**Environment Variables:**

```bash
# Enable torch.compile for faster inference (requires PyTorch 2.0+)
export ENABLE_TORCH_COMPILE=true

# Enable cuDNN auto-tuning
export ENABLE_CUDNN_BENCHMARK=true

# TF32 precision for Ampere+ GPUs
export TORCH_MATMUL_PRECISION=high
```

#### Inference

```python
wav, sample_rate, spectrogram = tts.infer(
    ref_file,                 # Reference audio path
    ref_text,                 # Reference text
    gen_text,                 # Text to generate
    show_info=print,          # Progress callback
    progress=tqdm,            # Progress bar
    target_rms=0.1,           # Volume normalization
    cross_fade_duration=0.15, # Crossfade duration (seconds)
    sway_sampling_coef=-1,    # Sway sampling coefficient
    cfg_strength=2.0,         # Classifier-free guidance
    nfe_step=32,              # Number of function evaluations
    speed=1.0,                # Speech rate multiplier
    fix_duration=None,        # Fixed duration (seconds)
    remove_silence=False,     # Remove silence from output
    file_wave=None,           # Output WAV path
    file_spect=None,          # Output spectrogram path
    seed=-1                   # Random seed (-1 for random)
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ref_file` | `str` | *required* | Path to reference audio (WAV) |
| `ref_text` | `str` | *required* | Reference audio transcription |
| `gen_text` | `str` | *required* | Text to synthesize |
| `show_info` | `Callable` | `print` | Progress callback function |
| `progress` | `Callable` | `tqdm` | Progress bar class |
| `target_rms` | `float` | `0.1` | Target RMS for normalization (0.0-1.0) |
| `cross_fade_duration` | `float` | `0.15` | Crossfade duration between chunks (seconds) |
| `sway_sampling_coef` | `float` | `-1` | Sway sampling coefficient (-1 to disable) |
| `cfg_strength` | `float` | `2.0` | Classifier-free guidance strength (1.0-5.0) |
| `nfe_step` | `int` | `32` | NFE steps (8-64, higher=better quality) |
| `speed` | `float` | `1.0` | Speech rate (0.5-2.0) |
| `fix_duration` | `float\|None` | `None` | Fixed duration in seconds |
| `remove_silence` | `bool` | `False` | Remove leading/trailing silence |
| `file_wave` | `str\|None` | `None` | Save output to WAV file |
| `file_spect` | `str\|None` | `None` | Save spectrogram to PNG file |
| `seed` | `int` | `-1` | Random seed for reproducibility |

**Returns:**

- `wav` (`np.ndarray`): Audio waveform (float32, 24kHz)
- `sample_rate` (`int`): Sample rate (24000)
- `spectrogram` (`np.ndarray`): Mel spectrogram

**Example:**

```python
from f5_tts.api import F5TTS

tts = F5TTS(model_type="F5-TTS", device="cuda")

# High-quality synthesis
wav, sr, spect = tts.infer(
    ref_file="reference.wav",
    ref_text="This is my reference voice.",
    gen_text="Hello world! This is Spanish F5 TTS.",
    nfe_step=32,
    cfg_strength=2.0,
    file_wave="output.wav",
    seed=42
)

# Fast synthesis (lower quality)
wav, sr, spect = tts.infer(
    ref_file="reference.wav",
    ref_text="Reference text",
    gen_text="Quick test",
    nfe_step=16,
    cross_fade_duration=0.1,
    seed=42
)
```

#### Export Methods

```python
# Export audio to file
tts.export_wav(
    wav,                # Waveform array
    file_path,          # Output path
    remove_silence=False  # Remove silence
)

# Export spectrogram to image
tts.export_spectrogram(
    spectrogram,        # Spectrogram array
    file_path           # Output path (PNG)
)
```

---

### Text Processing

#### Regional Spanish Processing

```python
from f5_tts.text import process_spanish_text, SpanishRegionalProcessor

# High-level API
result = process_spanish_text(
    text="Che boludo, ¿vos querés tomar unos mates?",
    region="rioplatense",      # Regional variant
    auto_detect=False,         # Auto-detect region
    apply_phonetics=True,      # Apply phonetic transformations
    apply_prosody=True         # Add prosodic markers
)

# Low-level API
processor = SpanishRegionalProcessor(region="rioplatense")
result = processor.process(text, apply_phonetics=True)
```

**Result Object:**

```python
result.text               # Processed text
result.original_text      # Original input
result.region             # Selected region
result.detected_region    # Auto-detected region (if enabled)
result.slang_markers      # List of detected slang terms
result.phonetic_changes   # List of phonetic transformations
result.prosodic_markers   # List of prosodic patterns
result.metadata           # Additional metadata
```

**Supported Regions:**

- `rioplatense` - Argentina/Uruguay
- `colombian` - Colombia
- `mexican` - Mexico
- `chilean` - Chile
- `caribbean` - Caribbean
- `andean` - Andean region

#### Text Normalization

```python
from f5_tts.text import normalize_spanish_text, SpanishTextNormalizer

# High-level API
normalized = normalize_spanish_text(
    "Tengo 25 euros y son las 14:30"
)
# "Tengo veinticinco euros y son las catorce treinta"

# Low-level API
normalizer = SpanishTextNormalizer()
normalized = normalizer.normalize("Tengo 25 euros")
```

**Normalization Features:**

- Numbers: `25` → `veinticinco`
- Currencies: `€15` → `quince euros`
- Times: `14:30` → `catorce treinta`
- Dates: `01/03/2024` → `primero de marzo de dos mil veinticuatro`
- Abbreviations: `Sr.` → `señor`
- Ordinals: `1º` → `primero`

#### Prosody Analysis

```python
from f5_tts.text import analyze_spanish_prosody

prosody = analyze_spanish_prosody("¿Cómo estás? ¡Muy bien!")

print(prosody.markers)         # List of prosodic markers
print(prosody.questions)       # Question positions
print(prosody.exclamations)    # Exclamation positions
print(prosody.stress_patterns) # Stress patterns
```

#### Breath & Pause Analysis

```python
from f5_tts.text import analyze_breath_pauses

breath = analyze_breath_pauses("First. Second. Third.")

print(breath.pauses)                    # List of detected pauses
print(breath.breath_points)             # Breath point positions
print(breath.total_duration_estimate)   # Estimated duration (seconds)
```

---

### Audio Processing

#### Crossfading

```python
from f5_tts.audio import EqualPowerCrossfader, RaisedCosineCrossfader, LinearCrossfader

# Equal power (recommended)
crossfader = EqualPowerCrossfader(duration=0.5)
result = crossfader.crossfade(audio1, audio2, sample_rate=24000)

# Raised cosine (smooth)
crossfader = RaisedCosineCrossfader(duration=0.5)
result = crossfader.crossfade(audio1, audio2, sample_rate=24000)

# Linear (simple)
crossfader = LinearCrossfader(duration=0.5)
result = crossfader.crossfade(audio1, audio2, sample_rate=24000)
```

#### Audio Processing Pipeline

```python
from f5_tts.audio import AudioProcessingPipeline

pipeline = AudioProcessingPipeline(
    target_sample_rate=24000,
    target_rms=0.1,
    normalize=True
)

processed = pipeline.prepare_reference_audio(audio, sample_rate=44100)
```

---

### Quality Analysis

#### Audio Quality Analyzer

```python
from f5_tts.audio import AudioQualityAnalyzer, QualityLevel

analyzer = AudioQualityAnalyzer()
quality = analyzer.analyze("generated_audio.wav")

print(quality.overall_level)     # QualityLevel enum
print(quality.snr_db)            # Signal-to-noise ratio
print(quality.spectral_flatness) # Spectral flatness
print(quality.detected_issues)   # List of detected issues
```

**Quality Levels:**

- `EXCELLENT` - Professional quality
- `GOOD` - High quality, minor issues
- `FAIR` - Acceptable quality, some artifacts
- `POOR` - Low quality, significant issues

#### Adaptive Configuration

```python
from f5_tts.core import get_adaptive_nfe_step, get_adaptive_crossfade_duration

# Adaptive NFE steps based on text complexity
nfe = get_adaptive_nfe_step(
    text="¿Cómo estás? ¡Muy bien!",
    base_nfe=16
)

# Adaptive crossfade duration
duration = get_adaptive_crossfade_duration()
```

---

## REST API

### Endpoints

#### POST `/tts` - Text-to-Speech Generation

Generate speech from text with optional enhancement features.

**Request:**

```bash
curl -X POST "http://localhost:8000/tts" \
  -F "gen_text=Hola mundo" \
  -F "ref_audio=@reference.wav" \
  -F "ref_text=Reference transcription" \
  -F "nfe_step=32" \
  -F "normalize_text=true"
```

**Form Data:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `gen_text` | `string` | ✅ | Text to synthesize |
| `ref_audio` | `file` | ✅ | Reference audio (WAV/MP3) |
| `ref_text` | `string` | ❌ | Reference transcription (ASR if empty) |
| `model_type` | `string` | ❌ | Model: `"F5-TTS"` or `"E2-TTS"` |
| `remove_silence` | `boolean` | ❌ | Remove silence (default: false) |
| `cross_fade_duration` | `float` | ❌ | Crossfade duration (default: 0.8) |
| `speed` | `float` | ❌ | Speech rate (default: 1.0) |
| `nfe_step` | `int` | ❌ | NFE steps (default: 32) |
| `normalize_text` | `boolean` | ❌ | Apply normalization (default: false) |
| `analyze_prosody` | `boolean` | ❌ | Analyze prosody (default: false) |
| `analyze_breath_pauses` | `boolean` | ❌ | Analyze breaths (default: false) |
| `adaptive_nfe` | `boolean` | ❌ | Use adaptive NFE (default: false) |
| `adaptive_crossfade` | `boolean` | ❌ | Use adaptive crossfade (default: false) |
| `check_audio_quality` | `boolean` | ❌ | Check output quality (default: false) |

**Response:**

- Success: `audio/wav` file (24kHz, mono)
- Error: JSON with error details

**Example (Python):**

```python
import requests

response = requests.post(
    "http://localhost:8000/tts",
    files={"ref_audio": open("reference.wav", "rb")},
    data={
        "gen_text": "¿Cómo estás? ¡Muy bien!",
        "ref_text": "Hello, this is a test.",
        "nfe_step": 32,
        "normalize_text": True,
        "adaptive_nfe": True
    }
)

if response.status_code == 200:
    with open("output.wav", "wb") as f:
        f.write(response.content)
else:
    print(response.json())
```

#### POST `/tts/stream` - Streaming TTS

Stream audio generation in real-time.

**Request:**

```python
import requests

response = requests.post(
    "http://localhost:8000/tts/stream",
    files={"ref_audio": open("reference.wav", "rb")},
    data={
        "gen_text": "Long text to stream...",
        "ref_text": "Reference"
    },
    stream=True
)

for chunk in response.iter_content(chunk_size=8192):
    # Process audio chunks
    pass
```

#### POST `/analyze` - Text Analysis

Analyze text for regional features, prosody, and breath patterns.

**Request:**

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

**JSON Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | `string` | ✅ | Text to analyze |
| `normalize_text` | `boolean` | ❌ | Apply normalization |
| `analyze_prosody` | `boolean` | ❌ | Analyze prosody |
| `analyze_breath_pauses` | `boolean` | ❌ | Analyze breath pauses |

**Response:**

```json
{
  "original_text": "Che boludo, ¿vos querés tomar unos mates?",
  "normalized_text": "Che boludo, ¿vos querés tomar unos mates?",
  "prosody": {
    "markers": [...],
    "questions": [22],
    "exclamations": []
  },
  "breath_pauses": {
    "pauses": [...],
    "breath_points": [42],
    "duration_estimate": 3.5
  }
}
```

#### GET `/health` - Health Check

Check API status and model availability.

**Request:**

```bash
curl "http://localhost:8000/health"
```

**Response:**

```json
{
  "status": "healthy",
  "model_loaded": true,
  "gpu_available": true
}
```

#### GET `/workers` - Worker Status

Check connected workers (if using distributed setup).

**Request:**

```bash
curl "http://localhost:8000/workers"
```

---

### Request/Response Models

#### TTSRequest

```python
class TTSRequest(BaseModel):
    gen_text: str
    ref_text: str = ""
    model_type: str = "F5-TTS"
    remove_silence: bool = False
    cross_fade_duration: float = 0.8
    speed: float = 1.0
    nfe_step: int = 32

    # Enhancement flags
    normalize_text: bool = False
    analyze_prosody: bool = False
    analyze_breath_pauses: bool = False
    adaptive_nfe: bool = False
    adaptive_crossfade: bool = False
    check_audio_quality: bool = False
```

#### AnalysisRequest

```python
class AnalysisRequest(BaseModel):
    text: str
    normalize_text: bool = False
    analyze_prosody: bool = False
    analyze_breath_pauses: bool = False
```

---

### Error Handling

**HTTP Status Codes:**

- `200` - Success
- `400` - Bad Request (invalid parameters)
- `422` - Validation Error
- `500` - Internal Server Error

**Error Response:**

```json
{
  "detail": "Error message describing the issue"
}
```

---

## CLI Tools

### Inference CLI

```bash
# Basic usage
f5-tts_infer-cli \
  --model "F5-TTS" \
  --ref_audio "reference.wav" \
  --ref_text "Reference text" \
  --gen_text "Text to generate"

# With config file
f5-tts_infer-cli --config config.toml

# Multi-speaker
f5-tts_infer-cli --config story.toml
```

### Training CLI

```bash
# Finetune with Gradio
f5-tts_finetune-gradio

# Command-line training
f5-tts_train --config training_config.yaml
```

### Dataset Preparation

```bash
# CSV dataset
python -m f5_tts.train.datasets.prepare_csv_wavs \
  --csv_file dataset.csv \
  --audio_dir /path/to/audio

# Regional Spanish dataset
python -m f5_tts.train.datasets.prepare_spanish_regional \
  --mode csv \
  --csv-path dataset.csv \
  --auto-detect
```

---

## Configuration Files

### Inference Config (TOML)

```toml
[inference]
model = "F5-TTS"
ref_audio = "reference.wav"
ref_text = "Reference transcription"
gen_text = "Text to generate"

[parameters]
nfe_step = 32
cfg_strength = 2.0
cross_fade_duration = 0.15
speed = 1.0

[output]
file_wave = "output.wav"
file_spect = "output.png"
remove_silence = false
```

### Training Config (YAML)

```yaml
model:
  type: "F5-TTS"
  dim: 1024
  depth: 22

training:
  batch_size: 32
  learning_rate: 1e-4
  num_epochs: 100

dataset:
  path: "/path/to/dataset"
  sample_rate: 24000
```

---

## Best Practices

### Performance Tips

1. **Use short reference audio** (6-10s) for faster inference
2. **Enable torch.compile** for 30-40% speedup
3. **Adjust NFE steps** based on quality needs (16=fast, 32=balanced, 64=quality)
4. **Use adaptive features** for automatic optimization

### Quality Tips

1. **High-quality reference audio** (clean, no background noise)
2. **Accurate reference transcription** for better results
3. **Normalize text** for numbers, dates, abbreviations
4. **Check audio quality** after generation

### Regional Spanish Tips

1. **Use auto-detection** for mixed regional content
2. **Apply phonetics** for authentic accents
3. **Match reference speaker** to target region
4. **Test with regional slang** to verify processing

---

## Examples

See the [examples/](../examples/) directory for complete working examples:

- [examples/basic/](../examples/basic/) - Basic TTS usage
- [examples/regional_spanish/](../examples/regional_spanish/) - Regional features
- [examples/api/](../examples/api/) - REST API integration
- [examples/advanced/](../examples/advanced/) - Advanced features

---

## Support

- **Documentation**: [docs/](.)
- **Issues**: [GitHub Issues](https://github.com/jpgallegoar/Spanish-F5/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jpgallegoar/Spanish-F5/discussions)

---

[⬆ Back to Top](#spanish-f5-tts-api-reference-)
