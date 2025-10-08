"""Simplified tests for F5-TTS API module using pytest."""

import sys
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestF5TTSInitialization:
    """Test F5TTS class initialization."""

    @patch.dict(os.environ, {'ENABLE_TORCH_COMPILE': 'false'})
    @patch('f5_tts.api.load_vocoder')
    @patch('f5_tts.api.load_model')
    @patch('f5_tts.api.cached_path')
    def test_default_initialization(self, mock_cached_path, mock_load_model, mock_load_vocoder):
        """Test F5TTS initialization with default parameters."""
        from f5_tts.api import F5TTS

        mock_cached_path.return_value = "/fake/model.safetensors"
        mock_load_model.return_value = Mock()
        mock_load_vocoder.return_value = Mock()

        f5tts = F5TTS()

        assert f5tts.target_sample_rate == 24000
        assert f5tts.hop_length == 256
        assert f5tts.seed == -1
        assert f5tts.mel_spec_type == "vocos"
        assert f5tts.device in ["cuda", "mps", "cpu"]

    @patch.dict(os.environ, {'ENABLE_TORCH_COMPILE': 'false'})
    @patch('f5_tts.api.load_vocoder')
    @patch('f5_tts.api.load_model')
    @patch('f5_tts.api.cached_path')
    def test_custom_device(self, mock_cached_path, mock_load_model, mock_load_vocoder):
        """Test initialization with custom device."""
        from f5_tts.api import F5TTS

        mock_cached_path.return_value = "/fake/model.safetensors"
        mock_load_model.return_value = Mock()
        mock_load_vocoder.return_value = Mock()

        f5tts = F5TTS(device="cpu")

        assert f5tts.device == "cpu"

    @patch.dict(os.environ, {'ENABLE_TORCH_COMPILE': 'false'})
    @patch('f5_tts.api.load_vocoder')
    @patch('f5_tts.api.load_model')
    @patch('f5_tts.api.cached_path')
    def test_invalid_model_type(self, mock_cached_path, mock_load_model, mock_load_vocoder):
        """Test initialization with invalid model type raises error."""
        from f5_tts.api import F5TTS

        mock_cached_path.return_value = "/fake/model.safetensors"
        mock_load_model.return_value = Mock()
        mock_load_vocoder.return_value = Mock()

        try:
            F5TTS(model_type="INVALID-MODEL")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Unknown model type" in str(e)


class TestF5TTSVocoder:
    """Test vocoder loading."""

    @patch.dict(os.environ, {'ENABLE_TORCH_COMPILE': 'false'})
    @patch('f5_tts.api.load_vocoder')
    @patch('f5_tts.api.load_model')
    @patch('f5_tts.api.cached_path')
    def test_load_vocoder_vocos(self, mock_cached_path, mock_load_model, mock_load_vocoder):
        """Test loading Vocos vocoder."""
        from f5_tts.api import F5TTS

        mock_cached_path.return_value = "/fake/model.safetensors"
        mock_load_model.return_value = Mock()
        mock_load_vocoder.return_value = Mock()

        f5tts = F5TTS(vocoder_name="vocos")

        mock_load_vocoder.assert_called_once_with("vocos", False, None, f5tts.device)

    @patch.dict(os.environ, {'ENABLE_TORCH_COMPILE': 'false'})
    @patch('f5_tts.api.load_vocoder')
    @patch('f5_tts.api.load_model')
    @patch('f5_tts.api.cached_path')
    def test_vocoder_with_local_path(self, mock_cached_path, mock_load_model, mock_load_vocoder):
        """Test vocoder loading with local path."""
        from f5_tts.api import F5TTS

        mock_cached_path.return_value = "/fake/model.safetensors"
        mock_load_model.return_value = Mock()
        mock_load_vocoder.return_value = Mock()

        f5tts = F5TTS(local_path="/local/vocoder/path")

        mock_load_vocoder.assert_called_once_with("vocos", True, "/local/vocoder/path", f5tts.device)


