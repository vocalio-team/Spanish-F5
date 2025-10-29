# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Spanish-F5 is a Spanish-language Text-to-Speech (TTS) system based on F5-TTS with regional accent support. The system uses Diffusion Transformer (DiT) and Flat-UNet architectures with flow matching for high-quality Spanish speech synthesis.

**Key Features:**
- Comprehensive regional Spanish support for Latin American variants (Rioplatense, Colombian, Mexican, Chilean, Caribbean, Andean)
- Automatic accent detection, phonetic transformations, and slang handling
- **Empirically-validated prosody** based on academic research (Cuello & Oro Ozán 2024, Guglielmone et al. 2014)
- **Discourse-level prosody** with declination units and nuclear tone configurations
- Intelligent text normalization (numbers, dates, times, currencies, abbreviations)
- Adaptive NFE steps for optimal quality-speed tradeoff
- Enhanced crossfading for smoother audio transitions

## Development Commands

### Environment Setup
```bash
# Create conda environment
conda create -n f5-tts python=3.10
conda activate f5-tts

# Install PyTorch with CUDA (adjust CUDA version as needed)
pip install torch==2.3.0+cu118 torchaudio==2.3.0+cu118 --extra-index-url https://download.pytorch.org/whl/cu118

# Install package (editable mode for development)
pip install -e .

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

### Testing
```bash
# Run all tests (uses pytest)
./run_all_tests.sh

# Run specific test suite (two options)
pytest tests/test_spanish_regional.py -v
# or
python tests/test_spanish_regional.py

# Run specific test within a file
pytest tests/test_spanish_regional.py::TestSpanishRegionalProcessor::test_rioplatense_phonetics -v

# Run with coverage
pytest --cov=src/f5_tts --cov-report=html tests/

# Analyze coverage
python analyze_coverage.py
```

### Code Quality
```bash
# Run linting and formatting (Ruff)
pre-commit run --all-files

# Run manually
ruff check . --fix
ruff format .

# Note: Ruff config is in ruff.toml (120 char line length, Python 3.10 target)
```

### Running the API
```bash
# Development mode (FastAPI with uvicorn)
python f5_tts_api.py

# Production mode (with gunicorn)
gunicorn f5_tts_api:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Docker build (optimized for fast rebuilds - see docs/DOCKER_OPTIMIZATION.md)
./docker-build.sh latest base              # Development image
./docker-build.sh latest production        # Production image (smaller, optimized)
./docker-build.sh latest production --push # Build and push to ECR

# Docker run
docker run --gpus all -p 8000:8000 spanish-f5-tts

# Note: Dockerfile is optimized for layer caching
# - Code changes rebuild in ~45 seconds (vs 12 minutes before)
# - 90%+ reduction in rebuild time through proper layer ordering
# Note: The API has been refactored into a modular structure (see docs/API_REFACTORING.md)
# The f5_tts_api.py entry point remains the same for backward compatibility
```

### Production Deployment

```bash
# Deploy to AWS ECS with GPU Spot instances
./deploy-gpu-spot.sh

# What gets deployed:
# - CloudFormation stack with g5.xlarge/g4dn.xlarge Spot instances (2 instances)
# - Application Load Balancer with health checks
# - ECS Capacity Provider for auto-scaling
# - Cost: ~$0.15-0.25/hour (~$110-180/month) - 60-70% savings vs On-Demand
# - Stack name: gpu-spot-stack
# - Cluster: dev-vocalio-chatterbox
# - Service: f5-tts-spot-service

# Monitor deployment
aws ecs describe-services \
  --cluster dev-vocalio-chatterbox \
  --services f5-tts-spot-service \
  --region us-east-1

# View logs
aws logs tail /ecs/dev-f5-tts --follow --region us-east-1

# Check backend integration
# Backend: https://api.test.aithentia.com:8000/workers
```

### CLI Tools
```bash
# Gradio web interface
f5-tts_infer-gradio
f5-tts_infer-gradio --port 7860 --host 0.0.0.0

# CLI inference
f5-tts_infer-cli \
  --model "F5-TTS" \
  --ref_audio "ref_audio.wav" \
  --ref_text "Reference text" \
  --gen_text "Text to synthesize"

