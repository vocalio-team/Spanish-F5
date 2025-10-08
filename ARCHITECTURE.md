# F5-TTS Modular Architecture

## Overview

This document describes the new modular architecture for F5-TTS, designed to improve maintainability, testability, and extensibility.

## Architecture Principles

1. **Separation of Concerns** - Each module has a single, well-defined responsibility
2. **Dependency Injection** - Components can be easily swapped and tested
3. **Protocol-Based Design** - Use protocols/interfaces for flexibility
4. **Configuration Management** - Centralized, environment-aware configuration
5. **Type Safety** - Strong typing with dataclasses and protocols

## Module Structure

```
src/f5_tts/
├── core/                   # Core types, config, and protocols
│   ├── config.py          # Centralized configuration
│   ├── types.py           # Type definitions and protocols
│   └── __init__.py
│
├── audio/                  # Audio processing components
│   ├── crossfading.py     # Crossfade algorithms
│   ├── processors.py      # Audio processing pipeline
│   └── __init__.py
│
├── text/                   # Text processing
│   ├── chunker.py         # Text chunking strategies
│   └── __init__.py
│
├── inference/              # Inference pipeline (to be implemented)
│   ├── pipeline.py        # Main inference orchestration
│   ├── batch_processor.py # Batch processing logic
│   └── cache.py           # Reference audio caching
│
├── vocoder/                # Vocoder abstraction (to be implemented)
│   ├── base.py            # Vocoder interface
│   ├── vocos.py           # Vocos implementation
│   └── bigvgan.py         # BigVGAN implementation
│
├── api.py                  # Original F5TTS class (legacy)
├── infer/                  # Original inference code (legacy)
└── model/                  # Model definitions (unchanged)
```

## Key Components

### 1. Core Module (`f5_tts.core`)

**Purpose:** Foundational types, configurations, and protocols

**Key Classes:**
- `GlobalConfig` - Centralized configuration management
- `AudioData` - Standardized audio data representation
- `InferenceConfig` - Inference parameters
- `AudioProcessingConfig` - Audio processing settings

**Protocols:**
- `AudioProcessor` - Interface for audio processing components
- `Crossfader` - Interface for crossfading algorithms
- `TextChunker` - Interface for text chunking strategies
- `VocoderInterface` - Interface for vocoder implementations

**Usage:**
```python
from f5_tts.core import get_config, AudioData

# Get global configuration
config = get_config()

# Create audio data
audio = AudioData(waveform=wav, sample_rate=24000)
```

### 2. Audio Module (`f5_tts.audio`)

**Purpose:** All audio processing operations

**Components:**

#### Crossfading (`crossfading.py`)
- `EqualPowerCrossfader` - Industry-standard equal-power crossfading
- `RaisedCosineCrossfader` - Hann window crossfading
- `LinearCrossfader` - Simple linear crossfading
- `apply_edge_fades()` - Apply gentle fades at audio edges

#### Processors (`processors.py`)
- `AudioNormalizer` - DC offset removal, RMS/amplitude normalization
- `AudioResampler` - High-quality Kaiser window resampling
- `StereoToMono` - Stereo to mono conversion
- `AudioClipping` - Prevent clipping
- `AudioProcessingPipeline` - Complete processing pipeline

**Usage:**
```python
from f5_tts.audio import (
    get_crossfader,
    CrossfadeType,
    AudioProcessingPipeline,
    apply_edge_fades
)

# Get equal-power crossfader
crossfader = get_crossfader(CrossfadeType.EQUAL_POWER)
result = crossfader.crossfade(audio1, audio2, duration=0.5, sample_rate=24000)

# Use processing pipeline
pipeline = AudioProcessingPipeline()
processed = pipeline.prepare_reference_audio(audio, sr, target_rms=0.1)
```

### 3. Text Module (`f5_tts.text`)

**Purpose:** Text processing and chunking

**Components:**

#### Chunkers (`chunker.py`)
- `SentenceBasedChunker` - Intelligent sentence-based chunking
- `AdaptiveChunker` - Adjusts chunk size based on reference audio
- `FixedLengthChunker` - Simple fixed-length chunking

**Usage:**
```python
from f5_tts.text import get_chunker

# Sentence-based chunking
chunker = get_chunker("sentence")
chunks = chunker.chunk(text, max_chars=500)

# Adaptive chunking
chunker = get_chunker(
    "adaptive",
    ref_audio_duration=10.0,
    ref_text_length=200
)
chunks = chunker.chunk(text)
```

## Migration Guide

### Before (Monolithic)

```python
from f5_tts.infer.utils_infer import infer_process

# Everything is tightly coupled in one function
wav, sr, spect = infer_process(
    ref_file="ref.wav",
    ref_text="reference text",
    gen_text="generated text",
    model_obj=model,
    vocoder=vocoder,
    # ... many parameters
)
```

