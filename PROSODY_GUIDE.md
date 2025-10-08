```markdown
# Spanish Prosody Analysis Guide

## Overview

The Spanish Prosody Analyzer enhances TTS naturalness by detecting and marking prosodic features in Spanish text. It identifies questions, exclamations, emphasis points, natural pauses, stress patterns, and pitch contours to guide the TTS engine toward more expressive speech.

## Why Prosody Matters

Proper prosody is what makes speech sound natural vs. robotic:

- **Questions** need the right intonation (rising for yes/no, falling for wh-questions)
- **Exclamations** need increased intensity and energy
- **Emphasis** highlights important words
- **Pauses** give natural breathing and phrasing
- **Stress** patterns create natural rhythm

Without prosody markers, TTS output sounds flat and unnatural.

## Quick Start

### Basic Usage

```python
from f5_tts.text import analyze_spanish_prosody

text = "¿Cómo estás? ¡Muy bien, gracias!"
analysis = analyze_spanish_prosody(text)

print(f"Marked text: {analysis.marked_text}")
# Output: ¿Cómo estás?↘ ¡Muy* bien, gracias!❗

print(f"Found {len(analysis.markers)} prosody markers")
print(f"Pattern: {analysis.pitch_contours['overall_pattern']}")
```

### CLI Tool

```bash
# Analyze a single text
python examples/analyze_prosody.py "¿Dónde está el baño?"

# Interactive mode
python examples/analyze_prosody.py --interactive

# Show examples
python examples/analyze_prosody.py --examples

# Detailed analysis
python examples/analyze_prosody.py "Tu texto aquí" --detailed
```

## Prosodic Features Detected

### 1. Question Intonation

Spanish has two types of questions with different intonation patterns:

#### Yes/No Questions (Rising Intonation ↗)
Questions that can be answered with "yes" or "no"

**Examples:**
- `¿Quieres café?` → Rising tone at end
- `¿Vienes mañana?` → Rising intonation
- `¿Está listo?` → Questioning rise

**Detection:** Questions without interrogative words (qué, dónde, etc.)

**Marker:** `↗` (rising tone)

#### Information Questions (Falling Intonation ↘)
Questions starting with interrogative words (wh-questions)

**Examples:**
- `¿Dónde está?` → Falling tone at end
- `¿Qué hora es?` → Declarative-like fall
- `¿Cuándo vienes?` → Downward intonation

**Detection:** Questions with qué, dónde, cuándo, cómo, quién, cuál, cuánto

**Marker:** `↘` (falling tone)

**Why Different:** Information questions in Spanish typically have falling intonation similar to statements, while yes/no questions rise at the end.

### 2. Exclamations

Express strong emotion, surprise, or emphasis.

#### Intensity Levels

**Very High (‼️)**
- Strong exclamatory words: `¡Qué hermoso!`
- Multiple markers: `¡Qué día tan increíble!`
- Extreme emphasis: `¡INCREÍBLE!`

**High (❗)**
- Interjections: `¡Ay!`, `¡Uf!`, `¡Oh!`
- Emotional expressions: `¡Dios mío!`
- Strong reactions: `¡No puede ser!`

**Medium**
- Simple exclamations: `¡Bueno!`
- Mild surprise: `¡Vaya!`

**Examples:**
```
¡Qué día tan hermoso!     → ‼️ (very high)
¡Ay, qué dolor!           → ❗ (high)
¡Increíble!               → ❗ (high)
¡Bueno!                   → (medium)
```

### 3. Emphasis

Words that should receive extra stress or prominence.

#### Emphasis Categories

**Intensity Modifiers**
- `muy`, `mucho`, `bastante`, `demasiado`
- Example: "Esto es `muy*` importante"

**Strong Negation**
- `nunca`, `jamás`, `nada`, `nadie`, `ninguno`
- Example: "Yo `nunca*` lo haría"
- Intensity: HIGH

**Superlatives**
- `muchísimo`, `extremadamente`, `sumamente`
- Example: "`Muchísimo*` mejor"
- Intensity: VERY_HIGH

**Universal Quantifiers**
- `todo`, `todos`, `siempre`, `cada`
- Example: "`Todos*` los días"

**ALL CAPS**
- Automatically detected as strong emphasis
- Example: "Es IMPORTANTE" → "Es `IMPORTANTE*`"
- Intensity: VERY_HIGH

**Marker:** `*` (asterisk after word)

### 4. Pauses

Natural breaks in speech for breathing, phrasing, and comprehension.

#### Pause Types

**Long Pause (|)** - Sentence boundaries
- At periods, exclamation marks, question marks
- Duration: ~500-1000ms
- Example: "Buenos días. | ¿Cómo estás?"

**Medium Pause (/)** - Clause boundaries
- At semicolons, colons
- At major connectors
- Duration: ~300-500ms
- Example: "Me gusta; / sin embargo, / es caro."

**Short Pause (‧)** - Minor breaks
- At commas
- Light phrasing
- Duration: ~100-200ms
- Example: "Hola, ‧ ¿cómo estás?"

**Connector Pauses**
Special pauses before/after connectors:
- `pero`, `sin embargo`, `no obstante`
- `porque`, `ya que`, `por lo tanto`
- `además`, `también`, `por ejemplo`

Example:
```
Me gusta, ‧ pero / es caro. | Sin embargo, / lo compraré. |
```

### 5. Sentence Boundaries

Marks the end of complete sentences. Important for:
- Natural breathing points
- Resetting intonation
- Paragraph pacing

**Detection:**
- Period (.)
- Question mark (?)
- Exclamation mark (!)
- Semicolon (;)

### 6. Breath Points

Natural places to take a breath. Includes:
- All sentence boundaries
- Major clause boundaries (but not too frequent)
- Long sentence mid-points

**Heuristic:** Add breath points at clause boundaries if they're not too close to sentence ends (>20 chars apart).

### 7. Stress Points

Lexical stress on content words.

**Stressed Words:**
- Nouns: `perro`, `casa`, `ciudad`
- Verbs: `correr`, `pensar`, `decir`
- Adjectives: `grande`, `hermoso`, `importante`
- Adverbs: `rápidamente`, `bien`, `siempre`

**Not Stressed:**
- Articles: `el`, `la`, `un`, `una`
- Prepositions: `de`, `en`, `a`, `con`
- Short words: typically ≤ 3 characters

**Example:**
```
El perro grande corre rápidamente por el parque.
   ^      ^      ^       ^             ^
  (stress points - content words)
