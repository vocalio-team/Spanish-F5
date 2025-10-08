# Spanish-F5 TTS Documentation 📚

Welcome to the comprehensive documentation for Spanish-F5 TTS! This guide will help you get started, understand the architecture, and master advanced features.

---

## 📖 Documentation Index

### Getting Started

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

- **[Prosody Guide](../PROSODY_GUIDE.md)** - Prosodic modeling features
  - Intonation patterns
  - Stress markers
  - Rhythm analysis

- **[Audio Quality Guide](../AUDIO_QUALITY_GUIDE.md)** - Audio quality analysis
  - Quality metrics
  - Issue detection
  - Improvement strategies

### Technical Documentation

- **[Architecture](../ARCHITECTURE.md)** - System architecture and design
  - Modular structure
  - Core components
  - Data flow
  - Extension points

- **[Performance Optimizations](../PERFORMANCE_OPTIMIZATIONS.md)** - Optimization techniques
  - Torch.compile
  - cuDNN tuning
  - Adaptive features
  - Benchmarks

- **[Developer Guide](DEVELOPER_GUIDE.md)** - Development and contribution
  - Development setup
  - Project structure
  - Adding features
  - Testing guidelines
  - Code quality standards

- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Production deployment
  - Docker deployment
  - Kubernetes
  - Load balancing
  - Monitoring
  - Security

### API & Integration

- **[Enhanced API Features](API_ENHANCED.md)** - Advanced API features
  - Enhancement endpoints
  - Analysis tools
  - Integration examples

- **[Training Guide](../src/f5_tts/train/README.md)** - Training and finetuning
  - Dataset preparation
  - Training configuration
  - Finetuning process

- **[Inference Guide](../src/f5_tts/infer/README.md)** - Detailed inference instructions
  - CLI usage
  - Gradio interface
  - Advanced parameters

---

## 🎯 Quick Navigation

### For End Users

1. Start with [Main README](../README.md) for installation
2. Try [Quick Start](../README.md#-quick-start) examples
3. Explore [Regional Spanish Guide](SPANISH_REGIONAL_GUIDE.md) for accent features
4. Reference [API Documentation](API_REFERENCE.md) for integration

### For Developers

1. Follow [Developer Guide](DEVELOPER_GUIDE.md) for setup
2. Read [Architecture](../ARCHITECTURE.md) to understand design
3. Check [Testing Guide](DEVELOPER_GUIDE.md#testing) for contribution
4. Review [Code Quality](DEVELOPER_GUIDE.md#code-quality) standards

### For DevOps

1. Start with [Deployment Guide](DEPLOYMENT_GUIDE.md)
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

1. **[Architecture](../ARCHITECTURE.md)** - System design
2. **[Performance Tuning](../PERFORMANCE_OPTIMIZATIONS.md)** - Optimization
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
| Prosody Analysis | [Prosody Guide](../PROSODY_GUIDE.md) | [API Ref](API_REFERENCE.md#prosody-analysis) |
| Breath & Pauses | [Developer Guide](DEVELOPER_GUIDE.md) | [API Ref](API_REFERENCE.md#breath--pause-analysis) |
| Audio Quality | [Quality Guide](../AUDIO_QUALITY_GUIDE.md) | [API Ref](API_REFERENCE.md#quality-analysis) |
| Adaptive NFE | [Performance](../PERFORMANCE_OPTIMIZATIONS.md) | [API Ref](API_REFERENCE.md#adaptive-configuration) |
| Crossfading | [Architecture](../ARCHITECTURE.md) | [API Ref](API_REFERENCE.md#crossfading) |

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

# Logging
LOG_LEVEL=INFO                 # Logging verbosity
```

See: [Performance Guide](../PERFORMANCE_OPTIMIZATIONS.md#environment-variables)

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
- **Breath & Pause**: 99% coverage
- **API**: 96% coverage

See: [Test Results](DEVELOPER_GUIDE.md#test-suite)

---

## 🔗 External Resources

### Papers & Research

- [F5-TTS Paper](https://arxiv.org/abs/2410.06885) - Original F5-TTS
- [E2-TTS Paper](https://arxiv.org/abs/2406.18009) - E2-TTS architecture
- [Emilia Dataset](https://arxiv.org/abs/2407.05361) - Training data
- [WenetSpeech4TTS](https://arxiv.org/abs/2406.05763) - Speech corpus

### Models & Datasets

- [Spanish F5 Model](https://huggingface.co/jpgallegoar/F5-Spanish/) - Hugging Face
- [Original F5-TTS](https://github.com/SWivid/F5-TTS) - GitHub
- [Vocos Vocoder](https://huggingface.co/charactr/vocos-mel-24khz) - Hugging Face

### Tools & Libraries

- [PyTorch](https://pytorch.org/docs/) - Deep learning framework
- [FastAPI](https://fastapi.tiangolo.com/) - API framework
- [Gradio](https://gradio.app/) - Web interfaces
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

- **2025-01**: Complete documentation overhaul
  - New README with comprehensive examples
  - Complete API reference
  - Developer guide
  - Deployment guide
  - This documentation index

- **2024-12**: Regional Spanish features
  - Regional Spanish guide
  - Getting started tutorial
  - Quick reference

- **2024-11**: Initial documentation
  - Basic README
  - Architecture overview
  - CLAUDE.md guidelines

---

## 🎨 Documentation Style Guide

When contributing documentation:

- **Headings**: Use descriptive, action-oriented headings
- **Code Blocks**: Include language identifiers
- **Examples**: Provide complete, runnable examples
- **Links**: Use relative paths for internal links
- **Emojis**: Use sparingly for visual navigation
- **Tables**: For structured comparisons
- **Line Length**: Keep under 100 characters
- **Tone**: Clear, helpful, professional

---

## 📂 Documentation Structure

```
docs/
├── README.md                        # This file (index)
├── API_REFERENCE.md                 # Complete API documentation
├── DEVELOPER_GUIDE.md               # Development and contribution
├── DEPLOYMENT_GUIDE.md              # Production deployment
├── SPANISH_REGIONAL_GUIDE.md        # Regional Spanish features
├── GETTING_STARTED_REGIONAL.md      # Regional Spanish tutorial
├── REGIONAL_QUICK_REFERENCE.md      # Quick patterns reference
├── API_ENHANCED.md                  # Enhanced API features
└── ENHANCEMENT_SUMMARY.md           # Feature summary

../  (root)
├── README.md                        # Main project README
├── ARCHITECTURE.md                  # System architecture
├── PERFORMANCE_OPTIMIZATIONS.md     # Performance guide
├── PROSODY_GUIDE.md                 # Prosody features
├── AUDIO_QUALITY_GUIDE.md           # Quality analysis
└── CLAUDE.md                        # Claude Code guidelines
```

---

<div align="center">

**Complete documentation for Spanish-F5 TTS**

[Main README](../README.md) | [API Reference](API_REFERENCE.md) | [Developer Guide](DEVELOPER_GUIDE.md) | [Deployment](DEPLOYMENT_GUIDE.md)

[⬆ Back to Top](#spanish-f5-tts-documentation-)

</div>