### After (Modular)

```python
from f5_tts.core import get_config, InferenceConfig
from f5_tts.audio import AudioProcessingPipeline, get_crossfader, CrossfadeType
from f5_tts.text import get_chunker

# 1. Setup configuration
config = get_config()
inference_config = InferenceConfig(nfe_step=16, cfg_strength=2.0)

# 2. Create processing components
audio_pipeline = AudioProcessingPipeline()
crossfader = get_crossfader(CrossfadeType.EQUAL_POWER)
chunker = get_chunker("sentence")

# 3. Process in steps (easier to debug and customize)
# Load and prepare reference audio
ref_audio = torchaudio.load("ref.wav")
prepared_audio = audio_pipeline.prepare_reference_audio(
    ref_audio[0],
    ref_audio[1],
    target_rms=0.1
)

# Chunk text
chunks = chunker.chunk(gen_text, max_chars=500)

# Process each chunk (simplified - full pipeline in inference module)
generated_chunks = []
for chunk in chunks:
    # Run model inference
    output = model.sample(...)
    generated_chunks.append(output)

# Combine with crossfading
final_audio = generated_chunks[0]
for next_chunk in generated_chunks[1:]:
    final_audio = crossfader.crossfade(
        final_audio,
        next_chunk,
        duration=0.5,
        sample_rate=24000
    )

# Finalize output
final_audio = audio_pipeline.finalize_output_audio(final_audio)
```

## Benefits

### 1. Testability
- Each component can be tested independently
- Easy to mock dependencies
- Clear input/output contracts

```python
# Test crossfader in isolation
def test_equal_power_crossfade():
    crossfader = EqualPowerCrossfader()
    audio1 = np.ones(48000)
    audio2 = np.zeros(48000)
    result = crossfader.crossfade(audio1, audio2, 0.5, 24000)
    assert len(result) == 96000 - 12000  # Overlap removed
```

### 2. Extensibility
- Add new crossfading algorithms by implementing `Crossfader` protocol
- Add new chunking strategies by extending `BaseTextChunker`
- Swap components without changing other code

```python
# Add custom crossfader
class ExponentialCrossfader:
    def crossfade(self, audio1, audio2, duration, sample_rate):
        # Custom implementation
        ...

# Use it
crossfader = ExponentialCrossfader()
```

### 3. Maintainability
- Clear module boundaries
- Easy to locate and fix bugs
- Self-documenting code structure

### 4. Performance Optimization
- Easy to swap implementations (e.g., GPU-accelerated processors)
- Can cache/reuse components
- Profile individual components

### 5. Configuration Management
- Centralized configuration
- Environment-aware defaults
- Easy to override per-request

```python
# Override config for specific use case
from f5_tts.core import GlobalConfig, set_config

custom_config = GlobalConfig(
    default_cross_fade_duration=0.8,
    min_chunk_chars=1000,
    enable_torch_compile=False
)
set_config(custom_config)
```

## Next Steps

### Immediate (Phase 1)
- [x] Core module with types and config
- [x] Audio processing module
- [x] Text chunking module
- [ ] Inference pipeline module
- [ ] Vocoder abstraction module

### Near-term (Phase 2)
- [ ] Migrate API to use new modules
- [ ] Add comprehensive tests
- [ ] Add benchmarks for performance validation
- [ ] Create example notebooks

### Long-term (Phase 3)
- [ ] Plugin system for custom processors
- [ ] Streaming inference support
- [ ] Advanced caching strategies
- [ ] Multi-GPU support
- [ ] WebSocket streaming API

## Examples

See `examples/` directory for:
- Basic usage examples
- Custom component examples
- Performance tuning examples
- Integration examples

## Backwards Compatibility

The original `f5_tts.api.F5TTS` class remains unchanged for backwards compatibility.
New code should use the modular components for better flexibility.

## Contributing

When adding new features:
1. Identify the appropriate module
2. Create protocol/interface if needed
3. Implement with clear type hints
4. Add tests
5. Update documentation
6. Ensure backwards compatibility

## Performance Considerations

### Optimized Settings
```python
from f5_tts.core import AudioProcessingConfig

# High quality (slower)
config = AudioProcessingConfig(
    resampling_method="kaiser_window",
    lowpass_filter_width=64,
    rolloff=0.99
)

# Fast (lower quality)
config = AudioProcessingConfig(
    resampling_method="sinc_interpolation",
    lowpass_filter_width=16,
    rolloff=0.95
)
```

### Memory Management
- Use generators for large batches
- Clean up intermediate tensors
- Consider chunk size vs. memory tradeoff

## Questions?

See:
- `PERFORMANCE_OPTIMIZATIONS.md` - Performance tuning guide
- `examples/` - Usage examples
- `tests/` - Test examples
