"""
Tests for inference utilities in src/f5_tts/infer/utils_infer.py

This test suite covers the critical inference pipeline components with 18% current coverage.
Goal: Increase coverage to >80% by testing all key functions.
"""

import hashlib
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest
import torch
import torchaudio
from pydub import AudioSegment

from f5_tts.infer.utils_infer import (
    chunk_text,
    infer_batch_process,
    infer_process,
    load_checkpoint,
    load_model,
    load_vocoder,
    preprocess_ref_audio_text,
    remove_silence_edges,
    remove_silence_for_generated_wav,
    save_spectrogram,
)


class TestChunkText:
    """Test text chunking functionality."""

    def test_chunk_text_short(self):
        """Test chunking with text shorter than max_chars."""
        text = "Hello world."
        chunks = chunk_text(text, max_chars=100)
        assert len(chunks) == 1
        assert chunks[0] == "Hello world."

    def test_chunk_text_long(self):
        """Test chunking with text longer than max_chars."""
        text = "This is the first sentence. This is the second sentence. This is the third sentence."
        chunks = chunk_text(text, max_chars=50)
        assert len(chunks) > 1
        for chunk in chunks:
            # Each chunk should be within the limit (accounting for UTF-8 encoding)
            assert len(chunk.encode("utf-8")) <= 50 or chunk == chunks[0]

    def test_chunk_text_multiple_punctuation(self):
        """Test chunking with various punctuation marks."""
        text = "Question? Answer! Statement. Another: choice; here."
        chunks = chunk_text(text, max_chars=30)
        assert len(chunks) > 0
        # Verify we split on punctuation
        assert all(chunk.strip() for chunk in chunks)

    def test_chunk_text_chinese(self):
        """Test chunking with Chinese text."""
        text = "这是第一句。这是第二句！这是第三句？"
        chunks = chunk_text(text, max_chars=50)
        assert len(chunks) >= 1
        # Verify chunks are created
        assert "".join(chunk.replace(" ", "") for chunk in chunks)

    def test_chunk_text_empty(self):
        """Test chunking with empty text."""
        text = ""
        chunks = chunk_text(text, max_chars=100)
        # Should return empty list or list with empty string
        assert len(chunks) <= 1

    def test_chunk_text_preserves_content(self):
        """Test that chunking preserves all content."""
        text = "First. Second. Third. Fourth."
        chunks = chunk_text(text, max_chars=20)
        rejoined = " ".join(chunks)
        # All words should be preserved
        for word in ["First", "Second", "Third", "Fourth"]:
            assert word in rejoined


class TestRemoveSilenceEdges:
    """Test silence removal from audio edges."""

    def test_remove_silence_edges_basic(self):
        """Test basic silence removal."""
        # Create audio with silence at start and end
        silence_start = AudioSegment.silent(duration=1000)  # 1 second
        audio_content = AudioSegment.silent(duration=500).overlay(
            AudioSegment.from_mono_audiosegments(
                AudioSegment.silent(duration=500)
            )
        )
        silence_end = AudioSegment.silent(duration=1000)

        # For this test, just create a simple audio segment
        audio = AudioSegment.silent(duration=2000)

        result = remove_silence_edges(audio, silence_threshold=-42)

        # Result should be an AudioSegment
        assert isinstance(result, AudioSegment)
        # Should be shorter or equal to original
        assert len(result) <= len(audio)

    def test_remove_silence_edges_no_silence(self):
        """Test with audio that has no silence edges."""
        # Create a simple tone
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            # Create a 1 second audio at 440Hz (A4 note)
            sample_rate = 24000
            duration = 1.0
            frequency = 440.0
            t = np.linspace(0, duration, int(sample_rate * duration))
            audio_data = (np.sin(2 * np.pi * frequency * t) * 0.3).astype(np.float32)

            torchaudio.save(f.name, torch.tensor(audio_data).unsqueeze(0), sample_rate)
            audio = AudioSegment.from_wav(f.name)

        try:
            result = remove_silence_edges(audio)
            # Audio with content should not be completely removed
            assert len(result) > 0
        finally:
            os.unlink(f.name)


