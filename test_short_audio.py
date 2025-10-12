#!/usr/bin/env python3
"""Test short audio generation to debug chopping issue."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from f5_tts.api import F5TTS
import torchaudio

# Test cases: very short texts that should generate audible speech
test_cases = [
    "Hola",
    "Sí",
    "No",
    "Adiós",
    "Bien",
    "Gracias",
    "Por favor",
]

def test_short_audio_generation():
    """Test generation of short audio clips."""
    print("Initializing F5TTS...")
    tts = F5TTS(model_type="F5-TTS")

    # Use a simple reference
    ref_text = "Hola, ¿cómo estás hoy?"
    ref_file = "ref_audio/spanish_ref_6s.wav"  # Use existing ref audio

    for i, text in enumerate(test_cases):
        print(f"\n{'='*60}")
        print(f"Test {i+1}/{len(test_cases)}: '{text}' ({len(text)} chars)")
        print(f"{'='*60}")

        try:
            # Generate without fix_duration (default behavior)
            print("Generating WITHOUT fix_duration...")
            wav1, sr1, _ = tts.infer(
                ref_file=ref_file,
                ref_text=ref_text,
                gen_text=text,
                speed=0.7,  # Slower for short text
            )

            duration1 = len(wav1) / sr1
            print(f"  Result: {duration1:.3f}s ({len(wav1)} samples)")

            # Save to file
            output_file1 = f"test_output_short_{i+1}_no_fix.wav"
            torchaudio.save(output_file1, wav1.unsqueeze(0), sr1)
            print(f"  Saved to: {output_file1}")

            # Generate WITH fix_duration
            print("Generating WITH fix_duration=8.0s...")
            wav2, sr2, _ = tts.infer(
                ref_file=ref_file,
                ref_text=ref_text,
                gen_text=text,
                speed=0.7,
                fix_duration=8.0,
            )

            duration2 = len(wav2) / sr2
            print(f"  Result: {duration2:.3f}s ({len(wav2)} samples)")

            # Save to file
            output_file2 = f"test_output_short_{i+1}_with_fix.wav"
            torchaudio.save(wav2.unsqueeze(0), wav2.unsqueeze(0), sr2)
            print(f"  Saved to: {output_file2}")

            # Analysis
            if duration1 < 0.5:
                print(f"  ⚠️  WARNING: Audio too short without fix_duration ({duration1:.3f}s)")
            if duration2 < 1.0:
                print(f"  ⚠️  WARNING: Audio too short even WITH fix_duration ({duration2:.3f}s)")

        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*60}")
    print("Test completed! Check the generated files.")
    print(f"{'='*60}")

if __name__ == "__main__":
    test_short_audio_generation()