```

### 8. Pitch Contours

Overall intonation patterns across longer spans.

**Pattern Types:**

**Interrogative**
- Multiple questions
- Rising overall contour
- Example: "¿Vienes? ¿Puedes? ¿Quieres?"

**Expressive**
- Multiple exclamations
- High energy throughout
- Example: "¡Increíble! ¡Fantástico! ¡Maravilloso!"

**Declarative**
- Statements with falling contours
- Example: "Hoy hace buen día."

**Neutral**
- Mixed or balanced patterns
- Default for most text

## Real-World Examples

### Example 1: Greeting Conversation

**Input:**
```
¡Buenos días! ¿Cómo estás? Espero que muy bien, gracias.
```

**Analysis:**
```
¡Buenos días!❗ ¿Cómo estás?↘ Espero que muy* bien, ‧ gracias. |
```

**Markers Detected:**
- Exclamation: "¡Buenos días!" (medium intensity)
- Information question: "¿Cómo estás?" (falling tone)
- Emphasis: "muy" (medium intensity)
- Short pause: after "bien,"
- Long pause: after "gracias."

**Prosody Pattern:** Declarative (overall falling)

### Example 2: Emotional Expression

**Input:**
```
¡Qué día tan increíble! Nunca había visto algo así. ¡Fantástico!
```

**Analysis:**
```
¡Qué día tan increíble!‼️ Nunca* había visto algo así. | ¡Fantástico!❗
```

**Markers Detected:**
- Strong exclamation: "¡Qué día tan increíble!" (very high)
- Emphasis: "Nunca" (high - negation)
- Sentence pause: after "así."
- Exclamation: "¡Fantástico!" (high)

**Prosody Pattern:** Expressive

### Example 3: Complex Statement

**Input:**
```
El análisis reveló patrones interesantes. Sin embargo, necesitamos más datos.
```

**Analysis:**
```
El análisis reveló patrones interesantes. | Sin embargo, / necesitamos más* datos. |
```

**Markers Detected:**
- Sentence pause: after "interesantes."
- Connector pause: before "Sin embargo"
- Medium pause: after "Sin embargo,"
- Emphasis: "más"
- Sentence pause: after "datos."

**Prosody Pattern:** Declarative

### Example 4: Question Series

**Input:**
```
¿Vienes? ¿Puedes? ¿Quieres?
```

**Analysis:**
```
¿Vienes?↗ ¿Puedes?↗ ¿Quieres?↗
```

**Markers Detected:**
- Three yes/no questions (all rising)
- Sentence pauses after each

**Prosody Pattern:** Interrogative

## API Reference

### Main Function

```python
analyze_spanish_prosody(text: str) -> ProsodyAnalysis
```

Analyzes text and returns complete prosody information.

**Parameters:**
- `text`: Spanish text to analyze

**Returns:** `ProsodyAnalysis` object

### ProsodyAnalysis Object

```python
@dataclass
class ProsodyAnalysis:
    text: str                        # Original text
    marked_text: str                 # Text with visual markers
    markers: List[ProsodyMarker]     # All detected markers
    sentence_boundaries: List[int]   # Sentence end positions
    breath_points: List[int]         # Natural breath positions
    stress_points: List[int]         # Lexical stress positions
    pitch_contours: Dict[str, any]   # Pitch pattern analysis