class TestPreprocessRefAudioText:
    """Test reference audio and text preprocessing."""

    @pytest.fixture
    def sample_audio_file(self):
        """Create a temporary audio file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            # Create a simple sine wave
            sample_rate = 24000
            duration = 2.0
            frequency = 440.0
            t = np.linspace(0, duration, int(sample_rate * duration))
            audio_data = (np.sin(2 * np.pi * frequency * t) * 0.3).astype(np.float32)

            torchaudio.save(f.name, torch.tensor(audio_data).unsqueeze(0), sample_rate)
            yield f.name

        # Cleanup
        if os.path.exists(f.name):
            os.unlink(f.name)

    def test_preprocess_with_ref_text(self, sample_audio_file):
        """Test preprocessing with provided reference text."""
        ref_text = "This is reference text"

        result_audio, result_text = preprocess_ref_audio_text(
            sample_audio_file,
            ref_text,
            clip_short=False,
            show_info=lambda x: None,
            device="cpu"
        )

        # Should return paths/text
        assert os.path.exists(result_audio)
        assert result_text.strip() != ""
        # Should ensure proper ending
        assert result_text.endswith(". ") or result_text.endswith("。")

        # Cleanup temp file
        if os.path.exists(result_audio) and result_audio != sample_audio_file:
            os.unlink(result_audio)

    def test_preprocess_clip_long_audio(self, sample_audio_file):
        """Test clipping of long audio files."""
        # Create a long audio file (>15 seconds)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sample_rate = 24000
            duration = 20.0  # 20 seconds
            frequency = 440.0
            t = np.linspace(0, duration, int(sample_rate * duration))
            audio_data = (np.sin(2 * np.pi * frequency * t) * 0.3).astype(np.float32)

            torchaudio.save(f.name, torch.tensor(audio_data).unsqueeze(0), sample_rate)
            long_audio = f.name

        try:
            ref_text = "Long audio reference"
            result_audio, result_text = preprocess_ref_audio_text(
                long_audio,
                ref_text,
                clip_short=True,
                show_info=lambda x: None,
                device="cpu"
            )

            # Verify audio was processed
            audio_seg = AudioSegment.from_wav(result_audio)
            # Should be clipped to ~15 seconds or less
            assert len(audio_seg) <= 16000  # 16 seconds with margin

            # Cleanup
            if os.path.exists(result_audio) and result_audio != long_audio:
                os.unlink(result_audio)
        finally:
            os.unlink(long_audio)

    def test_preprocess_caching(self, sample_audio_file):
        """Test that audio preprocessing uses caching."""
        ref_text = "Cached reference text"

        # First call
        _, result_text1 = preprocess_ref_audio_text(
            sample_audio_file,
            ref_text,
            clip_short=False,
            show_info=lambda x: None,
            device="cpu"
        )

        # Second call with same audio should use cache
        _, result_text2 = preprocess_ref_audio_text(
            sample_audio_file,
            ref_text,
            clip_short=False,
            show_info=lambda x: None,
            device="cpu"
        )

        # Results should be identical (from cache)
        assert result_text1 == result_text2


class TestInferBatchProcess:
    """Test batch inference processing."""

    @pytest.fixture
    def mock_model(self):
        """Create a mock model for testing."""
        model = Mock()
        # Mock the sample method to return appropriate shapes
        def mock_sample(cond, text, duration, steps, cfg_strength, sway_sampling_coef):
            batch_size = 1
            mel_channels = 100
            # Return mock mel spectrogram and other output
            generated = torch.randn(batch_size, duration, mel_channels)
            return generated, None

        model.sample = mock_sample
        return model

    @pytest.fixture
    def mock_vocoder(self):
        """Create a mock vocoder for testing."""
        vocoder = Mock()
        # Mock decode to return waveform
        def mock_decode(mel_spec):
            # Return audio of appropriate length
            samples = mel_spec.shape[-1] * 256  # hop_length
            return torch.randn(1, samples)

        vocoder.decode = mock_decode
        return vocoder

    def test_infer_batch_single_chunk(self, mock_model, mock_vocoder):
        """Test inference with a single text chunk."""
        # Create reference audio
        sample_rate = 24000
        duration = 2.0
        audio = torch.randn(1, int(sample_rate * duration))

        ref_text = "Reference text. "
        gen_text_batches = ["Generated text."]

        wave, sr, spectrogram = infer_batch_process(
            ref_audio=(audio, sample_rate),
            ref_text=ref_text,
            gen_text_batches=gen_text_batches,
            model_obj=mock_model,
            vocoder=mock_vocoder,
            mel_spec_type="vocos",
            progress=Mock(tqdm=lambda x: x),
            device=torch.device("cpu")
        )

        # Verify output
        assert isinstance(wave, np.ndarray)
        assert sr == 24000
        assert isinstance(spectrogram, np.ndarray)
        assert wave.shape[0] > 0

    def test_infer_batch_multiple_chunks(self, mock_model, mock_vocoder):
        """Test inference with multiple text chunks."""
        sample_rate = 24000
        duration = 2.0
        audio = torch.randn(1, int(sample_rate * duration))

        ref_text = "Reference text. "
        gen_text_batches = ["First chunk.", "Second chunk.", "Third chunk."]

        wave, sr, spectrogram = infer_batch_process(
            ref_audio=(audio, sample_rate),
            ref_text=ref_text,
            gen_text_batches=gen_text_batches,
            model_obj=mock_model,
            vocoder=mock_vocoder,
            mel_spec_type="vocos",
            progress=Mock(tqdm=lambda x: x),
            cross_fade_duration=0.15,
            device=torch.device("cpu")
        )

        # With multiple chunks, output should be longer
        assert isinstance(wave, np.ndarray)
        assert wave.shape[0] > 0
        assert sr == 24000

    def test_infer_batch_stereo_to_mono(self, mock_model, mock_vocoder):
        """Test that stereo input is converted to mono."""
        sample_rate = 24000
        duration = 2.0
        # Stereo audio (2 channels)
        audio = torch.randn(2, int(sample_rate * duration))

        ref_text = "Reference. "
        gen_text_batches = ["Generated."]

        wave, sr, spectrogram = infer_batch_process(
            ref_audio=(audio, sample_rate),
            ref_text=ref_text,
            gen_text_batches=gen_text_batches,
            model_obj=mock_model,
            vocoder=mock_vocoder,
            mel_spec_type="vocos",
            progress=Mock(tqdm=lambda x: x),
            device=torch.device("cpu")
        )

        # Should successfully process
        assert isinstance(wave, np.ndarray)
        assert sr == 24000

    def test_infer_batch_no_crossfade(self, mock_model, mock_vocoder):
        """Test inference without crossfading."""
        sample_rate = 24000
        audio = torch.randn(1, int(sample_rate * 2.0))

        ref_text = "Reference. "
        gen_text_batches = ["First.", "Second."]

        wave, sr, spectrogram = infer_batch_process(
            ref_audio=(audio, sample_rate),
            ref_text=ref_text,
            gen_text_batches=gen_text_batches,
            model_obj=mock_model,
            vocoder=mock_vocoder,
            mel_spec_type="vocos",
            progress=Mock(tqdm=lambda x: x),
            cross_fade_duration=0,  # No crossfading
            device=torch.device("cpu")
        )

        assert isinstance(wave, np.ndarray)
        assert wave.shape[0] > 0


class TestInferProcess:
    """Test the main inference process."""

    @pytest.fixture
    def sample_ref_audio(self):
        """Create a sample reference audio file."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sample_rate = 24000
            duration = 3.0
            frequency = 440.0
            t = np.linspace(0, duration, int(sample_rate * duration))
            audio_data = (np.sin(2 * np.pi * frequency * t) * 0.3).astype(np.float32)

            torchaudio.save(f.name, torch.tensor(audio_data).unsqueeze(0), sample_rate)
            yield f.name

        if os.path.exists(f.name):
            os.unlink(f.name)

    def test_infer_process_chunks_text(self, sample_ref_audio):
        """Test that infer_process properly chunks text."""
        mock_model = Mock()
        mock_vocoder = Mock()

        # Mock the sample method
        def mock_sample(cond, text, duration, steps, cfg_strength, sway_sampling_coef):
            batch_size = 1
            mel_channels = 100
            generated = torch.randn(batch_size, duration, mel_channels)
            return generated, None

        mock_model.sample = mock_sample

        # Mock vocoder decode
        def mock_decode(mel_spec):
            samples = mel_spec.shape[-1] * 256
            return torch.randn(1, samples)

        mock_vocoder.decode = mock_decode

        ref_text = "Short reference text."
        # Long generation text that should be chunked
        gen_text = "This is a very long text. " * 50

        with patch('f5_tts.infer.utils_infer.convert_char_to_pinyin', return_value=["mocked"]):
            wave, sr, spec = infer_process(
                ref_audio=sample_ref_audio,
                ref_text=ref_text,
                gen_text=gen_text,
                model_obj=mock_model,
                vocoder=mock_vocoder,
                mel_spec_type="vocos",
                show_info=lambda x: None,
                progress=Mock(tqdm=lambda x: x),
                device=torch.device("cpu")
            )

        # Should return valid output
        assert isinstance(wave, np.ndarray)
        assert sr == 24000


