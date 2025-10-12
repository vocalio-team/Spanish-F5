#!/usr/bin/env python3
"""
Quality Benchmarking Script for Spanish-F5 TTS

Measures:
- Audio quality metrics (SNR, spectral quality)
- Prosody accuracy (question detection, emphasis, pauses)
- Regional accent fidelity
- Naturalness scores

Usage:
    python benchmark_quality.py --output baseline_quality.json
    python benchmark_quality.py --compare baseline_quality.json
"""

import argparse
import json
import torch
import torchaudio
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
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


class QualityBenchmark:
    """Quality benchmarking suite for TTS system."""

    def __init__(self, model_path: str = None, vocab_path: str = None):
        """Initialize benchmark with model."""
        print("🎨 Initializing Quality Benchmark...")

        self.model_path = model_path or "models/Spanish/model_1250000.safetensors"
        self.vocab_path = vocab_path or "models/Spanish/vocab.txt"
        self.ref_audio_path = "ref_audio/short.wav"

        # Test texts for different quality aspects
        self.test_cases = {
            "question": {
                "text": "¿Cómo estás hoy?",
                "expected_prosody": "rising_intonation",
            },
            "exclamation": {
                "text": "¡Qué hermoso día hace hoy!",
                "expected_prosody": "emphatic",
            },
            "statement": {
                "text": "El cielo está completamente despejado.",
                "expected_prosody": "neutral_falling",
            },
            "rioplatense": {
                "text": "Che boludo, ¿vos querés ir a tomar unos mates conmigo?",
                "region": "rioplatense",
                "expected_features": ["sheísmo", "voseo", "che"],
            },
            "colombian": {
                "text": "¿Qué más pues? ¿Todo bien o qué?",
                "region": "colombian",
                "expected_features": ["question_tags", "clear_articulation"],
            },
            "mexican": {
                "text": "Ahorita regreso, dame un momentito por favor.",
                "region": "mexican",
                "expected_features": ["diminutives", "ahorita"],
            },
        }

        # Results storage
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "audio_quality": {},
            "prosody_accuracy": {},
            "regional_accuracy": {},
        }

        # Load model
        print(f"📦 Loading model from {self.model_path}...")
        self.model = self._load_model()
        print("✅ Model loaded")

        # Initialize quality analyzer
        self.quality_analyzer = AudioQualityAnalyzer()

    def _load_model(self):
        """Load F5-TTS model."""
        device = "cuda" if torch.cuda.is_available() else "cpu"

        model = F5TTS(
            model_type="F5-TTS",
            ckpt_file=self.model_path,
            vocab_file=self.vocab_path,
            ode_method="euler",
            use_ema=True,
            vocoder_name="vocos",
            device=device,
        )

        return model

    def _generate_audio(self, text: str, region: str = None) -> Tuple[torch.Tensor, int]:
        """Generate audio for given text."""
        # Process with regional settings if specified
        if region:
            processed_result = process_spanish_text(text, region=region)
            processed_text = processed_result.processed_text
        else:
            processed_text = normalize_spanish_text(text)

        # Generate audio
        wav, sr, _ = self.model.infer(
            ref_file=self.ref_audio_path,
            ref_text="",
            gen_text=processed_text,
            target_rms=0.1,
            speed=1.0,
            nfe_step=16,
        )

        return wav, sr

    def benchmark_audio_quality(self) -> Dict:
        """
        Measure audio quality metrics for generated speech.

        Returns:
            Dictionary with audio quality metrics
        """
        print("\n🔊 Benchmarking Audio Quality...")

        quality_results = {}

        for test_name, test_case in self.test_cases.items():
            print(f"  Testing: {test_name}")

            # Generate audio
            wav, sr = self._generate_audio(
                test_case["text"],
                region=test_case.get("region")
            )

            # Analyze quality
            quality_metrics = self.quality_analyzer.analyze(wav, sr)

            quality_results[test_name] = {
                "overall_score": float(quality_metrics.overall_score),
                "quality_level": quality_metrics.quality_level.value,
                "snr_db": float(quality_metrics.snr_db),
                "clipping_rate": float(quality_metrics.clipping_rate),
                "silence_ratio": float(quality_metrics.silence_ratio),
                "dynamic_range_db": float(quality_metrics.dynamic_range_db),
                "spectral_flatness": float(quality_metrics.spectral_flatness),
                "issues_count": len(quality_metrics.issues),
            }

            print(f"    Overall: {quality_results[test_name]['overall_score']:.1f} "
                  f"({quality_results[test_name]['quality_level']}) "
                  f"SNR: {quality_results[test_name]['snr_db']:.1f}dB")

        # Calculate averages
        avg_score = np.mean([r["overall_score"] for r in quality_results.values()])
        avg_snr = np.mean([r["snr_db"] for r in quality_results.values()])

        quality_results["_summary"] = {
            "avg_overall_score": float(avg_score),
            "avg_snr_db": float(avg_snr),
        }

        print(f"\n  📊 Average Overall Score: {avg_score:.1f}")
        print(f"  📊 Average SNR: {avg_snr:.1f}dB")

        self.results["audio_quality"] = quality_results
        return quality_results

    def benchmark_prosody_accuracy(self) -> Dict:
        """
        Measure prosody detection and application accuracy.

        Returns:
            Dictionary with prosody accuracy metrics
        """
        print("\n🎭 Benchmarking Prosody Accuracy...")

        prosody_results = {}

        # Test question detection
        print("  Testing question intonation...")
        question_text = self.test_cases["question"]["text"]
        prosody_analysis = analyze_spanish_prosody(question_text)

        question_markers = sum(1 for m in prosody_analysis.markers if "QUESTION" in str(m.type))
        prosody_results["question_detection"] = {
            "text": question_text,
            "markers_detected": question_markers,
            "has_question_marker": question_markers > 0,
        }
        print(f"    Question markers detected: {question_markers}")

        # Test exclamation detection
        print("  Testing exclamation...")
        exclamation_text = self.test_cases["exclamation"]["text"]
        prosody_analysis = analyze_spanish_prosody(exclamation_text)

        exclamation_markers = sum(1 for m in prosody_analysis.markers if "EXCLAMATION" in str(m.type))
        prosody_results["exclamation_detection"] = {
            "text": exclamation_text,
            "markers_detected": exclamation_markers,
            "has_exclamation_marker": exclamation_markers > 0,
        }
        print(f"    Exclamation markers detected: {exclamation_markers}")

        # Test breath pause detection
        print("  Testing breath pause detection...")
        long_text = "Este es un texto largo con varias oraciones. Cada oración tiene su propia entonación. Las pausas son importantes para la naturalidad del habla."
        breath_analysis = analyze_breath_pauses(long_text)

        prosody_results["breath_pause_detection"] = {
            "text_length": len(long_text),
            "total_pauses": len(breath_analysis.pauses),
            "breath_points": len(breath_analysis.breath_points),
            "avg_pause_interval": float(breath_analysis.avg_pause_interval),
        }
        print(f"    Pauses detected: {len(breath_analysis.pauses)}, Breath points: {len(breath_analysis.breath_points)}")

        # Test stress detection
        print("  Testing stress/emphasis detection...")
        emphasis_text = "Esto es REALMENTE importante y ABSOLUTAMENTE necesario"
        prosody_analysis = analyze_spanish_prosody(emphasis_text)

        stress_markers = sum(1 for m in prosody_analysis.markers if "STRESS" in str(m.type))
        prosody_results["stress_detection"] = {
            "text": emphasis_text,
            "stress_markers_detected": stress_markers,
        }
        print(f"    Stress markers detected: {stress_markers}")

        # Calculate prosody accuracy score
        accuracy_score = 0.0
        if prosody_results["question_detection"]["has_question_marker"]:
            accuracy_score += 25.0
        if prosody_results["exclamation_detection"]["has_exclamation_marker"]:
            accuracy_score += 25.0
        if prosody_results["breath_pause_detection"]["total_pauses"] > 0:
            accuracy_score += 25.0
        if prosody_results["stress_detection"]["stress_markers_detected"] > 0:
            accuracy_score += 25.0

        prosody_results["_summary"] = {
            "accuracy_score": accuracy_score,
            "max_score": 100.0,
        }

        print(f"\n  📊 Prosody Accuracy Score: {accuracy_score}/100")

        self.results["prosody_accuracy"] = prosody_results
        return prosody_results

    def benchmark_regional_accuracy(self) -> Dict:
        """
        Measure regional accent detection and application accuracy.

        Returns:
            Dictionary with regional accuracy metrics
        """
        print("\n🌎 Benchmarking Regional Accent Accuracy...")

        regional_results = {}

        for region_name, test_case in [(k, v) for k, v in self.test_cases.items() if "region" in v]:
            print(f"  Testing: {region_name}")

            text = test_case["text"]
            region = test_case["region"]
            expected_features = test_case["expected_features"]

            # Process with regional settings
            result = process_spanish_text(text, region=region)

            # Check detected features
            detected_features = []

            # Check phonetic transformations
            if result.phonetic_transformations:
                detected_features.extend(result.phonetic_transformations)

            # Check slang terms
            if result.slang_terms:
                for term in result.slang_terms:
                    detected_features.append(term["term"])

            # Check prosodic profile
            if result.prosodic_profile:
                detected_features.append(f"pace_{result.prosodic_profile.pace_multiplier}")

            regional_results[region_name] = {
                "region": region,
                "text": text,
                "expected_features": expected_features,
                "detected_features": detected_features,
                "prosodic_profile": result.prosodic_profile.name if result.prosodic_profile else None,
                "slang_count": len(result.slang_terms) if result.slang_terms else 0,
                "phonetic_count": len(result.phonetic_transformations) if result.phonetic_transformations else 0,
            }

            print(f"    Slang detected: {regional_results[region_name]['slang_count']}")
            print(f"    Phonetic features: {regional_results[region_name]['phonetic_count']}")

        # Calculate regional accuracy
        total_regions = len(regional_results)
        regions_with_features = sum(1 for r in regional_results.values() if r["slang_count"] > 0 or r["phonetic_count"] > 0)
        regional_accuracy = (regions_with_features / total_regions * 100) if total_regions > 0 else 0

        regional_results["_summary"] = {
            "total_regions_tested": total_regions,
            "regions_with_features": regions_with_features,
            "accuracy_percentage": float(regional_accuracy),
        }

        print(f"\n  📊 Regional Accuracy: {regional_accuracy:.1f}% ({regions_with_features}/{total_regions} regions)")

        self.results["regional_accuracy"] = regional_results
        return regional_results

    def run_full_benchmark(self) -> Dict:
        """Run all quality benchmarks and return results."""
        print("\n" + "="*60)
        print("🎯 Running Full Quality Benchmark")
        print("="*60)

        self.benchmark_audio_quality()
        self.benchmark_prosody_accuracy()
        self.benchmark_regional_accuracy()

        print("\n" + "="*60)
        print("✅ Quality Benchmark Complete!")
        print("="*60)

        return self.results

    def save_results(self, output_path: str):
        """Save benchmark results to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Results saved to {output_path}")

    def compare_with_baseline(self, baseline_path: str):
        """Compare current results with baseline."""
        with open(baseline_path, 'r') as f:
            baseline = json.load(f)

        print("\n" + "="*60)
        print("📊 Quality Comparison with Baseline")
        print("="*60)

        # Compare audio quality
        print("\n🔊 Audio Quality Comparison:")
        if "_summary" in self.results["audio_quality"] and "_summary" in baseline["audio_quality"]:
            current_score = self.results["audio_quality"]["_summary"]["avg_overall_score"]
            base_score = baseline["audio_quality"]["_summary"]["avg_overall_score"]
            diff = current_score - base_score

            symbol = "🟢" if diff > 1.0 else ("🔴" if diff < -1.0 else "🟡")
            print(f"  Overall {symbol} {current_score:.1f} vs {base_score:.1f} ({diff:+.1f})")

            current_snr = self.results["audio_quality"]["_summary"]["avg_snr_db"]
            base_snr = baseline["audio_quality"]["_summary"]["avg_snr_db"]
            diff_snr = current_snr - base_snr

            symbol = "🟢" if diff_snr > 1.0 else ("🔴" if diff_snr < -1.0 else "🟡")
            print(f"  SNR     {symbol} {current_snr:.1f}dB vs {base_snr:.1f}dB ({diff_snr:+.1f}dB)")

        # Compare prosody accuracy
        print("\n🎭 Prosody Accuracy Comparison:")
        if "_summary" in self.results["prosody_accuracy"] and "_summary" in baseline["prosody_accuracy"]:
            current_accuracy = self.results["prosody_accuracy"]["_summary"]["accuracy_score"]
            base_accuracy = baseline["prosody_accuracy"]["_summary"]["accuracy_score"]
            diff = current_accuracy - base_accuracy

            symbol = "🟢" if diff > 5.0 else ("🔴" if diff < -5.0 else "🟡")
            print(f"  {symbol} {current_accuracy:.0f}/100 vs {base_accuracy:.0f}/100 ({diff:+.0f})")

        # Compare regional accuracy
        print("\n🌎 Regional Accuracy Comparison:")
        if "_summary" in self.results["regional_accuracy"] and "_summary" in baseline["regional_accuracy"]:
            current_regional = self.results["regional_accuracy"]["_summary"]["accuracy_percentage"]
            base_regional = baseline["regional_accuracy"]["_summary"]["accuracy_percentage"]
            diff = current_regional - base_regional

            symbol = "🟢" if diff > 5.0 else ("🔴" if diff < -5.0 else "🟡")
            print(f"  {symbol} {current_regional:.1f}% vs {base_regional:.1f}% ({diff:+.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="Benchmark Spanish-F5 TTS Quality")
    parser.add_argument("--model", help="Path to model checkpoint")
    parser.add_argument("--vocab", help="Path to vocab file")
    parser.add_argument("--output", default="quality_baseline.json", help="Output JSON file")
    parser.add_argument("--compare", help="Compare with baseline JSON file")

    args = parser.parse_args()

    # Run benchmark
    benchmark = QualityBenchmark(model_path=args.model, vocab_path=args.vocab)
    results = benchmark.run_full_benchmark()

    # Save results
    benchmark.save_results(args.output)

    # Compare if baseline provided
    if args.compare:
        benchmark.compare_with_baseline(args.compare)


if __name__ == "__main__":
    main()
