# Prosody and Regionalization Quality Improvement Roadmap

## Current State Analysis

### ✅ What's Working Well

**Prosody System** ([src/f5_tts/text/prosody.py](../src/f5_tts/text/prosody.py)):
- Question/exclamation detection
- Emphasis word identification
- Pause marker insertion
- Sentence boundary detection
- Basic intensity levels

**Regionalization** ([src/f5_tts/text/spanish_regional.py](../src/f5_tts/text/spanish_regional.py)):
- 6 regional variants (Rioplatense, Colombian, Mexican, Chilean, Caribbean, Andean)
- Phonetic transformations (sheísmo, yeísmo, s-aspiration)
- Regional slang dictionaries
- Auto-detection from text markers
- Prosodic pattern recognition

### 🔍 Current Limitations

**Prosody:**
1. **Rule-based only** - No ML/data-driven patterns
2. **Limited emotional range** - Basic intensity levels
3. **No rhythm modeling** - Missing syllabic timing
4. **Static markers** - Not context-aware
5. **No speaker adaptation** - One-size-fits-all

**Regionalization:**
1. **Limited phonetic coverage** - Missing many regional features
2. **No acoustic modeling** - Phonetic rules only
3. **Incomplete slang** - Small dictionaries (~10-20 terms per region)
4. **No sub-regional variants** - E.g., Mexico City vs. Northern Mexico
5. **Manual feature engineering** - No learned representations

## Improvement Strategies

### 📊 Strategy 1: Data-Driven Prosody Learning

#### Objective
Replace rule-based prosody with **learned patterns** from native speaker recordings.

#### Implementation Plan

**Phase 1: Data Collection** (2-4 weeks)
1. **Record Native Speakers**
   - 10+ speakers per region
   - Read 100+ diverse sentences (questions, exclamations, narratives)
   - Professional voice actors preferred
   - Multiple emotional contexts

2. **Annotate Prosodic Features**
   - Pitch contours (F0 tracking)
   - Energy/intensity curves
   - Speech rate variations
   - Pause durations
   - Emotional labels

3. **Build Prosody Dataset**
   ```
   dataset/
   ├── rioplatense/
   │   ├── speaker_001/
   │   │   ├── audio/
   │   │   │   ├── question_001.wav
   │   │   │   ├── exclamation_001.wav
   │   │   │   └── ...
   │   │   └── annotations/
   │   │       ├── question_001.json  # Prosody annotations
   │   │       └── ...
   │   └── ...
   ├── colombian/
   └── ...
   ```

**Phase 2: Prosody Model Training** (2-3 weeks)
1. **Extract Features**
   ```python
   # Acoustic features
   - Pitch (F0) contours
   - Energy envelopes
   - Duration patterns
   - Spectral tilt

   # Linguistic features
   - Word embeddings
   - POS tags
   - Syntactic structure
   - Punctuation context
   ```

2. **Train Prosody Predictor**
   ```python
   # Architecture options:

   # Option A: Transformer-based
   class ProsodyTransformer(nn.Module):
       """Predict prosody from text + context"""
       def __init__(self):
           self.text_encoder = BertModel(...)
           self.prosody_decoder = TransformerDecoder(...)
           self.pitch_head = nn.Linear(...)
           self.energy_head = nn.Linear(...)
           self.duration_head = nn.Linear(...)

   # Option B: FastSpeech2-style
   class ProsodyPredictor(nn.Module):
       """Variance adaptor for prosody"""
       def __init__(self):
           self.variance_adaptor = VarianceAdaptor(
               n_mel_channels=80,
               pitch_quantization="linear",
               energy_quantization="linear",
               n_bins=256
           )
   ```

3. **Regional Prosody Models**
   - Train separate models per region
   - Or: Multi-task model with region embedding
   ```python
   prosody = model(
       text="¿Cómo estás?",
       region="rioplatense",
       emotion="neutral"
   )
   # Returns: pitch_contour, energy_curve, durations
   ```

