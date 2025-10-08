"""Tests for audio processing components."""

import sys
import os
import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from f5_tts.audio.processors import (
    AudioNormalizer,
    AudioResampler,
    StereoToMono,
    AudioClipping,
    AudioProcessingPipeline
)
from f5_tts.core import AudioData, AudioProcessingConfig


class TestAudioNormalizer:
    """Test AudioNormalizer class."""

    def test_initialization_default(self):
        """Test default initialization."""
        normalizer = AudioNormalizer()

        assert normalizer.config is not None
        assert isinstance(normalizer.config, AudioProcessingConfig)

    def test_initialization_with_config(self):
        """Test initialization with custom config."""
        config = AudioProcessingConfig(max_amplitude=0.95)
        normalizer = AudioNormalizer(config)

        assert normalizer.config.max_amplitude == 0.95

    def test_remove_dc_offset(self):
        """Test DC offset removal."""
        normalizer = AudioNormalizer()

        # Create audio with DC offset
        audio = np.array([1.0, 1.0, 1.0, 1.0])

        result = normalizer.remove_dc_offset(audio)

        # Mean should be ~0
        assert abs(np.mean(result)) < 1e-10

    def test_remove_dc_offset_centered(self):
        """Test DC offset removal on already centered audio."""
        normalizer = AudioNormalizer()

        # Create centered audio
        audio = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])

        result = normalizer.remove_dc_offset(audio)

        # Should still be centered
        assert abs(np.mean(result)) < 1e-10

    def test_normalize_amplitude_clipping(self):
        """Test amplitude normalization prevents clipping."""
        normalizer = AudioNormalizer()

        # Create audio that exceeds max amplitude
        audio = np.array([0.0, 0.5, 1.5, -1.5, 0.0])

        result = normalizer.normalize_amplitude(audio, max_amplitude=0.99)

        # Should be scaled down
        assert np.max(np.abs(result)) <= 0.99

    def test_normalize_amplitude_no_clipping(self):
        """Test amplitude normalization preserves quiet audio."""
        normalizer = AudioNormalizer()

        # Create audio below max amplitude
        audio = np.array([0.0, 0.2, 0.5, -0.3, 0.0])

        result = normalizer.normalize_amplitude(audio, max_amplitude=0.99)

        # Should be unchanged
        assert np.array_equal(result, audio)

    def test_normalize_rms(self):
        """Test RMS normalization."""
        normalizer = AudioNormalizer()

        # Create quiet audio
        audio = torch.tensor([0.01, 0.02, 0.01, -0.01])

        result = normalizer.normalize_rms(audio, target_rms=0.1)

        # Should be boosted
        result_rms = torch.sqrt(torch.mean(torch.square(result)))
        assert abs(result_rms.item() - 0.1) < 0.01

    def test_normalize_rms_loud_audio(self):
        """Test RMS normalization preserves loud audio."""
        normalizer = AudioNormalizer()

        # Create loud audio
        audio = torch.tensor([0.5, 0.7, 0.3, -0.4])

        result = normalizer.normalize_rms(audio, target_rms=0.1)

        # Should be unchanged (already loud)
        assert torch.equal(result, audio)

    def test_process_full_pipeline(self):
        """Test complete normalization pipeline."""
        config = AudioProcessingConfig(
            remove_dc_offset=True,
            normalize_output=True,
            max_amplitude=0.99
        )
        normalizer = AudioNormalizer(config)

        # Create audio with DC offset and clipping
        waveform = np.array([1.0, 1.5, 2.0, 1.5, 1.0])
        audio_data = AudioData(waveform=waveform, sample_rate=24000)

        result = normalizer.process(audio_data)

        # Check DC offset removed
        assert abs(np.mean(result.waveform)) < 0.1

        # Check amplitude normalized
        assert np.max(np.abs(result.waveform)) <= 0.99

    def test_process_with_config_disabled(self):
        """Test processing with normalization disabled."""
        config = AudioProcessingConfig(
            remove_dc_offset=False,
            normalize_output=False
        )
        normalizer = AudioNormalizer(config)

        waveform = np.array([1.0, 1.5, 2.0, 1.5, 1.0])
        audio_data = AudioData(waveform=waveform, sample_rate=24000)

        result = normalizer.process(audio_data)

        # Should be unchanged
        assert np.array_equal(result.waveform, waveform)