# Training/finetuning
f5-tts_finetune-gradio
```

## Architecture

### Module Structure

```
src/f5_tts/
├── core/                    # Core types, config, protocols
│   ├── config.py           # GlobalConfig for system-wide settings
│   ├── types.py            # AudioData, InferenceConfig, protocols
│   └── __init__.py
│
├── audio/                   # Audio processing components
│   ├── crossfading.py      # Crossfading algorithms (EqualPower, RaisedCosine, Linear)
│   ├── processors.py       # Audio pipeline (normalize, resample, etc.)
│   └── __init__.py
│
├── text/                    # Text processing
│   ├── chunker.py          # Text chunking strategies (Sentence, Adaptive, Fixed)
│   ├── spanish_regional.py # Regional Spanish processor with empirical prosody
│   ├── discourse_prosody.py # Discourse-level prosody (Guglielmone et al. 2014)
│   └── __init__.py
│
├── model/                   # Model definitions
│   ├── backbones/          # DiT, MMDiT, UNetT architectures
│   ├── cfm.py              # Conditional Flow Matching
│   ├── dataset.py          # Dataset handling
│   ├── trainer.py          # Training logic
│   └── utils.py            # Model utilities
│
├── infer/                   # Inference logic
│   ├── utils_infer.py      # Main inference utilities
│   ├── infer_cli.py        # CLI interface
│   └── infer_gradio.py     # Gradio interface
│
├── train/                   # Training and finetuning
│   ├── train.py            # Main training script
│   ├── finetune_cli.py     # Finetuning CLI
│   └── datasets/           # Dataset preparation scripts
│       ├── prepare_spanish_regional.py  # Regional Spanish datasets
│       └── ...
│
├── rest_api/                # REST API (MODULAR REFACTORED)
│   ├── app.py              # FastAPI app creation & startup
│   ├── config.py           # API configuration
│   ├── state.py            # Global state management
│   ├── models.py           # Pydantic request/response models
│   ├── enhancements.py     # Enhancement processing
│   ├── tts_processor.py    # TTS generation logic
│   └── routes/             # API endpoint handlers
│       ├── tts.py          # Main TTS endpoints
│       ├── upload.py       # File upload endpoints
│       ├── tasks.py        # Task management
│       └── analysis.py     # Analysis endpoints
│
├── api.py                   # F5TTS Python API class
└── socket_server.py         # Streaming server (legacy)
```

### Key Design Patterns

**1. Protocol-Based Design:** Components implement protocols (AudioProcessor, Crossfader, TextChunker) for flexibility and testability.

**2. Modular Audio Pipeline:**
- Separate crossfading algorithms (equal-power, raised-cosine, linear)
- Composable audio processors (normalize, resample, clip)
- AudioProcessingPipeline for complete workflows

**3. Configuration Management:**
- `GlobalConfig` singleton for system-wide settings
- Environment variable support (ENABLE_TORCH_COMPILE, TORCH_MATMUL_PRECISION, etc.)
- Per-request config overrides

**4. Regional Spanish System:**
- Automatic accent detection from slang markers
- Phonetic transformations (sheísmo, yeísmo, s-aspiration)
- Prosodic pattern recognition
- Voseo support (Argentina/Uruguay)

## Important Implementation Details

### Model Loading and Inference

The system uses two entry points:

1. **API class** (`f5_tts.api.F5TTS`): Main programmatic interface
   - Loads model with `load_model()` from `infer.utils_infer`
   - Uses DiT (F5-TTS) or UNetT (E2-TTS) architectures
   - Supports torch.compile for optimization

2. **REST API** (`f5_tts_api.py`): FastAPI server
   - Pre-loads models on startup
   - Supports streaming and file-based inference
   - Uses short reference audio (6s) for faster processing

### Regional Spanish Processing

Located in `src/f5_tts/text/spanish_regional.py`:

- `SpanishRegionalProcessor`: Main processing class
- `RegionalPhonetics`: Phonetic transformation rules
- `RegionalProsody`: Prosodic pattern detection with **empirically-validated profiles**
- `RegionalProsodicProfile`: Complete prosodic profiles based on academic research
- `RegionalSlang`: Slang dictionaries per region

**Empirical Prosody (NEW - Based on Academic Research):**
- **Rioplatense**: Slow pace (0.75x multiplier), double accentuation, plaintive quality
  - Cuello & Oro Ozán (2024): T.E.P.HA prosody measurements
  - F0 range: 75-340Hz (female), 75-200Hz (male)
  - **CRITICAL FIX**: Changed from "fast" to "slow" based on empirical data
- **Colombian**: Medium pace, clear articulation, neutral prosody
- **Mexican**: Medium pace, melodic contours, expressive intonation

**Auto-detection:** Scores text based on slang markers, selects region with highest score.

**Processing flow:**
1. Normalize text (basic cleanup)
2. Detect/apply regional slang
3. Apply phonetic transformations (if enabled)
4. Add prosodic markers
5. Apply empirical prosodic profile (pace, stress, F0 range)
6. Return structured result with metadata including prosodic profile

### Audio Processing

**Crossfading:** Default is EqualPowerCrossfader (industry standard)
- Prevents amplitude dips during transitions
- Uses power law (sqrt) for fade curves
- Configurable duration (default 0.5s)

**Audio Pipeline:**
- DC offset removal → RMS normalization → Resampling → Clipping prevention
- Uses Kaiser window for high-quality resampling
- Target: 24kHz, mono, float32

### Performance Optimizations

The system includes several CUDA optimizations:

```python
# Set in GlobalConfig or environment
ENABLE_TORCH_COMPILE=true          # torch.compile() for model
ENABLE_CUDNN_BENCHMARK=true        # cuDNN kernel selection
TORCH_MATMUL_PRECISION=high        # TF32 for Ampere+ GPUs
```

Key optimizations:
- Model warmup during startup
- Compiled inference kernels
- Short reference audio for real-time use (6s vs 30s+)
- Reduced NFE steps (16 vs 32) for faster generation

## Testing Strategy

### Test Coverage Areas

1. **Regional Spanish** (`test_spanish_regional.py`):
   - Phonetic transformations per region
   - Slang detection and normalization
   - Auto-detection from text
   - Prosodic marker addition

2. **Prosody Improvements** (`test_prosody_improvements.py`) **NEW**:
   - Empirical prosodic profiles (pace, stress, F0 ranges)
   - Discourse-level prosody (declination units, nuclear tones)
   - Integration tests (regional + discourse prosody)
   - Regression prevention (pace correction)
   - 31 comprehensive tests - all passing ✓

3. **Audio Processing** (`test_audio_processors.py`, `test_audio.py`):
   - Crossfading algorithms
   - Audio normalization
   - Resampling quality
   - Edge cases (silence, clipping)

4. **Text Processing** (`test_text_chunker.py`):
   - Sentence-based chunking
   - Adaptive chunking
   - Boundary detection

5. **Core System** (`test_core.py`):
   - Configuration management
   - Type definitions
   - Protocol compliance

6. **API Integration** (`test_api.py`):
   - F5TTS class interface
   - Inference pipeline
   - File I/O operations

7. **REST API Modules** (`test_api_modules.py`):
   - Pydantic models validation
   - State management (models, tasks, audio)
   - TTS processor (short text adjustments)
   - Enhancement processor (normalization, prosody, adaptive parameters)

**Test Coverage Tools:**
- `pytest --cov`: Generate coverage reports
- `analyze_coverage.py`: Detailed coverage analysis script
- Coverage reports saved to `htmlcov/` directory

**Note:** Some model components have linting exceptions for E722 to accommodate tensor notation.

## Regional Spanish Usage

### Quick Example
```python
from f5_tts.text import process_spanish_text