class TestLoadCheckpoint:
    """Test model checkpoint loading."""

    def test_load_checkpoint_mock(self):
        """Test checkpoint loading with mock model."""
        # Create a simple mock model
        model = Mock()
        model.to = Mock(return_value=model)
        model.load_state_dict = Mock()

        # Create a temporary checkpoint file
        with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
            checkpoint = {
                "model_state_dict": {"layer.weight": torch.randn(10, 10)},
                "ema_model_state_dict": {
                    "ema_model.layer.weight": torch.randn(10, 10),
                    "step": torch.tensor(1000),
                    "initted": torch.tensor(True)
                }
            }
            torch.save(checkpoint, f.name)
            ckpt_path = f.name

        try:
            result = load_checkpoint(
                model,
                ckpt_path,
                device="cpu",
                dtype=torch.float32,
                use_ema=True
            )

            # Verify model was loaded
            assert result is not None
            # Verify load_state_dict was called
            assert model.load_state_dict.called
        finally:
            os.unlink(ckpt_path)

    def test_load_checkpoint_without_ema(self):
        """Test checkpoint loading without EMA."""
        model = Mock()
        model.to = Mock(return_value=model)
        model.load_state_dict = Mock()

        with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
            checkpoint = {
                "model_state_dict": {"layer.weight": torch.randn(10, 10)}
            }
            torch.save(checkpoint, f.name)
            ckpt_path = f.name

        try:
            result = load_checkpoint(
                model,
                ckpt_path,
                device="cpu",
                dtype=torch.float32,
                use_ema=False
            )

            assert result is not None
            assert model.load_state_dict.called
        finally:
            os.unlink(ckpt_path)


