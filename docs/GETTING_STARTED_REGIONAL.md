# Getting Started with Regional Spanish Features

A step-by-step guide to using regional Spanish accents, prosody, and slang in Spanish-F5 TTS.

## 5-Minute Quick Start

### Step 1: Test the Feature

```bash
cd Spanish-F5
python3 -c "
import sys
sys.path.insert(0, 'src')
from f5_tts.text import process_spanish_text

result = process_spanish_text(
    'Che boludo, ¿vos querés tomar unos mates?',
    region='rioplatense'
)

print('Original:', result['original'])
print('Phonetic:', result['phonetic'])
print('Slang detected:', [s['term'] for s in result['detected_slang']])
"
```

**Expected output:**
```
Original: Che boludo, ¿vos querés tomar unos mates?
Phonetic: Che boludo, ¿voh queréh tomar unoh mateh?
Slang detected: ['che', 'boludo', 'vos', 'querés']
```

### Step 2: Try Auto-Detection

```python
from f5_tts.text import process_spanish_text

texts = [
    "Che, ¿vos sabés?",           # Should detect: rioplatense
    "Parce, eso está muy bacano", # Should detect: colombian
    "Órale güey, qué padre"       # Should detect: mexican
]

for text in texts:
    result = process_spanish_text(text, auto_detect=True)
    print(f"{text} → {result['region']}")
```

### Step 3: Run the Examples

```bash
cd examples/regional_spanish
python basic_usage.py
```

## Common Use Cases

### Use Case 1: Generate Rioplatense Spanish Speech

```python
from f5_tts.api import F5TTS
from f5_tts.text import get_regional_processor

# Setup
tts = F5TTS(model_type="F5-TTS", vocoder_name="vocos")
processor = get_regional_processor(region="rioplatense")

# Prepare text
text = "Che, ¿vos tenés tiempo para tomar un café?"
processed = processor.process(text)

print(f"Detected slang: {[s['term'] for s in processed['detected_slang']]}")
# → ['che', 'vos', 'tenés']

# Generate (use reference audio from Rioplatense speaker)
wav, sr, _ = tts.infer(
    ref_file="path/to/rioplatense_reference.wav",
    ref_text="Hola, ¿cómo andás?",
    gen_text=processed['phonetic'],
    seed=42
)

# Save
tts.export_wav(wav, "rioplatense_output.wav")
```

### Use Case 2: Process Multiple Regions

```python
from f5_tts.text import get_regional_processor

# Create processors for each region
processors = {
    'rioplatense': get_regional_processor('rioplatense'),
    'colombian': get_regional_processor('colombian'),
    'mexican': get_regional_processor('mexican')
}

# Your data with known regions
data = [
    {'region': 'rioplatense', 'text': '¿Vos querés ir al cine?'},
    {'region': 'colombian', 'text': 'Parce, vamos a almorzar'},
    {'region': 'mexican', 'text': 'Órale, vamos por tacos'}
]

# Process each
for item in data:
    processor = processors[item['region']]
    result = processor.process(item['text'])

    print(f"{item['region']}: {result['phonetic']}")
    # Use result['phonetic'] for TTS generation
```

### Use Case 3: Auto-Detect from User Input

```python
from f5_tts.text import process_spanish_text

def process_user_text(user_input):
    """Process user text and auto-detect region."""
    result = process_spanish_text(user_input, auto_detect=True)

    return {
        'text': result['phonetic'],
        'region': result['region'],
        'slang': result['detected_slang'],
        'hints': result['prosodic_hints']
    }

# Example
user_text = "Che boludo, esto está re copado"
info = process_user_text(user_text)

print(f"Detected region: {info['region']}")
print(f"Slang found: {len(info['slang'])} terms")
print(f"Use this for TTS: {info['text']}")
```

### Use Case 4: Dataset Preparation

