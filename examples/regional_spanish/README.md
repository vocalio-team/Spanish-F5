# Regional Spanish Examples

This directory contains practical examples for using the regional Spanish features in Spanish-F5 TTS.

## Examples Overview

### 1. `basic_usage.py`

Demonstrates basic text processing with regional features:
- Quick processing for different regions
- Auto-detection of regions
- Detailed prosodic analysis
- Regional comparisons
- Voseo handling (Rioplatense)
- Mixed regional content

**Run:**
```bash
python basic_usage.py
```

**Output:**
```
Example 1: Quick Processing
RIOPLATENSE:
  Original:   ¿Che, vos sabés dónde está el laburo?
  Normalized: ¿Che, vos sabés dónde está el laburo?
  Phonetic:   ¿Che, voh habéh dónde ehtá el laburo?
  Slang:      ['che', 'vos', 'sabés', 'laburo']
...
```

### 2. `tts_inference.py`

Shows how to use regional processing with the F5TTS API:
- Basic inference with regional text
- Multi-region generation
- Auto-detect and generate
- Long-form content
- Prosodic emphasis
- Batch processing

**Setup:**
Before running, prepare reference audio files:
```
ref_audio/
├── rioplatense.wav
├── colombian.wav
├── mexican.wav
└── neutral.wav
```

**Run:**
```bash
python tts_inference.py
```

### 3. `dataset_preparation.ipynb` (Coming Soon)

Jupyter notebook for preparing datasets with regional annotations.

## Quick Start

### Install Dependencies

```bash
pip install -e .
```

### Basic Text Processing

```python
from f5_tts.text import process_spanish_text

# Process Rioplatense Spanish
result = process_spanish_text(
    "Che boludo, ¿vos querés ir al cine?",
    region="rioplatense"
)

print(result['phonetic'])
print(result['detected_slang'])
```

### TTS with Regional Support

```python
from f5_tts.api import F5TTS
from f5_tts.text import get_regional_processor

# Initialize
tts = F5TTS(model_type="F5-TTS", vocoder_name="vocos")
processor = get_regional_processor(region="rioplatense")

# Process text
gen_text = "¿Vos querés tomar unos mates?"
processed = processor.process(gen_text)

# Generate
wav, sr, _ = tts.infer(
    ref_file="rioplatense_ref.wav",
    ref_text="Hola che",
    gen_text=processed['phonetic']
)

# Save
tts.export_wav(wav, "output.wav")
```

## Regions Supported

| Region | Code | Key Features |
|--------|------|--------------|
| Rioplatense | `rioplatense` | Sheísmo, voseo, Italian prosody |
| Colombian | `colombian` | Clear articulation, question tags |
| Mexican | `mexican` | Diminutives, distinctive intonation |
| Neutral | `neutral` | Standard Latin American Spanish |

## Regional Features Reference

### Rioplatense (Argentina/Uruguay)

**Phonetics:**
- "ll" → [ʃ] (sheísmo)
- "y" → [ʒ] (yeísmo rehilado)
- Final 's' aspiration

**Slang:**
- che, boludo, quilombo, laburo, pibe
- Voseo: vos, tenés, querés, sos

**Example:**
```python
text = "Che boludo, ¿vos tenés tiempo?"
# → "Che boludo, ¿voh tenéh tiempo?"
```

### Colombian Spanish

**Phonetics:**
- Conservative 's'
- Clear consonants

**Slang:**
- parcero/parce, chimba, bacano, polas
- Question tags: ¿cierto?, ¿sí?

**Example:**
```python
text = "Parcero, eso está muy bacano, ¿cierto?"
# → (maintains clear pronunciation)
```

### Mexican Spanish

**Phonetics:**
- Clear affricates
- Maintained finals

**Slang:**
- órale, güey, chido, padre, neta
- Diminutives: ahorita, lueguito

**Example:**
```python
text = "Órale güey, está muy chido"
# → (maintains Mexican prosody markers)
```

## Environment Configuration

Set defaults via environment variables:

```bash
export SPANISH_REGION=rioplatense
export AUTO_DETECT_REGION=true
export APPLY_REGIONAL_PHONETICS=true
```

Or in Python:

```python
from f5_tts.core import get_config, set_config

config = get_config()
config.spanish_region = "rioplatense"
config.auto_detect_region = True
set_config(config)
```

## Dataset Preparation

Prepare a dataset with regional annotations:

```bash
python -m f5_tts.train.datasets.prepare_spanish_regional \
    --mode csv \
    --csv-path dataset.csv \
    --audio-base-dir /path/to/audio \
    --dataset-name my_spanish_dataset \
    --auto-detect \
    --max-workers 8
```

CSV format:
```csv
audio_path,text,region
audio1.wav,"Che, ¿cómo andás?",rioplatense
audio2.wav,"Parce, todo bien",colombian
```

## Tips for Best Results

### 1. Reference Audio
- Use native speakers from the target region
- 3-10 seconds of clear speech
- Match the emotional tone

### 2. Text Preparation
- Include natural slang and expressions
- Use proper punctuation
- For voseo, use correct conjugations

### 3. Prosody
- Exclamations help (¡, !)
- Question marks guide intonation (¿?)
- Regional interjections (che, órale, parce)

### 4. Fine-tuning
For production use:
- Collect 5+ hours per region
- Use the dataset preparation script
- Fine-tune with regional metadata

## Troubleshooting

### Region not detected
```python
# Be explicit
processor = get_regional_processor(region="rioplatense", auto_detect=False)
```

### Unexpected phonetics
```python
# Disable phonetic transforms
result = processor.process(text, apply_phonetics=False)
```

### Missing reference audio
```bash
# Create a reference directory
mkdir -p ref_audio
# Add your reference files
```

## Further Reading

- [Full Regional Spanish Guide](../../docs/SPANISH_REGIONAL_GUIDE.md)
- [Architecture Documentation](../../ARCHITECTURE.md)
- [Main README](../../README.md)

## Contributing

To add examples:
1. Create a new `.py` file in this directory
2. Follow the example structure
3. Document usage in this README
4. Test with multiple regions

---

**Need help?** Check the [main documentation](../../docs/SPANISH_REGIONAL_GUIDE.md) or open an issue.