# Process Rioplatense Spanish with empirical prosody
result = process_spanish_text(
    "Che boludo, ¿vos querés tomar unos mates?",
    region="rioplatense"
)
# Detects: che, boludo, vos, querés
# Applies: s-aspiration, sheísmo, voseo stress patterns
# Prosody: slow pace (0.75x), double accentuation, plaintive quality
# Returns prosodic_profile with F0 ranges, pace multipliers, stress patterns
```

### Discourse-Level Prosody Example (NEW)
```python
from f5_tts.text.discourse_prosody import analyze_discourse_prosody

# Analyze discourse structure based on Guglielmone et al. (2014)
result = analyze_discourse_prosody(
    "Hola amigo. ¿Cómo estás? Estoy muy bien, gracias.",
    voice_type="female"
)
# Returns:
# - phrases: List of intonational phrases with nuclear tones
# - declination_units: Thematic sections with F0 start/end
# - Nuclear tones: descending (↘), suspensive (→), ascending (↗)
# - F0 ranges: 75-340Hz (female), 75-200Hz (male)
```

### Supported Regions
- **rioplatense**: Argentina/Uruguay (sheísmo, voseo, s-aspiration)
- **colombian**: Colombia (clear articulation, question tags)
- **mexican**: Mexico (diminutives, distinctive intonation)
- **chilean**, **caribbean**, **andean**: Extensible framework

### Dataset Preparation
```bash
python -m f5_tts.train.datasets.prepare_spanish_regional \
    --mode csv \
    --csv-path dataset.csv \
    --audio-base-dir /path/to/audio \
    --dataset-name my_dataset \
    --auto-detect \
    --max-workers 8
