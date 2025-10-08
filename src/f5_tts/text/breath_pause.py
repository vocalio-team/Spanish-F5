"""Advanced breath and pause modeling for natural TTS pacing."""

import re
from typing import List, Tuple, Dict
from dataclasses import dataclass
from enum import Enum


class PauseType(Enum):
    """Types of pauses in speech."""
    MICRO = "micro"          # < 100ms - slight hesitation
    SHORT = "short"          # 100-300ms - comma, light break
    MEDIUM = "medium"        # 300-500ms - clause, semicolon
    LONG = "long"           # 500-800ms - sentence end
    PARAGRAPH = "paragraph"  # 800-1200ms - paragraph break
    BREATH = "breath"       # Natural breathing pause


@dataclass
class Pause:
    """A pause in speech."""
    position: int           # Character position
    type: PauseType
    duration_ms: int        # Recommended duration in milliseconds
    is_breath_point: bool   # Whether this is a natural breath point
    context: str           # Surrounding context


@dataclass
class BreathPattern:
    """Breathing pattern for a text segment."""
    text: str
    pauses: List[Pause]
    breath_points: List[int]  # Positions where breathing should occur
    avg_pause_interval: float  # Average ms between pauses
    total_duration_estimate: float  # Estimated total duration in seconds


class BreathPauseAnalyzer:
    """Analyze and model breath and pause patterns for natural speech."""

    # Punctuation-based pause durations (ms)
    PAUSE_DURATIONS = {
        ',': 200,      # Comma - short pause
        ';': 400,      # Semicolon - medium pause
        ':': 350,      # Colon - medium pause
        '.': 600,      # Period - long pause
        '!': 650,      # Exclamation - long pause with energy
        '?': 600,      # Question - long pause
        '...': 800,    # Ellipsis - extra long
        '—': 300,      # Em dash - medium pause
        '-': 150,      # Hyphen - micro pause (rare)
    }

    # Breath capacity estimation
    AVG_BREATH_DURATION_MS = 15000  # Average speaking duration per breath (~15s)
    MIN_BREATH_INTERVAL_MS = 8000   # Minimum time between breaths (~8s)
    MAX_BREATH_INTERVAL_MS = 25000  # Maximum time between breaths (~25s)

    # Speaking rate (characters per second - approximate)
    SPEAKING_RATE_CHARS_PER_SEC = 15.0  # Average Spanish speaking rate

    def __init__(self):
        """Initialize breath/pause analyzer."""
        pass

    def analyze(self, text: str) -> BreathPattern:
        """
        Analyze text for breath and pause patterns.

        Args:
            text: Input text

        Returns:
            Complete breath and pause analysis
        """
        pauses = []

        # 1. Add punctuation-based pauses
        pauses.extend(self._detect_punctuation_pauses(text))

        # 2. Add micro-pauses at conjunctions
        pauses.extend(self._detect_conjunction_pauses(text))

        # 3. Add paragraph-level pauses
        pauses.extend(self._detect_paragraph_pauses(text))

        # 4. Identify natural breath points
        breath_points = self._identify_breath_points(text, pauses)

        # Mark breath points in pauses
        for pause in pauses:
            if pause.position in breath_points:
                pause.is_breath_point = True
                # Extend pause duration slightly for breath
                pause.duration_ms = min(pause.duration_ms + 150, 1200)

        # 5. Calculate statistics
        avg_interval = self._calculate_avg_pause_interval(pauses)
        duration_estimate = self._estimate_duration(text, pauses)

        return BreathPattern(
            text=text,
            pauses=sorted(pauses, key=lambda p: p.position),
            breath_points=sorted(breath_points),
            avg_pause_interval=avg_interval,
            total_duration_estimate=duration_estimate
        )

    def _detect_punctuation_pauses(self, text: str) -> List[Pause]:
        """Detect pauses at punctuation marks."""
        pauses = []

        # Ellipsis (must check before single periods)
        for match in re.finditer(r'\.\.\.', text):
            pauses.append(Pause(
                position=match.start(),
                type=PauseType.LONG,
                duration_ms=self.PAUSE_DURATIONS['...'],
                is_breath_point=False,
                context=self._get_context(text, match.start())
            ))

        # Other punctuation
        for punct, duration in self.PAUSE_DURATIONS.items():
            if punct == '...':
                continue  # Already handled

            pattern = re.escape(punct)
            for match in re.finditer(pattern, text):
                # Skip if part of ellipsis
                if punct == '.' and text[match.start():match.start()+3] == '...':
                    continue

                # Determine pause type
                if duration < 200:
                    pause_type = PauseType.MICRO
                elif duration < 350:
                    pause_type = PauseType.SHORT
                elif duration < 550:
                    pause_type = PauseType.MEDIUM
                else:
                    pause_type = PauseType.LONG

                pauses.append(Pause(
                    position=match.start(),
                    type=pause_type,
                    duration_ms=duration,
                    is_breath_point=False,
                    context=self._get_context(text, match.start())
                ))

        return pauses

    def _detect_conjunction_pauses(self, text: str) -> List[Pause]:
        """Detect micro-pauses at conjunctions and connectors."""
        pauses = []

        # Conjunctions that warrant micro-pauses
        conjunctions = [
            r'\by\b', r'\be\b', r'\bo\b', r'\bpero\b', r'\bmas\b',
            r'\baunque\b', r'\bsi\b', r'\bcuando\b', r'\bmientras\b',
            r'\bporque\b', r'\bpues\b', r'\bcomo\b'
        ]

        for conj_pattern in conjunctions:
            for match in re.finditer(conj_pattern, text, re.IGNORECASE):
                # Only add if not already covered by punctuation
                if not self._has_nearby_punctuation(text, match.start(), radius=5):
                    pauses.append(Pause(
                        position=match.start(),
                        type=PauseType.MICRO,
                        duration_ms=80,  # Very brief
                        is_breath_point=False,
                        context=self._get_context(text, match.start())
                    ))

        return pauses

    def _detect_paragraph_pauses(self, text: str) -> List[Pause]:
        """Detect paragraph breaks (double newline)."""
        pauses = []

        # Paragraph breaks (double newline or more)
        for match in re.finditer(r'\n\s*\n', text):
            pauses.append(Pause(
                position=match.start(),
                type=PauseType.PARAGRAPH,
                duration_ms=1000,  # Long pause between paragraphs
                is_breath_point=True,  # Always breathe at paragraph breaks
                context="[PARAGRAPH BREAK]"
            ))

        return pauses

    def _identify_breath_points(self, text: str, pauses: List[Pause]) -> List[int]:
        """
        Identify natural breath points based on text structure and duration.

        Strategy:
        1. Always breathe at paragraph breaks
        2. Breathe at sentence ends if enough time has passed
        3. Breathe at major clause boundaries if necessary
        """
        breath_points = []

        # Get sentence/paragraph boundaries
        major_pauses = [p for p in pauses if p.type in [PauseType.LONG, PauseType.PARAGRAPH]]

        if not major_pauses:
            return breath_points

        # Estimate time since last breath
        current_time_ms = 0
        last_breath_ms = 0

        for pause in sorted(major_pauses, key=lambda p: p.position):
            # Estimate speaking time up to this pause
            chars_spoken = pause.position - (last_breath_ms if breath_points else 0)
            speaking_time_ms = (chars_spoken / self.SPEAKING_RATE_CHARS_PER_SEC) * 1000
            current_time_ms = speaking_time_ms

            # Add pause duration
            current_time_ms += pause.duration_ms

            # Check if we need a breath
            need_breath = False

            # Always breathe at paragraph breaks
            if pause.type == PauseType.PARAGRAPH:
                need_breath = True

            # Breathe at sentence ends if enough time has passed
            elif pause.type == PauseType.LONG:
                time_since_breath = current_time_ms - last_breath_ms
                if time_since_breath >= self.MIN_BREATH_INTERVAL_MS:
                    need_breath = True

            if need_breath:
                breath_points.append(pause.position)
                last_breath_ms = current_time_ms

        return breath_points

    def _has_nearby_punctuation(self, text: str, position: int, radius: int = 5) -> bool:
        """Check if there's punctuation nearby."""
        start = max(0, position - radius)
        end = min(len(text), position + radius)
        nearby = text[start:end]
        return any(p in nearby for p in ',.;:!?')

    def _get_context(self, text: str, position: int, window: int = 20) -> str:
        """Get context around a position."""
        start = max(0, position - window)
        end = min(len(text), position + window)
        return text[start:end].replace('\n', ' ')

    def _calculate_avg_pause_interval(self, pauses: List[Pause]) -> float:
        """Calculate average interval between pauses."""
        if len(pauses) < 2:
            return 0.0

        intervals = []
        for i in range(len(pauses) - 1):
            interval_ms = pauses[i + 1].position - pauses[i].position
            intervals.append(interval_ms)

        return sum(intervals) / len(intervals) if intervals else 0.0

    def _estimate_duration(self, text: str, pauses: List[Pause]) -> float:
        """Estimate total speaking duration in seconds."""
        # Character-based duration
        char_duration_s = len(text) / self.SPEAKING_RATE_CHARS_PER_SEC

        # Add pause durations
        total_pause_ms = sum(p.duration_ms for p in pauses)
        pause_duration_s = total_pause_ms / 1000.0

        return char_duration_s + pause_duration_s

    def insert_pauses_in_text(self, text: str, pauses: List[Pause]) -> str:
        """
        Insert pause markers into text (for visualization).

        Args:
            text: Original text
            pauses: List of pauses to insert

        Returns:
            Text with pause markers
        """
        # Sort pauses by position (reverse to insert from end)
        sorted_pauses = sorted(pauses, key=lambda p: p.position, reverse=True)

        marked = text
        for pause in sorted_pauses:
            # Choose marker based on type
            if pause.is_breath_point:
                marker = f" [BREATH:{pause.duration_ms}ms] "
            elif pause.type == PauseType.MICRO:
                marker = " ‧ "
            elif pause.type == PauseType.SHORT:
                marker = " · "
            elif pause.type == PauseType.MEDIUM:
                marker = " / "
            elif pause.type == PauseType.LONG:
                marker = " | "
            elif pause.type == PauseType.PARAGRAPH:
                marker = "\n\n[PAUSE]\n\n"
            else:
                marker = " "

            # Insert at position
            pos = pause.position
            if pos < len(marked):
                # Try to insert after punctuation if present
                if pos < len(marked) - 1 and marked[pos] in ',.;:!?':
                    pos += 1
                marked = marked[:pos] + marker + marked[pos:]

        return marked


