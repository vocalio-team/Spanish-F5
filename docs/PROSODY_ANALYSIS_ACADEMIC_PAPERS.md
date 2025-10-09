# Academic Papers Analysis: Rioplatense Prosody

This document summarizes findings from two academic papers on Rioplatense Spanish prosody and their implications for our F5-TTS implementation.

## Paper 1: Cuello & Oro Ozán (2024) - Santa Rosa del Conlara

**Citation:** Cuello, S. & Oro Ozán, M. (2024). "Prosodia del español de Santa Rosa del Conlara: estudio perceptivo y acústico de la tonada nortina". REVID, Universidad Nacional de San Luis.

### Key Findings

**Pace Characteristics:**
- **CRITICAL:** Rioplatense "tonada nortina" is SLOWER than standard Spanish (not fast)
- Speech: 50% slower (pace multiplier: **0.75x**)
- Reading: 60% slower (pace multiplier: **0.60x**)
- Contradicts common perception of Rioplatense as "fast"

**Double Accentuation:**
- Combines rhythmic AND lexical stress patterns
- Creates characteristic "sing-song" quality
- Both accent types occur simultaneously in speech

**Plaintive/Whining Tone:**
- "Tono quejumbroso" (plaintive/whining quality)
- "Lamento perezoso" (lazy lament)
- Distinctive intonation contour different from other variants

**Methodology:**
- T.E.P.HA (Test de Evaluación Prosódica del Habla)
- Perceptual and acoustic analysis
- Native speaker recordings from Santa Rosa del Conlara region

### Implementation Corrections Needed

**WRONG (current implementation):**
```python
"rioplatense": {
    "pace": "fast",  # ❌ Contradicts empirical data
    "stress_pattern": "standard"
}
```

**CORRECT (based on paper):**
```python
"rioplatense": {
    "pace": "slow",
    "pace_multiplier": 0.75,  # 25% slower (conversational speech)
    "reading_pace_multiplier": 0.60,  # 40% slower (reading/formal)
    "stress_pattern": "double_accent",  # Rhythmic + lexical
    "intonation_quality": "plaintive",  # Whining/lament quality
    "f0_contour": "extended_range"  # Wider pitch variation
}
```

---

## Paper 2: Guglielmone, Labastía & Valls (2014) - Discourse Prosody

**Citation:** Guglielmone, M.Á., Labastía, L.O., & Valls, L.S. (2014). "Prosodia y discurso en el español rioplatense". Diálogos Latinoamericanos, 22, pp. 91-102.

### Key Findings

**Pitch Range:**
- Female speakers: 75-340 Hz
- Male speakers: 75-200 Hz
- Wide range indicates emotional expressiveness

**Declination Units:**
- Discourse organized by **declination** (pitch decrease over time)
- High beginning = new topic/theme
- Low ending = topic closure
- Each unit corresponds to a thematic section

**Nuclear Tone Configurations:**

Three primary configurations identified:

1. **Descending (↘):**
   - Function: Assertion/statement
   - Signals: Process this information NOW
   - Effect: Creates foreground information
   - Listener should evaluate relevance immediately

2. **Suspensive (→):**
   - Function: Continuation marker
   - Signals: Hold judgment, more context coming
   - Effect: Creates background/context
   - Wait for descending tone to process

3. **Ascending (↗):**
   - Function: Known/given information
   - Signals: This is already in context
   - Effect: Recapitulates/reminds listener
   - Information from prior discourse or shared knowledge

**Processing Units Structure:**
```
┌─ Processing Unit ─────────┐
│                            │
│  Background  → Foreground  │
│  (context)   ↗ (focus)     │
│  →  ↗         ↘            │
└────────────────────────────┘
```

**Theoretical Framework:**
- Based on **Relevance Theory** (Sperber & Wilson, 1995)
- Prosody encodes **procedural meaning** (not conceptual)
- Guides listener on HOW to process information
- Maximizes cognitive effects, minimizes processing effort

### Pedagogical Applications

**Teaching Strategy (5 activities):**

1. **Activity 1:** Content familiarization
   - Listen to interview, identify themes
   - Fill in table with topic information

2. **Activity 2a/2b:** Tone recognition
   - Observe physical realization via PRAAT spectrograms
   - Associate movements with meanings
   - Connect perception to discourse function

3. **Activity 3:** Naturalness evaluation
   - Analyze same text with different tone choices
   - Identify which version sounds most natural
   - Justify choices based on learned concepts

4. **Activity 4:** Tone prediction
   - Predict tone selections in new fragments
   - Compare predictions to actual speaker choices
   - Discuss similarities/differences
   - Learn that topics often use ascending/suspensive tones (expected information)

5. **Activity 5:** Production practice
   - Read analyzed interview with marked intonation
   - Create personal presentation with family data
   - Apply learned concepts in real communication
   - Compare with native language prosody

### Implementation Implications

**Discourse-Level Prosody:**

