"""Enhanced prosody analysis and marker generation for Spanish TTS."""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ProsodyType(Enum):
    """Types of prosodic features."""
    QUESTION = "question"
    EXCLAMATION = "exclamation"
    STATEMENT = "statement"
    EMPHASIS = "emphasis"
    PAUSE = "pause"
    RISING_TONE = "rising"
    FALLING_TONE = "falling"
    NEUTRAL = "neutral"


class IntensityLevel(Enum):
    """Emotional intensity levels."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class ProsodyMarker:
    """A single prosody marker."""
    type: ProsodyType
    position: int  # Character position
    length: int  # Length of affected text
    intensity: IntensityLevel
    metadata: Dict[str, any]


@dataclass
class ProsodyAnalysis:
    """Complete prosody analysis result."""
    text: str
    marked_text: str  # Text with prosody markers
    markers: List[ProsodyMarker]
    sentence_boundaries: List[int]
    breath_points: List[int]
    stress_points: List[int]
    pitch_contours: Dict[str, any]


class SpanishProsodyAnalyzer:
    """Analyze and enhance prosody for Spanish text."""

    # Spanish question words that indicate rising intonation
    QUESTION_WORDS = [
        'qué', 'quién', 'quiénes', 'cuál', 'cuáles', 'cómo', 'cuándo',
        'dónde', 'adónde', 'por qué', 'para qué', 'cuánto', 'cuánta',
        'cuántos', 'cuántas'
    ]

    # Exclamation words that indicate strong emotion
    EXCLAMATION_WORDS = [
        'qué', 'cuán', 'cómo', 'ay', 'oh', 'ah', 'uf', 'ojalá',
        'caramba', 'dios mío', 'madre mía'
    ]

    # Words that typically receive emphasis
    EMPHASIS_WORDS = [
        'muy', 'mucho', 'muchísimo', 'bastante', 'demasiado',
        'realmente', 'verdaderamente', 'sumamente', 'extremadamente',
        'increíble', 'imposible', 'nunca', 'jamás', 'siempre',
        'todo', 'nada', 'nadie', 'todos', 'ninguno'
    ]

    # Conjunctions and connectors that need pauses
    PAUSE_MARKERS = [
        'pero', 'sin embargo', 'no obstante', 'aunque', 'mientras',
        'porque', 'ya que', 'puesto que', 'por lo tanto', 'entonces',
        'además', 'también', 'asimismo', 'por ejemplo', 'es decir',
        'o sea', 'en otras palabras', 'por cierto', 'en realidad'
    ]

    # Sentence-ending punctuation
    SENTENCE_ENDS = re.compile(r'[.!?;]\s+')

    # Clause boundaries
    CLAUSE_BOUNDARIES = re.compile(r'[,;:]\s+')

    def __init__(self):
        """Initialize prosody analyzer."""
        pass

    def analyze(self, text: str) -> ProsodyAnalysis:
        """
        Analyze text for prosodic features.

        Args:
            text: Input text to analyze

        Returns:
            Complete prosody analysis
        """
        # Find all prosodic features
        markers = []
        markers.extend(self._detect_questions(text))
        markers.extend(self._detect_exclamations(text))
        markers.extend(self._detect_emphasis(text))
        markers.extend(self._detect_pauses(text))

        # Find boundaries
        sentence_boundaries = self._find_sentence_boundaries(text)
        breath_points = self._find_breath_points(text, sentence_boundaries)
        stress_points = self._find_stress_points(text)

        # Analyze pitch contours
        pitch_contours = self._analyze_pitch_contours(text, markers)

        # Generate marked text
        marked_text = self._generate_marked_text(text, markers)

        return ProsodyAnalysis(
            text=text,
            marked_text=marked_text,
            markers=markers,
            sentence_boundaries=sentence_boundaries,
            breath_points=breath_points,
            stress_points=stress_points,
            pitch_contours=pitch_contours
        )

    def _detect_questions(self, text: str) -> List[ProsodyMarker]:
        """Detect question patterns and their characteristics."""
        markers = []

        # Spanish questions with question marks
        question_pattern = re.compile(r'¿([^?]+)\?')
        for match in question_pattern.finditer(text):
            question_text = match.group(1).lower()

            # Determine question type and intensity
            if any(qw in question_text for qw in self.QUESTION_WORDS):
                # Information question (wh-question) - typically falling intonation
                prosody_type = ProsodyType.FALLING_TONE
                intensity = IntensityLevel.MEDIUM
                metadata = {'question_type': 'information', 'requires_falling_intonation': True}
            else:
                # Yes/no question - rising intonation
                prosody_type = ProsodyType.RISING_TONE
                intensity = IntensityLevel.MEDIUM
                metadata = {'question_type': 'yes_no', 'requires_rising_intonation': True}

            # Check for intensity markers
            if any(word in question_text for word in ['realmente', 'verdaderamente', 'por favor']):
                intensity = IntensityLevel.HIGH

            markers.append(ProsodyMarker(
                type=prosody_type,
                position=match.start(),
                length=match.end() - match.start(),
                intensity=intensity,
                metadata=metadata
            ))

        return markers

    def _detect_exclamations(self, text: str) -> List[ProsodyMarker]:
        """Detect exclamation patterns."""
        markers = []

        # Spanish exclamations with exclamation marks
        exclamation_pattern = re.compile(r'¡([^!]+)!')
        for match in exclamation_pattern.finditer(text):
            exclamation_text = match.group(1).lower()

            # Determine intensity
            if any(ew in exclamation_text for ew in self.EXCLAMATION_WORDS[:3]):
                # Strong exclamations (qué, cuán, cómo)
                intensity = IntensityLevel.VERY_HIGH
            elif any(ew in exclamation_text for ew in self.EXCLAMATION_WORDS[3:]):
                # Interjections
                intensity = IntensityLevel.HIGH
            else:
                intensity = IntensityLevel.MEDIUM

            # Check for emphasis words
            if any(word in exclamation_text for word in ['muy', 'mucho', 'tan', 'tanto']):
                if intensity == IntensityLevel.HIGH:
                    intensity = IntensityLevel.VERY_HIGH

            markers.append(ProsodyMarker(
                type=ProsodyType.EXCLAMATION,
                position=match.start(),
                length=match.end() - match.start(),
                intensity=intensity,
                metadata={'has_exclamation_marks': True}
            ))

        return markers

    def _detect_emphasis(self, text: str) -> List[ProsodyMarker]:
        """Detect words and phrases that need emphasis."""
        markers = []

        # Word-based emphasis
        words = text.split()
        position = 0

        for word in words:
            word_clean = re.sub(r'[^\w]', '', word.lower())

            if word_clean in self.EMPHASIS_WORDS:
                # Determine intensity
                if word_clean in ['nunca', 'jamás', 'nadie', 'nada', 'ninguno']:
                    intensity = IntensityLevel.HIGH
                elif word_clean in ['muchísimo', 'extremadamente', 'sumamente']:
                    intensity = IntensityLevel.VERY_HIGH
                elif word_clean in ['muy', 'mucho', 'bastante']:
                    intensity = IntensityLevel.MEDIUM
                else:
                    intensity = IntensityLevel.MEDIUM

                markers.append(ProsodyMarker(
                    type=ProsodyType.EMPHASIS,
                    position=text.find(word, position),
                    length=len(word),
                    intensity=intensity,
                    metadata={'word': word_clean}
                ))

            position += len(word) + 1  # +1 for space

        # ALL CAPS detection (strong emphasis)
        caps_pattern = re.compile(r'\b[A-ZÁÉÍÓÚÑ]{2,}\b')
        for match in caps_pattern.finditer(text):
            markers.append(ProsodyMarker(
                type=ProsodyType.EMPHASIS,
                position=match.start(),
                length=match.end() - match.start(),
                intensity=IntensityLevel.VERY_HIGH,
                metadata={'all_caps': True}
            ))

        return markers

    def _detect_pauses(self, text: str) -> List[ProsodyMarker]:
        """Detect where pauses should occur."""
        markers = []

        # Punctuation-based pauses
        for match in self.CLAUSE_BOUNDARIES.finditer(text):
            # Comma, semicolon, colon
            pause_char = match.group()[0]
            if pause_char == ',':
                intensity = IntensityLevel.LOW  # Short pause
            elif pause_char == ';':
                intensity = IntensityLevel.MEDIUM  # Medium pause
            else:  # ':'
                intensity = IntensityLevel.MEDIUM

            markers.append(ProsodyMarker(
                type=ProsodyType.PAUSE,
                position=match.start(),
                length=1,
                intensity=intensity,
                metadata={'punctuation': pause_char}
            ))

        # Sentence-ending pauses (longer)
        for match in self.SENTENCE_ENDS.finditer(text):
            markers.append(ProsodyMarker(
                type=ProsodyType.PAUSE,
                position=match.start(),
                length=1,
                intensity=IntensityLevel.HIGH,  # Longer pause
                metadata={'sentence_end': True}
            ))

        # Connector-based pauses
        for connector in self.PAUSE_MARKERS:
            pattern = re.compile(r'\b' + re.escape(connector) + r'\b', re.IGNORECASE)
            for match in pattern.finditer(text):
                # Add pause before connector
                markers.append(ProsodyMarker(
                    type=ProsodyType.PAUSE,
                    position=match.start(),
                    length=0,  # Insert pause before
                    intensity=IntensityLevel.MEDIUM,
                    metadata={'connector': connector, 'position': 'before'}
                ))

        return markers

    def _find_sentence_boundaries(self, text: str) -> List[int]:
        """Find sentence boundaries."""
        boundaries = []
        for match in self.SENTENCE_ENDS.finditer(text):
            boundaries.append(match.start())
        return boundaries

    def _find_breath_points(self, text: str, sentence_boundaries: List[int]) -> List[int]:
        """Find natural breath points."""
        breath_points = []

        # Sentence boundaries are natural breath points
        breath_points.extend(sentence_boundaries)

        # Long sentences: add breath at major clause boundaries
        for match in self.CLAUSE_BOUNDARIES.finditer(text):
            pos = match.start()
            # Only if not too close to sentence boundary
            if not any(abs(pos - sb) < 20 for sb in sentence_boundaries):
                breath_points.append(pos)

        return sorted(breath_points)

    def _find_stress_points(self, text: str) -> List[int]:
        """Find syllables/words that should receive stress."""
        stress_points = []

        # Content words typically receive stress
        # In Spanish: nouns, verbs, adjectives, adverbs
        # Function words usually don't: articles, prepositions, etc.

        words = text.split()
        position = 0

        for word in words:
            word_clean = re.sub(r'[^\w]', '', word.lower())

            # Simple heuristic: words > 3 chars that aren't common function words
            function_words = {'el', 'la', 'los', 'las', 'un', 'una', 'de', 'del',
                            'en', 'a', 'al', 'con', 'por', 'para', 'que', 'es',
                            'son', 'está', 'están', 'y', 'o', 'pero'}

            if len(word_clean) > 3 and word_clean not in function_words:
                word_pos = text.find(word, position)
                stress_points.append(word_pos)

            position += len(word) + 1

        return stress_points

    def _analyze_pitch_contours(self, text: str, markers: List[ProsodyMarker]) -> Dict[str, any]:
        """Analyze overall pitch contour patterns."""
        contours = {
            'questions': [],
            'exclamations': [],
            'statements': [],
            'overall_pattern': 'neutral'
        }

        # Count pattern types
        rising_count = sum(1 for m in markers if m.type == ProsodyType.RISING_TONE)
        falling_count = sum(1 for m in markers if m.type == ProsodyType.FALLING_TONE)
        exclamation_count = sum(1 for m in markers if m.type == ProsodyType.EXCLAMATION)

        # Determine overall pattern
        if exclamation_count > 2:
            contours['overall_pattern'] = 'expressive'
        elif rising_count > falling_count:
            contours['overall_pattern'] = 'interrogative'
        elif falling_count > 0:
            contours['overall_pattern'] = 'declarative'

        # Record specific patterns
        for marker in markers:
            if marker.type == ProsodyType.RISING_TONE:
                contours['questions'].append({
                    'position': marker.position,
                    'type': marker.metadata.get('question_type', 'unknown')
                })
            elif marker.type == ProsodyType.FALLING_TONE:
                contours['questions'].append({
                    'position': marker.position,
                    'type': marker.metadata.get('question_type', 'unknown')
                })
            elif marker.type == ProsodyType.EXCLAMATION:
                contours['exclamations'].append({
                    'position': marker.position,
                    'intensity': marker.intensity.value
                })

        return contours

    def _generate_marked_text(self, text: str, markers: List[ProsodyMarker]) -> str:
        """Generate text with prosody markers embedded."""
        # Sort markers by position (reverse to insert from end)
        sorted_markers = sorted(markers, key=lambda m: m.position, reverse=True)

        marked = text
        for marker in sorted_markers:
            # Generate marker symbol
            if marker.type == ProsodyType.RISING_TONE:
                symbol = "↗"
            elif marker.type == ProsodyType.FALLING_TONE:
                symbol = "↘"
            elif marker.type == ProsodyType.EXCLAMATION:
                symbol = "‼️" if marker.intensity == IntensityLevel.VERY_HIGH else "❗"
            elif marker.type == ProsodyType.EMPHASIS:
                symbol = "*"
            elif marker.type == ProsodyType.PAUSE:
                if marker.intensity == IntensityLevel.HIGH:
                    symbol = " | "  # Long pause
                elif marker.intensity == IntensityLevel.MEDIUM:
                    symbol = " / "  # Medium pause
                else:
                    symbol = " ‧ "  # Short pause
                continue  # Pauses replace punctuation
            else:
                continue

            # Insert marker
            pos = marker.position + marker.length
            if pos < len(marked):
                marked = marked[:pos] + symbol + marked[pos:]

        return marked


def analyze_spanish_prosody(text: str) -> ProsodyAnalysis:
    """
    Convenience function to analyze Spanish text prosody.

    Args:
        text: Spanish text to analyze

    Returns:
        Complete prosody analysis
    """
    analyzer = SpanishProsodyAnalyzer()
    return analyzer.analyze(text)


def format_prosody_report(analysis: ProsodyAnalysis) -> str:
    """
    Format prosody analysis as readable report.

    Args:
        analysis: Prosody analysis result

    Returns:
        Formatted report string
    """
    report = []
    report.append("=" * 60)
    report.append("PROSODY ANALYSIS REPORT")
    report.append("=" * 60)
    report.append("")

    report.append(f"Original Text:")
    report.append(f"  {analysis.text}")
    report.append("")

    report.append(f"Marked Text:")
    report.append(f"  {analysis.marked_text}")
    report.append("")

    report.append(f"Markers Found: {len(analysis.markers)}")
    report.append("")

    # Group by type
    by_type = {}
    for marker in analysis.markers:
        type_name = marker.type.value
        if type_name not in by_type:
            by_type[type_name] = []
        by_type[type_name].append(marker)

    for type_name, markers_list in sorted(by_type.items()):
        report.append(f"{type_name.upper()}: {len(markers_list)} markers")
        for marker in markers_list[:5]:  # Show first 5
            snippet = analysis.text[marker.position:marker.position+marker.length]
            report.append(f"  • pos {marker.position}: '{snippet}' (intensity: {marker.intensity.value})")
        if len(markers_list) > 5:
            report.append(f"  ... and {len(markers_list) - 5} more")
        report.append("")

    report.append(f"Sentence Boundaries: {len(analysis.sentence_boundaries)}")
    report.append(f"Breath Points: {len(analysis.breath_points)}")
    report.append(f"Stress Points: {len(analysis.stress_points)}")
    report.append("")

    report.append(f"Pitch Contour: {analysis.pitch_contours['overall_pattern']}")
    report.append("=" * 60)

    return "\n".join(report)
