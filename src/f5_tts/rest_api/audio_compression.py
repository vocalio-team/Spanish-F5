"""
Audio compression utilities for bandwidth-efficient API responses.

Supports multiple compression formats optimized for voice:
- OPUS/OGG: Best quality-to-size ratio for voice (default)
- MP3: Wide compatibility
- WAV: Uncompressed (original)
"""

import os
import logging
from typing import Tuple, Optional
from pathlib import Path

import torch
import torchaudio
from pydub import AudioSegment

logger = logging.getLogger(__name__)


class AudioCompressor:
    """Handles audio compression for API responses."""

    # Compression format configurations
    FORMATS = {
        "opus": {
            "extension": "ogg",
            "mime_type": "audio/ogg; codecs=opus",
            "codec": "libopus",
            "bitrate": "32k",  # Excellent for voice, ~4KB/s
            "description": "OPUS codec in OGG container (best for voice, lowest bandwidth)",
        },
        "mp3": {
            "extension": "mp3",
            "mime_type": "audio/mpeg",
            "codec": "libmp3lame",
            "bitrate": "64k",  # Good quality for voice, ~8KB/s
            "description": "MP3 format (good compatibility)",
        },
        "wav": {
            "extension": "wav",
            "mime_type": "audio/wav",
            "codec": None,  # No compression
            "bitrate": None,
            "description": "Uncompressed WAV (highest bandwidth)",
        },
    }

    def __init__(self, default_format: str = "opus"):
        """
        Initialize audio compressor.

        Args:
            default_format: Default compression format (opus, mp3, wav)
        """
        self.default_format = default_format
        if default_format not in self.FORMATS:
            raise ValueError(
                f"Invalid format: {default_format}. Must be one of {list(self.FORMATS.keys())}"
            )

    def compress(
        self,
        wav_path: str,
        output_format: str = None,
        bitrate: str = None,
        delete_source: bool = True,
    ) -> Tuple[str, str, int]:
        """
        Compress audio file to specified format.

        Args:
            wav_path: Path to input WAV file
            output_format: Output format (opus, mp3, wav)
            bitrate: Custom bitrate (e.g., "32k", "64k")
            delete_source: Delete source WAV after compression

        Returns:
            Tuple of (output_path, mime_type, file_size_bytes)

        Raises:
            ValueError: If format is invalid
            RuntimeError: If compression fails
        """
        format_key = output_format or self.default_format

        if format_key not in self.FORMATS:
            raise ValueError(
                f"Invalid format: {format_key}. Must be one of {list(self.FORMATS.keys())}"
            )

        format_config = self.FORMATS[format_key]

        # For WAV, just return original (or copy if needed)
        if format_key == "wav":
            file_size = os.path.getsize(wav_path)
            return wav_path, format_config["mime_type"], file_size

        # Generate output path
        wav_path_obj = Path(wav_path)
        output_path = str(wav_path_obj.with_suffix(f".{format_config['extension']}"))

        try:
            # Load WAV with pydub
            audio = AudioSegment.from_wav(wav_path)

            # Apply compression
            effective_bitrate = bitrate or format_config["bitrate"]

            logger.info(
                f"Compressing {wav_path} to {format_key} "
                f"(bitrate={effective_bitrate}, codec={format_config.get('codec', 'default')})"
            )

            # Export with compression
            if format_key == "opus":
                audio.export(
                    output_path,
                    format="ogg",
                    codec="libopus",
                    bitrate=effective_bitrate,
                    parameters=["-vbr", "on"],  # Variable bitrate for better quality
                )
            elif format_key == "mp3":
                audio.export(output_path, format="mp3", bitrate=effective_bitrate)

            # Get compressed file size
            file_size = os.path.getsize(output_path)
            original_size = os.path.getsize(wav_path)
            compression_ratio = (1 - file_size / original_size) * 100

            logger.info(
                f"Compression complete: {original_size} bytes -> {file_size} bytes "
                f"({compression_ratio:.1f}% reduction)"
            )

            # Delete source WAV if requested
            if delete_source:
                os.remove(wav_path)
                logger.debug(f"Deleted source WAV: {wav_path}")

            return output_path, format_config["mime_type"], file_size

        except Exception as e:
            logger.error(f"Compression failed for {wav_path}: {e}")
            # If compression fails, return original WAV
            file_size = os.path.getsize(wav_path)
            return wav_path, "audio/wav", file_size

    def get_format_info(self, format_key: str = None) -> dict:
        """
        Get information about a compression format.

        Args:
            format_key: Format to query (defaults to default_format)

        Returns:
            Dictionary with format configuration
        """
        key = format_key or self.default_format
        if key not in self.FORMATS:
            raise ValueError(f"Invalid format: {key}")
        return self.FORMATS[key].copy()

    @classmethod
    def list_formats(cls) -> dict:
        """List all available compression formats."""
        return {
            key: {"mime_type": config["mime_type"], "description": config["description"]}
            for key, config in cls.FORMATS.items()
        }

    def estimate_size(
        self, duration_seconds: float, format_key: str = None, bitrate: str = None
    ) -> int:
        """
        Estimate compressed file size.

        Args:
            duration_seconds: Audio duration in seconds
            format_key: Compression format
            bitrate: Bitrate (if None, uses format default)

        Returns:
            Estimated file size in bytes
        """
        key = format_key or self.default_format
        if key not in self.FORMATS:
            raise ValueError(f"Invalid format: {key}")

        config = self.FORMATS[key]

        if key == "wav":
            # WAV: 24kHz * 16-bit * 1 channel = 48000 bytes/sec
            return int(duration_seconds * 48000)

        # Compressed formats
        effective_bitrate = bitrate or config["bitrate"]
        bitrate_kbps = int(effective_bitrate.rstrip("k"))
        bytes_per_second = (bitrate_kbps * 1024) // 8

        return int(duration_seconds * bytes_per_second)


# Global compressor instance
audio_compressor = AudioCompressor(default_format="opus")
