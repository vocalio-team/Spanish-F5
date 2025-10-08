#!/usr/bin/env python3
"""
Enhanced F5-TTS API Client - Test all Phase 1-4 improvements

This client demonstrates how to use the enhanced API with:
- Text normalization
- Prosody analysis
- Breath/pause modeling
- Audio quality checks
- Adaptive NFE and crossfade
"""

import requests
import json
import argparse
from pathlib import Path
from typing import Optional


class F5TTSClient:
    """Client for F5-TTS enhanced REST API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize client with API base URL."""
        self.base_url = base_url.rstrip("/")

    def check_health(self) -> dict:
        """Check API health status."""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def analyze_text(
        self,
        text: str,
        normalize: bool = True,
        prosody: bool = True,
        breath_pauses: bool = True
    ) -> dict:
        """
        Analyze text without generating speech.

        Args:
            text: Text to analyze
            normalize: Apply text normalization
            prosody: Analyze prosody
            breath_pauses: Analyze breath and pauses

        Returns:
            Analysis results dictionary
        """
        data = {
            "text": text,
            "normalize_text": normalize,
            "analyze_prosody": prosody,
            "analyze_breath_pauses": breath_pauses
        }

        response = requests.post(
            f"{self.base_url}/analyze",
            json=data
        )
        response.raise_for_status()
        return response.json()

    def check_audio_quality(self, audio_path: str) -> dict:
        """
        Check audio quality without TTS.

        Args:
            audio_path: Path to audio file

        Returns:
            Quality metrics dictionary
        """
        with open(audio_path, "rb") as f:
            files = {"audio_file": f}
            response = requests.post(
                f"{self.base_url}/audio/quality",
                files=files
            )
        response.raise_for_status()
        return response.json()

    def generate_speech(
        self,
        text: str,
        output_path: str,
        model: str = "F5-TTS",
        ref_text: str = "",
        speed: float = 1.0,
        # Enhancement toggles
        normalize_text: bool = True,
        analyze_prosody: bool = True,
        analyze_breath_pauses: bool = True,
        adaptive_nfe: bool = True,
        adaptive_crossfade: bool = True,
        check_audio_quality: bool = True,
        # Advanced settings
        nfe_step: int = 16,
        cross_fade_duration: float = 0.8,
        cfg_strength: float = 2.0,
        seed: int = -1
    ) -> dict:
        """
        Generate speech with all enhancements.

        Args:
            text: Text to synthesize
            output_path: Where to save audio
            model: Model to use (F5-TTS or E2-TTS)
            ref_text: Reference text (empty for auto-transcription)
            speed: Speech speed multiplier
            normalize_text: Apply text normalization
            analyze_prosody: Analyze prosody
            analyze_breath_pauses: Analyze breath/pauses
            adaptive_nfe: Use adaptive NFE steps
            adaptive_crossfade: Use adaptive crossfade
            check_audio_quality: Check reference audio quality
            nfe_step: Base NFE steps (adaptive will adjust)
            cross_fade_duration: Base crossfade duration
            cfg_strength: CFG strength
            seed: Random seed

        Returns:
            Enhancement metadata from response headers
        """
        data = {
            "model": model,
            "ref_text": ref_text,
            "gen_text": text,
            "speed": speed,
            "normalize_text": normalize_text,
            "analyze_prosody": analyze_prosody,
            "analyze_breath_pauses": analyze_breath_pauses,
            "adaptive_nfe": adaptive_nfe,
            "adaptive_crossfade": adaptive_crossfade,
            "check_audio_quality": check_audio_quality,
            "nfe_step": nfe_step,
            "cross_fade_duration": cross_fade_duration,
            "cfg_strength": cfg_strength,
            "seed": seed
        }

        response = requests.post(
            f"{self.base_url}/tts",
            json=data
        )
        response.raise_for_status()

        # Save audio
        with open(output_path, "wb") as f:
            f.write(response.content)

        # Get enhancement metadata from headers
        metadata_str = response.headers.get("X-Enhancement-Metadata", "{}")
        metadata = json.loads(metadata_str)

        return metadata


def print_analysis_results(results: dict):
    """Pretty-print text analysis results."""
    print("\n" + "=" * 70)
    print("TEXT ANALYSIS RESULTS")
    print("=" * 70)

    print(f"\nOriginal text: {results['original_text']}")

    if results.get("normalized_text"):
        print(f"\nNormalized text: {results['normalized_text']}")

    if results.get("prosody_analysis"):
        prosody = results["prosody_analysis"]
        print(f"\nProsody Analysis:")
        print(f"  • Sentences: {prosody['sentence_count']}")
        print(f"  • Breath points: {prosody['breath_points']}")
        print(f"  • Stress points: {prosody['stress_points']}")
        print(f"\n  Marked text:\n  {prosody['marked_text']}")

    if results.get("breath_analysis"):
        breath = results["breath_analysis"]
        print(f"\nBreath & Pause Analysis:")
        print(f"  • Total pauses: {breath['total_pauses']}")
        print(f"  • Breath points: {len(breath['breath_points'])}")
        print(f"  • Avg pause interval: {breath['avg_pause_interval']:.1f} chars")
        print(f"  • Estimated duration: {breath['estimated_duration']:.1f}s")

    print("\n" + "=" * 70)