```bash
# Organize your data
mkdir -p my_dataset/audio
mkdir -p my_dataset/texts

# Create CSV
cat > dataset.csv << EOF
audio_path,text,region
audio/arg_001.wav,"Che, ¿cómo andás?",rioplatense
audio/col_001.wav,"Parce, todo bien",colombian
audio/mex_001.wav,"Órale, ¿qué onda?",mexican
EOF

# Process dataset
python -m f5_tts.train.datasets.prepare_spanish_regional \
    --mode csv \
    --csv-path dataset.csv \
    --audio-base-dir my_dataset \
    --dataset-name my_spanish_tts \
    --max-workers 4
```

## Configuration Options

### Option 1: Per-Request Configuration

```python
from f5_tts.text import get_regional_processor

# Create processor with specific settings
processor = get_regional_processor(
    region="rioplatense",
    auto_detect=False  # Don't auto-detect, use specified region
)

result = processor.process(
    text="Your text here",
    apply_phonetics=True  # Apply phonetic transformations
)
```

### Option 2: Global Configuration

```python
from f5_tts.core import get_config, set_config

config = get_config()
config.spanish_region = "rioplatense"
config.auto_detect_region = False
config.apply_regional_phonetics = True
set_config(config)

# Now all processing uses these defaults
```

### Option 3: Environment Variables

```bash
export SPANISH_REGION=rioplatense
export AUTO_DETECT_REGION=true
export APPLY_REGIONAL_PHONETICS=true

python your_script.py
```

## Understanding the Output

When you process text, you get a dictionary with these fields:

```python
result = {
    'original': 'Che, ¿vos sabés?',
    'normalized': 'Che, ¿vos sabés?',  # Normalized form
    'phonetic': 'Che, ¿voh sabéh?',    # Phonetic transformation
    'final': 'Che, ¿voh sabéh?',       # Final text for TTS
    'region': 'rioplatense',            # Detected/specified region
    'prosodic_hints': [...],            # Intonation, stress hints
    'detected_slang': [...]             # List of slang terms found
}
```

**Which field to use?**

- **For TTS**: Use `result['phonetic']` or `result['final']`
- **For display**: Use `result['normalized']`
- **For analysis**: Check `result['detected_slang']` and `result['prosodic_hints']`

## Regional Differences at a Glance

### Phonetic Differences

| Text | Rioplatense | Colombian | Mexican |
|------|-------------|-----------|---------|
| "¿Vos sabés?" | "¿Voh sabéh?" | N/A (uses tú) | N/A (uses tú) |
| "calle" | "caʃe" | "kaye" | "kaye" |
| "mucho" | "mutʃo" | "mucho" | "mutʃo" |
| "los dos" | "loh doh" | "los dos" | "los dos" |

### Slang Detection

```python
# Rioplatense markers
"che", "boludo", "vos", "quilombo"

# Colombian markers
"parcero", "parce", "chimba", "bacano"

# Mexican markers
"órale", "güey", "chido", "padre"
```

## Tips for Best Results

### 1. Choose the Right Reference Audio

For best accent quality, use reference audio from a speaker of the target region:

```python
region_refs = {
    'rioplatense': 'refs/argentina_speaker.wav',
    'colombian': 'refs/colombia_speaker.wav',
    'mexican': 'refs/mexico_speaker.wav'
}

region = 'rioplatense'
ref_file = region_refs[region]
```

### 2. Include Regional Expressions

For more authentic results, include regional slang:

```python
# Good - includes regional markers
"Che boludo, ¿vos querés ir a tomar unos mates?"

# Okay - standard Spanish
"Hola, ¿quieres ir a tomar algo?"
```

### 3. Use Proper Punctuation

Punctuation helps with prosody:

```python
# Good - helps prosody
"¿Che, vos sabés dónde está?"

# Less good - missing punctuation
"che vos sabes donde esta"
```

### 4. For Voseo (Rioplatense)

Use correct voseo conjugations:

```python
# Correct voseo
"vos tenés", "vos querés", "vos sabés", "vos sos"

# Not: "vos tienes", "vos quieres" (tuteo forms)
```

## Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'f5_tts'"

**Solution:**
```bash
# Make sure you're in the right directory
cd Spanish-F5

# If running from Python directly
python -c "import sys; sys.path.insert(0, 'src'); from f5_tts.text import ..."

# Or install in editable mode
pip install -e .
```

