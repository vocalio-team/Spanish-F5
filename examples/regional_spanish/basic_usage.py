"""Basic usage examples for regional Spanish TTS."""

from f5_tts.text import (
    get_regional_processor,
    process_spanish_text,
    SpanishRegion,
)


def example1_quick_processing():
    """Example 1: Quick text processing with different regions."""
    print("=" * 60)
    print("Example 1: Quick Processing")
    print("=" * 60)

    texts = {
        "rioplatense": "¿Che, vos sabés dónde está el laburo?",
        "colombian": "Parcero, eso está muy bacano, ¿cierto?",
        "mexican": "Órale güey, eso está muy chido",
    }

    for region, text in texts.items():
        print(f"\n{region.upper()}:")
        result = process_spanish_text(text, region=region)

        print(f"  Original:   {result['original']}")
        print(f"  Normalized: {result['normalized']}")
        print(f"  Phonetic:   {result['phonetic']}")
        print(f"  Slang:      {[s['term'] for s in result['detected_slang']]}")


def example2_auto_detection():
    """Example 2: Auto-detect region from text."""
    print("\n" + "=" * 60)
    print("Example 2: Auto-Detection")
    print("=" * 60)

    texts = [
        "Che boludo, ¿vos querés tomar unos mates?",
        "Parce, vamos a hacer una vaca para las polas",
        "¿Qué onda güey? No manches, está muy padre",
    ]

    for text in texts:
        result = process_spanish_text(text, auto_detect=True)
        print(f"\nText: {text}")
        print(f"Detected region: {result['region']}")
        print(f"Slang found: {len(result['detected_slang'])} terms")


def example3_detailed_processing():
    """Example 3: Detailed processing with prosodic analysis."""
    print("\n" + "=" * 60)
    print("Example 3: Detailed Processing")
    print("=" * 60)

    processor = get_regional_processor(region="rioplatense")

    text = "Che, ¿vos tenés idea de cómo llegar al quilombo ese?"

    result = processor.process(text)

    print(f"\nOriginal text: {result['original']}")
    print(f"Region: {result['region']}")
    print(f"\nNormalized: {result['normalized']}")
    print(f"Phonetic:   {result['phonetic']}")

    print(f"\nProsodic hints ({len(result['prosodic_hints'])}):")
    for hint in result['prosodic_hints']:
        print(f"  - {hint}")

    print(f"\nDetected slang ({len(result['detected_slang'])}):")
    for slang in result['detected_slang']:
        print(f"  - {slang['term']:12s}: {slang['meaning']:30s} [{slang['usage']}]")


def example4_comparison():
    """Example 4: Compare how different regions process the same base text."""
    print("\n" + "=" * 60)
    print("Example 4: Regional Comparison")
    print("=" * 60)

    # Base text with regional variations
    texts = {
        "rioplatense": "¿Vos querés ir al cine?",
        "colombian": "¿Tú quieres ir al cine, cierto?",
        "mexican": "¿Tú quieres ir al cine, ¿verdad?",
    }

    for region, text in texts.items():
        processor = get_regional_processor(region=region)
        result = processor.process(text, apply_phonetics=True)

        print(f"\n{region.upper()}:")
        print(f"  Input:    {text}")
        print(f"  Phonetic: {result['phonetic']}")
        if result['prosodic_hints']:
            print(f"  Prosody:  {', '.join(result['prosodic_hints'])}")


def example5_voseo_handling():
    """Example 5: Rioplatense voseo conjugation recognition."""
    print("\n" + "=" * 60)
    print("Example 5: Voseo Handling (Rioplatense)")
    print("=" * 60)

    processor = get_regional_processor(region="rioplatense")

    voseo_examples = [
        "Vos tenés razón",
        "¿Vos sabés qué hora es?",
        "Vos podés hacerlo",
        "¿Vos querés salir?",
    ]

    print("\nVoseo forms detected:")
    for text in voseo_examples:
        result = processor.process(text)
        slang = result['detected_slang']
        voseo_terms = [s for s in slang if s['type'] in ['pronoun', 'verb']]

        print(f"\n  {text}")
        if voseo_terms:
            print(f"    Voseo forms: {', '.join(s['term'] for s in voseo_terms)}")


def example6_mixed_content():
    """Example 6: Handling mixed regional content."""
    print("\n" + "=" * 60)
    print("Example 6: Mixed Regional Content")
    print("=" * 60)

    # Mixed conversation with auto-detection
    processor = get_regional_processor(auto_detect=True)

    conversation = [
        ("Speaker A", "Che boludo, ¿vos sabés algo de programación?"),
        ("Speaker B", "Sí parce, algo sé. ¿Qué necesitás?"),
        ("Speaker A", "Quiero aprender Python, ¿vos lo conocés?"),
        ("Speaker C", "Órale, yo también quiero aprender. ¿Está chido?"),
    ]

    for speaker, text in conversation:
        result = processor.process(text)
        print(f"\n{speaker}: {text}")
        print(f"  Region: {result['region']}")


if __name__ == "__main__":
    example1_quick_processing()
    example2_auto_detection()
    example3_detailed_processing()
    example4_comparison()
    example5_voseo_handling()
    example6_mixed_content()

    print("\n" + "=" * 60)
    print("✓ All examples completed!")
    print("=" * 60)