class TestF5TTSExport:
    """Test export functionality."""

    @patch.dict(os.environ, {'ENABLE_TORCH_COMPILE': 'false'})
    @patch('f5_tts.api.load_vocoder')
    @patch('f5_tts.api.load_model')
    @patch('f5_tts.api.cached_path')
    @patch('f5_tts.api.sf.write')
    def test_export_wav(self, mock_write, mock_cached_path, mock_load_model, mock_load_vocoder):
        """Test WAV export."""
        from f5_tts.api import F5TTS

        mock_cached_path.return_value = "/fake/model.safetensors"
        mock_load_model.return_value = Mock()
        mock_load_vocoder.return_value = Mock()

        f5tts = F5TTS()

        # Create fake audio
        wav = np.random.randn(24000)

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            f5tts.export_wav(wav, tmp_path, remove_silence=False)
            mock_write.assert_called_once_with(tmp_path, wav, f5tts.target_sample_rate)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @patch.dict(os.environ, {'ENABLE_TORCH_COMPILE': 'false'})
    @patch('f5_tts.api.load_vocoder')
    @patch('f5_tts.api.load_model')
    @patch('f5_tts.api.cached_path')
    @patch('f5_tts.api.save_spectrogram')
    def test_export_spectrogram(self, mock_save_spect, mock_cached_path, mock_load_model, mock_load_vocoder):
        """Test spectrogram export."""
        from f5_tts.api import F5TTS

        mock_cached_path.return_value = "/fake/model.safetensors"
        mock_load_model.return_value = Mock()
        mock_load_vocoder.return_value = Mock()

        f5tts = F5TTS()

        # Create fake spectrogram
        spect = np.random.randn(100, 100)

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            f5tts.export_spectrogram(spect, tmp_path)
            mock_save_spect.assert_called_once_with(spect, tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestF5TTSInference:
    """Test inference functionality."""

    @patch.dict(os.environ, {'ENABLE_TORCH_COMPILE': 'false'})
    @patch('f5_tts.api.load_vocoder')
    @patch('f5_tts.api.load_model')
    @patch('f5_tts.api.cached_path')
    @patch('f5_tts.api.preprocess_ref_audio_text')
    @patch('f5_tts.api.infer_process')
    @patch('f5_tts.api.seed_everything')
    def test_infer_basic(
        self,
        mock_seed,
        mock_infer_process,
        mock_preprocess,
        mock_cached_path,
        mock_load_model,
        mock_load_vocoder
    ):
        """Test basic inference."""
        from f5_tts.api import F5TTS

        mock_cached_path.return_value = "/fake/model.safetensors"
        mock_load_model.return_value = Mock()
        mock_load_vocoder.return_value = Mock()

        # Mock preprocessing
        mock_preprocess.return_value = ("/fake/audio.wav", "reference text")

        # Mock inference output
        fake_wav = np.random.randn(24000)
        fake_spect = np.random.randn(100, 100)
        mock_infer_process.return_value = (fake_wav, 24000, fake_spect)

        f5tts = F5TTS()

        wav, sr, spect = f5tts.infer(
            ref_file="/fake/ref.wav",
            ref_text="reference text",
            gen_text="generated text",
            seed=42
        )

        # Verify seed was set
        mock_seed.assert_called_once_with(42)
        assert f5tts.seed == 42

        # Verify preprocessing was called
        mock_preprocess.assert_called_once()

        # Verify inference was called
        mock_infer_process.assert_called_once()

        # Check outputs
        assert wav.shape == (24000,)
        assert sr == 24000
        assert spect.shape == (100, 100)

    @patch.dict(os.environ, {'ENABLE_TORCH_COMPILE': 'false'})
    @patch('f5_tts.api.load_vocoder')
    @patch('f5_tts.api.load_model')
    @patch('f5_tts.api.cached_path')
    @patch('f5_tts.api.preprocess_ref_audio_text')
    @patch('f5_tts.api.infer_process')
    @patch('f5_tts.api.seed_everything')
    @patch('f5_tts.api.random.randint')
    def test_infer_random_seed(
        self,
        mock_randint,
        mock_seed,
        mock_infer_process,
        mock_preprocess,
        mock_cached_path,
        mock_load_model,
        mock_load_vocoder
    ):
        """Test inference with random seed."""
        from f5_tts.api import F5TTS

        mock_cached_path.return_value = "/fake/model.safetensors"
        mock_load_model.return_value = Mock()
        mock_load_vocoder.return_value = Mock()
        mock_preprocess.return_value = ("/fake/audio.wav", "reference text")

        fake_wav = np.random.randn(24000)
        fake_spect = np.random.randn(100, 100)
        mock_infer_process.return_value = (fake_wav, 24000, fake_spect)

        # Mock random seed
        mock_randint.return_value = 12345

        f5tts = F5TTS()

        wav, sr, spect = f5tts.infer(
            ref_file="/fake/ref.wav",
            ref_text="reference text",
            gen_text="generated text",
            seed=-1  # Random seed
        )

        # Should generate random seed
        assert mock_randint.called
        assert f5tts.seed == 12345

    @patch.dict(os.environ, {'ENABLE_TORCH_COMPILE': 'false'})
    @patch('f5_tts.api.load_vocoder')
    @patch('f5_tts.api.load_model')
    @patch('f5_tts.api.cached_path')
    @patch('f5_tts.api.preprocess_ref_audio_text')
    @patch('f5_tts.api.infer_process')
    @patch('f5_tts.api.seed_everything')
    @patch('f5_tts.api.sf.write')
    def test_infer_with_file_export(
        self,
        mock_write,
        mock_seed,
        mock_infer_process,
        mock_preprocess,
        mock_cached_path,
        mock_load_model,
        mock_load_vocoder
    ):
        """Test inference with file export."""
        from f5_tts.api import F5TTS

        mock_cached_path.return_value = "/fake/model.safetensors"
        mock_load_model.return_value = Mock()
        mock_load_vocoder.return_value = Mock()
        mock_preprocess.return_value = ("/fake/audio.wav", "reference text")

        fake_wav = np.random.randn(24000)
        fake_spect = np.random.randn(100, 100)
        mock_infer_process.return_value = (fake_wav, 24000, fake_spect)

        f5tts = F5TTS()

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            wav, sr, spect = f5tts.infer(
                ref_file="/fake/ref.wav",
                ref_text="reference text",
                gen_text="generated text",
                file_wave=tmp_path,
                seed=42
            )

            # Should export to file
            mock_write.assert_called_once()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestF5TTSParameters:
    """Test inference parameters."""

    @patch.dict(os.environ, {'ENABLE_TORCH_COMPILE': 'false'})
    @patch('f5_tts.api.load_vocoder')
    @patch('f5_tts.api.load_model')
    @patch('f5_tts.api.cached_path')
    @patch('f5_tts.api.preprocess_ref_audio_text')
    @patch('f5_tts.api.infer_process')
    @patch('f5_tts.api.seed_everything')
    def test_infer_custom_parameters(
        self,
        mock_seed,
        mock_infer_process,
        mock_preprocess,
        mock_cached_path,
        mock_load_model,
        mock_load_vocoder
    ):
        """Test inference with custom parameters."""
        from f5_tts.api import F5TTS

        mock_cached_path.return_value = "/fake/model.safetensors"
        mock_load_model.return_value = Mock()
        mock_load_vocoder.return_value = Mock()
        mock_preprocess.return_value = ("/fake/audio.wav", "reference text")

        fake_wav = np.random.randn(24000)
        fake_spect = np.random.randn(100, 100)
        mock_infer_process.return_value = (fake_wav, 24000, fake_spect)

        f5tts = F5TTS()

        wav, sr, spect = f5tts.infer(
            ref_file="/fake/ref.wav",
            ref_text="reference text",
            gen_text="generated text",
            target_rms=0.2,
            cross_fade_duration=0.3,
            sway_sampling_coef=0.5,
            cfg_strength=3.0,
            nfe_step=16,
            speed=1.5,
            seed=42
        )

        # Verify custom parameters were passed to infer_process
        call_kwargs = mock_infer_process.call_args[1]
        assert call_kwargs['target_rms'] == 0.2
        assert call_kwargs['cross_fade_duration'] == 0.3
        assert call_kwargs['sway_sampling_coef'] == 0.5
        assert call_kwargs['cfg_strength'] == 3.0
        assert call_kwargs['nfe_step'] == 16
        assert call_kwargs['speed'] == 1.5


class TestF5TTSModelTypes:
    """Test different model types and configurations."""

    @patch.dict(os.environ, {'ENABLE_TORCH_COMPILE': 'false'})
    @patch('f5_tts.api.load_vocoder')
    @patch('f5_tts.api.load_model')
    @patch('f5_tts.api.cached_path')
    def test_e2tts_model(self, mock_cached_path, mock_load_model, mock_load_vocoder):
        """Test E2-TTS model initialization."""
        from f5_tts.api import F5TTS

        mock_cached_path.return_value = "/fake/model.safetensors"
        mock_load_model.return_value = Mock()
        mock_load_vocoder.return_value = Mock()

        f5tts = F5TTS(model_type="E2-TTS")

        # Verify E2-TTS model was loaded
        assert mock_load_model.called
        call_args = mock_load_model.call_args
        # E2-TTS uses UNetT model class
        assert call_args[0][1]['dim'] == 1024
        assert call_args[0][1]['depth'] == 24

    @patch.dict(os.environ, {'ENABLE_TORCH_COMPILE': 'false'})
    @patch('f5_tts.api.load_vocoder')
    @patch('f5_tts.api.load_model')
    @patch('f5_tts.api.cached_path')
    def test_bigvgan_vocoder(self, mock_cached_path, mock_load_model, mock_load_vocoder):
        """Test bigvgan vocoder with F5-TTS."""
        from f5_tts.api import F5TTS

        mock_cached_path.return_value = "/fake/model.pt"
        mock_load_model.return_value = Mock()
        mock_load_vocoder.return_value = Mock()

        f5tts = F5TTS(model_type="F5-TTS", vocoder_name="bigvgan")

        # Verify bigvgan checkpoint was requested
        assert mock_cached_path.called
        # Should load bigvgan checkpoint
        assert f5tts.mel_spec_type == "bigvgan"

    @patch.dict(os.environ, {'ENABLE_TORCH_COMPILE': 'true'})
    @patch('f5_tts.api.load_vocoder')
    @patch('f5_tts.api.load_model')
    @patch('f5_tts.api.cached_path')
    @patch('f5_tts.api.torch.compile')
    def test_torch_compile_enabled(self, mock_compile, mock_cached_path, mock_load_model, mock_load_vocoder):
        """Test torch.compile when enabled."""
        from f5_tts.api import F5TTS

        mock_cached_path.return_value = "/fake/model.safetensors"
        mock_model = Mock()
        mock_load_model.return_value = mock_model
        mock_load_vocoder.return_value = Mock()
        mock_compile.return_value = mock_model

        f5tts = F5TTS()

        # Verify torch.compile was called
        mock_compile.assert_called_once_with(mock_model, mode="reduce-overhead")

    @patch.dict(os.environ, {'ENABLE_TORCH_COMPILE': 'true'})
    @patch('f5_tts.api.load_vocoder')
    @patch('f5_tts.api.load_model')
    @patch('f5_tts.api.cached_path')
    def test_torch_compile_error_handling(self, mock_cached_path, mock_load_model, mock_load_vocoder):
        """Test torch.compile error handling."""
        from f5_tts.api import F5TTS

        mock_cached_path.return_value = "/fake/model.safetensors"
        mock_load_model.return_value = Mock()
        mock_load_vocoder.return_value = Mock()

        # Mock torch.compile to raise an error
        with patch('f5_tts.api.torch.compile', side_effect=Exception("Compile error")):
            # Should not raise, just warn
            f5tts = F5TTS()
            assert f5tts is not None


class TestF5TTSExportExtended:
    """Test additional export functionality."""

    @patch.dict(os.environ, {'ENABLE_TORCH_COMPILE': 'false'})
    @patch('f5_tts.api.load_vocoder')
    @patch('f5_tts.api.load_model')
    @patch('f5_tts.api.cached_path')
    @patch('f5_tts.api.sf.write')
    @patch('f5_tts.api.remove_silence_for_generated_wav')
    def test_export_wav_with_silence_removal(
        self,
        mock_remove_silence,
        mock_write,
        mock_cached_path,
        mock_load_model,
        mock_load_vocoder
    ):
        """Test WAV export with silence removal."""
        from f5_tts.api import F5TTS

        mock_cached_path.return_value = "/fake/model.safetensors"
        mock_load_model.return_value = Mock()
        mock_load_vocoder.return_value = Mock()

        f5tts = F5TTS()

        wav = np.random.randn(24000)

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            f5tts.export_wav(wav, tmp_path, remove_silence=True)

            # Verify silence removal was called
            mock_remove_silence.assert_called_once_with(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @patch.dict(os.environ, {'ENABLE_TORCH_COMPILE': 'false'})
    @patch('f5_tts.api.load_vocoder')
    @patch('f5_tts.api.load_model')
    @patch('f5_tts.api.cached_path')
    @patch('f5_tts.api.preprocess_ref_audio_text')
    @patch('f5_tts.api.infer_process')
    @patch('f5_tts.api.seed_everything')
    @patch('f5_tts.api.save_spectrogram')
    def test_infer_with_spectrogram_export(
        self,
        mock_save_spect,
        mock_seed,
        mock_infer_process,
        mock_preprocess,
        mock_cached_path,
        mock_load_model,
        mock_load_vocoder
    ):
        """Test inference with spectrogram export."""
        from f5_tts.api import F5TTS

        mock_cached_path.return_value = "/fake/model.safetensors"
        mock_load_model.return_value = Mock()
        mock_load_vocoder.return_value = Mock()
        mock_preprocess.return_value = ("/fake/audio.wav", "reference text")

        fake_wav = np.random.randn(24000)
        fake_spect = np.random.randn(100, 100)
        mock_infer_process.return_value = (fake_wav, 24000, fake_spect)

        f5tts = F5TTS()

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            wav, sr, spect = f5tts.infer(
                ref_file="/fake/ref.wav",
                ref_text="reference text",
                gen_text="generated text",
                file_spect=tmp_path,
                seed=42
            )

            # Should export spectrogram
            mock_save_spect.assert_called_once_with(fake_spect, tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
