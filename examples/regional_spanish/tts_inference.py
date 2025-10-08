"""Example TTS inference with regional Spanish support."""

import os
from f5_tts.api import F5TTS
from f5_tts.text import get_regional_processor
from f5_tts.core import get_config, set_config


def setup_regional_config(region: str = "rioplatense"):
    """Setup global configuration for regional Spanish."""
    config = get_config()
    config.spanish_region = region
    config.auto_detect_region = False
    config.apply_regional_phonetics = True
    set_config(config)
    print(f"✓ Configuration set for region: {region}")


def example1_basic_inference():
    """Example 1: Basic inference with regional processing."""
    print("=" * 60)
    print("Example 1: Basic Regional Inference")
    print("=" * 60)

    # Initialize TTS model
    tts = F5TTS(
        model_type="F5-TTS",
        vocoder_name="vocos",
        device="cuda"  # or "cpu"
    )

    # Create regional processor
    processor = get_regional_processor(region="rioplatense")

    # Reference audio (should be from a Rioplatense speaker)
    ref_audio = "path/to/rioplatense_reference.wav"
    ref_text = "Hola, ¿cómo andás?"

    # Text to generate
    gen_text = "Che boludo, ¿vos querés venir a tomar unos mates conmigo?"

    # Process text for regional features
    processed = processor.process(gen_text)

    print(f"\nOriginal text: {gen_text}")
    print(f"Processed text: {processed['phonetic']}")
    print(f"Detected slang: {[s['term'] for s in processed['detected_slang']]}")

    # Generate speech (using phonetic representation)
    print("\nGenerating speech...")
    wav, sr, spect = tts.infer(
        ref_file=ref_audio,
        ref_text=ref_text,
        gen_text=processed['phonetic'],  # Use phonetically-transformed text
        seed=42,
        remove_silence=True
    )

    # Export
    output_file = "output_rioplatense.wav"
    tts.export_wav(wav, output_file)
    print(f"✓ Audio saved to: {output_file}")


def example2_multi_region_inference():
    """Example 2: Generate audio for multiple regions."""
    print("\n" + "=" * 60)
    print("Example 2: Multi-Region Inference")
    print("=" * 60)

    tts = F5TTS(model_type="F5-TTS", vocoder_name="vocos")

    # Different regional variations
    scenarios = [
        {
            "region": "rioplatense",
            "ref_audio": "ref_audio/rioplatense.wav",
            "ref_text": "Hola, ¿cómo estás?",
            "gen_text": "Che, ¿vos sabés dónde queda el subte más cercano?",
            "output": "greeting_rioplatense.wav"
        },
        {
            "region": "colombian",
            "ref_audio": "ref_audio/colombian.wav",
            "ref_text": "Hola, ¿cómo estás?",
            "gen_text": "Parcero, ¿vamos a tomar unas polas?",
            "output": "greeting_colombian.wav"
        },
        {
            "region": "mexican",
            "ref_audio": "ref_audio/mexican.wav",
            "ref_text": "Hola, ¿cómo estás?",
            "gen_text": "Órale güey, ¿vamos a comer unos tacos?",
            "output": "greeting_mexican.wav"
        }
    ]

    for scenario in scenarios:
        print(f"\nProcessing {scenario['region']}...")

        # Create regional processor
        processor = get_regional_processor(region=scenario['region'])

        # Process text
        processed = processor.process(scenario['gen_text'])

        # Generate
        if os.path.exists(scenario['ref_audio']):
            wav, sr, _ = tts.infer(
                ref_file=scenario['ref_audio'],
                ref_text=scenario['ref_text'],
                gen_text=processed['phonetic'],
                seed=42
            )

            tts.export_wav(wav, scenario['output'])
            print(f"  ✓ Saved: {scenario['output']}")
        else:
            print(f"  ⚠ Reference audio not found: {scenario['ref_audio']}")


def example3_auto_detect_inference():
    """Example 3: Auto-detect region and generate."""
    print("\n" + "=" * 60)
    print("Example 3: Auto-Detect and Inference")
    print("=" * 60)

    tts = F5TTS(model_type="F5-TTS", vocoder_name="vocos")

    # Texts with obvious regional markers
    texts = [
        "Che boludo, esto está re bueno",
        "Parce, qué chimba de día",
        "No manches güey, está muy padre"
    ]

    # Reference audios (map detected regions to available refs)
    ref_mapping = {
        "rioplatense": ("ref_audio/rioplatense.wav", "Hola che"),
        "colombian": ("ref_audio/colombian.wav", "Hola parce"),
        "mexican": ("ref_audio/mexican.wav", "Hola güey"),
        "neutral": ("ref_audio/neutral.wav", "Hola")
    }

    for i, text in enumerate(texts):
        # Auto-detect
        processor = get_regional_processor(auto_detect=True)
        processed = processor.process(text)

        region = processed['region']
        print(f"\nText {i+1}: {text}")
        print(f"  Detected: {region}")

        # Get appropriate reference
        if region in ref_mapping:
            ref_audio, ref_text = ref_mapping[region]

            if os.path.exists(ref_audio):
                wav, sr, _ = tts.infer(
                    ref_file=ref_audio,
                    ref_text=ref_text,
                    gen_text=processed['phonetic'],
                    seed=i
                )

                output = f"output_auto_{region}_{i}.wav"
                tts.export_wav(wav, output)
                print(f"  ✓ Generated: {output}")