**Phase 3: Integration** (1 week)
```python
# New prosody module
from f5_tts.text.prosody_learned import LearnedProsodyPredictor

prosody_model = LearnedProsodyPredictor(
    model_path="models/prosody_rioplatense.pt",
    region="rioplatense"
)

# Predict prosody
prosody_features = prosody_model.predict(
    text="¿Cómo estás, che?",
    emotion="friendly"  # Optional emotional context
)

# Apply to TTS
tts_output = f5tts.infer(
    text=text,
    prosody_override=prosody_features  # Inject learned prosody
)
```

**Expected Improvements:**
- ✅ **Natural intonation patterns** (vs. rule-based)
- ✅ **Region-specific rhythm** (data-driven)
- ✅ **Emotional expressiveness** (from annotations)
- ✅ **Context-aware prosody** (learned from real speech)

---

### 🗣️ Strategy 2: Enhanced Phonetic Modeling

#### Objective
Expand phonetic coverage with **data-driven acoustic models**.

#### Implementation Plan

**Phase 1: Phonetic Corpus** (2-3 weeks)
1. **Collect Minimal Pairs**
   ```
   Rioplatense:
   - "calle" [kaʃe] vs "calle" [kaʎe] (other regions)
   - "yo" [ʒo] vs "yo" [jo]

   Caribbean:
   - "estas" [ehtah] vs "estas" [estas]
   - "carne" [kanne] vs "carne" [karne]
   ```

2. **Record Phonetic Variations**
   - Native speakers reading minimal pairs
   - Multiple speakers per variant
   - Clean studio recordings

3. **Extract Acoustic Patterns**
   ```python
   # Per-region acoustic signatures
   acoustic_profile = {
       'rioplatense': {
           'll': {
               'formants': [F1, F2, F3],  # From recordings
               'duration': mean_duration,
               'intensity': mean_energy
           },
           's_final': {
               'aspiration_strength': 0.7,
               'fricative_center': 4500,  # Hz
           }
       }
   }
   ```

**Phase 2: Acoustic Feature Bank** (1-2 weeks)
```python
# Create acoustic feature library
class AcousticFeatureBank:
    """Regional acoustic features from real recordings"""

    def __init__(self):
        self.features = self._load_acoustic_profiles()

    def get_feature(self, phoneme: str, region: str) -> AcousticFeature:
        """Get learned acoustic features for phoneme in region"""
        return self.features[region][phoneme]

    def apply_to_mel(self, mel_spec, phoneme, region):
        """Modify mel-spectrogram with regional features"""
        feature = self.get_feature(phoneme, region)
        return self._apply_acoustic_transform(mel_spec, feature)
```

**Phase 3: Fine-tune F5-TTS** (2-3 weeks)
```python
# Fine-tune on regional data
from f5_tts.train import finetune_regional

# Prepare regional dataset
dataset = RegionalSpanishDataset(
    audio_dir="data/rioplatense/audio",
    phonetic_alignments="data/rioplatense/alignments",
    acoustic_features="data/rioplatense/features"
)

# Fine-tune model
model = finetune_regional(
    base_model="F5-TTS",
    dataset=dataset,
    region="rioplatense",
    epochs=50,
    focus_phonemes=['ll', 'y', 's_final']  # Regional focus
)
```

**Expected Improvements:**
- ✅ **Authentic phonetic realizations** (from real speakers)
- ✅ **Acoustic accuracy** (not just textual rules)
- ✅ **Speaker-specific variation** (multiple reference points)

---

### 📚 Strategy 3: Expanded Regional Coverage

#### Objective
**10x increase** in regional linguistic coverage.

#### Implementation Plan

**Phase 1: Crowdsourced Slang Collection** (Ongoing)
1. **Community Contribution Platform**
   ```python
   # Web interface for native speakers
   class SlangContribution:
       region: str
       term: str
       standard_equivalent: str
       usage_example: str
       frequency: str  # "common", "regional", "rare"
       contributor_location: str  # City/province

   # Validation by native speakers
   # Voting system for accuracy
   ```