```

See [docs/SPANISH_REGIONAL_GUIDE.md](docs/SPANISH_REGIONAL_GUIDE.md) for complete documentation.

## Related Projects

- **Worker project**: Located at `../worker_aithentia` relative to this repo
- **Backend API**: Deployed at https://api.test.aithentia.com:8000/
- Workers status: https://api.test.aithentia.com:8000/workers

**Vocalio Ecosystem Integration:**
Spanish-F5 is the TTS GPU worker for the Vocalio distributed AI platform. See Spanish documentation for ecosystem details:
- **[README.es.md](README.es.md)** - Main documentation in Spanish
- **[docs/es/ARQUITECTURA_ECOSISTEMA.md](docs/es/ARQUITECTURA_ECOSISTEMA.md)** - Vocalio ecosystem architecture
- **[docs/es/GUIA_TECNICA.md](docs/es/GUIA_TECNICA.md)** - Detailed technical guide

## Key Files Reference

### Documentation in Spanish (Vocalio Ecosystem)
- **README.es.md**: Main Spanish documentation with ecosystem overview
- **docs/es/ARQUITECTURA_ECOSISTEMA.md**: Vocalio ecosystem architecture and integration
- **docs/es/GUIA_TECNICA.md**: Detailed technical guide (components, models, pipelines)

### Technical Documentation (English)
- **docs/ARCHITECTURE.md**: Detailed modular architecture documentation
- **docs/SPANISH_REGIONAL_GUIDE.md**: Complete regional Spanish features guide
- **docs/API_REFACTORING.md**: REST API refactoring documentation (monolith → modular)
- **docs/AUDIO_COMPRESSION.md**: Audio compression guide for low-bandwidth deployment
- **docs/PROSODY_ANALYSIS_ACADEMIC_PAPERS.md**: Academic research findings on Rioplatense prosody
- **docs/AUDIO_QUALITY_GUIDE.md**: Audio quality analysis and metrics
- **docs/PROSODY_GUIDE.md**: Prosodic features and usage
- **docs/DOCKER_OPTIMIZATION.md**: Docker build optimization guide
- **f5_tts_api.py**: REST API server entry point (48 lines, modular)
- **src/f5_tts/rest_api/**: Modular REST API implementation
  - **app.py**: FastAPI application factory with model loading
  - **models.py**: Pydantic request/response models
  - **state.py**: Global state management (models, tasks, audio)
  - **enhancements.py**: Text/audio enhancement processing
  - **tts_processor.py**: TTS generation with adaptive parameters
  - **audio_compression.py**: Audio compression (OPUS, MP3, WAV) for bandwidth efficiency
  - **routes/**: Organized endpoint handlers (tts, upload, tasks, analysis)
- **src/f5_tts/api.py**: Main F5TTS Python API class
- **src/f5_tts/infer/utils_infer.py**: Core inference utilities
- **src/f5_tts/core/config.py**: Global configuration system
- **src/f5_tts/text/spanish_regional.py**: Regional accent processor with empirical prosody **UPDATED**
- **src/f5_tts/text/discourse_prosody.py**: Discourse-level prosody processor **NEW**

## Notes for Claude Code

1. **Prefer modular imports**: Use new modular components from `f5_tts.core`, `f5_tts.audio`, `f5_tts.text`, and `f5_tts.rest_api` rather than legacy monolithic utilities when adding new features.

2. **REST API development**: The API has been refactored into a modular structure. When adding new endpoints:
   - Add route handlers in `src/f5_tts/rest_api/routes/`
   - Add models in `src/f5_tts/rest_api/models.py`
   - Reuse enhancement/processing logic from existing modules
   - Add tests in `tests/test_api_modules.py`
   - See `docs/API_REFACTORING.md` for detailed guidance

3. **Regional Spanish**: When working with Spanish text, consider regional processing. Check if auto-detection or explicit region handling is appropriate. **IMPORTANT**: All prosodic profiles are now based on empirical research (see `docs/PROSODY_ANALYSIS_ACADEMIC_PAPERS.md`).

4. **Empirical Prosody**: Prosodic parameters (pace, F0 ranges, stress patterns) are based on academic research. Do NOT modify these values without corresponding empirical evidence. Key correction: Rioplatense is SLOW (0.75x), not fast.

5. **Discourse Prosody**: For multi-sentence text, consider using `discourse_prosody.py` module to apply declination units and nuclear tone configurations based on Guglielmone et al. (2014) framework.

6. **Performance-sensitive code**: Be aware of CUDA optimizations. Changes to inference pipeline should consider torch.compile compatibility and NFE step tuning.

7. **Testing**: Always add tests for new features. Regional Spanish and prosody tests are particularly important for linguistic accuracy. See `test_prosody_improvements.py` for examples.

8. **Backwards compatibility**: The original F5TTS API class is maintained for compatibility. The REST API maintains 100% backward compatibility at the endpoint level.

9. **Docker deployment**: Code is deployed via Docker with multi-stage builds (development/production). Consider container implications for new dependencies.