```

### ProsodyMarker

```python
@dataclass
class ProsodyMarker:
    type: ProsodyType                # Marker type (enum)
    position: int                    # Character position in text
    length: int                      # Length of affected span
    intensity: IntensityLevel        # Intensity (enum)
    metadata: Dict[str, any]         # Additional information
```

### Enums

```python
class ProsodyType(Enum):
    QUESTION = "question"
    EXCLAMATION = "exclamation"
    STATEMENT = "statement"
    EMPHASIS = "emphasis"
    PAUSE = "pause"
    RISING_TONE = "rising"
    FALLING_TONE = "falling"
    NEUTRAL = "neutral"

class IntensityLevel(Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
```

### Helper Functions

```python
# Format analysis as readable report
format_prosody_report(analysis: ProsodyAnalysis) -> str

# Example usage
from f5_tts.text import analyze_spanish_prosody, format_prosody_report

analysis = analyze_spanish_prosody("Tu texto aquí")
print(format_prosody_report(analysis))
```

## Integration with TTS

### Basic Integration

```python
from f5_tts.api import F5TTS
from f5_tts.text import normalize_spanish_text, analyze_spanish_prosody

# Initialize TTS
tts = F5TTS()

# Input text
text = "¡Buenos días! ¿Cómo estás? Espero que muy bien."

# 1. Normalize text
normalized = normalize_spanish_text(text)

# 2. Analyze prosody
prosody = analyze_spanish_prosody(normalized)

# 3. Use marked text or prosody info
# (In future, TTS can use prosody markers to guide synthesis)
wav, sr, _ = tts.infer(
    ref_file="reference.wav",
    ref_text="",
    gen_text=normalized,  # Or prosody.marked_text
    seed=42
)
```

### Advanced: Using Prosody for Parameter Tuning

```python
from f5_tts.core import get_adaptive_nfe_step

# Adjust NFE steps based on prosody complexity
def get_prosody_aware_nfe(text):
    analysis = analyze_spanish_prosody(text)

    base_nfe = get_adaptive_nfe_step(text)

    # Increase NFE for expressive text
    exclamations = sum(1 for m in analysis.markers
                       if m.type == ProsodyType.EXCLAMATION)
    if exclamations > 2:
        base_nfe += 2  # More steps for expressiveness

    # Increase for questions
    questions = sum(1 for m in analysis.markers
                    if m.type in [ProsodyType.RISING_TONE, ProsodyType.FALLING_TONE])
    if questions > 1:
        base_nfe += 1  # More steps for intonation

    return min(base_nfe, 32)  # Clamp to max
```

## Best Practices

### 1. Text Preparation

**Do:**
- ✅ Use proper Spanish punctuation (¿?, ¡!)
- ✅ Include natural pauses (commas, periods)
- ✅ Write naturally with emotion
- ✅ Use emphasis words when appropriate

**Don't:**
- ❌ Use only English-style punctuation (?)
- ❌ Write run-on sentences without breaks
- ❌ Over-use ALL CAPS (reserve for actual emphasis)
- ❌ Omit punctuation entirely

### 2. Understanding Marker Output

Markers are visual guides, not part of actual TTS input. They help you:
- Verify prosody detection is correct
- Understand how text will be interpreted
- Debug unexpected TTS output
- Guide manual text adjustments

### 3. Combining with Normalization

Always normalize before prosody analysis:

```python
from f5_tts.text import normalize_spanish_text, analyze_spanish_prosody

text = "El Dr. García llega a las 14:30."
normalized = normalize_spanish_text(text)  # Expand abbreviations, times
prosody = analyze_spanish_prosody(normalized)  # Then analyze
```

### 4. Regional Variations

Combine with regional Spanish processing:

```python
from f5_tts.text import (
    process_spanish_text,
    analyze_spanish_prosody
)

# Process regional features
regional = process_spanish_text(
    "Che, ¿vos querés tomar unos mates?",
    region="rioplatense"
)

# Then analyze prosody
prosody = analyze_spanish_prosody(regional['normalized'])
```

## Troubleshooting

### "Questions not detected"

**Problem:** Missing ¿? markers

**Solution:**
```python
# Wrong
text = "Como estas?"  # Missing opening ¿

# Correct
text = "¿Cómo estás?"  # Proper Spanish punctuation
```

### "Exclamations too weak"

**Problem:** Intensity not high enough

**Solution:** Use stronger exclamatory words:
```python
# Weak
"¡Bien!"  # → medium intensity

# Strong
"¡Qué bien!"  # → high intensity
"¡Qué día tan maravilloso!"  # → very high intensity
```

### "Too many/few pauses"

**Problem:** Unnatural pacing

**Solution:** Adjust punctuation:
```python
# Too many pauses
"Hola, buenos, días, como, estás"  # Comma overload

# Better
"Hola, buenos días. ¿Cómo estás?"  # Natural phrasing
```

### "Emphasis on wrong words"

**Problem:** Wrong words receive stress

**Solution:** Add explicit emphasis words:
```python
# Generic
"Esto es importante."  # → Might not emphasize

# Explicit
"Esto es muy importante."  # → "muy" triggers emphasis
"Esto es realmente importante."  # → "realmente" triggers emphasis
```

## Future Enhancements

The prosody analyzer is designed to be extended with:

1. **Model Integration**: Direct connection to TTS inference
2. **Custom Markers**: User-defined prosody patterns
3. **Regional Prosody**: Region-specific intonation patterns
4. **Emotion Detection**: Sentiment-based intensity adjustment
5. **Speaker Style**: Personality-driven prosody variations
6. **Real-time Feedback**: Interactive prosody editing

## Conclusion

Prosody analysis is a crucial step in achieving natural-sounding TTS. By detecting and marking prosodic features, we guide the TTS system toward more expressive, human-like speech.

The Spanish Prosody Analyzer provides:
- ✅ Automatic detection of 8 prosodic features
- ✅ 5 intensity levels for fine-grained control
- ✅ Visual markers for debugging
- ✅ Comprehensive analysis reports
- ✅ Easy integration with TTS pipeline

Use it to make your TTS output sound more natural, expressive, and engaging!

---

**For more examples, run:**
```bash
python examples/analyze_prosody.py --examples
python examples/analyze_prosody.py --interactive
```
```
