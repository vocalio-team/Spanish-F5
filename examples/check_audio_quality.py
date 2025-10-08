"""
Example script to check reference audio quality for TTS.

Usage:
    python examples/check_audio_quality.py path/to/audio.wav
    python examples/check_audio_quality.py --check-dir path/to/audio/files/
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from f5_tts.audio import analyze_audio_quality, print_quality_report, QualityLevel


def check_single_file(audio_path: str):
    """Check quality of a single audio file."""
    print(f"\nAnalyzing: {audio_path}")
    print("=" * 60)

    try:
        metrics = analyze_audio_quality(audio_path)
        print_quality_report(metrics)

        # Return True if quality is acceptable
        return metrics.quality_level in [QualityLevel.EXCELLENT, QualityLevel.GOOD, QualityLevel.FAIR]

    except Exception as e:
        print(f"❌ Error analyzing {audio_path}: {e}")
        return False


def check_directory(dir_path: str, extensions=None):
    """Check quality of all audio files in a directory."""
    if extensions is None:
        extensions = ['.wav', '.mp3', '.flac', '.ogg']

    dir_path = Path(dir_path)
    audio_files = []

    for ext in extensions:
        audio_files.extend(dir_path.glob(f'**/*{ext}'))

    if not audio_files:
        print(f"No audio files found in {dir_path}")
        return

    print(f"\nFound {len(audio_files)} audio files")
    print("=" * 60)

    results = {
        'excellent': [],
        'good': [],
        'fair': [],
        'poor': [],
        'unacceptable': [],
        'error': []
    }

    for audio_file in audio_files:
        try:
            metrics = analyze_audio_quality(str(audio_file))
            quality = metrics.quality_level.value
            results[quality].append(audio_file.name)

            # Print summary line
            emoji = {
                'excellent': '🟢',
                'good': '🟢',
                'fair': '🟡',
                'poor': '🟠',
                'unacceptable': '🔴'
            }[quality]

            print(f"{emoji} {audio_file.name:<40} {metrics.overall_score:>5.1f}/100  {quality}")

        except Exception as e:
            print(f"❌ {audio_file.name:<40} ERROR: {e}")
            results['error'].append(audio_file.name)

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"🟢 Excellent: {len(results['excellent'])}")
    print(f"🟢 Good:      {len(results['good'])}")
    print(f"🟡 Fair:      {len(results['fair'])}")
    print(f"🟠 Poor:      {len(results['poor'])}")
    print(f"🔴 Unacceptable: {len(results['unacceptable'])}")
    if results['error']:
        print(f"❌ Errors:    {len(results['error'])}")

    # Recommendations for poor quality files
    poor_files = results['poor'] + results['unacceptable']
    if poor_files:
        print("\n⚠️  FILES NEEDING ATTENTION:")
        for filename in poor_files:
            print(f"  • {filename}")
        print("\nConsider re-recording or improving these files for better TTS quality.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check audio quality for TTS reference audio"
    )
    parser.add_argument(
        'path',
        help="Path to audio file or directory"
    )
    parser.add_argument(
        '--check-dir',
        action='store_true',
        help="Check all audio files in directory"
    )
    parser.add_argument(
        '--extensions',
        nargs='+',
        default=['.wav', '.mp3', '.flac'],
        help="Audio file extensions to check (default: .wav .mp3 .flac)"
    )

    args = parser.parse_args()

    path = Path(args.path)

    if not path.exists():
        print(f"Error: Path '{path}' does not exist")
        sys.exit(1)

    if args.check_dir or path.is_dir():
        check_directory(str(path), args.extensions)
    else:
        acceptable = check_single_file(str(path))
        if not acceptable:
            print("\n⚠️  Warning: Audio quality may be too low for good TTS results")
            sys.exit(1)


if __name__ == "__main__":
    main()
