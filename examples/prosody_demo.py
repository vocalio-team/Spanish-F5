"""Demonstration of empirically-validated prosody features.

Shows:
1. Regional prosodic profiles (Cuello & Oro Ozán, 2024)
2. Discourse-level prosody (Guglielmone et al., 2014)
3. Combined regional + discourse analysis
"""

import sys
sys.path.append("src")

from f5_tts.text.spanish_regional import (
    SpanishRegion,
    RegionalProsody,
    process_spanish_text,
)
from f5_tts.text.discourse_prosody import analyze_discourse_prosody


def demo_regional_profiles():
    """Demonstrate empirical prosodic profiles."""
    print("=" * 80)
    print("REGIONAL PROSODIC PROFILES (Empirically Validated)")
    print("=" * 80)

    regions = [SpanishRegion.RIOPLATENSE, SpanishRegion.COLOMBIAN, SpanishRegion.MEXICAN]

    for region in regions:
        profile = RegionalProsody.get_profile(region)
        print(f"\n{region.value.upper()}:")
        print(f"  Pace: {profile.pace} ({profile.pace_multiplier}x multiplier)")
        print(f"  Reading pace: {profile.reading_pace_multiplier}x")
        print(f"  Stress pattern: {profile.stress_pattern}")
        print(f"  Intonation quality: {profile.intonation_quality}")
        print(f"  F0 range (female): {profile.f0_range_female[0]}-{profile.f0_range_female[1]} Hz")
        print(f"  F0 range (male): {profile.f0_range_male[0]}-{profile.f0_range_male[1]} Hz")
        print(f"  Rhythmic pattern: {profile.rhythmic_pattern}")
        print(f"  Emotional coloring: {profile.emotional_coloring}")


def demo_regional_processing():
    """Demonstrate regional text processing with prosodic profiles."""
    print("\n" + "=" * 80)
    print("REGIONAL TEXT PROCESSING WITH PROSODY")
    print("=" * 80)

    examples = [
        ("Che boludo, ¿vos querés tomar unos mates?", "rioplatense"),
        ("Parce, ¿vamos a tomar unas polas?", "colombian"),
        ("Órale güey, ¿qué onda?", "mexican"),
    ]

    for text, region in examples:
        print(f"\n{region.upper()}: \"{text}\"")
        print("-" * 80)

        result = process_spanish_text(text, region=region)

        print(f"Detected slang: {[s['term'] for s in result['detected_slang']]}")

        if "prosodic_profile" in result:
            profile = result["prosodic_profile"]
            print(f"Prosody:")
            print(f"  - Pace: {profile['pace']} ({profile['pace_multiplier']}x)")
            print(f"  - Stress: {profile['stress_pattern']}")
            print(f"  - Intonation: {profile['intonation_quality']}")
            print(f"  - F0 range (female): {profile['f0_range_female']} Hz")


def demo_discourse_prosody():
    """Demonstrate discourse-level prosody analysis."""
    print("\n" + "=" * 80)
    print("DISCOURSE-LEVEL PROSODY (Guglielmone et al., 2014)")
    print("=" * 80)

    text = "Hola amigo. ¿Cómo estás? Estoy muy bien, gracias por preguntar."

    print(f"\nText: \"{text}\"")
    print("-" * 80)

    result = analyze_discourse_prosody(text, voice_type="female")

    print(f"\nDiscourse structure:")
    print(f"  - Phrases: {len(result['phrases'])}")
    print(f"  - Declination units: {result['declination_units']}")
    print(f"  - F0 range: {result['f0_range']['min']}-{result['f0_range']['max']} Hz")

    print("\nPhrase-by-phrase analysis:")
    for i, phrase in enumerate(result["phrases"], 1):
        nuclear_symbol = phrase["symbol"]
        role = phrase["discourse_role"]
        print(f"  {i}. \"{phrase['text']}\"")
        print(f"     Nuclear tone: {phrase['nuclear_tone']} {nuclear_symbol}")
        print(f"     Discourse role: {role}")
        print(f"     F0 pattern: {phrase['f0_pattern']}")
        print(f"     Processing: {phrase['processing_instruction']}")

    # Show nuclear tone legend
    print("\nNuclear tone legend:")
    print("  ↘ Descending: Assertion/foreground (process now)")
    print("  → Suspensive: Continuation/background (suspend judgment)")
    print("  ↗ Ascending: Given info/background (context reminder)")


def demo_combined_analysis():
    """Demonstrate combined regional + discourse prosody."""
    print("\n" + "=" * 80)
    print("COMBINED REGIONAL + DISCOURSE PROSODY")
    print("=" * 80)

    text = "Che boludo, ¿vos sabés que mañana hay partido? Sí, estoy re contento."

    print(f"\nRioplatense text: \"{text}\"")
    print("-" * 80)

    # Step 1: Regional processing
    regional_result = process_spanish_text(text, region="rioplatense")

    print("\n1. REGIONAL ANALYSIS:")
    print(f"   Region: {regional_result['region']}")
    print(f"   Detected slang: {[s['term'] for s in regional_result['detected_slang']]}")

    if "prosodic_profile" in regional_result:
        profile = regional_result["prosodic_profile"]
        print(f"   Pace: {profile['pace']} ({profile['pace_multiplier']}x)")
        print(f"   Stress: {profile['stress_pattern']}")
        print(f"   Intonation: {profile['intonation_quality']}")
        print(f"   F0 range (female): {profile['f0_range_female']} Hz")

    # Step 2: Discourse processing
    discourse_result = analyze_discourse_prosody(text, voice_type="female")

    print("\n2. DISCOURSE ANALYSIS:")
    print(f"   Phrases: {len(discourse_result['phrases'])}")

    for phrase in discourse_result["phrases"]:
        print(f"   - \"{phrase['text']}\" → {phrase['symbol']} ({phrase['nuclear_tone']})")

    print("\n3. SYNTHESIS PARAMETERS (combined):")
    print(f"   Speech rate: {profile['pace_multiplier']}x (empirical)")
    print(f"   F0 normalization: {profile['f0_range_female']} Hz (empirical)")
    print(f"   Stress pattern: {profile['stress_pattern']} (double accentuation)")
    print(f"   Intonation contours: Based on nuclear tones (↘ → ↗)")
    print(f"   Quality: {profile['intonation_quality']} (plaintive)")


def main():
    """Run all demonstrations."""
    demo_regional_profiles()
    demo_regional_processing()
    demo_discourse_prosody()
    demo_combined_analysis()

    print("\n" + "=" * 80)
    print("All prosody features are based on empirical academic research:")
    print("  - Cuello & Oro Ozán (2024): Rioplatense prosody measurements")
    print("  - Guglielmone et al. (2014): Discourse-level intonation patterns")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
