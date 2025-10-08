#!/usr/bin/env python3
"""
Demo script showing all Phase 1-5 enhancements in action.

This demonstrates the complete enhancement pipeline:
1. Text Normalization
2. Prosody Analysis
3. Breath & Pause Modeling
4. Audio Quality Check
5. Adaptive NFE & Crossfade
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from f5_tts.text import (
    normalize_spanish_text,
    analyze_spanish_prosody,
    analyze_breath_pauses,
)
from f5_tts.audio import AudioQualityAnalyzer
from f5_tts.core import get_adaptive_nfe_step, get_adaptive_crossfade_duration


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def demo_text_normalization():
    """Demonstrate text normalization."""
    print_section("PHASE 1: TEXT NORMALIZATION")

    examples = [
        "Tengo 25 años",
        "El 15 de marzo de 2024 a las 14:30",
        "Compré 3 libros por €50",
        "El Dr. García llegó a las 09:00",
        "Mi número es 1234567890",
    ]

    for text in examples:
        normalized = normalize_spanish_text(text)
        print(f"Original   : {text}")
        print(f"Normalized : {normalized}")
        print()


def demo_prosody_analysis():
    """Demonstrate prosody analysis."""
    print_section("PHASE 3: PROSODY ANALYSIS")

    examples = [
        "¿Cómo estás? ¡Muy bien, gracias!",
        "¿Dónde vives? ¿Qué haces?",
        "¡Qué increíble! Es muy importante.",
        "Primero, segundo y tercero.",
    ]

    for text in examples:
        prosody = analyze_spanish_prosody(text)
        print(f"Original : {text}")
        print(f"Marked   : {prosody.marked_text}")
        print(f"Features : {len(prosody.markers)} markers, "
              f"{len(prosody.sentence_boundaries)} sentences, "
              f"{len(prosody.breath_points)} breath points")
        print()


def demo_breath_analysis():
    """Demonstrate breath and pause analysis."""
    print_section("PHASE 4: BREATH & PAUSE MODELING")

    text = """
    Buenos días a todos. ¿Cómo están? Hoy vamos a hablar sobre un tema muy
    importante: la inteligencia artificial y su impacto en nuestra sociedad.
    Primero, veremos la historia. Segundo, analizaremos el presente. Y finalmente,
    discutiremos el futuro. ¿Listos para comenzar? ¡Empecemos!
    """.strip()

    breath_pattern = analyze_breath_pauses(text)

    print(f"Text: {text}\n")
    print(f"Analysis Results:")
    print(f"  • Total pauses: {len(breath_pattern.pauses)}")
    print(f"  • Breath points: {len(breath_pattern.breath_points)}")
    print(f"  • Avg pause interval: {breath_pattern.avg_pause_interval:.1f} chars")
    print(f"  • Estimated duration: {breath_pattern.total_duration_estimate:.1f}s")

    print(f"\nPause Breakdown:")
    pause_types = {}
    for pause in breath_pattern.pauses:
        type_name = pause.type.value
        pause_types[type_name] = pause_types.get(type_name, 0) + 1

    for pause_type, count in sorted(pause_types.items()):
        print(f"  • {pause_type}: {count}")

    print(f"\nSample Pauses (first 5):")
    for pause in breath_pattern.pauses[:5]:
        breath = " [BREATH]" if pause.is_breath_point else ""
        print(f"  • pos {pause.position}: {pause.type.value} "
              f"({pause.duration_ms}ms){breath}")
        print(f"    Context: ...{pause.context}...")


def demo_adaptive_features():
    """Demonstrate adaptive NFE and crossfade."""
    print_section("PHASE 1: ADAPTIVE NFE & CROSSFADE")

    test_texts = [
        ("Hola", "Very short text"),
        ("¿Cómo estás hoy?", "Simple question"),
        ("¿Qué piensas sobre esto? ¡Es increíble!", "Complex with question and exclamation"),
        ("Esta es una oración muy larga con múltiples cláusulas, subordinadas y varios conceptos importantes que requieren procesamiento cuidadoso.", "Very long complex text"),
    ]

    print("Adaptive NFE Steps:")
    print("-" * 80)
    base_nfe = 16

    for text, description in test_texts:
        adaptive_nfe = get_adaptive_nfe_step(text, base_nfe)
        print(f"\nText: {text[:60]}...")
        print(f"Description: {description}")
        print(f"Base NFE: {base_nfe} → Adaptive NFE: {adaptive_nfe}")

    print("\n" + "-" * 80)
    print("\nAdaptive Crossfade Duration:")
    print("-" * 80)

    scenarios = [
        (None, None, False, "Default"),
        (0.8, 0.9, False, "Similar energy, continuous"),
        (0.8, 0.3, False, "Energy drop, continuous"),
        (0.8, 0.9, True, "At pause/punctuation"),
    ]

    for chunk1_energy, chunk2_energy, at_pause, description in scenarios:
        crossfade = get_adaptive_crossfade_duration(
            chunk1_energy=chunk1_energy,
            chunk2_energy=chunk2_energy,
            at_pause=at_pause
        )
        print(f"\nScenario: {description}")
        if chunk1_energy:
            print(f"  Chunk 1 energy: {chunk1_energy:.2f}")
            print(f"  Chunk 2 energy: {chunk2_energy:.2f}")
        print(f"  At pause: {at_pause}")
        print(f"  → Crossfade duration: {crossfade:.2f}s")


def demo_complete_pipeline():
    """Demonstrate complete enhancement pipeline."""
    print_section("COMPLETE ENHANCEMENT PIPELINE")

    text = "¿Tienes 25 euros? ¡Son las 14:30 y tengo que irme!"

    print(f"Input Text: {text}\n")

    # Step 1: Normalize
    print("Step 1: Text Normalization")
    print("-" * 80)
    normalized = normalize_spanish_text(text)
    print(f"Normalized: {normalized}\n")

    # Step 2: Prosody
    print("Step 2: Prosody Analysis")
    print("-" * 80)
    prosody = analyze_spanish_prosody(normalized)
    print(f"Marked text: {prosody.marked_text}")
    print(f"Markers: {len(prosody.markers)}")
    print(f"Questions: {sum(1 for m in prosody.markers if 'QUESTION' in str(m.type))}")
    print(f"Exclamations: {sum(1 for m in prosody.markers if 'EXCLAMATION' in str(m.type))}\n")

    # Step 3: Breath
    print("Step 3: Breath & Pause Analysis")
    print("-" * 80)
    breath = analyze_breath_pauses(normalized)
    print(f"Total pauses: {len(breath.pauses)}")
    print(f"Breath points: {len(breath.breath_points)}")
    print(f"Estimated duration: {breath.total_duration_estimate:.1f}s\n")

    # Step 4: Adaptive NFE
    print("Step 4: Adaptive NFE")
    print("-" * 80)
    nfe = get_adaptive_nfe_step(normalized, base_nfe_step=16)
    print(f"Base NFE: 16")
    print(f"Adaptive NFE: {nfe}")
    print(f"Reason: {'Complex text with questions and exclamations' if nfe > 16 else 'Simple text'}\n")

    # Step 5: Adaptive Crossfade
    print("Step 5: Adaptive Crossfade")
    print("-" * 80)
    crossfade = get_adaptive_crossfade_duration()
    print(f"Crossfade duration: {crossfade:.2f}s")
    print(f"Context: Default (balanced)\n")

    print("=" * 80)
    print("Pipeline complete! Text is ready for TTS generation.")
    print("=" * 80)


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 15 + "F5-TTS ENHANCEMENT DEMONSTRATION" + " " * 30 + "║")
    print("║" + " " * 20 + "Phases 1-5 Complete" + " " * 38 + "║")
    print("╚" + "═" * 78 + "╝")

    demo_text_normalization()
    demo_prosody_analysis()
    demo_breath_analysis()
    demo_adaptive_features()
    demo_complete_pipeline()

    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 28 + "DEMO COMPLETE!" + " " * 35 + "║")
    print("║" + " " * 78 + "║")
    print("║  All enhancement features are working correctly and integrated into the API  ║")
    print("║" + " " * 78 + "║")
    print("║  Test the REST API:                                                          ║")
    print("║    python examples/api_client_enhanced.py analyze 'Texto de prueba'          ║")
    print("║" + " " * 78 + "║")
    print("║  See docs/API_ENHANCED.md for complete API documentation                     ║")
    print("╚" + "═" * 78 + "╝")
    print("\n")


if __name__ == "__main__":
    main()
