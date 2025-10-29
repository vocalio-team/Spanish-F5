# Spanish-F5 TTS 🗣️🇪🇸

> **Advanced Text-to-Speech system with comprehensive Spanish regional support**

Spanish-F5 is a high-quality Spanish Text-to-Speech (TTS) system based on F5-TTS, featuring realistic regional accent support for Latin American variants, advanced prosody modeling, and optimized inference performance.

**Part of the Vocalio Ecosystem** - Distributed AI platform for Spanish voice processing.

[![Tests](https://img.shields.io/badge/tests-287%20passing-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-60%25-yellow)](tests/)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

📖 **[Documentación en Español](README.es.md)** | [Arquitectura del Ecosistema Vocalio](docs/es/ARQUITECTURA_ECOSISTEMA.md) | [Guía Técnica Detallada](docs/es/GUIA_TECNICA.md)

---

## 🌟 Key Features

### 🌎 Regional Spanish Support
- **6 Regional Variants**: Rioplatense (🇦🇷🇺🇾), Colombian (🇨🇴), Mexican (🇲🇽), Chilean (🇨🇱), Caribbean, Andean
- **Automatic Accent Detection**: Analyzes text for regional markers (slang, syntax)
- **Phonetic Transformations**: Sheísmo, yeísmo, s-aspiration, and more
- **Prosodic Patterns**: Region-specific intonation, stress, and rhythm
- **Voseo Support**: Authentic Argentine/Uruguayan conjugations (vos sos, tenés, querés)

### 🎯 Advanced TTS Features
- **Diffusion Transformer (DiT)** and **Flat-UNet** architectures
- **Flow Matching** for high-quality synthesis
- **Sway Sampling**: Inference-time optimization for better performance
- **Multi-Style/Multi-Speaker**: Generate diverse voices
- **Chunk Inference**: Efficient processing of long texts

### 🚀 Performance Optimizations
- **Adaptive NFE Steps**: Quality-speed tradeoff based on text complexity
- **Enhanced Crossfading**: Smooth transitions (Equal Power, Raised Cosine, Linear)
- **Torch.compile Support**: Up to 40% faster inference on compatible GPUs
- **Audio Quality Detection**: Automatic artifact detection and prevention
- **Breath & Pause Modeling**: Natural speech pacing

### 🛠️ Production Ready
- **REST API**: FastAPI-based server with streaming support
- **Docker Support**: Multi-stage builds for development and production
- **Comprehensive Testing**: 287 tests with 60% code coverage
- **Modular Architecture**: Clean separation of concerns

---

## 📋 Table of Contents

- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Regional Spanish Features](#-regional-spanish-features)
- [API Usage](#-api-usage)
- [REST API Server](#-rest-api-server)
- [Training & Finetuning](#-training--finetuning)
- [Architecture](#-architecture)
- [Performance](#-performance)
- [Testing](#-testing)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🔧 Installation

### Prerequisites
- Python 3.10+
- CUDA-compatible GPU (recommended)
- 8GB+ GPU VRAM for inference

### Option 1: Quick Install (Pip)

```bash
# Create conda environment
conda create -n f5-tts python=3.10
conda activate f5-tts

# Install PyTorch with CUDA support
pip install torch==2.3.0+cu118 torchaudio==2.3.0+cu118 --extra-index-url https://download.pytorch.org/whl/cu118

# Install Spanish-F5
pip install git+https://github.com/jpgallegoar/Spanish-F5.git
```

### Option 2: Development Install

```bash
# Clone repository
git clone https://github.com/jpgallegoar/Spanish-F5.git
cd Spanish-F5

# Create environment
conda create -n f5-tts python=3.10
conda activate f5-tts

# Install PyTorch
pip install torch==2.3.0+cu118 torchaudio==2.3.0+cu118 --extra-index-url https://download.pytorch.org/whl/cu118

# Install in editable mode
pip install -e .

# Install development tools (optional)
pip install pre-commit
pre-commit install
```

### Option 3: Docker

```bash
# Build image
docker build -t spanish-f5-tts .

# Run container with GPU support
docker run --gpus all -p 8000:8000 spanish-f5-tts
```

---

## 🚀 Quick Start

### 1. Gradio Web Interface

```bash
# Launch web interface
f5-tts_infer-gradio

# Custom port/host
f5-tts_infer-gradio --port 7860 --host 0.0.0.0

# Public sharing link
f5-tts_infer-gradio --share
```

### 2. CLI Inference

```bash
# Basic usage
f5-tts_infer-cli \
  --model "F5-TTS" \
  --ref_audio "ref_audio.wav" \
  --ref_text "Reference text transcription." \
  --gen_text "Text to synthesize."

# With config file
f5-tts_infer-cli -c config.toml

# Multi-voice story
f5-tts_infer-cli -c src/f5_tts/infer/examples/multi/story.toml
```

### 3. Python API

```python
from f5_tts.api import F5TTS

# Initialize TTS engine
tts = F5TTS(model_type="F5-TTS")

# Generate speech
wav, sr, spect = tts.infer(
    ref_file="reference.wav",
    ref_text="Reference audio transcription",
    gen_text="Hello, this is a test of Spanish F5 TTS!",
    file_wave="output.wav",
    seed=42
)
```

---

## 🌎 Regional Spanish Features

Spanish-F5 includes comprehensive support for Latin American Spanish regional variants with authentic accents, prosody, and slang.

### Supported Regions

| Region | Code | Features | Example Markers |
|--------|------|----------|-----------------|
| 🇦🇷🇺🇾 **Rioplatense** | `rioplatense` | Sheísmo, voseo, s-aspiration | che, boludo, vos, sos |
| 🇨🇴 **Colombian** | `colombian` | Clear articulation, Paisa rhythm | parcero, chimba, ¿sí? |
| 🇲🇽 **Mexican** | `mexican` | Distinctive intonation, diminutives | órale, ahorita, -ito |
| 🇨🇱 **Chilean** | `chilean` | Rapid speech, slang | po', cachai, fome |
| 🌴 **Caribbean** | `caribbean` | Coastal rhythm, aspiration | ¿tú sabes?, chévere |
| ⛰️ **Andean** | `andean` | Highland patterns | pues, nomás |

### Quick Examples

#### Auto-Detection

```python
from f5_tts.text import process_spanish_text

# Automatically detects region from slang
result = process_spanish_text(
    "Che boludo, ¿vos querés tomar unos mates?",
    auto_detect=True
)
print(result.detected_region)  # "rioplatense"
print(result.slang_markers)    # ["che", "boludo", "vos", "querés"]
```

#### Regional Processing

```python
# Rioplatense (Argentina/Uruguay)
result = process_spanish_text(
    "¿Vos sabés dónde está el colectivo?",
    region="rioplatense",
    apply_phonetics=True
)
# Applies: sheísmo (ll/y → sh), voseo stress patterns

# Colombian
result = process_spanish_text(
    "Parcero, eso está muy bacano, ¿sí?",
    region="colombian"
)
# Detects: parcero, bacano, question tag ¿sí?

# Mexican
result = process_spanish_text(
    "Órale güey, ahorita vengo",
    region="mexican"
)
# Detects: órale, güey, ahorita (diminutive sense)
```

#### Text Normalization

```python
from f5_tts.text import normalize_spanish_text

# Automatically normalizes numbers, dates, currencies
text = normalize_spanish_text("Tengo 25 euros y son las 14:30")
print(text)  # "Tengo veinticinco euros y son las catorce treinta"
```

### 📖 Full Documentation

- **[Regional Spanish Guide](docs/SPANISH_REGIONAL_GUIDE.md)**: Complete feature documentation
- **[Quick Reference](docs/REGIONAL_QUICK_REFERENCE.md)**: Common patterns and examples
- **[Getting Started](docs/GETTING_STARTED_REGIONAL.md)**: Tutorial for regional features

---

## 🔌 API Usage

### Python API

```python
from f5_tts.api import F5TTS

# Initialize with configuration
tts = F5TTS(
    model_type="F5-TTS",      # or "E2-TTS"
    vocoder_name="vocos",     # or "bigvgan"
    device="cuda"             # or "cpu", "mps"
)

# Basic inference
wav, sr, spect = tts.infer(
    ref_file="examples/reference.wav",
    ref_text="This is the reference audio.",
    gen_text="Generate this Spanish text!",
    seed=42
)

# Advanced parameters
wav, sr, spect = tts.infer(
    ref_file="reference.wav",
    ref_text="Reference text",
    gen_text="Generated text",

    # Quality settings
    nfe_step=32,              # Higher = better quality (16-64)
    cfg_strength=2.0,         # Classifier-free guidance (1.5-3.0)

    # Audio processing
    target_rms=0.1,           # Volume normalization
    cross_fade_duration=0.15, # Chunk blending (seconds)
    speed=1.0,                # Speech rate multiplier

    # Output
    file_wave="output.wav",   # Save to file
    file_spect="output.png",  # Save spectrogram
    remove_silence=True,      # Trim silence
    seed=42                   # Reproducibility
)
```

### Regional Spanish Integration

```python
from f5_tts.api import F5TTS
from f5_tts.text import process_spanish_text

tts = F5TTS()

# Process with regional features
processed = process_spanish_text(
    "Che boludo, ¿cómo andás?",
    region="rioplatense",
    apply_phonetics=True
)

# Generate speech with processed text
wav, sr, spect = tts.infer(
    ref_file="rioplatense_speaker.wav",
    ref_text="Hola, soy de Buenos Aires.",
    gen_text=processed.text,
    file_wave="output_rioplatense.wav"
)
```

### Enhancement Features

```python
from f5_tts.text import (
    analyze_spanish_prosody,
    analyze_breath_pauses,
    normalize_spanish_text
)
from f5_tts.audio import AudioQualityAnalyzer
from f5_tts.core import get_adaptive_nfe_step, get_adaptive_crossfade_duration

# Text normalization
text = normalize_spanish_text("Tengo 25 euros y 3 gatos")
# "Tengo veinticinco euros y tres gatos"

# Prosody analysis
prosody = analyze_spanish_prosody("¿Cómo estás? ¡Muy bien!")
print(prosody.markers)  # Intonation markers for questions/exclamations

# Breath pause detection
breath = analyze_breath_pauses("First sentence. Second sentence. Third.")
print(f"Breath points: {len(breath.breath_points)}")
print(f"Duration estimate: {breath.total_duration_estimate:.1f}s")

# Audio quality analysis
analyzer = AudioQualityAnalyzer()
quality = analyzer.analyze("generated_audio.wav")
print(f"Quality: {quality.overall_level}")  # EXCELLENT/GOOD/FAIR/POOR
print(f"Issues: {quality.detected_issues}")

# Adaptive NFE steps (quality vs speed)
nfe = get_adaptive_nfe_step("¿Cómo estás? ¡Muy bien!", base_nfe=16)
print(f"Recommended NFE: {nfe}")  # 16-32 based on complexity

# Adaptive crossfade duration
duration = get_adaptive_crossfade_duration()
print(f"Crossfade: {duration}s")  # 0.4-1.2s based on quality needs
```

---

## 🌐 REST API Server

### Starting the Server

```bash
# Development mode
python f5_tts_api.py

# Production mode with gunicorn
gunicorn f5_tts_api:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Docker
docker run --gpus all -p 8000:8000 spanish-f5-tts
```

### API Endpoints

#### POST `/tts` - Generate Speech

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
        "ref_text": "Reference transcription",
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

#### POST `/analyze` - Text Analysis

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

### Full API Documentation

See **[API_ENHANCED.md](docs/API_ENHANCED.md)** for complete endpoint documentation.

---

## 🎓 Training & Finetuning

### Gradio Interface

```bash
# Launch training web interface
f5-tts_finetune-gradio
```

### CLI Training

```bash
# Prepare dataset (CSV format)
python -m f5_tts.train.datasets.prepare_csv_wavs \
  --csv_file dataset.csv \
  --audio_dir /path/to/audio \
  --output_dir /path/to/output

# Regional Spanish dataset preparation
python -m f5_tts.train.datasets.prepare_spanish_regional \
  --mode csv \
  --csv-path dataset.csv \
  --audio-base-dir /path/to/audio \
  --dataset-name my_dataset \
  --auto-detect \
  --max-workers 8
```

### Training Configuration

See **[Training Guide](src/f5_tts/train/README.md)** for detailed instructions.

---

## 🏗️ Architecture

### Modular Design

```
Spanish-F5/
├── src/f5_tts/
│   ├── core/           # Configuration, types, protocols
│   ├── model/          # DiT, UNetT, CFM architectures
│   ├── audio/          # Processors, crossfading, quality analysis
│   ├── text/           # Regional Spanish, normalization, prosody
│   ├── infer/          # Inference utilities, CLI, Gradio
│   ├── train/          # Training, finetuning, datasets
│   └── api.py          # Main Python API
├── f5_tts_api.py       # REST API server
├── tests/              # Comprehensive test suite
└── docs/               # Documentation
```

### Key Components

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)**: Complete system architecture
- **[Core Module](src/f5_tts/core/)**: Configuration and type system
- **[Text Processing](src/f5_tts/text/)**: Regional Spanish, normalization, prosody
- **[Audio Processing](src/f5_tts/audio/)**: Quality analysis, crossfading
- **[Model](src/f5_tts/model/)**: DiT, UNetT, Flow Matching

---

## ⚡ Performance

### Optimization Features

- **Torch.compile**: Enable with `ENABLE_TORCH_COMPILE=true`
- **cuDNN Benchmark**: Enable with `ENABLE_CUDNN_BENCHMARK=true`
- **TF32 Precision**: Set `TORCH_MATMUL_PRECISION=high` (Ampere+ GPUs)
- **Adaptive NFE**: Automatic quality-speed tradeoff
- **Short Reference Audio**: Use 6s clips for faster processing

### Environment Variables

```bash
export ENABLE_TORCH_COMPILE=true
export ENABLE_CUDNN_BENCHMARK=true
export TORCH_MATMUL_PRECISION=high
```

### Benchmarks

| Configuration | NFE Steps | GPU | Time (10s audio) |
|--------------|-----------|-----|------------------|
| Quality | 32 | RTX 3090 | ~8s |
| Balanced | 16 | RTX 3090 | ~4s |
| Fast | 8 | RTX 3090 | ~2s |

See the [Performance section](#-performance) above for optimization details.

---

## 🧪 Testing

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific module
pytest tests/test_spanish_regional.py -v

# With coverage
pytest --cov=src/f5_tts --cov-report=html tests/

# Coverage analysis
python analyze_coverage.py
```

### Test Suite

- **287 tests** with **60% code coverage**
- Regional Spanish: Phonetics, slang, prosody
- Audio processing: Crossfading, normalization, quality
- Text processing: Normalization, chunking, breath analysis
- API: Initialization, inference, export

### Code Quality

```bash
# Run linters and formatters
pre-commit run --all-files

# Manual linting
ruff check . --fix
ruff format .
```

---

## 📚 Documentation

### Spanish Documentation (Vocalio Ecosystem)
- **[📖 README en Español](README.es.md)**: Documentación principal completa
- **[🏗️ Arquitectura del Ecosistema](docs/es/ARQUITECTURA_ECOSISTEMA.md)**: Integración con Vocalio
- **[🔧 Guía Técnica](docs/es/GUIA_TECNICA.md)**: Componentes internos y modelos

### User Guides (English)
- **[Regional Spanish Guide](docs/SPANISH_REGIONAL_GUIDE.md)**: Complete regional features
- **[Quick Reference](docs/REGIONAL_QUICK_REFERENCE.md)**: Common patterns
- **[Getting Started](docs/GETTING_STARTED_REGIONAL.md)**: Tutorial

### Technical Documentation (English)
- **[Architecture](docs/ARCHITECTURE.md)**: System design and modules
- **[API Documentation](docs/API_REFERENCE.md)**: REST API reference
- **[Docker Optimization](docs/DOCKER_OPTIMIZATION.md)**: Docker build optimization
- **[Prosody Guide](docs/PROSODY_GUIDE.md)**: Prosodic features
- **[Audio Quality Guide](docs/AUDIO_QUALITY_GUIDE.md)**: Quality analysis

### Development
- **[CLAUDE.md](CLAUDE.md)**: Development guidelines for Claude Code
- **[Training Guide](src/f5_tts/train/README.md)**: Training and finetuning
- **[Inference Guide](src/f5_tts/infer/README.md)**: Detailed inference instructions

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Setup

```bash
# Clone and setup
git clone https://github.com/jpgallegoar/Spanish-F5.git
cd Spanish-F5
pip install -e .

# Install development tools
pip install pre-commit pytest pytest-cov ruff
pre-commit install
```

### Contribution Guidelines

1. **Fork** the repository
2. **Create a branch**: `git checkout -b feature/my-feature`
3. **Make changes** and add tests
4. **Run tests**: `pytest tests/ -v`
5. **Check code quality**: `pre-commit run --all-files`
6. **Commit**: `git commit -m "Add my feature"`
7. **Push**: `git push origin feature/my-feature`
8. **Create Pull Request**

### Code Standards

- Python 3.10+ compatibility
- Type hints for all functions
- Comprehensive tests (aim for >80% coverage)
- Docstrings for all public APIs
- Follow PEP 8 (enforced by ruff)
- Line length: 120 characters

---

## 📄 License

This project is released under the **MIT License**. See [LICENSE](LICENSE) for details.

**Pre-trained models** are licensed under CC-BY-NC due to the Emilia training dataset.

---

## 🙏 Acknowledgements

### Original F5-TTS
- **E2-TTS Paper**: [arXiv:2406.18009](https://arxiv.org/abs/2406.18009)
- **F5-TTS Repository**: [SWivid/F5-TTS](https://github.com/SWivid/F5-TTS)

### Datasets & Models
- **Emilia**: [arXiv:2407.05361](https://arxiv.org/abs/2407.05361)
- **WenetSpeech4TTS**: [arXiv:2406.05763](https://arxiv.org/abs/2406.05763)
- **Spanish Model**: [jpgallegoar/F5-Spanish](https://huggingface.co/jpgallegoar/F5-Spanish/)

### Libraries & Tools
- [PyTorch](https://pytorch.org/)
- [torchdiffeq](https://github.com/rtqichen/torchdiffeq)
- [Vocos](https://huggingface.co/charactr/vocos-mel-24khz)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Gradio](https://gradio.app/)

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/jpgallegoar/Spanish-F5/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jpgallegoar/Spanish-F5/discussions)
- **Original F5-TTS**: [SWivid/F5-TTS Issues](https://github.com/SWivid/F5-TTS/issues)

---

## 📊 Citation

If you use Spanish-F5 in your research, please cite:

```bibtex
@article{chen-etal-2024-f5tts,
  title={F5-TTS: A Fairytaler that Fakes Fluent and Faithful Speech with Flow Matching},
  author={Yushen Chen and Zhikang Niu and Ziyang Ma and Keqi Deng and Chunhui Wang and Jian Zhao and Kai Yu and Xie Chen},
  journal={arXiv preprint arXiv:2410.06885},
  year={2024},
}
```

---

<div align="center">

**Made with ❤️ for the Spanish-speaking TTS community**

[⬆ Back to Top](#spanish-f5-tts-)

</div>