2. **Social Media Mining**
   ```python
   # Extract regional expressions from Twitter/Reddit
   from f5_tts.data import RegionalSlangMiner

   miner = RegionalSlangMiner(
       regions=['argentina', 'mexico', 'colombia'],
       min_frequency=100,  # Appears 100+ times
       verify_with_natives=True
   )

   slang_dict = miner.mine_slang(
       sources=['twitter', 'reddit', 'forums'],
       date_range='2020-2024'
   )
   ```

3. **Target Coverage**
   - **Current**: ~20 terms per region
   - **Goal**: **200+ terms per region**
   - **Sub-regional**: City/province-specific variants

**Phase 2: Sub-Regional Variants** (3-4 weeks)
```python
# Hierarchical regional model
class HierarchicalRegionalizer:
    """
    Country → Region → City/Province
    """

    def process(self, text: str, location: str):
        # Parse location
        country, region, city = parse_location(location)

        # Apply cascading rules
        text = self.apply_country_features(text, country)
        text = self.apply_regional_features(text, region)
        text = self.apply_local_features(text, city)

        return text

# Example
regionalizer = HierarchicalRegionalizer()

# Specific variant
text = regionalizer.process(
    "¿Qué onda güey?",
    location="Mexico/North/Monterrey"  # Specific to Monterrey
)
```

**Sub-regional focus areas:**
```
Argentina:
- Buenos Aires (porteño)
- Córdoba (cordobés)
- Northwest (tucumano, salteño)

Mexico:
- Mexico City (chilango)
- Northern (norteño - Monterrey, Tijuana)
- Yucatán (yucateco)
- Jalisco (tapatío)

Colombia:
- Bogotá (rolo/cachaco)
- Medellín (paisa)
- Coastal (costeño)
- Cali (caleño)
```

**Phase 3: Dialectal Variation** (2-3 weeks)
```python
# Model sociolinguistic variation
class SociolinguisticVariation:
    """Age, education, formality variations"""

    def adjust_for_context(
        self,
        text: str,
        region: str,
        age_group: str = "adult",  # youth, adult, elderly
        formality: str = "neutral",  # formal, neutral, informal
        education: str = "standard"  # academic, standard, colloquial
    ):
        # Youth in Buenos Aires
        if region == "rioplatense" and age_group == "youth":
            text = self.apply_youth_slang(text)
            text = self.apply_informal_grammar(text)

        # Formal Colombian
        if region == "colombian" and formality == "formal":
            text = self.apply_formal_register(text)
            text = self.preserve_formal_phonetics(text)

        return text
```

**Expected Improvements:**
- ✅ **10x slang coverage** (20 → 200+ terms)
- ✅ **Sub-regional accuracy** (city-level variants)
- ✅ **Sociolinguistic variation** (age, formality, education)

---

### 🎭 Strategy 4: Emotional & Contextual Prosody

#### Objective
Add **emotional intelligence** to prosody generation.

#### Implementation Plan

**Phase 1: Emotion Annotation** (2-3 weeks)
1. **Emotional Speech Dataset**
   ```
   emotions/
   ├── neutral/
   ├── happy/
   ├── sad/
   ├── angry/
   ├── surprised/
   ├── fearful/
   └── sarcastic/  # Important for Spanish!
   ```

2. **Context-Aware Labeling**
   ```python
   # Not just emotion, but communicative intent
   class EmotionalContext:
       primary_emotion: str  # happy, sad, angry, etc.
       intensity: float  # 0.0 - 1.0
       intent: str  # inform, persuade, entertain, question
       formality: str  # formal, informal
       sarcasm: bool  # Important!
   ```

**Phase 2: Emotional Prosody Model** (3-4 weeks)
```python
# Multi-modal emotion model
class EmotionalProsodyModel(nn.Module):
    def __init__(self):
        self.emotion_encoder = EmotionEncoder()
        self.text_encoder = TextEncoder()
        self.fusion = CrossAttentionFusion()
        self.prosody_decoder = ProsodyDecoder()

    def forward(self, text, emotion_label, intensity):
        # Encode text and emotion separately
        text_emb = self.text_encoder(text)
        emotion_emb = self.emotion_encoder(emotion_label, intensity)

        # Fuse with cross-attention
        fused = self.fusion(text_emb, emotion_emb)

        # Decode to prosody parameters
        pitch, energy, duration = self.prosody_decoder(fused)
        return pitch, energy, duration
```