```python
class RioplatenseDiscourseProsodia:
    """
    Implements discourse-level prosodic patterns for Rioplatense Spanish
    based on Guglielmone et al. (2014).
    """

    NUCLEAR_TONES = {
        "descending": {
            "symbol": "↘",
            "function": "assertion",
            "f0_pattern": "L+H* L* L%",
            "processing": "immediate_evaluation",
            "discourse_role": "foreground"
        },
        "suspensive": {
            "symbol": "→",
            "function": "continuation",
            "f0_pattern": "L+H* M%",
            "processing": "suspend_judgment",
            "discourse_role": "background"
        },
        "ascending": {
            "symbol": "↗",
            "function": "given_information",
            "f0_pattern": "L+H* L+H* H%",
            "processing": "context_reminder",
            "discourse_role": "background"
        }
    }

    def apply_declination_unit(self, text_segments, theme_boundaries):
        """
        Apply declination over thematic units.

        Args:
            text_segments: List of text segments
            theme_boundaries: Indices where themes start/end

        Returns:
            List of (segment, f0_start, f0_end) tuples
        """
        processed = []

        for i, segment in enumerate(text_segments):
            if i in theme_boundaries["start"]:
                f0_start = "high"  # New topic
            else:
                f0_start = "mid"

            if i in theme_boundaries["end"]:
                f0_end = "low"  # Topic closure
            else:
                f0_end = "mid"

            processed.append((segment, f0_start, f0_end))

        return processed

    def determine_nuclear_tone(self, segment, discourse_context):
        """
        Determine appropriate nuclear tone based on discourse context.

        Args:
            segment: Current text segment
            discourse_context: Dict with "role" ("foreground"/"background")

        Returns:
            Nuclear tone configuration
        """
        if discourse_context.get("role") == "foreground":
            return self.NUCLEAR_TONES["descending"]
        elif discourse_context.get("given", False):
            return self.NUCLEAR_TONES["ascending"]
        else:
            return self.NUCLEAR_TONES["suspensive"]
```

**Integration with TTS:**

1. **Sentence-Level Analysis:**
   - Identify thematic boundaries automatically
   - Apply declination units (high start → low end)

2. **Clause-Level Analysis:**
   - Classify each clause as foreground/background
   - Apply appropriate nuclear tone

3. **Combined with Paper 1 Findings:**
   - Slower pace (0.75x)
   - Double accentuation (rhythmic + lexical)
   - Plaintive intonation quality
   - Extended F0 range (75-340Hz female, 75-200Hz male)

---

## Summary of Implementation Changes

### Priority 1: Pace Correction (Critical Error)
- **Change:** `"pace": "fast"` → `"pace": "slow"` with `pace_multiplier: 0.75`
- **Impact:** Fundamental characteristic was reversed
- **Files:** `src/f5_tts/text/spanish_regional.py`, `examples/prosody_improvements/quick_wins.py`

### Priority 2: Add Double Accentuation
- **New feature:** Implement rhythmic + lexical stress patterns
- **Impact:** Creates characteristic "sing-song" quality
- **Implementation:** Modify stress assignment logic

### Priority 3: Plaintive Intonation Contour
- **New feature:** Add "plaintive/whining" quality to F0 contour
- **Impact:** Distinctive emotional coloring
- **Implementation:** Adjust F0 generation parameters

### Priority 4: Discourse-Level Prosody
- **New feature:** Implement declination units and nuclear tone configurations
- **Impact:** More natural multi-sentence discourse
- **Implementation:** Add discourse-level prosody module

### Priority 5: Extended Pitch Range
- **Adjustment:** Ensure F0 range matches empirical data (75-340Hz female, 75-200Hz male)
- **Impact:** More emotional expressiveness
- **Implementation:** Adjust F0 normalization parameters

---

## References

1. Cuello, S. & Oro Ozán, M. (2024). Prosodia del español de Santa Rosa del Conlara: estudio perceptivo y acústico de la tonada nortina. REVID, Universidad Nacional de San Luis. https://revid.unsl.edu.ar/index.php/revid/article/view/280

2. Guglielmone, M.Á., Labastía, L.O., & Valls, L.S. (2014). Prosodia y discurso en el español rioplatense. Diálogos Latinoamericanos, 22, 91-102. https://www.redalyc.org/pdf/162/16230854009.pdf

3. Sperber, D. & Wilson, D. (1995). Relevance: Communication and Cognition. Blackwell: Oxford.

4. Prieto, P. & Roseano, P. (Eds.) (2010). Transcription of Intonation of the Spanish Language. Lincom Europa: Muenchen.

5. Escandell-Vidal, M.V. (2011). Prosodia y Pragmática. Studies in Hispanic and Lusophone Linguistics, 4(1), 193-208.

---

## Next Steps

1. **Implement pace correction** in [spanish_regional.py:247-251](src/f5_tts/text/spanish_regional.py#L247-L251)
2. **Add double accentuation logic** to prosody module
3. **Create discourse-level prosody processor** based on Guglielmone et al. framework
4. **Test with native Rioplatense speakers** for perceptual validation
5. **Expand to other regional variants** using similar empirical methodology
