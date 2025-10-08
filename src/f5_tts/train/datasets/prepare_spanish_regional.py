"""Dataset preparation script for regional Spanish audio with accent/prosody annotations.

This script processes Spanish audio datasets and adds regional metadata for:
- Regional accent (Rioplatense, Colombian, Mexican, etc.)
- Prosodic features (intonation patterns, stress)
- Slang/modismos detection
"""

import os
import sys
import json
from concurrent.futures import ProcessPoolExecutor
from importlib.resources import files
from tqdm import tqdm
from typing import Dict, List, Optional

import torchaudio
from datasets import Dataset

# Add parent directory to path for imports
sys.path.append(os.getcwd())

from f5_tts.text.spanish_regional import (
    SpanishRegion,
    get_regional_processor,
    RegionalSlang,
)


def process_audio_file(
    audio_path: str,
    text: str,
    region: Optional[str] = None,
    auto_detect: bool = True,
) -> Dict[str, any]:
    """
    Process a single audio file with regional Spanish processing.

    Args:
        audio_path: Path to audio file
        text: Transcription text
        region: Forced region (if None, will auto-detect)
        auto_detect: Whether to auto-detect region from text

    Returns:
        Dictionary with audio info and regional metadata
    """
    # Load audio to get duration
    audio, sample_rate = torchaudio.load(audio_path)
    duration = audio.shape[-1] / sample_rate

    # Determine region
    if region is None and auto_detect:
        detected_region = RegionalSlang.detect_region_from_text(text)
        region = detected_region.value if detected_region else "neutral"
    elif region is None:
        region = "neutral"

    # Process text with regional processor
    processor = get_regional_processor(region=region, auto_detect=False)
    processed = processor.process(text, apply_phonetics=True)

    return {
        "audio_path": audio_path,
        "text": text,
        "duration": duration,
        "region": region,
        "normalized_text": processed["normalized"],
        "phonetic_text": processed["phonetic"],
        "prosodic_hints": processed["prosodic_hints"],
        "detected_slang": processed["detected_slang"],
    }


def prepare_dataset_from_csv(
    csv_path: str,
    audio_base_dir: str,
    dataset_name: str,
    region_column: Optional[str] = None,
    auto_detect_region: bool = True,
    max_workers: int = 8,
) -> None:
    """
    Prepare regional Spanish dataset from CSV file.

    CSV should have columns: audio_path, text, [region]

    Args:
        csv_path: Path to CSV file with audio paths and transcriptions
        audio_base_dir: Base directory for audio files
        dataset_name: Name for the dataset
        region_column: Name of column with region info (optional)
        auto_detect_region: Whether to auto-detect region from text
        max_workers: Number of parallel workers
    """
    import pandas as pd

    print(f"Loading dataset from {csv_path}...")
    df = pd.read_csv(csv_path)

    # Validate required columns
    if "text" not in df.columns or "audio_path" not in df.columns:
        raise ValueError("CSV must have 'audio_path' and 'text' columns")

    audio_path_list = []
    text_list = []
    duration_list = []
    region_list = []
    normalized_text_list = []
    phonetic_text_list = []
    prosodic_hints_list = []
    slang_list = []

    # Process files
    futures = []
    executor = ProcessPoolExecutor(max_workers=max_workers)

    for idx, row in df.iterrows():
        audio_path = os.path.join(audio_base_dir, row["audio_path"])
        text = row["text"]
        region = row.get(region_column) if region_column else None

        futures.append(
            executor.submit(
                process_audio_file,
                audio_path,
                text,
                region,
                auto_detect_region,
            )
        )

    # Collect results
    for future in tqdm(futures, desc="Processing audio files"):
        result = future.result()

        audio_path_list.append(result["audio_path"])
        text_list.append(result["text"])
        duration_list.append(result["duration"])
        region_list.append(result["region"])
        normalized_text_list.append(result["normalized_text"])
        phonetic_text_list.append(result["phonetic_text"])
        prosodic_hints_list.append(result["prosodic_hints"])
        slang_list.append(result["detected_slang"])

    executor.shutdown()

    # Create save directory
    save_dir = str(files("f5_tts").joinpath("../../")) + f"/data/{dataset_name}"
    os.makedirs(save_dir, exist_ok=True)

    print(f"\nSaving to {save_dir}...")

    # Create dataset
    dataset_dict = {
        "audio_path": audio_path_list,
        "text": text_list,
        "duration": duration_list,
        "region": region_list,
        "normalized_text": normalized_text_list,
        "phonetic_text": phonetic_text_list,
        "prosodic_hints": prosodic_hints_list,
        "detected_slang": slang_list,
    }

    dataset = Dataset.from_dict(dataset_dict)
    dataset.save_to_disk(f"{save_dir}/raw", max_shard_size="2GB")

    # Save metadata
    with open(f"{save_dir}/duration.json", "w", encoding="utf-8") as f:
        json.dump({"duration": duration_list}, f, ensure_ascii=False)

    # Save regional statistics
    region_stats = {}
    for region in set(region_list):
        count = region_list.count(region)
        total_duration = sum(d for d, r in zip(duration_list, region_list) if r == region)
        region_stats[region] = {
            "count": count,
            "total_duration_hours": total_duration / 3600,
            "percentage": (count / len(region_list)) * 100,
        }

    with open(f"{save_dir}/regional_stats.json", "w", encoding="utf-8") as f:
        json.dump(region_stats, f, ensure_ascii=False, indent=2)

    # Print statistics
    print(f"\n{'='*60}")
    print(f"Dataset: {dataset_name}")
    print(f"Total samples: {len(text_list)}")
    print(f"Total duration: {sum(duration_list)/3600:.2f} hours")
    print(f"\nRegional distribution:")
    for region, stats in region_stats.items():
        print(f"  {region:15s}: {stats['count']:6d} samples ({stats['percentage']:5.2f}%) - {stats['total_duration_hours']:.2f} hours")
    print(f"{'='*60}\n")


