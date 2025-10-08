# Regional Spanish Support Guide

This guide covers the comprehensive regional Spanish accent, prosody, and slang support in Spanish-F5 TTS.

## Overview

Spanish-F5 includes native support for Latin American Spanish regional variants, including:

- **Rioplatense** (Argentina/Uruguay) - Distinctive sheísmo/yeísmo, voseo, Italian-influenced intonation
- **Colombian** - Clear articulation, conservative features, Paisa rhythm patterns
- **Mexican** - Clear affricates, widespread diminutives, distinctive intonation
- **Additional regions**: Chilean, Caribbean, Andean (extensible framework)

## Features

### 1. Phonetic Transformations

Automatically applies regional phonetic features:

**Rioplatense:**
- Sheísmo: "calle" → [kaʃe]
- Yeísmo rehilado: "yo" → [ʒo]
- S-aspiration: "los" → [loh]
- Participio reduction: "hablado" → "hablao"

**Colombian:**
- Conservative s-pronunciation
- Clear liquid consonants (r, l)
- Standard yeísmo

**Mexican:**
- Clear affricates (ch)
- Maintained final consonants
- Standard yeísmo

### 2. Prosodic Patterns

Identifies and marks prosodic features:

- **Intonation patterns** - Question tags, exclamations
- **Stress patterns** - Voseo forms, regional emphasis
- **Rhythm patterns** - Regional pacing and flow

### 3. Regional Slang Detection

Automatically detects and handles regional slang (modismos):

**Rioplatense:**
- che, boludo, quilombo, laburo, pibe
- Voseo: vos, tenés, querés, podés, sos

**Colombian:**
- parcero/parce, chimba, bacano, berraco, polas
- Question tags: ¿cierto?, ¿sí o qué?

**Mexican:**
- órale, güey/wey, chido, neta, padre
- Expressions: ¿qué onda?, no manches, ándele

## Usage

### Basic Usage

```python
from f5_tts.text import process_spanish_text, get_regional_processor

# Quick processing
result = process_spanish_text(
    "¿Che, vos querés ir al cine?",
    region="rioplatense"
)

print(result["normalized"])      # Normalized text
print(result["phonetic"])        # Phonetic representation
print(result["detected_slang"])  # Detected slang terms
print(result["prosodic_hints"])  # Prosodic markers
```

### Advanced Processing

```python
from f5_tts.text import SpanishRegionalProcessor, SpanishRegion

# Create processor for specific region
processor = SpanishRegionalProcessor(
    region=SpanishRegion.RIOPLATENSE,
    auto_detect=False
)

# Process text
text = "Che boludo, ¿vos sabés dónde está el laburo?"
result = processor.process(text)

print(f"Region: {result['region']}")
print(f"Original: {result['original']}")
print(f"Normalized: {result['normalized']}")
print(f"Phonetic: {result['phonetic']}")
print(f"Slang detected: {len(result['detected_slang'])} terms")

for slang in result['detected_slang']:
    print(f"  - {slang['term']}: {slang['meaning']} ({slang['usage']})")
```

### Auto-Detection

```python
# Auto-detect region from text
processor = SpanishRegionalProcessor(auto_detect=True)

texts = [
    "Che, ¿vos sabés qué onda?",           # Should detect Rioplatense
    "Parcero, eso está muy chimba",        # Should detect Colombian
    "Güey, no manches, está muy chido",    # Should detect Mexican
]

for text in texts:
    result = processor.process(text)
    print(f"Text: {text}")
    print(f"Detected region: {result['region']}\n")
```

### Using with F5TTS API

```python
from f5_tts.api import F5TTS
from f5_tts.text import get_regional_processor

# Initialize model
tts = F5TTS(model_type="F5-TTS", vocoder_name="vocos")

# Create regional processor
processor = get_regional_processor(region="rioplatense")

# Process text
gen_text = "Che, ¿vos querés tomar unos mates conmigo?"
processed = processor.process(gen_text)

# Use processed text for TTS
wav, sr, spect = tts.infer(
    ref_file="reference_rioplatense.wav",
    ref_text="Hola, ¿cómo andás?",
    gen_text=processed["phonetic"],  # Use phonetic representation
    seed=42
)

# Export
tts.export_wav(wav, "output_rioplatense.wav")
```

