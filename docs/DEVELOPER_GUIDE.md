# Developer Guide 🛠️

Complete guide for developing and contributing to Spanish-F5 TTS.

---

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Architecture Overview](#architecture-overview)
- [Adding New Features](#adding-new-features)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Contributing](#contributing)
- [Debugging](#debugging)

---

## Development Setup

### Prerequisites

- Python 3.10 or higher
- CUDA-compatible GPU (recommended)
- Git
- conda or virtualenv

### Initial Setup

```bash
# Clone repository
git clone https://github.com/jpgallegoar/Spanish-F5.git
cd Spanish-F5

# Create conda environment
conda create -n f5-tts-dev python=3.10
conda activate f5-tts-dev

# Install PyTorch with CUDA
pip install torch==2.3.0+cu118 torchaudio==2.3.0+cu118 \
  --extra-index-url https://download.pytorch.org/whl/cu118

# Install in editable mode
pip install -e .

# Install development dependencies
pip install pre-commit pytest pytest-cov pytest-asyncio ruff black mypy

# Setup pre-commit hooks
pre-commit install
```

### IDE Setup

#### VS Code

Recommended extensions:
- Python
- Pylance
- Ruff
- autoDocstring

Settings (`.vscode/settings.json`):

```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "editor.rulers": [120],
  "files.trimTrailingWhitespace": true
}
```

#### PyCharm

1. Settings → Project → Python Interpreter → Add conda environment
2. Enable pytest as test runner
3. Set line length to 120 in Code Style

---

## Project Structure

```
Spanish-F5/
├── src/f5_tts/              # Main package
│   ├── core/                # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py        # Global configuration
│   │   ├── types.py         # Type definitions
│   │   └── protocols.py     # Protocol interfaces
│   │
│   ├── model/               # Model architectures
│   │   ├── __init__.py
│   │   ├── backbones/       # DiT, UNetT, MMDiT
│   │   ├── cfm.py           # Conditional Flow Matching
│   │   ├── dataset.py       # Dataset handling
│   │   ├── trainer.py       # Training logic
│   │   └── utils.py         # Model utilities
│   │
│   ├── audio/               # Audio processing
│   │   ├── __init__.py
│   │   ├── crossfading.py   # Crossfading algorithms
│   │   ├── processors.py    # Audio pipeline
│   │   └── quality.py       # Quality analysis
│   │
│   ├── text/                # Text processing
│   │   ├── __init__.py
│   │   ├── spanish_regional.py  # Regional Spanish
│   │   ├── normalizer.py    # Text normalization
│   │   ├── chunker.py       # Text chunking
│   │   ├── prosody.py       # Prosody analysis
│   │   └── breath_pause.py  # Breath modeling
│   │
│   ├── infer/               # Inference
│   │   ├── __init__.py
│   │   ├── utils_infer.py   # Inference utilities
│   │   ├── infer_cli.py     # CLI interface
│   │   └── infer_gradio.py  # Gradio interface
│   │
│   ├── train/               # Training
│   │   ├── __init__.py
│   │   ├── train.py         # Training script
│   │   ├── finetune_cli.py  # Finetuning CLI
│   │   └── datasets/        # Dataset preparation
│   │
│   └── api.py               # Main Python API
│
├── tests/                   # Test suite
│   ├── test_core.py
│   ├── test_spanish_regional.py
│   ├── test_audio.py
│   ├── test_api.py
│   └── ...
│
├── docs/                    # Documentation
│   ├── API_REFERENCE.md
│   ├── DEVELOPER_GUIDE.md
│   └── ...
│
├── examples/                # Example scripts
│
├── f5_tts_api.py           # REST API server
├── pyproject.toml          # Package configuration
├── ruff.toml               # Linting configuration
└── CLAUDE.md               # Claude Code guidelines
```

---

## Architecture Overview

### Core Principles

1. **Modular Design**: Separate concerns into distinct modules
2. **Protocol-Based**: Use protocols for flexibility and testability
3. **Type-Safe**: Comprehensive type hints throughout
4. **Testable**: High test coverage with unit and integration tests
5. **Documented**: Docstrings for all public APIs

### Key Components

#### 1. Core Module

Configuration and type system.

```python
# Global configuration singleton
from f5_tts.core import GlobalConfig

config = GlobalConfig.get_instance()
config.enable_torch_compile = True

# Type definitions
from f5_tts.core.types import AudioData, InferenceConfig

# Protocols for dependency injection
from f5_tts.core.protocols import AudioProcessor, Crossfader
```

#### 2. Model Module

Neural network architectures and training.

```python
from f5_tts.model import DiT, UNetT
from f5_tts.model.cfm import CFM

# DiT architecture (F5-TTS)
model = DiT(
    dim=1024,
    depth=22,
    heads=16,
    ff_mult=2
)

# UNetT architecture (E2-TTS)
model = UNetT(
    dim=1024,
    depth=24,
    heads=16
)
```

#### 3. Text Module

Text processing and regional features.

```python
from f5_tts.text import (
    SpanishRegionalProcessor,
    SpanishTextNormalizer,
    SpanishProsodyAnalyzer,
    BreathPauseAnalyzer,
    AdaptiveTextChunker
)

# Regional processing
processor = SpanishRegionalProcessor(region="rioplatense")
result = processor.process(text)

# Text normalization
normalizer = SpanishTextNormalizer()
normalized = normalizer.normalize(text)
```

#### 4. Audio Module

Audio processing and quality analysis.

```python
from f5_tts.audio import (
    AudioProcessingPipeline,
    EqualPowerCrossfader,
    AudioQualityAnalyzer
)

# Audio pipeline
pipeline = AudioProcessingPipeline()
processed = pipeline.prepare_reference_audio(audio, sr)

# Quality analysis
analyzer = AudioQualityAnalyzer()
quality = analyzer.analyze(audio_file)
```

---

## Adding New Features

### Adding a New Regional Spanish Variant

1. **Update slang dictionary** in `src/f5_tts/text/spanish_regional.py`:

```python
class RegionalSlang:
    SLANG_MARKERS = {
        # ... existing regions ...

        "castilian": {
            "vale": 1.0,
            "tío": 1.0,
            "guay": 1.0,
            # Add more markers
        }
    }
```

2. **Add phonetic rules**:

```python
class RegionalPhonetics:
    PHONETIC_RULES = {
        # ... existing regions ...

        "castilian": {
            "z_transformation": lambda text: ...,
            "d_elision": lambda text: ...,
        }
    }
```

3. **Add prosodic patterns**:

```python
class RegionalProsody:
    PROSODY_PATTERNS = {
        # ... existing regions ...

        "castilian": {
            "intonation": "European rising",
            "stress": "final-stressed",
        }
    }
```

4. **Add tests** in `tests/test_spanish_regional.py`:

```python
def test_castilian_phonetics():
    processor = SpanishRegionalProcessor(region="castilian")
    result = processor.process("Vale tío, eso está guay")
    assert "castilian" in result.region
```

### Adding a New Audio Processor

1. **Create processor class** implementing the protocol:

```python
# src/f5_tts/audio/custom_processor.py
from f5_tts.core.protocols import AudioProcessor
import numpy as np

class CustomAudioProcessor(AudioProcessor):
    """Custom audio processing algorithm."""

    def __init__(self, param1: float = 1.0):
        self.param1 = param1

    def process(
        self,
        audio: np.ndarray,
        sample_rate: int
    ) -> np.ndarray:
        """Process audio with custom algorithm."""
        # Implementation here
        processed = audio * self.param1
        return processed
```

2. **Add to module exports**:

```python
# src/f5_tts/audio/__init__.py
from .custom_processor import CustomAudioProcessor

__all__ = [
    # ... existing exports ...
    "CustomAudioProcessor",
]
```

3. **Add tests**:

```python
# tests/test_custom_processor.py
from f5_tts.audio import CustomAudioProcessor
import numpy as np

def test_custom_processor():
    processor = CustomAudioProcessor(param1=2.0)
    audio = np.random.randn(24000)
    result = processor.process(audio, 24000)
    assert result.shape == audio.shape
```

### Adding a New REST API Endpoint

1. **Define request/response models**:

```python
# f5_tts_api.py
from pydantic import BaseModel

class CustomRequest(BaseModel):
    text: str
    param1: int = 42

class CustomResponse(BaseModel):
    result: str
    metadata: dict
```

2. **Add endpoint handler**:

```python
@app.post("/custom", response_model=CustomResponse)
async def custom_endpoint(request: CustomRequest):
    """Custom endpoint description."""
    try:
        # Process request
        result = process_custom(request.text, request.param1)

        return CustomResponse(
            result=result,
            metadata={"param1": request.param1}
        )
    except Exception as e:
        logger.error(f"Custom endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

3. **Add tests**:

```python
# tests/test_api_custom.py
from fastapi.testclient import TestClient
from f5_tts_api import app

client = TestClient(app)

def test_custom_endpoint():
    response = client.post(
        "/custom",
        json={"text": "test", "param1": 100}
    )
    assert response.status_code == 200
    assert "result" in response.json()
```

---

## Testing

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific module
pytest tests/test_spanish_regional.py -v

# Specific test
pytest tests/test_spanish_regional.py::test_rioplatense_detection -v

# With coverage
pytest --cov=src/f5_tts --cov-report=html tests/

# Coverage analysis
python analyze_coverage.py
```

### Writing Tests

#### Unit Tests

```python
import pytest
from f5_tts.text import normalize_spanish_text

def test_number_normalization():
    """Test number to text conversion."""
    result = normalize_spanish_text("Tengo 25 euros")
    assert "veinticinco" in result

def test_date_normalization():
    """Test date formatting."""
    result = normalize_spanish_text("Hoy es 01/03/2024")
    assert "primero de marzo" in result

@pytest.mark.parametrize("input,expected", [
    ("25", "veinticinco"),
    ("100", "cien"),
    ("1000", "mil"),
])
def test_numbers_parametrized(input, expected):
    """Test various number conversions."""
    result = normalize_spanish_text(f"Número {input}")
    assert expected in result
```

#### Integration Tests

```python
from f5_tts.api import F5TTS
from unittest.mock import Mock, patch

@patch('f5_tts.api.load_model')
@patch('f5_tts.api.load_vocoder')
def test_full_inference_pipeline(mock_vocoder, mock_model):
    """Test complete inference pipeline."""
    # Setup mocks
    mock_model.return_value = Mock()
    mock_vocoder.return_value = Mock()

    # Initialize TTS
    tts = F5TTS()

    # Mock inference
    with patch('f5_tts.api.infer_process') as mock_infer:
        mock_infer.return_value = (
            np.random.randn(24000),  # wav
            24000,                    # sr
            np.random.randn(100, 100) # spect
        )

        wav, sr, spect = tts.infer(
            ref_file="test.wav",
            ref_text="test",
            gen_text="test"
        )

        assert wav.shape[0] == 24000
        assert sr == 24000
```

#### Async Tests

```python
import pytest
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_async_endpoint():
    """Test asynchronous endpoint."""
    client = TestClient(app)
    response = await client.post("/async-endpoint", json={})
    assert response.status_code == 200
```

### Test Fixtures

```python
# tests/conftest.py
import pytest
import numpy as np

@pytest.fixture
def sample_audio():
    """Generate sample audio data."""
    return np.random.randn(24000).astype(np.float32)

@pytest.fixture
def sample_text():
    """Provide sample Spanish text."""
    return "Hola, ¿cómo estás? Muy bien, gracias."

# Use in tests
def test_with_fixtures(sample_audio, sample_text):
    """Test using fixtures."""
    assert sample_audio.shape == (24000,)
    assert isinstance(sample_text, str)
```

---

## Code Quality

### Linting and Formatting

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Ruff (linting)
ruff check . --fix

# Ruff (formatting)
ruff format .

# Check specific file
ruff check src/f5_tts/text/normalizer.py
```

### Type Checking

```bash
# mypy (optional, not enforced)
mypy src/f5_tts/
```

### Code Style Guidelines

#### Type Hints

```python
from typing import List, Dict, Optional, Union, Tuple
import numpy as np

def process_text(
    text: str,
    region: Optional[str] = None,
    apply_phonetics: bool = False
) -> Dict[str, any]:
    """Process text with regional features."""
    pass

def crossfade(
    audio1: np.ndarray,
    audio2: np.ndarray,
    sample_rate: int = 24000
) -> np.ndarray:
    """Crossfade two audio segments."""
    pass
```

#### Docstrings

Use Google-style docstrings:

```python
def normalize_spanish_text(text: str, region: Optional[str] = None) -> str:
    """
    Normalize Spanish text for TTS processing.

    Converts numbers, dates, currencies, and abbreviations to text form.
    Handles regional variations when region is specified.

    Args:
        text: Input text to normalize
        region: Optional regional variant (e.g., "rioplatense")

    Returns:
        Normalized text suitable for TTS

    Raises:
        ValueError: If text is empty or invalid

    Example:
        >>> normalize_spanish_text("Tengo 25 euros")
        'Tengo veinticinco euros'
        >>> normalize_spanish_text("Son las 14:30")
        'Son las catorce treinta'
    """
    pass
```

#### Error Handling

```python
class RegionalProcessorError(Exception):
    """Base exception for regional processor."""
    pass

class InvalidRegionError(RegionalProcessorError):
    """Invalid region specified."""
    pass

def process_regional_text(text: str, region: str) -> str:
    """Process text with regional features."""
    if not text:
        raise ValueError("Text cannot be empty")

    if region not in SUPPORTED_REGIONS:
        raise InvalidRegionError(
            f"Unsupported region: {region}. "
            f"Supported: {', '.join(SUPPORTED_REGIONS)}"
        )

    try:
        return _process(text, region)
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise RegionalProcessorError(f"Processing failed: {e}") from e
```

---

## Contributing

### Contribution Workflow

1. **Fork the repository**

2. **Create a feature branch**:
   ```bash
   git checkout -b feature/my-new-feature
   ```

3. **Make changes** following code guidelines

4. **Add tests** for new functionality

5. **Run tests and linting**:
   ```bash
   pytest tests/ -v
   pre-commit run --all-files
   ```

6. **Commit changes**:
   ```bash
   git add .
   git commit -m "Add my new feature"
   ```

7. **Push to your fork**:
   ```bash
   git push origin feature/my-new-feature
   ```

8. **Create Pull Request** on GitHub

### Pull Request Guidelines

- **Title**: Clear, descriptive title
- **Description**: Explain what and why
- **Tests**: Include tests for new features
- **Documentation**: Update relevant docs
- **Code Quality**: Pass all linting checks
- **Coverage**: Aim for >80% coverage for new code

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `test`: Adding tests
- `refactor`: Code restructuring
- `perf`: Performance improvement
- `chore`: Maintenance tasks

Example:
```
feat(regional): Add Castilian Spanish variant

- Add slang markers for Castilian
- Implement z/c distinction phonetics
- Add prosodic patterns
- Include comprehensive tests

Closes #123
```

---

## Debugging

### Logging

```python
import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Use in code
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### Debugging Tools

#### pdb (Python Debugger)

```python
import pdb

def my_function(x):
    pdb.set_trace()  # Breakpoint
    result = x * 2
    return result
```

#### VS Code Debugger

Launch configuration (`.vscode/launch.json`):

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal"
    },
    {
      "name": "Python: Pytest",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["-v", "${file}"]
    }
  ]
}
```

### Performance Profiling

```python
import cProfile
import pstats

# Profile function
profiler = cProfile.Profile()
profiler.enable()

# Code to profile
result = my_function()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

---

## Resources

### Documentation
- [Architecture](../ARCHITECTURE.md)
- [API Reference](API_REFERENCE.md)
- [Regional Spanish Guide](SPANISH_REGIONAL_GUIDE.md)

### External Resources
- [PyTorch Documentation](https://pytorch.org/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [pytest Documentation](https://docs.pytest.org/)

### Related Projects
- [F5-TTS Original](https://github.com/SWivid/F5-TTS)
- [E2-TTS Paper](https://arxiv.org/abs/2406.18009)

---

[⬆ Back to Top](#developer-guide-)
