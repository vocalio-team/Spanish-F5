#!/usr/bin/env python3
"""
Pre-transcribe Reference Audio

This script pre-transcribes reference audio files and saves their transcriptions
as JSON metadata. This eliminates the 7-8s Whisper transcription overhead on
first inference when ref_text is empty.

Usage:
    python scripts/pretranscribe_reference_audio.py
    python scripts/pretranscribe_reference_audio.py --audio ref_audio/short.wav
    python scripts/pretranscribe_reference_audio.py --audio ref_audio/default.wav --output ref_audio/default.json
"""

import argparse
import json
import sys
from pathlib import Path
import logging
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from f5_tts.infer.utils_infer import initialize_asr_pipeline

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def transcribe_audio(audio_path: str, device: str = "cpu") -> dict:
    """
    Transcribe an audio file using Whisper ASR.

    Args:
        audio_path: Path to audio file
        device: Device to use (cpu or cuda)

    Returns:
        Dictionary with transcription and metadata
    """
    import torch
    import torchaudio
    from f5_tts.infer.utils_infer import asr_pipe as global_asr_pipe

    logger.info(f"📝 Transcribing {audio_path}...")

    # Initialize ASR pipeline (modifies global asr_pipe)
    start_init = time.time()
    initialize_asr_pipeline(device=device)
    init_time = time.time() - start_init
    logger.info(f"   ASR pipeline initialized in {init_time:.2f}s")

    # Import the now-initialized global asr_pipe
    from f5_tts.infer import utils_infer
    asr_pipe = utils_infer.asr_pipe

    # Load audio
    audio, sr = torchaudio.load(audio_path)

    # Convert to mono if stereo
    if audio.shape[0] > 1:
        audio = audio.mean(dim=0, keepdim=True)

    # Resample to 16kHz (Whisper expects 16kHz)
    if sr != 16000:
        resampler = torchaudio.transforms.Resample(sr, 16000)
        audio = resampler(audio)
        sr = 16000

    # Convert to numpy for Whisper
    audio_numpy = audio.squeeze().numpy()

    # Transcribe
    start_transcribe = time.time()
    result = asr_pipe(
        audio_numpy,
        chunk_length_s=30,
        batch_size=128,
        generate_kwargs={"task": "transcribe"},
        return_timestamps=False,
    )
    transcribe_time = time.time() - start_transcribe

    transcription = result["text"].strip()
    logger.info(f"   Transcription completed in {transcribe_time:.2f}s")
    logger.info(f"   Text: \"{transcription}\"")

    # Get audio duration
    duration = len(audio_numpy) / sr

    return {
        "transcription": transcription,
        "audio_path": str(Path(audio_path).resolve()),
        "sample_rate": sr,
        "duration_seconds": round(duration, 2),
        "transcription_time_seconds": round(transcribe_time, 2),
        "device": device,
        "model": "openai/whisper-large-v3-turbo",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def save_transcription(transcription_data: dict, output_path: str):
    """
    Save transcription data to JSON file.

    Args:
        transcription_data: Transcription metadata
        output_path: Output JSON file path
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(transcription_data, f, indent=2, ensure_ascii=False)

    logger.info(f"💾 Saved transcription to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Pre-transcribe reference audio files for faster TTS inference"
    )
    parser.add_argument(
        "--audio",
        default="ref_audio/short.wav",
        help="Path to reference audio file (default: ref_audio/short.wav)"
    )
    parser.add_argument(
        "--output",
        help="Output JSON file path (default: same as audio with .json extension)"
    )
    parser.add_argument(
        "--device",
        default="cpu",
        choices=["cpu", "cuda"],
        help="Device to use for transcription (default: cpu)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Transcribe all audio files in ref_audio/ directory"
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("🎙️  Reference Audio Pre-transcription")
    logger.info("=" * 60)
    logger.info("")

    if args.all:
        # Transcribe all audio files in ref_audio/
        ref_audio_dir = Path("ref_audio")
        if not ref_audio_dir.exists():
            logger.error(f"Directory {ref_audio_dir} not found!")
            return 1

        audio_files = list(ref_audio_dir.glob("*.wav"))
        if not audio_files:
            logger.error(f"No .wav files found in {ref_audio_dir}")
            return 1

        logger.info(f"Found {len(audio_files)} audio file(s) to transcribe:")
        for audio_file in audio_files:
            logger.info(f"  - {audio_file}")
        logger.info("")

        for audio_file in audio_files:
            output_path = audio_file.with_suffix('.json')

            # Skip if transcription already exists
            if output_path.exists():
                logger.info(f"⏭️  Skipping {audio_file.name} (transcription already exists)")
                continue

            try:
                transcription_data = transcribe_audio(str(audio_file), device=args.device)
                save_transcription(transcription_data, str(output_path))
                logger.info("")
            except Exception as e:
                logger.error(f"❌ Failed to transcribe {audio_file}: {e}")
                continue

    else:
        # Transcribe single file
        audio_path = Path(args.audio)
        if not audio_path.exists():
            logger.error(f"Audio file not found: {audio_path}")
            return 1

        output_path = args.output or str(audio_path.with_suffix('.json'))

        try:
            transcription_data = transcribe_audio(str(audio_path), device=args.device)
            save_transcription(transcription_data, output_path)
        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}")
            return 1

    logger.info("")
    logger.info("=" * 60)
    logger.info("✅ Pre-transcription Complete!")
    logger.info("=" * 60)
    logger.info("")
    logger.info("📖 Usage in code:")
    logger.info("   # Load pre-transcribed text")
    logger.info("   with open('ref_audio/short.json') as f:")
    logger.info("       ref_text = json.load(f)['transcription']")
    logger.info("")
    logger.info("   # Use in inference (no Whisper overhead!)")
    logger.info("   model.infer(ref_file='ref_audio/short.wav', ref_text=ref_text, ...)")
    logger.info("")

    return 0


if __name__ == "__main__":
    sys.exit(main())