### Configuration

Set regional preferences globally:

```python
from f5_tts.core import get_config, set_config, GlobalConfig

# Get current config
config = get_config()

# Modify regional settings
config.spanish_region = "rioplatense"
config.auto_detect_region = True
config.apply_regional_phonetics = True

# Apply
set_config(config)
```

Or via environment variables:

```bash
export SPANISH_REGION=rioplatense
export AUTO_DETECT_REGION=true
export APPLY_REGIONAL_PHONETICS=true
```

## Dataset Preparation

### Prepare Dataset with Regional Annotations

```bash
# From CSV
python -m f5_tts.train.datasets.prepare_spanish_regional \
    --mode csv \
    --csv-path dataset.csv \
    --audio-base-dir /path/to/audio \
    --dataset-name my_spanish_dataset \
    --auto-detect \
    --max-workers 8

# From directory structure
python -m f5_tts.train.datasets.prepare_spanish_regional \
    --mode directory \
    --audio-dir /path/to/wavs \
    --transcription-dir /path/to/texts \
    --dataset-name my_spanish_dataset \
    --region rioplatense \
    --max-workers 8
```

### CSV Format

Your CSV should have these columns:

```csv
audio_path,text,region
speaker1/audio1.wav,"¿Che, cómo andás?",rioplatense
speaker2/audio2.wav,"Parcero, todo bien",colombian
speaker3/audio3.wav,"Órale güey, ¿qué onda?",mexican
```

The `region` column is optional if you use `--auto-detect`.

### Dataset Output

The script creates:

```
data/my_spanish_dataset/
├── raw/                      # Arrow format dataset
├── duration.json             # Duration metadata
└── regional_stats.json       # Regional distribution stats
```

Example `regional_stats.json`:
```json
{
  "rioplatense": {
    "count": 1500,
    "total_duration_hours": 2.5,
    "percentage": 45.0
  },
  "colombian": {
    "count": 1000,
    "total_duration_hours": 1.8,
    "percentage": 30.0
  },
  "mexican": {
    "count": 833,
    "total_duration_hours": 1.5,
    "percentage": 25.0
  }
}
```

## Regional Features Reference

### Rioplatense (Argentina/Uruguay)

**Phonetic:**
- Sheísmo/Yeísmo rehilado
- Final s-aspiration
- Participio reduction
- Italian-influenced prosody

**Slang:**
- che, boludo, quilombo, laburo, mina, pibe, chabón
- de una, al pedo, ni en pedo

**Grammar:**
- Voseo: vos, tenés, querés, podés, sos

**Prosody:**
- Rising intonation (Italian influence)
- Emphatic question intonation

### Colombian Spanish

**Phonetic:**
- Conservative s-pronunciation
- Clear liquid articulation
- Standard yeísmo

**Slang:**
- parcero/parce, chimba, bacano, berraco, polas
- ¿sí o qué?, hacer una vaca

**Grammar:**
- Standard tuteo
- Frequent question tags (¿cierto?, ¿no?)

**Prosody:**
- Clear, measured rhythm
- Softening with "pues"
- Paisa rhythm patterns (Antioquia)

### Mexican Spanish

**Phonetic:**
- Clear affricates (ch)
- Maintained final consonants
- Standard yeísmo

**Slang:**
- órale, güey/wey, chido, padre, chale, neta
- ¿qué onda?, no manches, ándele

**Grammar:**
- Widespread diminutives (ahorita, lueguito)
- Standard tuteo

**Prosody:**
- Distinctive question intonation
- Emphasis on exclamations (órale, ándele)

## Training with Regional Data

When training on regional datasets, the system automatically:

1. **Detects regional features** from text
2. **Normalizes slang** while preserving prosodic markers
3. **Applies phonetic transformations** for better acoustic modeling
4. **Tracks regional distribution** for balanced training

### Example Training

```python
from f5_tts.model import DiT
from f5_tts.train import train

# Your training script will automatically use regional annotations
# from the prepared dataset

trainer = train(
    dataset_name="my_spanish_dataset",
    # ... other training parameters
)
```

## API Reference

### `SpanishRegion` Enum

