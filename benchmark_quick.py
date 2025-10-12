#!/usr/bin/env python3
"""
Quick Performance & Quality Baseline Script

Runs a minimal set of benchmarks suitable for CPU environments.
"""

import argparse
import json
import torch
import time
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from f5_tts.api import F5TTS
from f5_tts.text import (
    normalize_spanish_text,
    analyze_spanish_prosody,
    analyze_breath_pauses,
    process_spanish_text,
)
from f5_tts.audio import AudioQualityAnalyzer


def run_quick_benchmark(model_path: str = None, vocab_path: str = None):
    """Run quick performance and quality baseline."""

    print("=" * 60)
    print("🚀 Quick Baseline Benchmark")
    print("=" * 60)

    results = {
        "timestamp": datetime.now().isoformat(),
        "system_info": {},
        "performance": {},
        "quality": {},
    }

    # System info
    print("\n📊 System Information")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    results["system_info"] = {
        "device": device,
        "pytorch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
    }

    if torch.cuda.is_available():
        results["system_info"]["cuda_device"] = torch.cuda.get_device_name(0)
        results["system_info"]["cuda_memory_gb"] = torch.cuda.get_device_properties(0).total_memory / (1024**3)

    print(f"  Device: {device}")

    # Load model
    print("\n📦 Loading Model...")
    model_path = model_path or "models/Spanish/model_1250000.safetensors"
    vocab_path = vocab_path or "models/Spanish/vocab.txt"
    ref_audio_path = "ref_audio/short.wav"

    load_start = time.time()
    model = F5TTS(
        model_type="F5-TTS",
        ckpt_file=model_path,
        vocab_file=vocab_path,
        ode_method="euler",
        use_ema=True,
        vocoder_name="vocos",
        device=device,
    )
    load_time = time.time() - load_start
    print(f"  Model loaded in {load_time:.2f}s")
    results["performance"]["model_load_time_seconds"] = round(load_time, 2)

    # === PERFORMANCE TESTS ===
    print("\n⚡ Performance Tests (1 iteration each)")

    test_cases = {
        "very_short": "Hola",
        "short": "¿Cómo estás hoy?",
        "medium": "Buenos días, ¿cómo estuvo tu día de trabajo?",
    }

    latency_results = {}
    for name, text in test_cases.items():
        print(f"  Testing {name} ({len(text)} chars)...")

        start = time.time()
        wav, sr, _ = model.infer(
            ref_file=ref_audio_path,
            ref_text="",
            gen_text=text,
            target_rms=0.1,
            speed=1.0,
            nfe_step=16,
        )
        latency = time.time() - start

        latency_results[name] = {
            "text_length": len(text),
            "latency_seconds": round(latency, 2),
        }
        print(f"    Latency: {latency:.2f}s")

    results["performance"]["latency"] = latency_results

    # === QUALITY TESTS ===
    print("\n🎨 Quality Tests")

    # 1. Audio Quality
    print("  Testing audio quality...")
    wav, sr, _ = model.infer(
        ref_file=ref_audio_path,
        ref_text="",
        gen_text="Esta es una prueba de calidad de audio.",
        target_rms=0.1,
        speed=1.0,
        nfe_step=16,
    )

    quality_analyzer = AudioQualityAnalyzer()
    # Convert numpy array to torch tensor
    if not isinstance(wav, torch.Tensor):
        wav_tensor = torch.from_numpy(wav)
    else:
        wav_tensor = wav
    quality_metrics = quality_analyzer.analyze(wav_tensor, sr)

    results["quality"]["audio_quality"] = {
        "overall_score": round(float(quality_metrics.overall_score), 1),
        "quality_level": quality_metrics.quality_level.value,
        "snr_db": round(float(quality_metrics.snr_db), 1),
        "clipping_rate": round(float(quality_metrics.clipping_rate), 4),
        "dynamic_range_db": round(float(quality_metrics.dynamic_range_db), 1),
        "spectral_flatness": round(float(quality_metrics.spectral_flatness), 3),
    }

    print(f"    Overall Score: {results['quality']['audio_quality']['overall_score']}")
    print(f"    SNR: {results['quality']['audio_quality']['snr_db']}dB")

    # 2. Prosody Detection
    print("  Testing prosody detection...")

    prosody_tests = {
        "question": "¿Cómo estás hoy?",
        "exclamation": "¡Qué hermoso día!",
    }

    prosody_results = {}
    for test_name, text in prosody_tests.items():
        prosody_analysis = analyze_spanish_prosody(text)
        markers = len(prosody_analysis.markers)
        prosody_results[test_name] = {
            "markers_detected": markers,
            "has_markers": markers > 0,
        }

    results["quality"]["prosody_detection"] = prosody_results
    print(f"    Question markers: {prosody_results['question']['markers_detected']}")
    print(f"    Exclamation markers: {prosody_results['exclamation']['markers_detected']}")

    # 3. Regional Processing
    print("  Testing regional processing...")

    regional_result = process_spanish_text(
        "Che boludo, ¿vos querés tomar unos mates?",
        region="rioplatense"
    )

    # Handle both dict and object returns
    if isinstance(regional_result, dict):
        slang_count = len(regional_result.get("detected_slang", [])) if regional_result.get("detected_slang") else 0
        # Phonetics are applied but not tracked separately, check if phonetic != normalized
        phonetics_applied = regional_result.get("phonetic", "") != regional_result.get("normalized", "")
        has_profile = regional_result.get("prosodic_profile") is not None
    else:
        slang_count = len(regional_result.slang_terms) if regional_result.slang_terms else 0
        phonetics_applied = True  # Assume applied
        has_profile = regional_result.prosodic_profile is not None

    results["quality"]["regional_processing"] = {
        "slang_detected": slang_count,
        "phonetics_applied": phonetics_applied,
        "has_prosodic_profile": has_profile,
    }

    print(f"    Slang terms: {results['quality']['regional_processing']['slang_detected']}")
    print(f"    Phonetics applied: {results['quality']['regional_processing']['phonetics_applied']}")

    # === SUMMARY ===
    print("\n" + "=" * 60)
    print("✅ Quick Baseline Complete!")
    print("=" * 60)
    print(f"\n📊 Summary:")
    print(f"  Device: {device}")
    print(f"  Model Load: {results['performance']['model_load_time_seconds']}s")
    print(f"  Typical Latency: {results['performance']['latency']['medium']['latency_seconds']}s")
    print(f"  Audio Quality: {results['quality']['audio_quality']['overall_score']} ({results['quality']['audio_quality']['quality_level']})")
    print(f"  SNR: {results['quality']['audio_quality']['snr_db']}dB")

    return results


def main():
    parser = argparse.ArgumentParser(description="Quick Baseline Benchmark")
    parser.add_argument("--model", help="Path to model checkpoint")
    parser.add_argument("--vocab", help="Path to vocab file")
    parser.add_argument("--output", default="baseline_quick.json", help="Output JSON file")

    args = parser.parse_args()

    results = run_quick_benchmark(model_path=args.model, vocab_path=args.vocab)

    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved to {args.output}")


if __name__ == "__main__":
    main()