**Phase 3: Sarcasm Detection** (2 weeks)
```python
# Critical for Spanish communication!
class SarcasmDetector:
    """Detect sarcasm to apply inverted prosody"""

    def detect(self, text: str, context: str = None) -> float:
        # Indicators:
        # - Exaggeration markers: "súper", "re", "requete"
        # - Contradiction with context
        # - Ironic punctuation: "¡Qué bien!" (when things are bad)

        sarcasm_score = self.model.predict(text, context)
        return sarcasm_score

    def apply_sarcastic_prosody(self, text: str):
        # Invert typical prosody
        # - Exaggerated pitch range
        # - Slower tempo
        # - Emphatic stress on unexpected words
        return prosody_features
```

**Phase 4: Context Integration** (2 weeks)
```python
# Use conversation context for better prosody
class ContextualProsody:
    """Multi-turn conversation prosody"""

    def __init__(self):
        self.conversation_history = []

    def add_turn(self, text: str, prosody: dict):
        self.conversation_history.append({
            'text': text,
            'prosody': prosody
        })

    def predict_next_prosody(self, text: str):
        # Consider:
        # - Previous speaker's emotion
        # - Topic continuity
        # - Turn-taking patterns
        # - Discourse markers

        context_embedding = self.encode_context(
            self.conversation_history[-3:]  # Last 3 turns
        )

        prosody = self.model.predict(
            text=text,
            context=context_embedding
        )
        return prosody
```

**Expected Improvements:**
- ✅ **Emotional expressiveness** (7+ emotions)
- ✅ **Sarcasm handling** (critical for Spanish!)
- ✅ **Context-aware prosody** (multi-turn conversations)
- ✅ **Intent-driven delivery** (inform vs. persuade vs. entertain)

---

### 🔬 Strategy 5: Phonetic Fine-tuning per Region

#### Objective
Create **region-specific acoustic models** through fine-tuning.

#### Implementation Plan

**Phase 1: Regional Training Data** (3-4 weeks)
1. **High-Quality Regional Corpora**
   ```
   Target: 10-20 hours per region

   Sources:
   - Professional voice actors (native)
   - Audiobooks by regional authors
   - Podcast transcriptions
   - Radio/TV transcripts
   ```

2. **Phonetic Alignment**
   ```python
   # Force-align audio with phonetic transcriptions
   from f5_tts.data import PhonemicAligner

   aligner = PhonemicAligner(
       model="mfa",  # Montreal Forced Aligner
       language="spanish",
       dialect="rioplatense"
   )

   alignments = aligner.align(
       audio="audio.wav",
       text="¿Cómo andás, che?",
       phonetic_inventory="rioplatense"  # Custom phoneme set
   )
   ```

**Phase 2: Region-Specific Fine-tuning** (2-3 weeks per region)
```python
# Fine-tune F5-TTS on regional data
from f5_tts.train import RegionalFineTuner

finetuner = RegionalFineTuner(
    base_model="F5-TTS-Spanish",
    region="rioplatense",
    focus_areas=[
        "ll_realization",  # [ʃ] vs [ʎ] vs [j]
        "s_aspiration",    # [s] vs [h] vs [∅]
        "intonation",      # Rising patterns
        "rhythm"           # Syllable timing
    ]
)

regional_model = finetuner.train(
    dataset=rioplatense_dataset,
    epochs=100,
    learning_rate=1e-5,
    phonetic_loss_weight=0.3  # Extra weight on phonetic accuracy
)

# Save region-specific model
regional_model.save("models/F5-TTS-Rioplatense")
```