```python
class SpanishRegion(Enum):
    NEUTRAL = "neutral"
    RIOPLATENSE = "rioplatense"
    COLOMBIAN = "colombian"
    MEXICAN = "mexican"
    CHILEAN = "chilean"
    CARIBBEAN = "caribbean"
    ANDEAN = "andean"
```

### `SpanishRegionalProcessor`

```python
class SpanishRegionalProcessor:
    def __init__(
        self,
        region: SpanishRegion = SpanishRegion.NEUTRAL,
        auto_detect: bool = False
    )

    def normalize_text(self, text: str) -> str
    def apply_phonetic_features(self, text: str) -> str
    def add_prosodic_markers(self, text: str) -> Tuple[str, List[str]]
    def process(self, text: str, apply_phonetics: bool = True) -> Dict
```

### Convenience Functions

```python
def get_regional_processor(
    region: str | SpanishRegion = "neutral",
    auto_detect: bool = False
) -> SpanishRegionalProcessor

def process_spanish_text(
    text: str,
    region: str = "neutral",
    auto_detect: bool = False
) -> Dict[str, any]
```

## Best Practices

### 1. Reference Audio Selection

For best results, use reference audio that matches the target region:

- **Rioplatense**: Native Argentine/Uruguayan speakers
- **Colombian**: Preferably Bogotá or Paisa accent
- **Mexican**: Central Mexican accent works best

### 2. Text Preparation

- Include natural slang and expressions
- Use proper punctuation for prosody
- For voseo (Rioplatense), use correct conjugations

### 3. Mixed Regions

If your dataset has mixed regions:

```python
# Auto-detect handles mixed content
processor = SpanishRegionalProcessor(auto_detect=True)

# Or process each sample with its specific region
for sample in dataset:
    processor = get_regional_processor(sample["region"])
    result = processor.process(sample["text"])
```

### 4. Fine-tuning

For best accent quality:

1. **Collect region-specific data** (ideally 5+ hours per region)
2. **Use the dataset preparation script** to add annotations
3. **Train or fine-tune** with regional metadata
4. **Use region-matched reference audio** during inference

## Extending to New Regions

To add a new regional variant:

1. **Define phonetic features** in `RegionalPhonetics`
2. **Add prosodic patterns** in `RegionalProsody`
3. **Create slang dictionary** in `RegionalSlang`
4. **Update `SpanishRegion` enum**

Example:

```python
# In spanish_regional.py

class SpanishRegion(Enum):
    # ... existing regions
    CHILEAN = "chilean"

class RegionalPhonetics:
    CHILEAN_FEATURES = [
        PhoneticFeature(
            pattern=r'([aeiouáéíóú])do\b',
            replacement=r'\1o',
            description="Chilean participio reduction"
        ),
        # ... more features
    ]
```

## Performance Tips

1. **Caching**: Regional processing is fast, but cache results for repeated texts
2. **Batch Processing**: Use dataset preparation script for large datasets
3. **Auto-detect**: Only use when necessary (adds minimal overhead)
4. **Phonetic Transform**: Can be disabled if you want original text preserved

## Troubleshooting

### Region Not Detected

```python
# Be explicit about the region
processor = get_regional_processor(region="rioplatense", auto_detect=False)
```

### Slang Not Recognized

Check if the term is in the slang dictionary:

```python
from f5_tts.text import RegionalSlang, SpanishRegion

slang_dict = RegionalSlang.get_slang_dict(SpanishRegion.RIOPLATENSE)
print("boludo" in slang_dict)  # True
```

### Phonetic Transform Issues

Disable if causing problems:

```python
result = processor.process(text, apply_phonetics=False)
```

## Examples

See [examples/regional_spanish/](../examples/regional_spanish/) for:

- Basic usage examples
- Dataset preparation examples
- Training with regional data
- Multi-region inference
- Custom regional extension

## References

- Lipski, J. M. (2011). *Varieties of Spanish in the United States*
- Hualde, J. I. (2014). *The Sounds of Spanish*
- RAE - Real Academia Española dictionaries and resources
- Regional dialectology studies from Argentina, Colombia, and Mexico

## Contributing

To contribute new regional features:

1. Research phonetic/prosodic features
2. Collect slang/modismo examples
3. Implement in `spanish_regional.py`
4. Add tests and documentation
5. Submit PR with examples

---

**Need help?** Open an issue on GitHub with the `regional-spanish` label.