def print_quality_results(results: dict):
    """Pretty-print audio quality results."""
    print("\n" + "=" * 70)
    print("AUDIO QUALITY RESULTS")
    print("=" * 70)

    print(f"\nFile: {results['filename']}")
    print(f"Overall Score: {results['overall_score']}/100")
    print(f"Quality Level: {results['quality_level']}")

    print(f"\nMetrics:")
    metrics = results['metrics']
    print(f"  • SNR: {metrics['snr_db']:.1f} dB")
    print(f"  • Clipping Rate: {metrics['clipping_rate']:.3f}")
    print(f"  • Silence Ratio: {metrics['silence_ratio']:.3f}")
    print(f"  • Dynamic Range: {metrics['dynamic_range_db']:.1f} dB")
    print(f"  • Spectral Flatness: {metrics['spectral_flatness']:.3f}")

    if results['issues']:
        print(f"\nIssues:")
        for issue in results['issues']:
            print(f"  ⚠ {issue}")

    if results['recommendations']:
        print(f"\nRecommendations:")
        for rec in results['recommendations']:
            print(f"  ➤ {rec}")

    print("\n" + "=" * 70)


def print_enhancement_metadata(metadata: dict):
    """Pretty-print enhancement metadata."""
    print("\n" + "=" * 70)
    print("ENHANCEMENT METADATA")
    print("=" * 70)

    if metadata.get("normalized_text"):
        print(f"\nNormalized text: {metadata['normalized_text'][:100]}...")

    if metadata.get("prosody_analysis"):
        p = metadata["prosody_analysis"]
        print(f"\nProsody: {p['num_questions']} questions, {p['num_exclamations']} exclamations, {p['num_pauses']} pauses")

    if metadata.get("breath_analysis"):
        b = metadata["breath_analysis"]
        print(f"Breath: {b['total_pauses']} pauses, {b['breath_points']} breath points, ~{b['estimated_duration']:.1f}s")

    if metadata.get("audio_quality"):
        q = metadata["audio_quality"]
        print(f"Audio Quality: {q['overall_score']}/100 ({q['quality_level']})")

    if metadata.get("nfe_step_used"):
        print(f"NFE Steps: {metadata['nfe_step_used']}")

    if metadata.get("crossfade_duration_used"):
        print(f"Crossfade: {metadata['crossfade_duration_used']:.2f}s")

    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Enhanced F5-TTS API Client - Test all improvements"
    )

    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Health check
    subparsers.add_parser("health", help="Check API health")

    # Text analysis
    analyze_parser = subparsers.add_parser("analyze", help="Analyze text")
    analyze_parser.add_argument("text", help="Text to analyze")
    analyze_parser.add_argument("--no-normalize", action="store_true", help="Skip normalization")
    analyze_parser.add_argument("--no-prosody", action="store_true", help="Skip prosody")
    analyze_parser.add_argument("--no-breath", action="store_true", help="Skip breath analysis")

    # Audio quality
    quality_parser = subparsers.add_parser("quality", help="Check audio quality")
    quality_parser.add_argument("audio_file", help="Audio file to check")

    # TTS generation
    tts_parser = subparsers.add_parser("tts", help="Generate speech")
    tts_parser.add_argument("text", help="Text to synthesize")
    tts_parser.add_argument("-o", "--output", default="output.wav", help="Output file")
    tts_parser.add_argument("--model", default="F5-TTS", help="Model to use")
    tts_parser.add_argument("--speed", type=float, default=1.0, help="Speech speed")
    tts_parser.add_argument("--nfe-step", type=int, default=16, help="Base NFE steps")
    tts_parser.add_argument("--no-adaptive-nfe", action="store_true", help="Disable adaptive NFE")
    tts_parser.add_argument("--no-normalize", action="store_true", help="Disable text normalization")
    tts_parser.add_argument("--no-prosody", action="store_true", help="Disable prosody analysis")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    client = F5TTSClient(args.url)

    try:
        if args.command == "health":
            health = client.check_health()
            print(json.dumps(health, indent=2))

        elif args.command == "analyze":
            results = client.analyze_text(
                text=args.text,
                normalize=not args.no_normalize,
                prosody=not args.no_prosody,
                breath_pauses=not args.no_breath
            )
            print_analysis_results(results)

        elif args.command == "quality":
            results = client.check_audio_quality(args.audio_file)
            print_quality_results(results)

        elif args.command == "tts":
            print(f"\nGenerating speech for: {args.text[:80]}...")
            metadata = client.generate_speech(
                text=args.text,
                output_path=args.output,
                model=args.model,
                speed=args.speed,
                nfe_step=args.nfe_step,
                adaptive_nfe=not args.no_adaptive_nfe,
                normalize_text=not args.no_normalize,
                analyze_prosody=not args.no_prosody
            )
            print(f"\n✓ Audio saved to: {args.output}")
            print_enhancement_metadata(metadata)

    except requests.exceptions.RequestException as e:
        print(f"\n✗ API Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        exit(1)


if __name__ == "__main__":
    main()
