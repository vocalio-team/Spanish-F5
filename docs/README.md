# Spanish-F5 TTS Documentation 📚

Welcome to the comprehensive documentation for Spanish-F5 TTS! This guide will help you get started, understand the architecture, and master advanced features.

**Part of the Vocalio Ecosystem** - Distributed AI platform for Spanish voice processing.

---

## 📖 Documentation Index

### 🇪🇸 Documentación en Español (Vocalio Ecosystem)

- **[📖 README en Español](../README.es.md)** - Documentación principal completa
- **[🏗️ Arquitectura del Ecosistema Vocalio](es/ARQUITECTURA_ECOSISTEMA.md)** - Integración con el ecosistema Vocalio
- **[🔧 Guía Técnica Detallada](es/GUIA_TECNICA.md)** - Componentes internos, modelos y pipelines

### Getting Started (English)

- **[Main README](../README.md)** - Project overview, installation, and quick start
- **[Getting Started with Regional Spanish](GETTING_STARTED_REGIONAL.md)** - Tutorial for regional features
- **[Quick Reference Guide](REGIONAL_QUICK_REFERENCE.md)** - Common patterns and examples

### User Guides

- **[API Reference](API_REFERENCE.md)** - Complete API documentation
  - Python API
  - REST API endpoints
  - CLI tools
  - Request/response models

- **[Regional Spanish Guide](SPANISH_REGIONAL_GUIDE.md)** - Comprehensive regional features
  - Supported regions and features
  - Auto-detection
  - Phonetic transformations
  - Prosodic patterns
  - Dataset preparation

- **[Prosody Guide](PROSODY_GUIDE.md)** - Prosodic modeling features
  - Intonation patterns
  - Stress markers
  - Rhythm analysis
  - Empirically-validated profiles

- **[Audio Quality Guide](AUDIO_QUALITY_GUIDE.md)** - Audio quality analysis
  - Quality metrics
  - Issue detection
  - Improvement strategies

### Technical Documentation

- **[Architecture](ARCHITECTURE.md)** - System architecture and design
  - Modular structure
  - Core components
  - Data flow
  - Extension points

- **[API Refactoring](API_REFACTORING.md)** - REST API architecture
  - Modular design
  - Separation of concerns
  - Testing strategy

- **[Audio Compression](AUDIO_COMPRESSION.md)** - Bandwidth optimization
  - OPUS compression (92% savings)
  - MP3 compression (83% savings)
  - Format comparison

- **[Prosody Analysis Papers](PROSODY_ANALYSIS_ACADEMIC_PAPERS.md)** - Research foundation
  - Rioplatense prosody studies
  - Empirical measurements
  - Academic citations

- **[Developer Guide](DEVELOPER_GUIDE.md)** - Development and contribution
  - Development setup
  - Project structure
  - Adding features
  - Testing guidelines
  - Code quality standards

### Deployment Documentation

- **[Docker Optimization](DOCKER_OPTIMIZATION.md)** - Docker build optimization
  - Layer caching strategy (94% faster rebuilds)
  - Build time comparison
  - Best practices
  - BuildKit optimizations

- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Production deployment
  - Docker deployment
  - Kubernetes
  - Load balancing
  - Monitoring
  - Security

---

## 🎯 Quick Navigation

### For End Users

