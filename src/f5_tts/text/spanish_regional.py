"""Regional Spanish phonetics, prosody, and slang support for Latin American variants.

Supports:
- Rioplatense (Argentina/Uruguay)
- Colombian Spanish
- Mexican Spanish
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple, Optional
import re


class SpanishRegion(Enum):
    """Spanish regional variants."""
    NEUTRAL = "neutral"  # Standard/neutral Latin American Spanish
    RIOPLATENSE = "rioplatense"  # Argentina/Uruguay
    COLOMBIAN = "colombian"  # Colombian
    MEXICAN = "mexican"  # Mexican
    CHILEAN = "chilean"  # Chilean
    CARIBBEAN = "caribbean"  # Caribbean (Cuba, Dominican Republic, Puerto Rico)
    ANDEAN = "andean"  # Andean (Peru, Ecuador, Bolivia)


@dataclass
class PhoneticFeature:
    """Phonetic feature for regional pronunciation."""
    pattern: str  # Regex pattern to match
    replacement: str  # Replacement for the pattern
    context: Optional[str] = None  # Context where this applies (e.g., "word_final")
    description: str = ""


@dataclass
class ProsodicPattern:
    """Prosodic pattern for regional intonation."""
    pattern_type: str  # "intonation", "stress", "rhythm"
    markers: List[str]  # Text markers that indicate this pattern
    description: str = ""


class RegionalPhonetics:
    """Regional phonetic transformations for Spanish variants."""

    # Rioplatense phonetic features
    RIOPLATENSE_FEATURES = [
        PhoneticFeature(
            pattern=r'([lL][lL])',
            replacement=r'ʃ',  # "ll" -> [ʃ] (sheísmo)
            description="Sheísmo: 'll' pronounced as 'sh'"
        ),
        PhoneticFeature(
            pattern=r'\b([yY])([aeiouáéíóú])',
            replacement=r'ʒ\2',  # "y" -> [ʒ] (yeísmo rehilado)
            description="Yeísmo rehilado: 'y' with voiced fricative"
        ),
        PhoneticFeature(
            pattern=r's\b',
            replacement='h',  # Aspiration of final 's'
            context="word_final",
            description="Aspiración de 's' final"
        ),
        PhoneticFeature(
            pattern=r'([aeiouáéíóú])do\b',
            replacement=r'\1o',  # Participio reduction: "hablado" -> "hablao"
            context="word_final",
            description="Reducción de participios"
        ),
    ]

    # Colombian phonetic features
    COLOMBIAN_FEATURES = [
        PhoneticFeature(
            pattern=r's\b',
            replacement='s',  # Maintain 's' (unlike Caribbean)
            context="word_final",
            description="Conservación de 's' final (especially Bogotá/Antioquia)"
        ),
        PhoneticFeature(
            pattern=r'll',
            replacement='y',  # Standard yeísmo
            description="Yeísmo estándar"
        ),
        PhoneticFeature(
            pattern=r'([aeiouáéíóú])([rl])\b',
            replacement=r'\1\2',  # Conservative pronunciation
            context="word_final",
            description="Articulación clara de líquidas finales"
        ),
    ]

    # Mexican phonetic features
    MEXICAN_FEATURES = [
        PhoneticFeature(
            pattern=r'ch',
            replacement='tʃ',  # Clear affricate
            description="Africada postalveolar"
        ),
        PhoneticFeature(
            pattern=r'll',
            replacement='y',  # Yeísmo
            description="Yeísmo mexicano"
        ),
        PhoneticFeature(
            pattern=r's\b',
            replacement='s',  # Maintained 's'
            context="word_final",
            description="Conservación de 's' final"
        ),
        PhoneticFeature(
            pattern=r'([aeiouáéíóú])([dt])o\b',
            replacement=r'\1\2o',  # Clear consonants
            context="word_final",
            description="Articulación clara de consonantes finales"
        ),
    ]

    @classmethod
    def get_features(cls, region: SpanishRegion) -> List[PhoneticFeature]:
        """Get phonetic features for a specific region."""
        mapping = {
            SpanishRegion.RIOPLATENSE: cls.RIOPLATENSE_FEATURES,
            SpanishRegion.COLOMBIAN: cls.COLOMBIAN_FEATURES,
            SpanishRegion.MEXICAN: cls.MEXICAN_FEATURES,
            SpanishRegion.NEUTRAL: [],  # No special features
        }
        return mapping.get(region, [])


class RegionalProsody:
    """Regional prosodic patterns for Spanish variants."""

    # Prosodic markers for intonation
    RIOPLATENSE_PROSODY = [
        ProsodicPattern(
            pattern_type="intonation",
            markers=["¿", "?", "che", "boludo", "¡"],
            description="Rioplatense rising intonation, Italian influence"
        ),
        ProsodicPattern(
            pattern_type="stress",
            markers=["vos", "tenés", "querés", "podés"],
            description="Voseo stress patterns"
        ),
    ]

    COLOMBIAN_PROSODY = [
        ProsodicPattern(
            pattern_type="intonation",
            markers=["¿cierto?", "¿sí?", "pues", "¿no?"],
            description="Colombian question tags and softening"
        ),
        ProsodicPattern(
            pattern_type="rhythm",
            markers=["entonces", "o sea", "pues"],
            description="Paisa rhythm patterns"
        ),
    ]

    MEXICAN_PROSODY = [
        ProsodicPattern(
            pattern_type="intonation",
            markers=["¿verdad?", "¿no?", "órale", "¿qué onda?"],
            description="Mexican question tags and exclamations"
        ),
        ProsodicPattern(
            pattern_type="stress",
            markers=["órale", "ándele", "híjole"],
            description="Mexican stress on exclamations"
        ),
    ]

    @classmethod
    def get_patterns(cls, region: SpanishRegion) -> List[ProsodicPattern]:
        """Get prosodic patterns for a specific region."""
        mapping = {
            SpanishRegion.RIOPLATENSE: cls.RIOPLATENSE_PROSODY,
            SpanishRegion.COLOMBIAN: cls.COLOMBIAN_PROSODY,
            SpanishRegion.MEXICAN: cls.MEXICAN_PROSODY,
            SpanishRegion.NEUTRAL: [],
        }
        return mapping.get(region, [])


class RegionalSlang:
    """Regional slang and modismos (idiomatic expressions) for Spanish variants."""

    # Rioplatense slang
    RIOPLATENSE_SLANG = {
        # Common expressions
        "che": {"type": "interjection", "meaning": "hey/dude", "usage": "informal"},
        "boludo": {"type": "noun", "meaning": "dude/fool", "usage": "very_informal"},
        "quilombo": {"type": "noun", "meaning": "mess/chaos", "usage": "informal"},
        "laburo": {"type": "noun", "meaning": "trabajo/work", "usage": "informal"},
        "mina": {"type": "noun", "meaning": "mujer/woman", "usage": "informal"},
        "pibe": {"type": "noun", "meaning": "chico/kid", "usage": "informal"},
        "chabón": {"type": "noun", "meaning": "tipo/guy", "usage": "informal"},

        # Voseo conjugations (important for stress!)
        "vos": {"type": "pronoun", "replaces": "tú", "usage": "standard"},
        "tenés": {"type": "verb", "replaces": "tienes", "stress": "final"},
        "querés": {"type": "verb", "replaces": "quieres", "stress": "final"},
        "podés": {"type": "verb", "replaces": "puedes", "stress": "final"},
        "sabés": {"type": "verb", "replaces": "sabes", "stress": "final"},
        "sos": {"type": "verb", "replaces": "eres", "usage": "standard"},

        # Modismos
        "de una": {"type": "phrase", "meaning": "right away/definitely", "usage": "informal"},
        "al pedo": {"type": "phrase", "meaning": "in vain/useless", "usage": "vulgar"},
        "ni en pedo": {"type": "phrase", "meaning": "no way", "usage": "vulgar"},
    }

    # Colombian slang
    COLOMBIAN_SLANG = {
        # Common expressions
        "parcero": {"type": "noun", "meaning": "amigo/friend", "usage": "informal"},
        "parce": {"type": "noun", "meaning": "amigo/friend", "usage": "informal"},
        "chimba": {"type": "adjective", "meaning": "great/awesome", "usage": "informal"},
        "bacano": {"type": "adjective", "meaning": "cool/nice", "usage": "informal"},
        "berraco": {"type": "adjective", "meaning": "tough/brave", "usage": "informal"},
        "gonorrea": {"type": "noun", "meaning": "jerk (strong)", "usage": "vulgar"},
        "polas": {"type": "noun", "meaning": "cervezas/beers", "usage": "informal"},
        "plata": {"type": "noun", "meaning": "dinero/money", "usage": "standard"},

        # Paisa expressions
        "pues": {"type": "particle", "meaning": "well/then", "usage": "standard_paisa"},
        "¿sí o qué?": {"type": "phrase", "meaning": "right?", "usage": "informal"},
        "hacer una vaca": {"type": "phrase", "meaning": "pool money together", "usage": "informal"},

        # Question tags
        "¿cierto?": {"type": "tag", "meaning": "right?", "usage": "standard"},
        "¿no?": {"type": "tag", "meaning": "right?/no?", "usage": "standard"},
    }

    # Mexican slang
    MEXICAN_SLANG = {
        # Common expressions
        "órale": {"type": "interjection", "meaning": "wow/okay/alright", "usage": "informal"},
        "güey": {"type": "noun", "meaning": "dude/man", "usage": "very_informal"},
        "wey": {"type": "noun", "meaning": "dude/man (alt spelling)", "usage": "very_informal"},
        "chido": {"type": "adjective", "meaning": "cool/nice", "usage": "informal"},
        "padre": {"type": "adjective", "meaning": "cool/great", "usage": "informal"},
        "chale": {"type": "interjection", "meaning": "damn/no way", "usage": "informal"},
        "chingón": {"type": "adjective", "meaning": "awesome/badass", "usage": "vulgar"},
        "neta": {"type": "noun", "meaning": "verdad/truth", "usage": "informal"},
        "fresa": {"type": "adjective", "meaning": "posh/preppy", "usage": "informal"},

        # Expressions
        "¿qué onda?": {"type": "phrase", "meaning": "what's up?", "usage": "informal"},
        "no manches": {"type": "phrase", "meaning": "no way/seriously?", "usage": "informal"},
        "qué padre": {"type": "phrase", "meaning": "how cool", "usage": "informal"},
        "ándele": {"type": "interjection", "meaning": "come on/that's right", "usage": "informal"},

        # Diminutives (very common in Mexican Spanish)
        "ahorita": {"type": "adverb", "meaning": "right now/in a bit", "usage": "standard"},
        "lueguito": {"type": "adverb", "meaning": "very soon", "usage": "informal"},
    }

    @classmethod
    def get_slang_dict(cls, region: SpanishRegion) -> Dict[str, dict]:
        """Get slang dictionary for a specific region."""
        mapping = {
            SpanishRegion.RIOPLATENSE: cls.RIOPLATENSE_SLANG,
            SpanishRegion.COLOMBIAN: cls.COLOMBIAN_SLANG,
            SpanishRegion.MEXICAN: cls.MEXICAN_SLANG,
            SpanishRegion.NEUTRAL: {},
        }
        return mapping.get(region, {})

    @classmethod
    def detect_region_from_text(cls, text: str) -> Optional[SpanishRegion]:
        """Auto-detect region from slang markers in text."""
        text_lower = text.lower()

        # Check for distinctive markers
        rioplatense_markers = ["che", "boludo", "vos ", "tenés", "querés", "pibe"]
        colombian_markers = ["parcero", "parce", "chimba", "bacano", "pues", "¿cierto?"]
        mexican_markers = ["órale", "güey", "wey", "chido", "¿qué onda?", "no manches"]

        scores = {
            SpanishRegion.RIOPLATENSE: sum(1 for m in rioplatense_markers if m in text_lower),
            SpanishRegion.COLOMBIAN: sum(1 for m in colombian_markers if m in text_lower),
            SpanishRegion.MEXICAN: sum(1 for m in mexican_markers if m in text_lower),
        }

        max_score = max(scores.values())
        if max_score > 0:
            return max(scores.items(), key=lambda x: x[1])[0]

        return None


class SpanishRegionalProcessor:
    """Main processor for regional Spanish text normalization and phonetic transformation."""

    def __init__(self, region: SpanishRegion = SpanishRegion.NEUTRAL, auto_detect: bool = False):
        """
        Initialize regional processor.

        Args:
            region: Target regional variant
            auto_detect: Whether to auto-detect region from text
        """
        self.region = region
        self.auto_detect = auto_detect
        self.phonetic_features = RegionalPhonetics.get_features(region)
        self.prosodic_patterns = RegionalProsody.get_patterns(region)
        self.slang_dict = RegionalSlang.get_slang_dict(region)

    def normalize_text(self, text: str) -> str:
        """
        Normalize text for regional variant.
        Handles slang, contractions, and regional expressions.
        """
        # Auto-detect region if enabled
        if self.auto_detect:
            detected = RegionalSlang.detect_region_from_text(text)
            if detected and detected != self.region:
                self.region = detected
                self.phonetic_features = RegionalPhonetics.get_features(detected)
                self.prosodic_patterns = RegionalProsody.get_patterns(detected)
                self.slang_dict = RegionalSlang.get_slang_dict(detected)

        # Normalize common contractions and regional variations
        normalized = text

        # Regional-specific normalizations
        if self.region == SpanishRegion.RIOPLATENSE:
            # Normalize voseo forms (already in correct form, just mark for prosody)
            pass
        elif self.region == SpanishRegion.MEXICAN:
            # Handle common Mexican contractions
            normalized = re.sub(r'\bpa\b', 'para', normalized)
            normalized = re.sub(r'\bpal\b', 'para el', normalized)

        return normalized

    def apply_phonetic_features(self, text: str) -> str:
        """
        Apply regional phonetic transformations to text.
        This creates a phonetic representation that guides TTS prosody.
        """
        result = text

        for feature in self.phonetic_features:
            if feature.context is None or feature.context in ["word_final", "word_initial"]:
                result = re.sub(feature.pattern, feature.replacement, result)

        return result

    def add_prosodic_markers(self, text: str) -> Tuple[str, List[str]]:
        """
        Identify and mark prosodic patterns in text.
        Returns: (text, list of prosodic hints)
        """
        hints = []

        for pattern in self.prosodic_patterns:
            for marker in pattern.markers:
                if marker.lower() in text.lower():
                    hints.append(f"{pattern.pattern_type}:{pattern.description}")

        return text, hints

    def process(self, text: str, apply_phonetics: bool = True) -> Dict[str, any]:
        """
        Full processing pipeline for regional Spanish text.

        Args:
            text: Input text
            apply_phonetics: Whether to apply phonetic transformations

        Returns:
            Dictionary with processed text and metadata
        """
        # Step 1: Normalize text
        normalized = self.normalize_text(text)

        # Step 2: Apply phonetic features if requested
        phonetic = self.apply_phonetic_features(normalized) if apply_phonetics else normalized

        # Step 3: Extract prosodic markers
        final_text, prosodic_hints = self.add_prosodic_markers(phonetic)

        return {
            "original": text,
            "normalized": normalized,
            "phonetic": phonetic,
            "final": final_text,
            "region": self.region.value,
            "prosodic_hints": prosodic_hints,
            "detected_slang": self._detect_slang_in_text(text),
        }

    def _detect_slang_in_text(self, text: str) -> List[Dict[str, str]]:
        """Detect slang terms present in text."""
        detected = []
        text_lower = text.lower()

        for term, info in self.slang_dict.items():
            if term.lower() in text_lower:
                detected.append({
                    "term": term,
                    "type": info.get("type", "unknown"),
                    "meaning": info.get("meaning", ""),
                    "usage": info.get("usage", "standard"),
                })

        return detected


# Convenience functions
def get_regional_processor(
    region: str | SpanishRegion = "neutral",
    auto_detect: bool = False
) -> SpanishRegionalProcessor:
    """
    Get a regional processor for Spanish text.

    Args:
        region: Region name (str) or SpanishRegion enum
        auto_detect: Whether to auto-detect region from text

    Returns:
        SpanishRegionalProcessor instance
    """
    if isinstance(region, str):
        region = SpanishRegion(region.lower())

    return SpanishRegionalProcessor(region=region, auto_detect=auto_detect)


def process_spanish_text(
    text: str,
    region: str = "neutral",
    auto_detect: bool = False
) -> Dict[str, any]:
    """
    Process Spanish text for regional variant.

    Args:
        text: Input text
        region: Target region (neutral, rioplatense, colombian, mexican)
        auto_detect: Auto-detect region from text

    Returns:
        Processing results dictionary
    """
    processor = get_regional_processor(region, auto_detect)
    return processor.process(text)