class TestAudioResampler:
    """Test AudioResampler class."""

    def test_initialization(self):
        """Test resampler initialization."""
        resampler = AudioResampler()

        assert resampler.config is not None
        assert resampler.config.target_sample_rate == 24000

    def test_resample_upsample(self):
        """Test upsampling audio."""
        resampler = AudioResampler()

        # Create 16kHz audio
        audio = torch.randn(1, 16000)

        result = resampler.resample(audio, orig_sr=16000, target_sr=24000)

        # Should be upsampled
        assert result.shape[1] == 24000

    def test_resample_downsample(self):
        """Test downsampling audio."""
        resampler = AudioResampler()

        # Create 48kHz audio
        audio = torch.randn(1, 48000)

        result = resampler.resample(audio, orig_sr=48000, target_sr=24000)

        # Should be downsampled
        assert result.shape[1] == 24000

    def test_resample_no_change(self):
        """Test resampling when rates match."""
        resampler = AudioResampler()

        audio = torch.randn(1, 24000)

        result = resampler.resample(audio, orig_sr=24000, target_sr=24000)

        # Should be unchanged
        assert torch.equal(result, audio)

    def test_resample_uses_config(self):
        """Test resampling uses config target rate."""
        config = AudioProcessingConfig(target_sample_rate=22050)
        resampler = AudioResampler(config)

        audio = torch.randn(1, 16000)

        result = resampler.resample(audio, orig_sr=16000)

        # Should use config rate
        assert result.shape[1] == 22050


class TestStereoToMono:
    """Test StereoToMono converter."""

    def test_convert_stereo(self):
        """Test converting stereo to mono."""
        # Create stereo audio (2 channels)
        stereo = torch.tensor([[1.0, 2.0, 3.0],
                               [0.0, 1.0, 2.0]])

        mono = StereoToMono.convert(stereo)

        # Should be mono (1 channel)
        assert mono.shape[0] == 1
        # Should be average of channels
        expected = torch.tensor([[0.5, 1.5, 2.5]])
        assert torch.allclose(mono, expected)

    def test_convert_already_mono(self):
        """Test converting already mono audio."""
        mono_input = torch.tensor([[1.0, 2.0, 3.0]])

        mono_output = StereoToMono.convert(mono_input)

        # Should be unchanged
        assert torch.equal(mono_output, mono_input)

    def test_convert_multi_channel(self):
        """Test converting multi-channel audio."""
        # Create 4-channel audio
        multi = torch.tensor([[1.0, 2.0],
                              [2.0, 3.0],
                              [3.0, 4.0],
                              [4.0, 5.0]])

        mono = StereoToMono.convert(multi)

        # Should average all channels
        assert mono.shape[0] == 1
        expected = torch.tensor([[2.5, 3.5]])
        assert torch.allclose(mono, expected)


class TestAudioClipping:
    """Test AudioClipping class."""

    def test_clamp_default_range(self):
        """Test clamping with default range."""
        audio = torch.tensor([0.0, 0.5, 1.5, -1.5, -0.5])

        clamped = AudioClipping.clamp(audio)

        # Should be clamped to [-1, 1]
        assert torch.max(clamped) <= 1.0
        assert torch.min(clamped) >= -1.0
        assert clamped[2].item() == 1.0  # 1.5 -> 1.0
        assert clamped[3].item() == -1.0  # -1.5 -> -1.0

    def test_clamp_custom_range(self):
        """Test clamping with custom range."""
        audio = torch.tensor([0.0, 0.5, 1.0, 1.5])

        clamped = AudioClipping.clamp(audio, min_val=-0.8, max_val=0.8)

        # Should be clamped to [-0.8, 0.8]
        assert torch.max(clamped) <= 0.8
        assert abs(clamped[3].item() - 0.8) < 1e-6  # 1.5 -> 0.8 (within precision)

    def test_clamp_no_change(self):
        """Test clamping when audio is within range."""
        audio = torch.tensor([0.0, 0.2, 0.5, -0.3])

        clamped = AudioClipping.clamp(audio)

        # Should be unchanged
        assert torch.equal(clamped, audio)


