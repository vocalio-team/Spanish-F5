#!/usr/bin/env python3
"""
Performance Benchmarking Script for Spanish-F5 TTS

Measures:
- Latency (p50, p95, p99) for various text lengths
- Throughput (requests/sec)
- Memory usage (peak, average)
- GPU utilization
- Component-level timing breakdown

Usage:
    python benchmark_performance.py --output baseline_perf.json
    python benchmark_performance.py --compare baseline_perf.json
"""

import argparse
import json
import time
import psutil
import torch
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from f5_tts.api import F5TTS
from f5_tts.text import normalize_spanish_text, analyze_spanish_prosody, analyze_breath_pauses
from f5_tts.rest_api.enhancements import enhancement_processor
from f5_tts.rest_api.tts_processor import tts_processor


class PerformanceBenchmark:
    """Performance benchmarking suite for TTS system."""

    def __init__(self, model_path: str = None, vocab_path: str = None):
        """Initialize benchmark with model."""
        print("🚀 Initializing Performance Benchmark...")

        self.model_path = model_path or "models/Spanish/model_1250000.safetensors"
        self.vocab_path = vocab_path or "models/Spanish/vocab.txt"
        self.ref_audio_path = "ref_audio/short.wav"

        # Test texts of various lengths
        self.test_texts = {
            "very_short": "Hola",
            "short": "Hola, ¿cómo estás?",
            "medium": "Buenos días. ¿Cómo te fue en el trabajo hoy? Espero que todo haya salido bien.",
            "long": (
                "La inteligencia artificial está revolucionando el mundo de la tecnología. "
                "Cada día surgen nuevas aplicaciones que mejoran nuestra vida cotidiana. "
                "Desde asistentes virtuales hasta sistemas de recomendación, la IA está en todas partes. "
                "El futuro promete avances aún más sorprendentes en este campo fascinante."
            ),
        }

        # Results storage
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "system_info": self._get_system_info(),
            "latency": {},
            "throughput": {},
            "memory": {},
            "component_timing": {},
        }

        # Load model
        print(f"📦 Loading model from {self.model_path}...")
        start = time.time()
        self.model = self._load_model()
        load_time = time.time() - start
        print(f"✅ Model loaded in {load_time:.2f}s")
        self.results["model_load_time"] = load_time

    def _get_system_info(self) -> Dict:
        """Get system information."""
        info = {
            "cpu_count": psutil.cpu_count(),
            "memory_gb": psutil.virtual_memory().total / (1024**3),
            "python_version": sys.version,
        }

        if torch.cuda.is_available():
            info["cuda_available"] = True
            info["cuda_device"] = torch.cuda.get_device_name(0)
            info["cuda_memory_gb"] = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        else:
            info["cuda_available"] = False

        return info

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

    def benchmark_latency(self, warmup: int = 3, iterations: int = 10) -> Dict:
        """
        Benchmark end-to-end latency for different text lengths.

        Args:
            warmup: Number of warmup iterations
            iterations: Number of measurement iterations

        Returns:
            Dictionary with latency statistics
        """
        print("\n📊 Benchmarking Latency...")
        latency_results = {}

        for text_type, text in self.test_texts.items():
            print(f"  Testing {text_type} text ({len(text)} chars)...")

            # Warmup
            for _ in range(warmup):
                self.model.infer(
                    ref_file=self.ref_audio_path,
                    ref_text="",
                    gen_text=text,
                    target_rms=0.1,
                    speed=1.0,
                    nfe_step=16,
                )

            # Measure
            latencies = []
            for _ in range(iterations):
                start = time.time()
                self.model.infer(
                    ref_file=self.ref_audio_path,
                    ref_text="",
                    gen_text=text,
                    target_rms=0.1,
                    speed=1.0,
                    nfe_step=16,
                )
                latency = time.time() - start
                latencies.append(latency)

            # Statistics
            latency_results[text_type] = {
                "mean": float(np.mean(latencies)),
                "std": float(np.std(latencies)),
                "p50": float(np.percentile(latencies, 50)),
                "p95": float(np.percentile(latencies, 95)),
                "p99": float(np.percentile(latencies, 99)),
                "min": float(np.min(latencies)),
                "max": float(np.max(latencies)),
                "text_length": len(text),
            }

            print(f"    Mean: {latency_results[text_type]['mean']:.3f}s, "
                  f"P95: {latency_results[text_type]['p95']:.3f}s")

        self.results["latency"] = latency_results
        return latency_results

    def benchmark_component_timing(self, iterations: int = 20) -> Dict:
        """
        Break down timing for each component of the pipeline.

        Args:
            iterations: Number of iterations

        Returns:
            Dictionary with component timing
        """
        print("\n⚙️  Benchmarking Component Timing...")
        text = self.test_texts["medium"]

        # Text preprocessing
        print("  Measuring text preprocessing...")
        preprocess_times = []
        for _ in range(iterations):
            start = time.time()
            normalized = normalize_spanish_text(text)
            prosody = analyze_spanish_prosody(normalized)
            breath = analyze_breath_pauses(normalized)
            preprocess_times.append(time.time() - start)

        # Model inference (isolated)
        print("  Measuring model inference...")
        inference_times = []
        for _ in range(iterations):
            start = time.time()
            self.model.infer(
                ref_file=self.ref_audio_path,
                ref_text="",
                gen_text=text,
                target_rms=0.1,
                speed=1.0,
                nfe_step=16,
            )
            inference_times.append(time.time() - start)

        component_timing = {
            "text_preprocessing": {
                "mean": float(np.mean(preprocess_times)),
                "std": float(np.std(preprocess_times)),
            },
            "model_inference": {
                "mean": float(np.mean(inference_times)),
                "std": float(np.std(inference_times)),
            },
        }

        print(f"    Text preprocessing: {component_timing['text_preprocessing']['mean']*1000:.1f}ms")
        print(f"    Model inference: {component_timing['model_inference']['mean']:.3f}s")

        self.results["component_timing"] = component_timing
        return component_timing

    def benchmark_memory(self) -> Dict:
        """
        Measure memory usage during inference.

        Returns:
            Dictionary with memory statistics
        """
        print("\n💾 Benchmarking Memory Usage...")

        # Get baseline memory
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / (1024**2)  # MB

        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
            baseline_gpu = torch.cuda.memory_allocated() / (1024**2)

        # Run inference and measure peak memory
        text = self.test_texts["long"]
        self.model.infer(
            ref_file=self.ref_audio_path,
            ref_text="",
            gen_text=text,
            target_rms=0.1,
            speed=1.0,
            nfe_step=16,
        )

        peak_memory = process.memory_info().rss / (1024**2)
        memory_usage = peak_memory - baseline_memory

        memory_results = {
            "baseline_mb": float(baseline_memory),
            "peak_mb": float(peak_memory),
            "usage_mb": float(memory_usage),
        }

        if torch.cuda.is_available():
            peak_gpu = torch.cuda.max_memory_allocated() / (1024**2)
            gpu_usage = peak_gpu - baseline_gpu
            memory_results["gpu_baseline_mb"] = float(baseline_gpu)
            memory_results["gpu_peak_mb"] = float(peak_gpu)
            memory_results["gpu_usage_mb"] = float(gpu_usage)
            print(f"  GPU Memory: {gpu_usage:.1f}MB (peak: {peak_gpu:.1f}MB)")

        print(f"  CPU Memory: {memory_usage:.1f}MB (peak: {peak_memory:.1f}MB)")

        self.results["memory"] = memory_results
        return memory_results

    def benchmark_throughput(self, duration: int = 30) -> Dict:
        """
        Measure throughput (requests/second).

        Args:
            duration: Test duration in seconds

        Returns:
            Dictionary with throughput statistics
        """
        print(f"\n🚀 Benchmarking Throughput ({duration}s)...")

        text = self.test_texts["medium"]
        start_time = time.time()
        request_count = 0
        request_times = []

        while time.time() - start_time < duration:
            req_start = time.time()
            self.model.infer(
                ref_file=self.ref_audio_path,
                ref_text="",
                gen_text=text,
                target_rms=0.1,
                speed=1.0,
                nfe_step=16,
            )
            request_times.append(time.time() - req_start)
            request_count += 1

            if request_count % 5 == 0:
                print(f"  Completed {request_count} requests...", end="\r")

        elapsed = time.time() - start_time
        throughput = request_count / elapsed

        throughput_results = {
            "total_requests": request_count,
            "duration_s": float(elapsed),
            "requests_per_sec": float(throughput),
            "avg_request_time": float(np.mean(request_times)),
        }

        print(f"\n  Throughput: {throughput:.2f} req/s ({request_count} requests in {elapsed:.1f}s)")

        self.results["throughput"] = throughput_results
        return throughput_results

    def run_full_benchmark(self) -> Dict:
        """Run all benchmarks and return results."""
        print("\n" + "="*60)
        print("🎯 Running Full Performance Benchmark")
        print("="*60)

        self.benchmark_latency()
        self.benchmark_component_timing()
        self.benchmark_memory()
        self.benchmark_throughput(duration=20)  # Shorter for initial testing

        print("\n" + "="*60)
        print("✅ Benchmark Complete!")
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
        print("📊 Comparison with Baseline")
        print("="*60)

        # Compare latency
        print("\n🕐 Latency Comparison:")
        for text_type in self.test_texts.keys():
            if text_type in self.results["latency"] and text_type in baseline["latency"]:
                current = self.results["latency"][text_type]["mean"]
                base = baseline["latency"][text_type]["mean"]
                diff_pct = ((current - base) / base) * 100

                symbol = "🔴" if diff_pct > 5 else ("🟢" if diff_pct < -5 else "🟡")
                print(f"  {text_type:12} {symbol} {current:.3f}s vs {base:.3f}s ({diff_pct:+.1f}%)")

        # Compare throughput
        print("\n🚀 Throughput Comparison:")
        if "throughput" in self.results and "throughput" in baseline:
            current_tput = self.results["throughput"]["requests_per_sec"]
            base_tput = baseline["throughput"]["requests_per_sec"]
            diff_pct = ((current_tput - base_tput) / base_tput) * 100

            symbol = "🟢" if diff_pct > 5 else ("🔴" if diff_pct < -5 else "🟡")
            print(f"  {symbol} {current_tput:.2f} req/s vs {base_tput:.2f} req/s ({diff_pct:+.1f}%)")

        # Compare memory
        print("\n💾 Memory Comparison:")
        if "memory" in self.results and "memory" in baseline:
            current_mem = self.results["memory"]["usage_mb"]
            base_mem = baseline["memory"]["usage_mb"]
            diff_pct = ((current_mem - base_mem) / base_mem) * 100

            symbol = "🔴" if diff_pct > 5 else ("🟢" if diff_pct < -5 else "🟡")
            print(f"  CPU {symbol} {current_mem:.1f}MB vs {base_mem:.1f}MB ({diff_pct:+.1f}%)")

            if "gpu_usage_mb" in self.results["memory"] and "gpu_usage_mb" in baseline["memory"]:
                current_gpu = self.results["memory"]["gpu_usage_mb"]
                base_gpu = baseline["memory"]["gpu_usage_mb"]
                diff_pct = ((current_gpu - base_gpu) / base_gpu) * 100

                symbol = "🔴" if diff_pct > 5 else ("🟢" if diff_pct < -5 else "🟡")
                print(f"  GPU {symbol} {current_gpu:.1f}MB vs {base_gpu:.1f}MB ({diff_pct:+.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="Benchmark Spanish-F5 TTS Performance")
    parser.add_argument("--model", help="Path to model checkpoint")
    parser.add_argument("--vocab", help="Path to vocab file")
    parser.add_argument("--output", default="performance_baseline.json", help="Output JSON file")
    parser.add_argument("--compare", help="Compare with baseline JSON file")

    args = parser.parse_args()

    # Run benchmark
    benchmark = PerformanceBenchmark(model_path=args.model, vocab_path=args.vocab)
    results = benchmark.run_full_benchmark()

    # Save results
    benchmark.save_results(args.output)

    # Compare if baseline provided
    if args.compare:
        benchmark.compare_with_baseline(args.compare)


if __name__ == "__main__":
    main()
