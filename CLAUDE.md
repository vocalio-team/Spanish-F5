# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Spanish-F5 is a Spanish-language Text-to-Speech (TTS) system based on F5-TTS with regional accent support. The system uses Diffusion Transformer (DiT) and Flat-UNet architectures with flow matching for high-quality Spanish speech synthesis.

**Key Features:**
- Comprehensive regional Spanish support for Latin American variants (Rioplatense, Colombian, Mexican, Chilean, Caribbean, Andean)
- Automatic accent detection, phonetic transformations, and slang handling
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

# Run specific test suite
python tests/test_spanish_regional.py
python tests/test_text_chunker.py
python tests/test_audio_processors.py

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
```

### Running the API
```bash
# Development mode (FastAPI with uvicorn)
python f5_tts_api.py

# Production mode (with gunicorn)
gunicorn f5_tts_api:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Docker build
docker build -t spanish-f5-tts .

# Docker run
docker run --gpus all -p 8000:8000 spanish-f5-tts
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
│   ├── spanish_regional.py # Regional Spanish processor (NEW)
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
- `RegionalProsody`: Prosodic pattern detection
- `RegionalSlang`: Slang dictionaries per region

**Auto-detection:** Scores text based on slang markers, selects region with highest score.

**Processing flow:**
1. Normalize text (basic cleanup)
2. Detect/apply regional slang
3. Apply phonetic transformations (if enabled)
4. Add prosodic markers
5. Return structured result with metadata

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

2. **Audio Processing** (`test_audio_processors.py`, `test_audio.py`):
   - Crossfading algorithms
   - Audio normalization
   - Resampling quality
   - Edge cases (silence, clipping)

3. **Text Processing** (`test_text_chunker.py`):
   - Sentence-based chunking
   - Adaptive chunking
   - Boundary detection

4. **Core System** (`test_core.py`):
   - Configuration management
   - Type definitions
   - Protocol compliance

5. **API Integration** (`test_api.py`):
   - F5TTS class interface
   - Inference pipeline
   - File I/O operations

**Note:** Some model components have linting exceptions for E722 to accommodate tensor notation.

## Regional Spanish Usage

### Quick Example
```python
from f5_tts.text import process_spanish_text

# Process Rioplatense Spanish
result = process_spanish_text(
    "Che boludo, ¿vos querés tomar unos mates?",
    region="rioplatense"
)
# Detects: che, boludo, vos, querés
# Applies: s-aspiration, sheísmo, voseo stress patterns
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

## Key Files Reference

- **ARCHITECTURE.md**: Detailed modular architecture documentation
- **SPANISH_REGIONAL_GUIDE.md**: Complete regional Spanish features guide
- **f5_tts_api.py**: REST API server implementation
- **src/f5_tts/api.py**: Main F5TTS Python API class
- **src/f5_tts/infer/utils_infer.py**: Core inference utilities
- **src/f5_tts/core/config.py**: Global configuration system
- **src/f5_tts/text/spanish_regional.py**: Regional accent processor

## Notes for Claude Code

1. **Prefer modular imports**: Use new modular components from `f5_tts.core`, `f5_tts.audio`, `f5_tts.text` rather than legacy monolithic utilities when adding new features.

2. **Regional Spanish**: When working with Spanish text, consider regional processing. Check if auto-detection or explicit region handling is appropriate.

3. **Performance-sensitive code**: Be aware of CUDA optimizations. Changes to inference pipeline should consider torch.compile compatibility and NFE step tuning.

4. **Testing**: Always add tests for new features. Regional Spanish tests are particularly important for linguistic accuracy.

5. **Backwards compatibility**: The original F5TTS API class is maintained for compatibility. New features should extend modular components.

6. **Docker deployment**: Code is deployed via Docker with multi-stage builds (development/production). Consider container implications for new dependencies.