def example4_long_form_regional():
    """Example 4: Long-form content with regional consistency."""
    print("\n" + "=" * 60)
    print("Example 4: Long-Form Regional Content")
    print("=" * 60)

    tts = F5TTS(model_type="F5-TTS", vocoder_name="vocos")

    # Long text with consistent regional markers
    long_text = """
    Che, la verdad es que el otro día estaba pensando, ¿vos sabés?,
    en todas esas cosas que hacíamos cuando éramos pibes.
    Nos juntábamos en la esquina, charlábamos hasta cualquier hora,
    y después nos íbamos a tomar unos mates a la plaza.
    Era un quilombo bárbaro, pero la pasábamos re bien.
    ¿Te acordás de eso, boludo?
    """

    processor = get_regional_processor(region="rioplatense")
    processed = processor.process(long_text)

    print(f"Region: {processed['region']}")
    print(f"Slang terms found: {len(processed['detected_slang'])}")
    print(f"\nSlang detected:")
    for slang in processed['detected_slang']:
        print(f"  - {slang['term']}: {slang['meaning']}")

    # For long text, you might want to chunk it
    from f5_tts.text import get_chunker

    chunker = get_chunker("sentence")
    chunks = chunker.chunk(processed['phonetic'], max_chars=200)

    print(f"\nSplit into {len(chunks)} chunks for processing")

    # Generate each chunk (in practice, these would be concatenated)
    ref_audio = "ref_audio/rioplatense.wav"
    ref_text = "Hola, ¿cómo andás che?"

    if os.path.exists(ref_audio):
        for i, chunk in enumerate(chunks[:2]):  # Just first 2 for demo
            print(f"\nGenerating chunk {i+1}...")
            wav, sr, _ = tts.infer(
                ref_file=ref_audio,
                ref_text=ref_text,
                gen_text=chunk,
                seed=42
            )

            tts.export_wav(wav, f"output_chunk_{i+1}.wav")


def example5_prosody_emphasis():
    """Example 5: Emphasizing prosodic features."""
    print("\n" + "=" * 60)
    print("Example 5: Prosodic Emphasis")
    print("=" * 60)

    tts = F5TTS(model_type="F5-TTS", vocoder_name="vocos")

    # Texts with strong prosodic markers
    prosodic_texts = {
        "rioplatense": "¡Che! ¿Vos me estás cargando, boludo?",  # Exclamations, questions
        "mexican": "¡Órale! ¿Qué onda güey? ¡Está padísimo!",     # Multiple exclamations
        "colombian": "¿En serio, parce? ¿Sí? ¡Qué chimba!",      # Question tags
    }

    for region, text in prosodic_texts.items():
        processor = get_regional_processor(region=region)
        processed = processor.process(text)

        print(f"\n{region.upper()}:")
        print(f"  Text: {text}")
        print(f"  Prosodic hints: {processed['prosodic_hints']}")

        # In a real scenario, these prosodic hints could be used to
        # adjust inference parameters (speed, emphasis, etc.)


def example6_batch_processing():
    """Example 6: Batch process multiple samples."""
    print("\n" + "=" * 60)
    print("Example 6: Batch Processing")
    print("=" * 60)

    tts = F5TTS(model_type="F5-TTS", vocoder_name="vocos")

    # Batch of samples
    samples = [
        {"region": "rioplatense", "text": "¿Vos querés un café?"},
        {"region": "rioplatense", "text": "Dale, vamos al laburo"},
        {"region": "colombian", "text": "Parce, ¿vamos a almorzar?"},
        {"region": "mexican", "text": "Órale, vamos por unos tacos"},
    ]

    processors = {
        region: get_regional_processor(region=region)
        for region in ["rioplatense", "colombian", "mexican"]
    }

    print(f"\nProcessing {len(samples)} samples...")

    for i, sample in enumerate(samples):
        region = sample['region']
        text = sample['text']

        # Process
        processor = processors[region]
        processed = processor.process(text)

        print(f"\n[{i+1}] {region}: {text}")
        print(f"    → {processed['phonetic']}")

        # In production, you would generate audio here


if __name__ == "__main__":
    print("Regional Spanish TTS Inference Examples")
    print("=" * 60)
    print("\nNOTE: These examples assume you have reference audio files.")
    print("Update the paths to your actual reference audio files.\n")

    # Run examples (comment out as needed)
    # example1_basic_inference()
    # example2_multi_region_inference()
    # example3_auto_detect_inference()
    # example4_long_form_regional()
    example5_prosody_emphasis()
    example6_batch_processing()

    print("\n" + "=" * 60)
    print("✓ Examples completed!")
    print("=" * 60)
