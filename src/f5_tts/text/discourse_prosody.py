"""Discourse-level prosody module for Spanish TTS.

Based on Guglielmone, Labastía & Valls (2014) research on Rioplatense
discourse prosody and Relevance Theory framework.

Implements:
- Declination units (pitch reset for new topics)
- Nuclear tone configurations (descending, suspensive, ascending)
- Processing units (background/foreground information structure)
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Optional, Dict
import re


class NuclearTone(Enum):
    """Nuclear tone configurations for discourse organization."""
    DESCENDING = "descending"  # ↘ - Assertion/foreground
    SUSPENSIVE = "suspensive"  # → - Continuation/background
    ASCENDING = "ascending"  # ↗ - Given information/background


@dataclass
class ToneConfiguration:
    """Configuration for a specific nuclear tone."""
    symbol: str
    function: str
    f0_pattern: str  # ToBI-like notation
    processing: str
    discourse_role: str
    description: str


@dataclass
class IntonationalPhrase:
    """An intonational phrase with its nuclear tone."""
    text: str
    nuclear_tone: NuclearTone
    f0_start: str  # "high", "mid", "low"
    f0_end: str  # "high", "mid", "low"
    is_topic_boundary: bool = False
    discourse_role: str = "background"  # "background" or "foreground"


@dataclass
class DeclinationUnit:
    """A declination unit representing a thematic section."""
    phrases: List[IntonationalPhrase]
    topic: str
    f0_start_hz: Optional[int] = None  # Starting F0 (high)
    f0_end_hz: Optional[int] = None  # Ending F0 (low)


class DiscourseProsodia:
    """Discourse-level prosody processor for Spanish.

    Based on Guglielmone et al. (2014) findings on Rioplatense discourse prosody.
    """

    # Nuclear tone configurations
    NUCLEAR_TONES = {
        NuclearTone.DESCENDING: ToneConfiguration(
            symbol="↘",
            function="assertion",
            f0_pattern="L+H* L* L%",  # High pitch accent, low boundary
            processing="immediate_evaluation",
            discourse_role="foreground",
            description="Assertion - process this information now"
        ),
        NuclearTone.SUSPENSIVE: ToneConfiguration(
            symbol="→",
            function="continuation",
            f0_pattern="L+H* M%",  # High pitch accent, mid boundary
            processing="suspend_judgment",
            discourse_role="background",
            description="Continuation - more context coming, suspend judgment"
        ),
        NuclearTone.ASCENDING: ToneConfiguration(
            symbol="↗",
            function="given_information",
            f0_pattern="L+H* H%",  # High pitch accent, high boundary
            processing="context_reminder",
            discourse_role="background",
            description="Given information - reminder of shared context"
        ),
    }

    # Empirical F0 ranges (Guglielmone et al., 2014)
    F0_RANGES = {
        "female": {"min": 75, "max": 340, "mid": 200},
        "male": {"min": 75, "max": 200, "mid": 140},
    }

    def __init__(self, voice_type: str = "female"):
        """
        Initialize discourse prosody processor.

        Args:
            voice_type: "female" or "male" for appropriate F0 range
        """
        self.voice_type = voice_type
        self.f0_range = self.F0_RANGES.get(voice_type, self.F0_RANGES["female"])

    def segment_into_phrases(self, text: str) -> List[str]:
        """
        Segment text into intonational phrases.

        Basic segmentation based on:
        - Sentence boundaries (. ! ?)
        - Comma boundaries
        - Conjunctions (y, o, pero)
        - Relative clauses

        Args:
            text: Input text

        Returns:
            List of phrase strings
        """
        # Split on major boundaries first
        sentences = re.split(r'([.!?]+)', text)

        phrases = []
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i].strip()
            punctuation = sentences[i + 1] if i + 1 < len(sentences) else ""

            if not sentence:
                continue

            # Further split on commas and conjunctions
            sub_phrases = re.split(r'([,;]|\b(?:y|o|pero|aunque|porque)\b)', sentence)

            current_phrase = ""
            for j, part in enumerate(sub_phrases):
                part = part.strip()
                if not part:
                    continue

                if part in [',', ';', 'y', 'o', 'pero', 'aunque', 'porque']:
                    if current_phrase:
                        phrases.append(current_phrase.strip())
                    current_phrase = ""
                else:
                    current_phrase += " " + part

            # Add last phrase with punctuation
            if current_phrase:
                phrases.append((current_phrase.strip() + punctuation).strip())

        return [p for p in phrases if p]

    def determine_nuclear_tone(
        self,
        phrase: str,
        phrase_index: int,
        total_phrases: int,
        is_topic_start: bool = False,
        contains_given_info: bool = False
    ) -> NuclearTone:
        """
        Determine appropriate nuclear tone for a phrase.

        Decision logic based on Guglielmone et al. (2014):
        - Last phrase in sequence → DESCENDING (foreground)
        - Given/topic information → ASCENDING (background)
        - Continuation → SUSPENSIVE (background)

        Args:
            phrase: The phrase text
            phrase_index: Index in phrase sequence (0-based)
            total_phrases: Total number of phrases
            is_topic_start: Whether this starts a new topic
            contains_given_info: Whether this contains given/known information

        Returns:
            Nuclear tone type
        """
        # Check for question marks (typically ascending)
        if '?' in phrase:
            return NuclearTone.ASCENDING

        # Last phrase in sequence → descending (assertion)
        if phrase_index == total_phrases - 1:
            return NuclearTone.DESCENDING

        # Given information markers
        given_markers = [
            r'\bel\b', r'\bla\b', r'\blos\b', r'\blas\b',  # Definite articles
            r'\bese\b', r'\besta\b', r'\besos\b', r'\bestas\b',  # Demonstratives
            r'\bmi\b', r'\btu\b', r'\bsu\b', r'\bnuestro\b',  # Possessives
            r'\btambién\b', r'\btampoco\b',  # Also/neither
        ]

        if contains_given_info or any(re.search(m, phrase.lower()) for m in given_markers):
            return NuclearTone.ASCENDING

        # Default: suspensive (continuation)
        return NuclearTone.SUSPENSIVE

    def identify_topic_boundaries(self, phrases: List[str]) -> List[bool]:
        """
        Identify which phrases mark topic boundaries.

        Topic boundaries typically occur at:
        - Sentence beginnings after major punctuation
        - After discourse markers (entonces, bueno, bien, ahora)

        Args:
            phrases: List of phrase strings

        Returns:
            List of booleans indicating topic boundaries
        """
        boundaries = []
        discourse_markers = ['entonces', 'bueno', 'bien', 'ahora', 'después', 'luego']

        for i, phrase in enumerate(phrases):
            is_boundary = False

            # First phrase is always a boundary
            if i == 0:
                is_boundary = True
            # Check for discourse markers
            elif any(phrase.lower().startswith(marker) for marker in discourse_markers):
                is_boundary = True
            # Check for major punctuation in previous phrase
            elif i > 0 and any(p in phrases[i - 1] for p in ['.', '!', '?']):
                is_boundary = True

            boundaries.append(is_boundary)

        return boundaries

    def create_declination_units(
        self, phrases: List[IntonationalPhrase]
    ) -> List[DeclinationUnit]:
        """
        Group phrases into declination units based on topic boundaries.

        Each unit:
        - Starts high (new topic)
        - Ends low (topic closure)

        Args:
            phrases: List of intonational phrases

        Returns:
            List of declination units
        """
        units = []
        current_unit_phrases = []
        unit_count = 0

        for i, phrase in enumerate(phrases):
            current_unit_phrases.append(phrase)

            # End unit on topic boundary or last phrase
            if phrase.is_topic_boundary and i > 0:
                # Create unit from accumulated phrases
                unit = DeclinationUnit(
                    phrases=current_unit_phrases[:-1],  # Exclude boundary phrase
                    topic=f"topic_{unit_count}",
                    f0_start_hz=self.f0_range["max"],  # High start
                    f0_end_hz=self.f0_range["min"]  # Low end
                )
                units.append(unit)
                unit_count += 1
                current_unit_phrases = [phrase]  # Start new unit with boundary phrase

        # Add final unit
        if current_unit_phrases:
            unit = DeclinationUnit(
                phrases=current_unit_phrases,
                topic=f"topic_{unit_count}",
                f0_start_hz=self.f0_range["max"],
                f0_end_hz=self.f0_range["min"]
            )
            units.append(unit)

        return units

    def process_text(self, text: str) -> Dict:
        """
        Full discourse prosody processing pipeline.

        Args:
            text: Input text

        Returns:
            Dictionary with discourse structure and prosodic annotations
        """
        # Step 1: Segment into phrases
        phrase_texts = self.segment_into_phrases(text)

        # Step 2: Identify topic boundaries
        topic_boundaries = self.identify_topic_boundaries(phrase_texts)

        # Step 3: Assign nuclear tones
        phrases = []
        for i, (phrase_text, is_boundary) in enumerate(zip(phrase_texts, topic_boundaries)):
            nuclear_tone = self.determine_nuclear_tone(
                phrase_text,
                phrase_index=i,
                total_phrases=len(phrase_texts),
                is_topic_start=is_boundary
            )

            # Determine F0 levels
            if is_boundary:
                f0_start = "high"  # New topic
            else:
                f0_start = "mid"

            tone_config = self.NUCLEAR_TONES[nuclear_tone]
            if tone_config.discourse_role == "foreground":
                f0_end = "low"  # Assertion
            elif nuclear_tone == NuclearTone.ASCENDING:
                f0_end = "high"  # Given info
            else:
                f0_end = "mid"  # Suspensive

            intonational_phrase = IntonationalPhrase(
                text=phrase_text,
                nuclear_tone=nuclear_tone,
                f0_start=f0_start,
                f0_end=f0_end,
                is_topic_boundary=is_boundary,
                discourse_role=tone_config.discourse_role
            )
            phrases.append(intonational_phrase)

        # Step 4: Create declination units
        declination_units = self.create_declination_units(phrases)

        # Step 5: Generate prosodic annotations
        annotations = []
        for phrase in phrases:
            tone_config = self.NUCLEAR_TONES[phrase.nuclear_tone]
            annotations.append({
                "text": phrase.text,
                "nuclear_tone": phrase.nuclear_tone.value,
                "symbol": tone_config.symbol,
                "f0_pattern": tone_config.f0_pattern,
                "f0_start": phrase.f0_start,
                "f0_end": phrase.f0_end,
                "discourse_role": phrase.discourse_role,
                "processing_instruction": tone_config.processing,
                "is_topic_boundary": phrase.is_topic_boundary,
            })

        return {
            "original_text": text,
            "phrases": annotations,
            "declination_units": len(declination_units),
            "voice_type": self.voice_type,
            "f0_range": self.f0_range,
            "framework": "Relevance Theory (Guglielmone et al., 2014)"
        }

    def generate_ssml_markup(self, text: str) -> str:
        """
        Generate SSML markup with prosodic annotations.

        Args:
            text: Input text

        Returns:
            SSML-marked text
        """
        result = self.process_text(text)
        ssml_parts = ['<speak>']

        for phrase_data in result["phrases"]:
            # Map nuclear tone to prosody attributes
            if phrase_data["nuclear_tone"] == "descending":
                contour = "falling"
                pitch_end = "-10%"
            elif phrase_data["nuclear_tone"] == "ascending":
                contour = "rising"
                pitch_end = "+15%"
            else:  # suspensive
                contour = "neutral"
                pitch_end = "0%"

            # Add boundary tone if topic boundary
            boundary = ' <break time="500ms"/>' if phrase_data["is_topic_boundary"] else ''

            ssml_parts.append(
                f'{boundary}<prosody pitch="{pitch_end}" contour="{contour}">'
                f'{phrase_data["text"]}</prosody>'
            )

        ssml_parts.append('</speak>')
        return ''.join(ssml_parts)


# Convenience functions
def analyze_discourse_prosody(text: str, voice_type: str = "female") -> Dict:
    """
    Analyze discourse prosody of Spanish text.

    Args:
        text: Input text
        voice_type: "female" or "male"

    Returns:
        Discourse structure analysis
    """
    processor = DiscourseProsodia(voice_type=voice_type)
    return processor.process_text(text)


def generate_prosodic_markup(text: str, voice_type: str = "female") -> str:
    """
    Generate SSML markup with discourse-level prosody.

    Args:
        text: Input text
        voice_type: "female" or "male"

    Returns:
        SSML-marked text
    """
    processor = DiscourseProsodia(voice_type=voice_type)
    return processor.generate_ssml_markup(text)