1. Start with [Main README](../README.md) for installation
2. Try [Quick Start](../README.md#-quick-start) examples
3. Explore [Regional Spanish Guide](SPANISH_REGIONAL_GUIDE.md) for accent features
4. Reference [API Documentation](API_REFERENCE.md) for integration

### For Developers

1. Follow [Developer Guide](DEVELOPER_GUIDE.md) for setup
2. Read [Architecture](ARCHITECTURE.md) to understand design
3. Check [Docker Optimization](DOCKER_OPTIMIZATION.md) for fast iteration
4. Review [Code Quality](DEVELOPER_GUIDE.md#code-quality) standards

### For DevOps

1. Start with [Docker Optimization](DOCKER_OPTIMIZATION.md) for build efficiency
2. Configure [Docker setup](DEPLOYMENT_GUIDE.md#docker-deployment)
3. Setup [Monitoring](DEPLOYMENT_GUIDE.md#monitoring)
4. Review [Security](DEPLOYMENT_GUIDE.md#security) best practices

---

## 📚 Learning Path

### Beginner

1. **[Installation](../README.md#-installation)** - Setup environment
2. **[Quick Start](../README.md#-quick-start)** - Run first example
3. **[Python API Basics](API_REFERENCE.md#python-api)** - Simple usage
4. **[CLI Tools](API_REFERENCE.md#cli-tools)** - Command-line interface

### Intermediate

1. **[Regional Spanish Features](SPANISH_REGIONAL_GUIDE.md)** - Accent support
2. **[Text Processing](API_REFERENCE.md#text-processing)** - Advanced text handling
3. **[Audio Processing](API_REFERENCE.md#audio-processing)** - Audio pipelines
4. **[REST API](API_REFERENCE.md#rest-api)** - Server integration

### Advanced

1. **[Architecture](ARCHITECTURE.md)** - System design
2. **[Docker Optimization](DOCKER_OPTIMIZATION.md)** - Fast development workflow
3. **[Custom Features](DEVELOPER_GUIDE.md#adding-new-features)** - Extend system
4. **[Production Deployment](DEPLOYMENT_GUIDE.md)** - Scale to production

---

## 🔍 Feature Documentation

### Regional Spanish Features

| Region | Documentation | Examples |
|--------|---------------|----------|
| Rioplatense 🇦🇷🇺🇾 | [Guide](SPANISH_REGIONAL_GUIDE.md#rioplatense) | [Examples](GETTING_STARTED_REGIONAL.md#rioplatense) |
| Colombian 🇨🇴 | [Guide](SPANISH_REGIONAL_GUIDE.md#colombian) | [Examples](GETTING_STARTED_REGIONAL.md#colombian) |
| Mexican 🇲🇽 | [Guide](SPANISH_REGIONAL_GUIDE.md#mexican) | [Examples](GETTING_STARTED_REGIONAL.md#mexican) |
| Chilean 🇨🇱 | [Guide](SPANISH_REGIONAL_GUIDE.md#chilean) | [Examples](GETTING_STARTED_REGIONAL.md#chilean) |
| Caribbean 🌴 | [Guide](SPANISH_REGIONAL_GUIDE.md#caribbean) | [Examples](GETTING_STARTED_REGIONAL.md#caribbean) |
| Andean ⛰️ | [Guide](SPANISH_REGIONAL_GUIDE.md#andean) | [Examples](GETTING_STARTED_REGIONAL.md#andean) |

### TTS Quality Features

| Feature | Documentation | Usage Guide |
|---------|---------------|-------------|
| Prosody Analysis | [Prosody Guide](PROSODY_GUIDE.md) | [API Ref](API_REFERENCE.md#prosody-analysis) |
| Breath & Pauses | [Developer Guide](DEVELOPER_GUIDE.md) | [API Ref](API_REFERENCE.md#breath--pause-analysis) |
| Audio Quality | [Quality Guide](AUDIO_QUALITY_GUIDE.md) | [API Ref](API_REFERENCE.md#quality-analysis) |
| Audio Compression | [Compression Guide](AUDIO_COMPRESSION.md) | [API Ref](API_REFERENCE.md#audio-compression) |
| Crossfading | [Architecture](ARCHITECTURE.md) | [API Ref](API_REFERENCE.md#crossfading) |

---

## 🛠️ Configuration References

### Environment Variables

```bash
# Performance
ENABLE_TORCH_COMPILE=true      # Enable torch.compile
ENABLE_CUDNN_BENCHMARK=true    # cuDNN auto-tuning
TORCH_MATMUL_PRECISION=high    # TF32 precision

# GPU
CUDA_VISIBLE_DEVICES=0         # GPU selection
CUDA_LAUNCH_BLOCKING=0         # Async kernel launch

# Docker BuildKit
DOCKER_BUILDKIT=1              # Enable BuildKit for better caching

# Logging
LOG_LEVEL=INFO                 # Logging verbosity
```

See: [Docker Optimization](DOCKER_OPTIMIZATION.md#environment-variables)

### Model Parameters

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| `nfe_step` | 8-64 | 32 | Quality vs speed |
| `cfg_strength` | 1.0-5.0 | 2.0 | Guidance strength |
| `cross_fade_duration` | 0.05-1.0 | 0.15 | Crossfade time |
| `speed` | 0.5-2.0 | 1.0 | Speech rate |

See: [API Reference](API_REFERENCE.md#inference)

---

## 📊 Examples & Tutorials

### Code Examples

```python
# Basic TTS
from f5_tts.api import F5TTS
tts = F5TTS()
wav, sr, spect = tts.infer(
    ref_file="ref.wav",
    ref_text="Reference",
    gen_text="Generated text"
)
```

See: [API Reference](API_REFERENCE.md#python-api)

### Regional Spanish

```python
# Auto-detect region
from f5_tts.text import process_spanish_text
result = process_spanish_text(
    "Che boludo, ¿vos querés mate?",
    auto_detect=True
)
print(result.detected_region)  # "rioplatense"
```

See: [Regional Guide](SPANISH_REGIONAL_GUIDE.md#auto-detection)

### REST API

```bash
# Generate speech
curl -X POST "http://localhost:8000/tts" \
  -F "gen_text=Hola mundo" \
  -F "ref_audio=@ref.wav" \
  --output output.wav
```

See: [API Reference](API_REFERENCE.md#rest-api)

### Docker Build (Optimized)

```bash
# Fast development build (uses cache)
./docker-build.sh latest base

# Production build
./docker-build.sh v1.0.0 production --push
```

See: [Docker Optimization](DOCKER_OPTIMIZATION.md)

---

## 🧪 Testing & Quality

### Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest --cov=src/f5_tts tests/

# Coverage report
python analyze_coverage.py
```

See: [Developer Guide](DEVELOPER_GUIDE.md#testing)

### Test Coverage

- **Overall**: 60% code coverage
- **287 tests** across modules
- **Regional Spanish**: 100% coverage
- **Prosody**: 100% coverage (31 tests)
- **API**: 96% coverage

See: [Test Results](DEVELOPER_GUIDE.md#test-suite)

---

## 🔗 External Resources

### Papers & Research

- [F5-TTS Paper](https://arxiv.org/abs/2410.06885) - Original F5-TTS
- [E2-TTS Paper](https://arxiv.org/abs/2406.18009) - E2-TTS architecture
- [Cuello & Oro Ozán (2024)](PROSODY_ANALYSIS_ACADEMIC_PAPERS.md) - Rioplatense prosody
- [Guglielmone et al. (2014)](PROSODY_ANALYSIS_ACADEMIC_PAPERS.md) - Discourse prosody

### Models & Datasets

- [Spanish F5 Model](https://huggingface.co/jpgallegoar/F5-Spanish/) - Hugging Face
- [Original F5-TTS](https://github.com/SWivid/F5-TTS) - GitHub
- [Vocos Vocoder](https://huggingface.co/charactr/vocos-mel-24khz) - Hugging Face

### Tools & Libraries

- [PyTorch](https://pytorch.org/docs/) - Deep learning framework
- [FastAPI](https://fastapi.tiangolo.com/) - API framework
- [Docker BuildKit](https://docs.docker.com/build/buildkit/) - Advanced Docker builds
- [torchaudio](https://pytorch.org/audio/) - Audio processing

---

## 📞 Getting Help

### Documentation Issues

If you find errors or missing information in the documentation:

1. Check [existing issues](https://github.com/jpgallegoar/Spanish-F5/issues)
2. Search [discussions](https://github.com/jpgallegoar/Spanish-F5/discussions)
3. Open a [new issue](https://github.com/jpgallegoar/Spanish-F5/issues/new)

### Usage Questions

For usage questions and community support:

- [GitHub Discussions](https://github.com/jpgallegoar/Spanish-F5/discussions)
- [Original F5-TTS Issues](https://github.com/SWivid/F5-TTS/issues)

### Contributing

Want to improve documentation?

1. Fork the repository
2. Edit documentation files (Markdown)
3. Submit a pull request

See: [Contributing Guide](DEVELOPER_GUIDE.md#contributing)

---

## 📝 Document Change Log

### Recent Updates

- **2025-10**: Docker optimization documentation
  - New Docker optimization guide
  - Visual layer diagram
  - Build script documentation
  - Updated deployment guide

- **2025-10**: Prosody improvements
  - Empirically-validated prosody profiles
  - Academic research documentation
  - Discourse-level prosody

- **2025-01**: Complete documentation overhaul
  - New README with comprehensive examples
  - Complete API reference
  - Developer guide
  - Deployment guide
  - This documentation index

---

## 📂 Documentation Structure

```
docs/
├── README.md                        # This file (index)
├── es/                              # 🇪🇸 Spanish Documentation (NEW)
│   ├── ARQUITECTURA_ECOSISTEMA.md   # Vocalio ecosystem architecture
│   └── GUIA_TECNICA.md              # Detailed technical guide
├── API_REFERENCE.md                 # Complete API documentation
├── API_REFACTORING.md               # REST API architecture
├── ARCHITECTURE.md                  # System architecture
├── AUDIO_COMPRESSION.md             # Bandwidth optimization
├── AUDIO_QUALITY_GUIDE.md           # Quality analysis
├── DEPLOYMENT_GUIDE.md              # Production deployment
├── DEVELOPER_GUIDE.md               # Development and contribution
├── DOCKER_OPTIMIZATION.md           # Docker build optimization
├── GETTING_STARTED_REGIONAL.md      # Regional Spanish tutorial
├── PROSODY_ANALYSIS_ACADEMIC_PAPERS.md  # Research foundation
├── PROSODY_GUIDE.md                 # Prosody features
├── REGIONAL_QUICK_REFERENCE.md      # Quick patterns reference
└── SPANISH_REGIONAL_GUIDE.md        # Regional Spanish features

../  (root)
├── README.md                        # Main project README (English)
├── README.es.md                     # 🇪🇸 Main README (Spanish) (NEW)
└── CLAUDE.md                        # Claude Code guidelines

archive/
├── performance/                     # Historical performance tracking
│   ├── PERFORMANCE_ROADMAP.md
│   ├── PERFORMANCE_BASELINE.md
│   ├── PHASE1_BASELINE_SUMMARY.md
│   ├── PHASE2_OPTIMIZATIONS.md
│   ├── PHASE2_COMPLETE_SUMMARY.md
│   ├── COVERAGE_REPORT.md
│   └── DOCKER_LAYER_DIAGRAM.md
├── legacy-docs/                     # Archived legacy documentation
└── session-reports/                 # Historical session reports
```

---

<div align="center">

**Complete documentation for Spanish-F5 TTS**

[Main README](../README.md) | [API Reference](API_REFERENCE.md) | [Developer Guide](DEVELOPER_GUIDE.md) | [Docker Optimization](DOCKER_OPTIMIZATION.md)

[⬆ Back to Top](#spanish-f5-tts-documentation-)

</div>
