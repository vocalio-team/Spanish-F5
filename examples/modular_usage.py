"""
Example: Using the new modular architecture for TTS generation

This example demonstrates how to use the new modular components
to perform TTS inference with better control and customization.
"""

import sys
sys.path.append('../src')

import numpy as np
import torch
import torchaudio

from f5_tts.core import get_config, InferenceConfig, AudioProcessingConfig
from f5_tts.audio import (
    AudioProcessingPipeline,
    get_crossfader,
    CrossfadeType,
    apply_edge_fades
)
from f5_tts.text import get_chunker


def example_basic_usage():
    """Basic usage of modular components."""
    print("=== Basic Modular Usage ===\n")

    # 1. Configuration
    config = get_config()
    print(f"Cross-fade duration: {config.default_cross_fade_duration}s")
    print(f"Min chunk size: {config.min_chunk_chars} chars\n")

    # 2. Audio processing
    audio_pipeline = AudioProcessingPipeline()

    # Load reference audio
    ref_audio, sr = torchaudio.load("../ref_audio/short.wav")
    print(f"Loaded reference audio: {ref_audio.shape}, {sr}Hz")

    # Prepare for inference
    prepared = audio_pipeline.prepare_reference_audio(
        ref_audio,
        sr,
        target_rms=0.1,
        device="cpu"  # or "cuda"
    )
    print(f"Prepared audio: {prepared.shape}\n")

    # 3. Text chunking
    text = "Esta es una demostración del nuevo sistema modular. " \
           "Permite un mejor control sobre el procesamiento de audio. " \
           "También facilita la extensión y prueba de componentes individuales."

    chunker = get_chunker("sentence")
    chunks = chunker.chunk(text, max_chars=500)
    print(f"Text split into {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks):
        print(f"  {i+1}. {chunk[:50]}...")
    print()


def example_custom_crossfading():
    """Example of using different crossfading strategies."""
    print("=== Crossfading Comparison ===\n")

    # Create sample audio segments
    sr = 24000
    duration = 2.0
    audio1 = np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(sr * duration)))
    audio2 = np.sin(2 * np.pi * 880 * np.linspace(0, duration, int(sr * duration)))

    crossfade_duration = 0.5

    # Try different crossfading algorithms
    strategies = [
        CrossfadeType.EQUAL_POWER,
        CrossfadeType.RAISED_COSINE,
        CrossfadeType.LINEAR,
    ]

    for strategy in strategies:
        crossfader = get_crossfader(strategy)
        result = crossfader.crossfade(audio1, audio2, crossfade_duration, sr)
        print(f"{strategy.value:20} -> {len(result)} samples")

    print()


def example_adaptive_chunking():
    """Example of adaptive text chunking based on reference audio."""
    print("=== Adaptive Chunking ===\n")

    # Simulate reference audio properties
    ref_audio_duration = 6.0  # 6 seconds
    ref_text = "Referencia de audio corta"
    ref_text_length = len(ref_text.encode("utf-8"))

    # Create adaptive chunker
    chunker = get_chunker(
        "adaptive",
        ref_audio_duration=ref_audio_duration,
        ref_text_length=ref_text_length
    )

    # Calculate optimal chunk size
    max_chars = chunker.calculate_max_chars()
    print(f"Calculated optimal max_chars: {max_chars}")

    # Chunk long text
    long_text = " ".join([
        "Esta es una frase de ejemplo." for _ in range(20)
    ])

    chunks = chunker.chunk(long_text)
    print(f"Chunked into {len(chunks)} pieces")
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i+1}: {len(chunk.encode('utf-8'))} bytes")
    print()