class TestAudioProcessingPipeline:
    """Test complete audio processing pipeline."""

    def test_initialization(self):
        """Test pipeline initialization."""
        pipeline = AudioProcessingPipeline()

        assert pipeline.config is not None
        assert pipeline.normalizer is not None
        assert pipeline.resampler is not None

    def test_prepare_reference_audio_stereo_to_mono(self):
        """Test preparing stereo reference audio."""
        pipeline = AudioProcessingPipeline()

        # Create stereo audio at 16kHz
        audio = torch.randn(2, 16000)

        result = pipeline.prepare_reference_audio(
            audio, sample_rate=16000, device="cpu"
        )

        # Should be mono
        assert result.shape[0] == 1
        # Should be resampled to 24kHz
        assert result.shape[1] == 24000

    def test_prepare_reference_audio_rms_normalization(self):
        """Test RMS normalization in reference audio prep."""
        pipeline = AudioProcessingPipeline()

        # Create quiet mono audio
        audio = torch.randn(1, 24000) * 0.01

        result = pipeline.prepare_reference_audio(
            audio, sample_rate=24000, target_rms=0.1, device="cpu"
        )

        # Should be boosted to target RMS
        result_rms = torch.sqrt(torch.mean(torch.square(result)))
        assert abs(result_rms.item() - 0.1) < 0.02

    def test_prepare_reference_audio_device_transfer(self):
        """Test device transfer in reference audio prep."""
        pipeline = AudioProcessingPipeline()

        audio = torch.randn(1, 24000)

        result = pipeline.prepare_reference_audio(
            audio, sample_rate=24000, device="cpu"
        )

        # Should be on CPU
        assert result.device.type == "cpu"

    def test_finalize_output_audio_dc_removal(self):
        """Test DC offset removal in output finalization."""
        config = AudioProcessingConfig(
            remove_dc_offset=True,
            normalize_output=False
        )
        pipeline = AudioProcessingPipeline(config)

        # Create audio with DC offset
        audio = np.array([1.0, 1.0, 1.0, 1.0])

        result = pipeline.finalize_output_audio(audio)

        # DC offset should be removed
        assert abs(np.mean(result)) < 1e-10

    def test_finalize_output_audio_amplitude_normalization(self):
        """Test amplitude normalization in output finalization."""
        config = AudioProcessingConfig(
            remove_dc_offset=False,
            normalize_output=True,
            max_amplitude=0.99
        )
        pipeline = AudioProcessingPipeline(config)

        # Create audio with clipping
        audio = np.array([0.0, 1.5, 2.0, -1.5, 0.0])

        result = pipeline.finalize_output_audio(audio)

        # Should be normalized
        assert np.max(np.abs(result)) <= 0.99

    def test_finalize_output_audio_full_pipeline(self):
        """Test complete output finalization."""
        config = AudioProcessingConfig(
            remove_dc_offset=True,
            normalize_output=True,
            max_amplitude=0.99
        )
        pipeline = AudioProcessingPipeline(config)

        # Create problematic audio
        audio = np.array([1.0, 1.5, 2.0, 1.8, 1.0])

        result = pipeline.finalize_output_audio(audio)

        # DC offset removed
        assert abs(np.mean(result)) < 0.1
        # Amplitude normalized
        assert np.max(np.abs(result)) <= 0.99

    def test_finalize_output_audio_disabled(self):
        """Test finalization with processing disabled."""
        config = AudioProcessingConfig(
            remove_dc_offset=False,
            normalize_output=False
        )
        pipeline = AudioProcessingPipeline(config)

        audio = np.array([1.0, 1.5, 2.0, 1.5, 1.0])

        result = pipeline.finalize_output_audio(audio)

        # Should be unchanged
        assert np.array_equal(result, audio)


class TestAudioProcessingEdgeCases:
    """Test edge cases and special scenarios."""

    def test_normalizer_empty_audio(self):
        """Test normalizer with empty audio."""
        normalizer = AudioNormalizer()

        audio = np.array([])

        # Should handle gracefully
        result = normalizer.remove_dc_offset(audio)
        assert len(result) == 0

    def test_normalizer_single_sample(self):
        """Test normalizer with single sample."""
        normalizer = AudioNormalizer()

        audio = np.array([0.5])

        result = normalizer.normalize_amplitude(audio)
        assert result.shape == (1,)

    def test_resampler_very_short_audio(self):
        """Test resampling very short audio."""
        resampler = AudioResampler()

        audio = torch.randn(1, 100)

        result = resampler.resample(audio, orig_sr=8000, target_sr=16000)

        # Should be approximately doubled
        assert result.shape[1] > 100

    def test_stereo_to_mono_single_channel(self):
        """Test stereo converter with single sample."""
        audio = torch.tensor([[0.5]])

        result = StereoToMono.convert(audio)

        assert torch.equal(result, audio)

    def test_clipping_all_zeros(self):
        """Test clipping with all zeros."""
        audio = torch.zeros(100)

        result = AudioClipping.clamp(audio)

        assert torch.equal(result, audio)