**Phase 3: Ensemble Regional Models** (1-2 weeks)
```python
# Multi-model approach for best quality
class RegionalModelEnsemble:
    """Ensemble of region-specific models"""

    def __init__(self):
        self.models = {
            'rioplatense': load_model("F5-TTS-Rioplatense"),
            'mexican': load_model("F5-TTS-Mexican"),
            'colombian': load_model("F5-TTS-Colombian"),
            # ...
        }

    def infer(self, text: str, region: str, blend: bool = False):
        if not blend:
            # Use single region model
            return self.models[region].infer(text)
        else:
            # Blend neighboring regions
            primary = self.models[region].infer(text)

            # Blend with similar regions
            similar_regions = self.get_similar_regions(region)
            blended = self.blend_outputs(primary, similar_regions)
            return blended
```

**Expected Improvements:**
- ✅ **Authentic regional pronunciation** (model-level)
- ✅ **Acoustic fidelity** (fine-tuned on native speech)
- ✅ **Reduced phonetic errors** (region-specific training)

---

## Quick Wins (Implement First)

### 1. Expand Slang Dictionaries (1 week)
- Crowdsource from native speakers
- Mine from social media
- **Goal**: 20 → 100+ terms per region

### 2. Enhanced Prosody Rules (1 week)
```python
# Add more sophisticated rules
class EnhancedProsodyRules:
    # Current: Basic question/exclamation
    # Add:
    - Conditional sentences (Si... entonces...)
    - Comparative structures (Más... que...)
    - Temporal sequences (Primero... luego... finalmente...)
    - Cause-effect (Porque... por lo tanto...)
```

### 3. Context-Aware Intensity (1 week)
```python
# Adjust intensity based on context
def calculate_intensity(word, context):
    base_intensity = get_base_intensity(word)

    # Amplify if:
    if has_intensifier_before(word, context):
        base_intensity *= 1.5
    if is_in_exclamation(word, context):
        base_intensity *= 1.3
    if is_repeated(word, context):
        base_intensity *= 1.2

    return min(base_intensity, 1.0)
```

### 4. Regional Prosody Patterns (2 weeks)
```python
# Region-specific intonation
REGIONAL_PROSODY = {
    'rioplatense': {
        'question_rise': 'steep',  # Sharp rising at end
        'stress_pattern': 'final_syllable',
        'pace': 'fast'
    },
    'mexican': {
        'question_rise': 'gradual',
        'stress_pattern': 'penultimate',
        'pace': 'moderate'
    },
    'colombian': {
        'question_rise': 'moderate',
        'stress_pattern': 'even',
        'pace': 'clear'  # Deliberate articulation
    }
}
```

---

## Data Collection Strategies

### Community-Driven Data Collection

**1. Native Speaker Contribution Portal**
```
Website: contribute.spanish-tts.com

Features:
- Record yourself reading sentences
- Annotate regional expressions
- Validate others' contributions
- Regional leaderboards
- Gamification (points, badges)
```

**2. Academic Partnerships**
- Universities with linguistics programs
- Spanish dialectology research centers
- Language documentation projects

**3. Media Partnerships**
- Podcast transcriptions (with permission)
- Audiobook publishers
- Regional radio stations
- YouTube creators

### Annotation Guidelines

**Prosody Annotation Protocol:**
```yaml
sentence: "¿Cómo estás, che?"
annotations:
  pitch:
    - position: 0-4   # "¿Cómo"
      contour: rising
      prominence: high
    - position: 5-10  # "estás"
      contour: peak
      prominence: very_high
    - position: 12-14 # "che"
      contour: falling
      prominence: medium

  pauses:
    - position: 11
      duration_ms: 150
      type: breath

  emphasis:
    - word: "estás"
      intensity: high
      reason: question_focus

  emotion: friendly
  formality: informal
  region: rioplatense
```

---

## Validation & Quality Metrics

### Prosody Quality Metrics

```python
class ProsodyQualityMetrics:
    """Evaluate prosody quality"""

    def evaluate(self, generated_audio, reference_audio):
        return {
            # Pitch metrics
            'pitch_rmse': self.pitch_error(generated, reference),
            'pitch_correlation': self.pitch_correlation(generated, reference),

            # Energy metrics
            'energy_rmse': self.energy_error(generated, reference),

            # Duration metrics
            'duration_error': self.duration_error(generated, reference),

            # Perceptual metrics
            'mos_prosody': self.perceptual_evaluation(generated),  # Mean Opinion Score
            'naturalness': self.naturalness_score(generated)
        }
```

