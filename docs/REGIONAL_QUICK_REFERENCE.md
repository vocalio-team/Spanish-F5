# Regional Spanish Quick Reference

## Quick Start

```python
from f5_tts.text import process_spanish_text

# Process with specific region
result = process_spanish_text(
    "Che, ¿vos querés ir al cine?",
    region="rioplatense"
)

# Auto-detect region
result = process_spanish_text(
    "Parcero, eso está muy bacano",
    auto_detect=True
)
```

## Supported Regions

| Region | Code | Key Markers |
|--------|------|-------------|
| 🇦🇷 Rioplatense | `rioplatense` | che, boludo, vos, querés |
| 🇨🇴 Colombian | `colombian` | parcero, chimba, ¿cierto? |
| 🇲🇽 Mexican | `mexican` | órale, güey, ¿qué onda? |
| 🌎 Neutral | `neutral` | Standard Latin American |

## Common Phonetic Features

### Rioplatense
```
ll → ʃ     "calle" → [kaʃe]
y → ʒ      "yo" → [ʒo]
s → h      "dos" → [doh]
-ado → -ao "hablado" → "hablao"
```

### Colombian
```
s → s      "los" → [los] (maintained)
ll → y     "calle" → [kaye]
r, l clear "amor" → clear [r]
```

### Mexican
```
ch → tʃ    "chico" → [tʃiko]
ll → y     "calle" → [kaye]
finals maintained
```

## Top 10 Slang Terms

### Rioplatense 🇦🇷
1. **che** - hey/dude
2. **boludo** - dude/fool
3. **vos** - you (informal)
4. **tenés/querés/sabés** - voseo verbs
5. **quilombo** - mess/chaos
6. **laburo** - work
7. **pibe** - kid
8. **mina** - woman
9. **de una** - right away
10. **sos** - you are (voseo)

### Colombian 🇨🇴
1. **parcero/parce** - friend/buddy
2. **chimba** - great/awesome
3. **bacano** - cool/nice
4. **berraco** - tough/brave
5. **polas** - beers
6. **plata** - money
7. **¿cierto?** - right? (tag)
8. **pues** - well/then
9. **¿sí o qué?** - right?
10. **hacer una vaca** - pool money

### Mexican 🇲🇽
1. **órale** - wow/okay/alright
2. **güey/wey** - dude/man
3. **chido** - cool/nice
4. **padre** - cool/great
5. **neta** - truth
6. **¿qué onda?** - what's up?
7. **no manches** - no way
8. **ándele** - come on
9. **ahorita** - right now/soon
10. **chale** - damn/no way

## Prosodic Patterns

### Rioplatense
- ✓ Rising intonation (Italian influence)
- ✓ Emphatic stress on voseo verbs
- ✓ Question elongation

### Colombian
- ✓ Question tags (¿cierto?, ¿sí?)
- ✓ Measured, clear rhythm
- ✓ Softening with "pues"

### Mexican
- ✓ Distinctive question rise
- ✓ Exclamation emphasis
- ✓ Diminutive patterns

## Code Snippets

### Basic Processing
```python
from f5_tts.text import get_regional_processor

processor = get_regional_processor(region="rioplatense")
result = processor.process("¿Vos sabés?")
```

### With TTS
```python
from f5_tts.api import F5TTS
from f5_tts.text import get_regional_processor

tts = F5TTS()
processor = get_regional_processor(region="mexican")

text = "Órale güey, ¿qué onda?"
processed = processor.process(text)

wav, sr, _ = tts.infer(
    ref_file="mexican_ref.wav",
    ref_text="Hola",
    gen_text=processed['phonetic']
)
```

### Configure Globally
```python
from f5_tts.core import get_config, set_config

config = get_config()
config.spanish_region = "rioplatense"
config.auto_detect_region = True
set_config(config)
```

### Environment Variables
```bash
export SPANISH_REGION=rioplatense
export AUTO_DETECT_REGION=true
export APPLY_REGIONAL_PHONETICS=true
```

## Dataset Preparation

```bash
# From CSV
python -m f5_tts.train.datasets.prepare_spanish_regional \
    --mode csv \
    --csv-path data.csv \
    --audio-base-dir /audio \
    --dataset-name my_dataset \
    --auto-detect

# From directory
python -m f5_tts.train.datasets.prepare_spanish_regional \
    --mode directory \
    --audio-dir /wavs \
    --transcription-dir /texts \
    --dataset-name my_dataset \
    --region rioplatense
```