def analyze_breath_pauses(text: str) -> BreathPattern:
    """
    Convenience function to analyze breath and pause patterns.

    Args:
        text: Text to analyze

    Returns:
        Breath pattern analysis
    """
    analyzer = BreathPauseAnalyzer()
    return analyzer.analyze(text)


def format_breath_report(pattern: BreathPattern) -> str:
    """
    Format breath/pause analysis as readable report.

    Args:
        pattern: Breath pattern to format

    Returns:
        Formatted report
    """
    report = []
    report.append("=" * 60)
    report.append("BREATH & PAUSE ANALYSIS")
    report.append("=" * 60)
    report.append("")

    # Statistics
    report.append(f"Total Pauses: {len(pattern.pauses)}")
    report.append(f"Breath Points: {len(pattern.breath_points)}")
    report.append(f"Estimated Duration: {pattern.total_duration_estimate:.1f}s")
    report.append(f"Avg Pause Interval: {pattern.avg_pause_interval:.0f} chars")
    report.append("")

    # Pause breakdown
    pause_types = {}
    for pause in pattern.pauses:
        type_name = pause.type.value
        pause_types[type_name] = pause_types.get(type_name, 0) + 1

    report.append("Pause Breakdown:")
    for type_name, count in sorted(pause_types.items()):
        report.append(f"  • {type_name}: {count}")
    report.append("")

    # Show first few pauses
    report.append("Sample Pauses:")
    for pause in pattern.pauses[:10]:
        breath_marker = " [BREATH]" if pause.is_breath_point else ""
        report.append(f"  • pos {pause.position}: {pause.type.value} ({pause.duration_ms}ms){breath_marker}")
        report.append(f"    Context: ...{pause.context}...")
    if len(pattern.pauses) > 10:
        report.append(f"  ... and {len(pattern.pauses) - 10} more")
    report.append("")

    # Marked text preview
    analyzer = BreathPauseAnalyzer()
    marked = analyzer.insert_pauses_in_text(pattern.text, pattern.pauses)
    report.append("Marked Text Preview:")
    preview = marked[:300] + "..." if len(marked) > 300 else marked
    report.append(f"  {preview}")
    report.append("")

    report.append("=" * 60)

    return "\n".join(report)