### Problem: Region not detected

**Solution:**
```python
# Be explicit about the region
from f5_tts.text import get_regional_processor

processor = get_regional_processor(region="rioplatense", auto_detect=False)
result = processor.process(text)
```

### Problem: Unexpected phonetic output

**Solution:**
```python
# Check what transformations are being applied
result = processor.process(text)
print("Original:", result['original'])
print("Phonetic:", result['phonetic'])

# Or disable phonetics
result = processor.process(text, apply_phonetics=False)
```

### Problem: Reference audio doesn't match region

**Solution:**
```python
# Make sure reference audio is from correct region
# For Rioplatense, use Argentine/Uruguayan speaker
# For Colombian, use Colombian speaker
# For Mexican, use Mexican speaker

# Check your reference file
ref_file = "path/to/reference.wav"
ref_region = "rioplatense"  # Make sure this matches the speaker
```

## Next Steps

### Learn More

1. **Read the full guide**: [Regional Spanish Guide](SPANISH_REGIONAL_GUIDE.md)
2. **Run examples**: `python examples/regional_spanish/basic_usage.py`
3. **Check API reference**: See [Quick Reference](REGIONAL_QUICK_REFERENCE.md)

### Try Advanced Features

1. **Long-form content**: Process longer texts with chunking
2. **Batch processing**: Process multiple samples efficiently
3. **Dataset creation**: Prepare regional datasets for training

### Contribute

1. **Add new regions**: Extend to Chilean, Caribbean, Andean
2. **Improve phonetics**: Add more phonetic rules
3. **Expand slang**: Add more regional expressions

## Complete Example Script

Here's a complete script you can copy and run:

```python
"""Complete example of regional Spanish TTS."""

import sys
sys.path.insert(0, 'src')  # If not installed

from f5_tts.api import F5TTS
from f5_tts.text import get_regional_processor

def main():
    # Setup
    print("Loading model...")
    tts = F5TTS(model_type="F5-TTS", vocoder_name="vocos")

    # Process different regions
    examples = [
        {
            'region': 'rioplatense',
            'text': 'Che boludo, ¿vos querés tomar unos mates?',
            'ref': 'path/to/rioplatense_ref.wav',
            'ref_text': 'Hola che',
            'output': 'output_rioplatense.wav'
        },
        {
            'region': 'colombian',
            'text': 'Parce, ¿vamos a tomar unas polas?',
            'ref': 'path/to/colombian_ref.wav',
            'ref_text': 'Hola parce',
            'output': 'output_colombian.wav'
        },
        {
            'region': 'mexican',
            'text': 'Órale güey, ¿vamos por unos tacos?',
            'ref': 'path/to/mexican_ref.wav',
            'ref_text': 'Hola güey',
            'output': 'output_mexican.wav'
        }
    ]

    for example in examples:
        print(f"\nProcessing {example['region']}...")

        # Create processor
        processor = get_regional_processor(region=example['region'])

        # Process text
        result = processor.process(example['text'])

        print(f"  Original: {result['original']}")
        print(f"  Phonetic: {result['phonetic']}")
        print(f"  Slang: {[s['term'] for s in result['detected_slang']]}")

        # Generate speech (if reference audio exists)
        try:
            wav, sr, _ = tts.infer(
                ref_file=example['ref'],
                ref_text=example['ref_text'],
                gen_text=result['phonetic'],
                seed=42
            )

            tts.export_wav(wav, example['output'])
            print(f"  ✓ Saved: {example['output']}")
        except Exception as e:
            print(f"  ⚠ Could not generate audio: {e}")

    print("\n✓ Complete!")

if __name__ == "__main__":
    main()
```

Save this as `regional_example.py` and run:
```bash
python regional_example.py
```

---

**Ready to get started?** Pick a use case above and try it out!

For more help, see:
- [Full Regional Guide](SPANISH_REGIONAL_GUIDE.md)
- [Quick Reference](REGIONAL_QUICK_REFERENCE.md)
- [Examples](../examples/regional_spanish/)