## Common Use Cases

### 1. Single Region TTS
```python
processor = get_regional_processor(region="rioplatense")
result = processor.process("Che, ¿vos querés café?")
# Use result['phonetic'] for TTS
```

### 2. Multi-Region Content
```python
processor = get_regional_processor(auto_detect=True)

for text in texts:
    result = processor.process(text)
    region = result['region']
    # Process with appropriate reference audio
```

### 3. Batch Processing
```python
from f5_tts.text import process_spanish_text

results = [
    process_spanish_text(text, auto_detect=True)
    for text in text_list
]
```

### 4. Custom Region Extension
```python
# In spanish_regional.py
class RegionalPhonetics:
    CHILEAN_FEATURES = [
        PhoneticFeature(
            pattern=r's\b',
            replacement='h',
            description="Chilean s-aspiration"
        )
    ]
```

## Output Structure

```python
result = {
    'original': 'Che, ¿vos sabés?',
    'normalized': 'Che, ¿vos sabés?',
    'phonetic': 'Che, ¿voh sabéh?',
    'final': 'Che, ¿voh sabéh?',
    'region': 'rioplatense',
    'prosodic_hints': [
        'intonation:Rioplatense rising intonation',
        'stress:Voseo stress patterns'
    ],
    'detected_slang': [
        {'term': 'che', 'meaning': 'hey/dude', 'usage': 'informal'},
        {'term': 'vos', 'type': 'pronoun', 'usage': 'standard'},
        {'term': 'sabés', 'type': 'verb', 'stress': 'final'}
    ]
}
```

## Detection Logic

**Auto-detection checks for distinctive markers:**

Rioplatense: `che`, `boludo`, `vos `, `tenés`, `pibe`
Colombian: `parcero`, `parce`, `chimba`, `bacano`, `¿cierto?`
Mexican: `órale`, `güey`, `wey`, `¿qué onda?`, `no manches`

**Example:**
```python
"Che boludo" → rioplatense (2 markers)
"Parce" → colombian (1 marker)
"Órale güey" → mexican (2 markers)
```

## API Reference

### Main Functions

```python
# Convenience function
process_spanish_text(
    text: str,
    region: str = "neutral",
    auto_detect: bool = False
) -> Dict

# Get processor
get_regional_processor(
    region: str | SpanishRegion = "neutral",
    auto_detect: bool = False
) -> SpanishRegionalProcessor
```

### Processor Methods

```python
processor.normalize_text(text: str) -> str
processor.apply_phonetic_features(text: str) -> str
processor.add_prosodic_markers(text: str) -> Tuple[str, List]
processor.process(text: str, apply_phonetics: bool = True) -> Dict
```

### Static Methods

```python
RegionalSlang.detect_region_from_text(text: str) -> Optional[SpanishRegion]
RegionalSlang.get_slang_dict(region: SpanishRegion) -> Dict
RegionalPhonetics.get_features(region: SpanishRegion) -> List
RegionalProsody.get_patterns(region: SpanishRegion) -> List
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Region not detected | Use explicit region: `region="rioplatense"` |
| Wrong phonetics | Check input text, disable: `apply_phonetics=False` |
| Missing slang | Verify term in slang dict or add custom entry |
| Import error | Check path: `from f5_tts.text import ...` |

## Performance Tips

1. **Cache processors**: Create once, reuse many times
2. **Disable auto-detect**: If region is known
3. **Batch process**: Use list comprehension
4. **Skip phonetics**: If original text needed

## Examples Directory

- `examples/regional_spanish/basic_usage.py` - 6 basic examples
- `examples/regional_spanish/tts_inference.py` - 6 TTS examples
- `examples/regional_spanish/README.md` - Full example docs

## Documentation

- 📖 [Full Regional Guide](SPANISH_REGIONAL_GUIDE.md)
- 🏗️ [Implementation Summary](../REGIONAL_SPANISH_IMPLEMENTATION.md)
- 📚 [Main README](../README.md)
- 🏛️ [Architecture](../ARCHITECTURE.md)

---

**Last Updated:** 2025-10-07
**Version:** 1.0.0
