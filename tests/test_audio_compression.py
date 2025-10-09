"""
Tests for audio compression utilities.

Tests the audio compression module for bandwidth-efficient API responses.
"""

import pytest
import os
import tempfile
from pathlib import Path

import torch
import torchaudio
from pydub import AudioSegment

from f5_tts.rest_api.audio_compression import AudioCompressor, audio_compressor


class TestAudioCompressor:
    """Test audio compression functionality."""

    @pytest.fixture
    def sample_wav(self):
        """Create a sample WAV file for testing."""
        # Generate 1 second of 24kHz audio
        sample_rate = 24000
        duration = 1.0
        frequency = 440  # A4 note

        t = torch.linspace(0, duration, int(sample_rate * duration))
        waveform = torch.sin(2 * torch.pi * frequency * t).unsqueeze(0)

        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path = f.name
            torchaudio.save(temp_path, waveform, sample_rate)

        yield temp_path

        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

    def test_initialization(self):
        """Test AudioCompressor initialization."""
        compressor = AudioCompressor(default_format="opus")
        assert compressor.default_format == "opus"

    def test_invalid_format_initialization(self):
        """Test initialization with invalid format."""
        with pytest.raises(ValueError):
            AudioCompressor(default_format="invalid")

    def test_list_formats(self):
        """Test listing available formats."""
        formats = AudioCompressor.list_formats()

        assert "opus" in formats
        assert "mp3" in formats
        assert "wav" in formats

        assert "mime_type" in formats["opus"]
        assert "description" in formats["opus"]

    def test_get_format_info(self):
        """Test getting format information."""
        compressor = AudioCompressor()

        opus_info = compressor.get_format_info("opus")
        assert opus_info["extension"] == "ogg"
        assert opus_info["mime_type"] == "audio/ogg; codecs=opus"
        assert opus_info["bitrate"] == "32k"

    def test_compress_to_opus(self, sample_wav):
        """Test compression to OPUS format."""
        compressor = AudioCompressor()

        output_path, mime_type, file_size = compressor.compress(
            sample_wav,
            output_format="opus",
            delete_source=False
        )

        assert os.path.exists(output_path)
        assert output_path.endswith(".ogg")
        assert mime_type == "audio/ogg; codecs=opus"
        assert file_size > 0

        # Verify file is smaller than original
        original_size = os.path.getsize(sample_wav)
        assert file_size < original_size

        # Cleanup
        os.remove(output_path)

    def test_compress_to_mp3(self, sample_wav):
        """Test compression to MP3 format."""
        compressor = AudioCompressor()

        output_path, mime_type, file_size = compressor.compress(
            sample_wav,
            output_format="mp3",
            delete_source=False
        )

        assert os.path.exists(output_path)
        assert output_path.endswith(".mp3")
        assert mime_type == "audio/mpeg"
        assert file_size > 0

        # Cleanup
        os.remove(output_path)

    def test_wav_passthrough(self, sample_wav):
        """Test WAV format returns original file."""
        compressor = AudioCompressor()

        original_size = os.path.getsize(sample_wav)
        output_path, mime_type, file_size = compressor.compress(
            sample_wav,
            output_format="wav",
            delete_source=False
        )

        assert output_path == sample_wav
        assert mime_type == "audio/wav"
        assert file_size == original_size

    def test_custom_bitrate(self, sample_wav):
        """Test compression with custom bitrate."""
        compressor = AudioCompressor()

        # Compress with higher bitrate
        output_path_high, mime_type, file_size_high = compressor.compress(
            sample_wav,
            output_format="opus",
            bitrate="64k",
            delete_source=False
        )

        # Create a copy for second compression
        import shutil
        sample_wav2 = sample_wav.replace('.wav', '_copy.wav')
        shutil.copy(sample_wav, sample_wav2)

        # Compress with lower bitrate
        output_path_low, mime_type2, file_size_low = compressor.compress(
            sample_wav2,
            output_format="opus",
            bitrate="16k",
            delete_source=True  # This will delete sample_wav2
        )

        # Higher bitrate should produce larger file
        assert file_size_high > file_size_low

        # Cleanup
        if os.path.exists(output_path_high):
            os.remove(output_path_high)
        if os.path.exists(output_path_low):
            os.remove(output_path_low)

    def test_delete_source(self, sample_wav):
        """Test source deletion after compression."""
        compressor = AudioCompressor()

        output_path, mime_type, file_size = compressor.compress(
            sample_wav,
            output_format="opus",
            delete_source=True
        )

        # Source should be deleted
        assert not os.path.exists(sample_wav)
        assert os.path.exists(output_path)

        # Cleanup
        os.remove(output_path)

    def test_estimate_size_opus(self):
        """Test size estimation for OPUS format."""
        compressor = AudioCompressor()

        # 10 seconds at 32kbps = ~40KB
        estimated = compressor.estimate_size(10.0, format_key="opus")

        # Should be around 40,000 bytes (32kbps * 10s / 8)
        assert 35000 < estimated < 45000

    def test_estimate_size_mp3(self):
        """Test size estimation for MP3 format."""
        compressor = AudioCompressor()

        # 10 seconds at 64kbps = ~80KB
        estimated = compressor.estimate_size(10.0, format_key="mp3")

        # Should be around 80,000 bytes (64kbps * 10s / 8)
        assert 75000 < estimated < 85000

    def test_estimate_size_wav(self):
        """Test size estimation for WAV format."""
        compressor = AudioCompressor()

        # 10 seconds at 24kHz * 16-bit = ~480KB
        estimated = compressor.estimate_size(10.0, format_key="wav")

        # Should be around 480,000 bytes
        assert 470000 < estimated < 490000

    def test_global_compressor_instance(self):
        """Test global compressor instance."""
        assert audio_compressor.default_format == "opus"

        formats = audio_compressor.list_formats()
        assert "opus" in formats

    def test_invalid_format_compress(self, sample_wav):
        """Test compression with invalid format."""
        compressor = AudioCompressor()

        with pytest.raises(ValueError):
            compressor.compress(sample_wav, output_format="invalid")

    def test_compression_ratio(self, sample_wav):
        """Test that compression achieves good ratios."""
        compressor = AudioCompressor()

        original_size = os.path.getsize(sample_wav)
        output_path, mime_type, compressed_size = compressor.compress(
            sample_wav,
            output_format="opus",
            delete_source=False
        )

        compression_ratio = (1 - compressed_size / original_size) * 100

        # OPUS should achieve at least 80% compression for voice
        assert compression_ratio > 80

        # Cleanup
        os.remove(output_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