def prepare_dataset_from_directory(
    audio_dir: str,
    transcription_dir: str,
    dataset_name: str,
    region: Optional[str] = None,
    auto_detect_region: bool = True,
    max_workers: int = 8,
) -> None:
    """
    Prepare regional Spanish dataset from directory structure.

    Expected structure:
    audio_dir/
        file1.wav
        file2.wav
    transcription_dir/
        file1.txt
        file2.txt

    Args:
        audio_dir: Directory with audio files
        transcription_dir: Directory with transcription files
        dataset_name: Name for the dataset
        region: Force specific region (if None, will auto-detect)
        auto_detect_region: Whether to auto-detect region
        max_workers: Number of parallel workers
    """
    print(f"Loading dataset from {audio_dir}...")

    audio_files = sorted([f for f in os.listdir(audio_dir) if f.endswith(('.wav', '.mp3', '.flac'))])

    audio_path_list = []
    text_list = []
    duration_list = []
    region_list = []
    normalized_text_list = []
    phonetic_text_list = []
    prosodic_hints_list = []
    slang_list = []

    futures = []
    executor = ProcessPoolExecutor(max_workers=max_workers)

    for audio_file in audio_files:
        # Find corresponding transcription
        base_name = os.path.splitext(audio_file)[0]
        trans_file = os.path.join(transcription_dir, f"{base_name}.txt")

        if not os.path.exists(trans_file):
            print(f"Warning: No transcription found for {audio_file}, skipping...")
            continue

        # Read transcription
        with open(trans_file, "r", encoding="utf-8") as f:
            text = f.read().strip()

        audio_path = os.path.join(audio_dir, audio_file)

        futures.append(
            executor.submit(
                process_audio_file,
                audio_path,
                text,
                region,
                auto_detect_region,
            )
        )

    # Collect results
    for future in tqdm(futures, desc="Processing audio files"):
        result = future.result()

        audio_path_list.append(result["audio_path"])
        text_list.append(result["text"])
        duration_list.append(result["duration"])
        region_list.append(result["region"])
        normalized_text_list.append(result["normalized_text"])
        phonetic_text_list.append(result["phonetic_text"])
        prosodic_hints_list.append(result["prosodic_hints"])
        slang_list.append(result["detected_slang"])

    executor.shutdown()

    # Create save directory
    save_dir = str(files("f5_tts").joinpath("../../")) + f"/data/{dataset_name}"
    os.makedirs(save_dir, exist_ok=True)

    print(f"\nSaving to {save_dir}...")

    # Create dataset (same as CSV version)
    dataset_dict = {
        "audio_path": audio_path_list,
        "text": text_list,
        "duration": duration_list,
        "region": region_list,
        "normalized_text": normalized_text_list,
        "phonetic_text": phonetic_text_list,
        "prosodic_hints": prosodic_hints_list,
        "detected_slang": slang_list,
    }

    dataset = Dataset.from_dict(dataset_dict)
    dataset.save_to_disk(f"{save_dir}/raw", max_shard_size="2GB")

    # Save metadata
    with open(f"{save_dir}/duration.json", "w", encoding="utf-8") as f:
        json.dump({"duration": duration_list}, f, ensure_ascii=False)

    # Save regional statistics
    region_stats = {}
    for region in set(region_list):
        count = region_list.count(region)
        total_duration = sum(d for d, r in zip(duration_list, region_list) if r == region)
        region_stats[region] = {
            "count": count,
            "total_duration_hours": total_duration / 3600,
            "percentage": (count / len(region_list)) * 100,
        }

    with open(f"{save_dir}/regional_stats.json", "w", encoding="utf-8") as f:
        json.dump(region_stats, f, ensure_ascii=False, indent=2)

    # Print statistics
    print(f"\n{'='*60}")
    print(f"Dataset: {dataset_name}")
    print(f"Total samples: {len(text_list)}")
    print(f"Total duration: {sum(duration_list)/3600:.2f} hours")
    print(f"\nRegional distribution:")
    for region, stats in region_stats.items():
        print(f"  {region:15s}: {stats['count']:6d} samples ({stats['percentage']:5.2f}%) - {stats['total_duration_hours']:.2f} hours")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    # Example usage - customize these parameters
    import argparse

    parser = argparse.ArgumentParser(description="Prepare regional Spanish TTS dataset")
    parser.add_argument("--mode", choices=["csv", "directory"], required=True,
                       help="Dataset preparation mode")
    parser.add_argument("--dataset-name", required=True,
                       help="Name for the dataset")
    parser.add_argument("--region", default=None,
                       help="Force specific region (neutral, rioplatense, colombian, mexican)")
    parser.add_argument("--auto-detect", action="store_true",
                       help="Auto-detect region from text")
    parser.add_argument("--max-workers", type=int, default=8,
                       help="Number of parallel workers")

    # CSV mode arguments
    parser.add_argument("--csv-path", help="Path to CSV file (for csv mode)")
    parser.add_argument("--audio-base-dir", help="Base directory for audio files (for csv mode)")
    parser.add_argument("--region-column", help="CSV column with region info (optional)")

    # Directory mode arguments
    parser.add_argument("--audio-dir", help="Directory with audio files (for directory mode)")
    parser.add_argument("--transcription-dir", help="Directory with transcription files (for directory mode)")

    args = parser.parse_args()

    if args.mode == "csv":
        if not args.csv_path or not args.audio_base_dir:
            parser.error("csv mode requires --csv-path and --audio-base-dir")

        prepare_dataset_from_csv(
            csv_path=args.csv_path,
            audio_base_dir=args.audio_base_dir,
            dataset_name=args.dataset_name,
            region_column=args.region_column,
            auto_detect_region=args.auto_detect,
            max_workers=args.max_workers,
        )

    elif args.mode == "directory":
        if not args.audio_dir or not args.transcription_dir:
            parser.error("directory mode requires --audio-dir and --transcription-dir")

        prepare_dataset_from_directory(
            audio_dir=args.audio_dir,
            transcription_dir=args.transcription_dir,
            dataset_name=args.dataset_name,
            region=args.region,
            auto_detect_region=args.auto_detect,
            max_workers=args.max_workers,
        )

    print("\n✓ Dataset preparation complete!")