### Regional Accuracy Metrics

```python
class RegionalAccuracyMetrics:
    """Evaluate regional authenticity"""

    def evaluate(self, audio, region):
        return {
            # Phonetic accuracy
            'll_accuracy': self.check_ll_realization(audio, region),
            's_accuracy': self.check_s_realization(audio, region),
            'y_accuracy': self.check_y_realization(audio, region),

            # Prosodic accuracy
            'intonation_match': self.check_intonation(audio, region),
            'rhythm_match': self.check_rhythm(audio, region),

            # Perceptual
            'regional_authenticity': self.native_speaker_rating(audio, region),
            'intelligibility': self.intelligibility_score(audio)
        }
```

### A/B Testing with Native Speakers

```python
# Collect feedback from native speakers
class NativeSpeakerEvaluation:
    def conduct_ab_test(self, audio_a, audio_b, region):
        # Present to native speakers
        feedback = self.collect_ratings(
            audio_a=audio_a,
            audio_b=audio_b,
            questions=[
                "Which sounds more natural?",
                "Which sounds more like your region?",
                "Which would you prefer to hear?",
                "Rate regional accuracy (1-5)",
                "Rate prosody naturalness (1-5)"
            ],
            participants=filter_by_region(region, min_count=50)
        )
        return feedback
```

---

## Implementation Timeline

### Short-term (1-3 months)
1. ✅ **Expand slang dictionaries** (100+ per region)
2. ✅ **Enhanced prosody rules** (context-aware)
3. ✅ **Regional prosody patterns** (rule-based)
4. ✅ **Sub-regional variants** (city-level)
5. ✅ **Basic emotion support** (5 emotions)

### Medium-term (3-6 months)
1. ✅ **Collect prosody dataset** (10 speakers per region)
2. ✅ **Train learned prosody model** (data-driven)
3. ✅ **Fine-tune regional models** (3 regions)
4. ✅ **Sarcasm detection** (Spanish-specific)
5. ✅ **Context-aware prosody** (multi-turn)

### Long-term (6-12 months)
1. ✅ **Full emotional range** (7+ emotions)
2. ✅ **All regional models** (6+ regions)
3. ✅ **Sociolinguistic variation** (age, formality, education)
4. ✅ **Ensemble models** (blend regions)
5. ✅ **Real-time adaptation** (speaker feedback)

---

## Success Metrics

### Quantitative Targets
- **Prosody MOS**: 3.5 → **4.5** (1.0 improvement)
- **Regional accuracy**: 60% → **90%** (native speaker evaluation)
- **Slang coverage**: 20 → **200+** terms per region
- **Emotional range**: 2 → **7+** emotions
- **Sub-regional variants**: 0 → **3+** per country

### Qualitative Goals
- ✅ Native speakers can't distinguish from real person
- ✅ Regional speakers recognize their own variant
- ✅ Emotional context is appropriately conveyed
- ✅ Sarcasm and irony are properly rendered
- ✅ Formal/informal registers are distinct

---

## Conclusion

**Priority Order:**
1. **Data Collection** - Foundation for everything
2. **Slang Expansion** - Quick wins, high impact
3. **Prosody Learning** - Biggest quality improvement
4. **Regional Fine-tuning** - Authentic regional voices
5. **Emotional Intelligence** - Natural expressiveness

**Expected Overall Impact:**
- 📈 **50% quality improvement** in prosody naturalness
- 🗣️ **90% regional accuracy** (native speaker validated)
- 🎭 **Full emotional range** (7+ emotions)
- 🌍 **Sub-regional precision** (city-level variants)
- 💬 **10x linguistic coverage** (slang, expressions, variations)

The key is **data-driven approaches** combined with **linguistic expertise**. Start with quick wins (slang expansion, enhanced rules), then invest in data collection and model training for long-term quality improvements.