def example_audio_processing_pipeline():
    """Example of complete audio processing pipeline."""
    print("=== Audio Processing Pipeline ===\n")

    # Custom configuration
    custom_config = AudioProcessingConfig(
        target_sample_rate=24000,
        resampling_method="kaiser_window",
        remove_dc_offset=True,
        normalize_output=True,
        max_amplitude=0.99
    )

    pipeline = AudioProcessingPipeline(custom_config)

    # Generate test audio with DC offset and clipping
    sr = 48000  # Different sample rate
    duration = 1.0
    audio = np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(sr * duration)))
    audio += 0.1  # Add DC offset
    audio *= 1.5  # Cause clipping

    print(f"Original audio:")
    print(f"  Sample rate: {sr}Hz")
    print(f"  Mean (DC offset): {audio.mean():.4f}")
    print(f"  Max amplitude: {audio.max():.4f}")
    print(f"  Min amplitude: {audio.min():.4f}\n")

    # Process
    audio_tensor = torch.from_numpy(audio).unsqueeze(0).float()
    processed = pipeline.prepare_reference_audio(
        audio_tensor,
        sr,
        target_rms=0.1,
        device="cpu"
    )

    processed_np = processed.squeeze().numpy()

    # Convert back to numpy for final processing
    final = pipeline.finalize_output_audio(processed_np)

    print(f"Processed audio:")
    print(f"  Sample rate: {custom_config.target_sample_rate}Hz (resampled)")
    print(f"  Mean (DC offset): {final.mean():.4f}")
    print(f"  Max amplitude: {final.max():.4f}")
    print(f"  Min amplitude: {final.min():.4f}\n")


def example_edge_fading():
    """Example of applying edge fades to prevent clicks."""
    print("=== Edge Fading ===\n")

    sr = 24000
    duration = 1.0
    audio = np.ones(int(sr * duration))  # Constant signal

    print(f"Original audio: constant 1.0")
    print(f"  First 5 samples: {audio[:5]}")
    print(f"  Last 5 samples: {audio[-5:]}\n")

    # Apply 5ms edge fades
    faded = apply_edge_fades(audio, fade_duration=0.005, sample_rate=sr)

    print(f"After edge fading (5ms):")
    print(f"  First 5 samples: {faded[:5]}")
    print(f"  Last 5 samples: {faded[-5:]}\n")


def example_combining_chunks():
    """Example of processing and combining multiple chunks."""
    print("=== Combining Multiple Chunks ===\n")

    # Simulate generated audio chunks
    sr = 24000
    chunk_duration = 2.0
    n_chunks = 3

    chunks = []
    for i in range(n_chunks):
        # Different frequency for each chunk (simulating different content)
        freq = 440 * (i + 1)
        chunk = np.sin(2 * np.pi * freq * np.linspace(0, chunk_duration, int(sr * chunk_duration)))

        # Apply edge fades to each chunk
        chunk = apply_edge_fades(chunk, fade_duration=0.005, sample_rate=sr)
        chunks.append(chunk)

    print(f"Generated {n_chunks} chunks of {chunk_duration}s each")

    # Combine with crossfading
    crossfader = get_crossfader(CrossfadeType.EQUAL_POWER)
    crossfade_duration = 0.5

    combined = chunks[0]
    for i, next_chunk in enumerate(chunks[1:], 1):
        print(f"Crossfading chunk {i} -> {i+1}")
        combined = crossfader.crossfade(
            combined,
            next_chunk,
            duration=crossfade_duration,
            sample_rate=sr
        )

    expected_length = (n_chunks * chunk_duration - (n_chunks - 1) * crossfade_duration) * sr
    print(f"\nFinal audio length: {len(combined)} samples")
    print(f"Expected: ~{int(expected_length)} samples")
    print(f"Duration: {len(combined) / sr:.2f}s\n")


if __name__ == "__main__":
    # Run all examples
    example_basic_usage()
    example_custom_crossfading()
    example_adaptive_chunking()
    example_audio_processing_pipeline()
    example_edge_fading()
    example_combining_chunks()

    print("=" * 50)
    print("All examples completed successfully!")
    print("=" * 50)