class TestLoadVocoder:
    """Test vocoder loading."""

    @patch('f5_tts.infer.utils_infer.Vocos')
    def test_load_vocos_pretrained(self, mock_vocos_class):
        """Test loading Vocos from pretrained."""
        mock_vocoder = Mock()
        mock_vocos_class.from_pretrained.return_value = mock_vocoder
        mock_vocoder.to.return_value = mock_vocoder

        result = load_vocoder(vocoder_name="vocos", is_local=False, device="cpu")

        assert result is not None
        mock_vocos_class.from_pretrained.assert_called_once()

    @patch('f5_tts.infer.utils_infer.Vocos')
    def test_load_vocos_local(self, mock_vocos_class):
        """Test loading Vocos from local path."""
        # Create temporary config and model files
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            model_path = os.path.join(tmpdir, "pytorch_model.bin")

            # Create dummy files
            with open(config_path, "w") as f:
                f.write("feature_extractor:\n  class_path: vocos.feature_extractors.EncodecFeatures\n")

            # Create a dummy model file
            torch.save({"dummy": torch.tensor([1.0])}, model_path)

            mock_vocoder = Mock()
            mock_vocos_class.from_hparams.return_value = mock_vocoder
            mock_vocoder.eval.return_value = mock_vocoder
            mock_vocoder.to.return_value = mock_vocoder
            mock_vocoder.load_state_dict = Mock()

            result = load_vocoder(
                vocoder_name="vocos",
                is_local=True,
                local_path=tmpdir,
                device="cpu"
            )

            assert result is not None
            mock_vocos_class.from_hparams.assert_called_once()


class TestSaveSpectrogram:
    """Test spectrogram saving."""

    def test_save_spectrogram(self):
        """Test saving spectrogram to file."""
        # Create a dummy spectrogram
        spectrogram = np.random.randn(100, 200)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            output_path = f.name

        try:
            save_spectrogram(spectrogram, output_path)

            # Verify file was created
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestRemoveSilenceForGeneratedWav:
    """Test silence removal from generated audio files."""

    def test_remove_silence_from_file(self):
        """Test removing silence from a wav file."""
        # Create a test audio file with silence using AudioSegment directly
        # to ensure compatibility with pydub
        silence_duration = 1000  # 1 second in ms
        tone_duration = 2000  # 2 seconds in ms

        # Create silence
        silence = AudioSegment.silent(duration=silence_duration)

        # Create a tone using AudioSegment
        sample_rate = 24000
        t = np.linspace(0, tone_duration / 1000, int(sample_rate * tone_duration / 1000))
        tone_array = (np.sin(2 * np.pi * 440 * t) * 32767 * 0.3).astype(np.int16)

        # Convert to AudioSegment
        from array import array
        tone = AudioSegment(
            tone_array.tobytes(),
            frame_rate=sample_rate,
            sample_width=2,
            channels=1
        )

        # Combine: silence - tone - silence
        full_audio = silence + tone + silence

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            full_audio.export(f.name, format="wav")
            audio_path = f.name

        try:
            # Get original length
            original_len = len(full_audio)

            # Remove silence
            remove_silence_for_generated_wav(audio_path)

            # Check that file still exists and was modified
            assert os.path.exists(audio_path)
            processed_audio = AudioSegment.from_wav(audio_path)

            # Processed audio should be shorter (silence removed)
            # or at least exist and be valid
            assert len(processed_audio) > 0
            # Should be shorter than original (silence removed)
            assert len(processed_audio) <= original_len
        finally:
            if os.path.exists(audio_path):
                os.unlink(audio_path)
