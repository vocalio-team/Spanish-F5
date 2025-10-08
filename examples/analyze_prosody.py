"""
Example script to analyze Spanish text prosody for TTS.

Usage:
    python examples/analyze_prosody.py "¿Cómo estás?"
    python examples/analyze_prosody.py --file text.txt
    python examples/analyze_prosody.py --interactive
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from f5_tts.text import analyze_spanish_prosody, format_prosody_report, ProsodyType


def analyze_text(text: str, detailed: bool = False):
    """Analyze and display prosody for text."""
    print(f"\nAnalyzing: {text}")
    print("=" * 60)

    analysis = analyze_spanish_prosody(text)

    if detailed:
        # Print full report
        report = format_prosody_report(analysis)
        print(report)
    else:
        # Print summary
        print(f"\nMarked Text:")
        print(f"  {analysis.marked_text}")
        print()

        # Count by type
        type_counts = {}
        for marker in analysis.markers:
            type_name = marker.type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        print(f"Prosody Markers:")
        for type_name, count in sorted(type_counts.items()):
            print(f"  • {type_name}: {count}")

        print()
        print(f"Sentence Boundaries: {len(analysis.sentence_boundaries)}")
        print(f"Breath Points: {len(analysis.breath_points)}")
        print(f"Overall Pattern: {analysis.pitch_contours['overall_pattern']}")

    print("=" * 60)


def analyze_file(file_path: str, detailed: bool = False):
    """Analyze prosody for text from file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read().strip()

    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    print(f"\nAnalyzing file: {file_path}")
    print(f"Found {len(paragraphs)} paragraph(s)")
    print("=" * 60)

    for i, paragraph in enumerate(paragraphs, 1):
        print(f"\nParagraph {i}:")
        analyze_text(paragraph, detailed=detailed)


def interactive_mode():
    """Interactive prosody analysis mode."""
    print("=" * 60)
    print("INTERACTIVE PROSODY ANALYZER")
    print("=" * 60)
    print()
    print("Enter Spanish text to analyze (or 'quit' to exit)")
    print("Commands:")
    print("  - Type text to analyze")
    print("  - 'detail' to toggle detailed output")
    print("  - 'examples' to see example texts")
    print("  - 'quit' to exit")
    print()

    detailed = False

    while True:
        try:
            text = input("\n> ").strip()

            if not text:
                continue

            if text.lower() == 'quit':
                print("¡Adiós!")
                break

            if text.lower() == 'detail':
                detailed = not detailed
                print(f"Detailed mode: {'ON' if detailed else 'OFF'}")
                continue

            if text.lower() == 'examples':
                show_examples()
                continue

            analyze_text(text, detailed=detailed)

        except KeyboardInterrupt:
            print("\n¡Adiós!")
            break
        except Exception as e:
            print(f"Error: {e}")


def show_examples():
    """Show example texts with different prosody patterns."""
    examples = {
        "Yes/No Question (Rising)": "¿Quieres café?",
        "Information Question (Falling)": "¿Dónde está el baño?",
        "Simple Exclamation": "¡Qué hermoso!",
        "Strong Exclamation": "¡Increíble! ¡Fantástico!",
        "Emphasis": "Esto es muy importante.",
        "Complex Statement": "Buenos días, ¿cómo estás? Espero que bien.",
        "With Connectors": "Me gusta, pero es caro. Sin embargo, lo compraré.",
        "Long Sentence": "El análisis de datos reveló patrones interesantes que nos ayudarán."
    }

    print("\n" + "=" * 60)
    print("EXAMPLE TEXTS")
    print("=" * 60)

    for category, example in examples.items():
        print(f"\n{category}:")
        print(f"  '{example}'")
        analysis = analyze_spanish_prosody(example)
        print(f"  → {analysis.marked_text}")

    print("\n" + "=" * 60)


def compare_texts():
    """Compare prosody of similar texts."""
    comparisons = [
        ("Statement", "Vienes mañana."),
        ("Yes/No Question", "¿Vienes mañana?"),
        ("Information Question", "¿Cuándo vienes?"),
    ]

    print("\n" + "=" * 60)
    print("PROSODY COMPARISON")
    print("=" * 60)

    for label, text in comparisons:
        analysis = analyze_spanish_prosody(text)
        print(f"\n{label}:")
        print(f"  Text: {text}")
        print(f"  Marked: {analysis.marked_text}")
        print(f"  Pattern: {analysis.pitch_contours['overall_pattern']}")

        types = [m.type.value for m in analysis.markers]
        if types:
            print(f"  Markers: {', '.join(set(types))}")

    print("\n" + "=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze Spanish text prosody for TTS"
    )
    parser.add_argument(
        'text',
        nargs='?',
        help="Text to analyze (or use --file or --interactive)"
    )
    parser.add_argument(
        '--file', '-f',
        help="Read text from file"
    )
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help="Interactive mode"
    )
    parser.add_argument(
        '--detailed', '-d',
        action='store_true',
        help="Show detailed analysis"
    )
    parser.add_argument(
        '--examples',
        action='store_true',
        help="Show example texts"
    )
    parser.add_argument(
        '--compare',
        action='store_true',
        help="Compare similar texts"
    )

    args = parser.parse_args()

    if args.examples:
        show_examples()
    elif args.compare:
        compare_texts()
    elif args.interactive:
        interactive_mode()
    elif args.file:
        analyze_file(args.file, detailed=args.detailed)
    elif args.text:
        analyze_text(args.text, detailed=args.detailed)
    else:
        parser.print_help()
        print("\nTry:")
        print("  python examples/analyze_prosody.py '¿Cómo estás?'")
        print("  python examples/analyze_prosody.py --examples")
        print("  python examples/analyze_prosody.py --interactive")


if __name__ == "__main__":
    main()
