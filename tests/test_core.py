"""Test suite for core modules (config, types)."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from f5_tts.core.config import GlobalConfig, get_config, set_config, reset_config
from f5_tts.core.types import AudioData, InferenceConfig, AudioProcessingConfig


class TestGlobalConfig:
    """Test GlobalConfig class."""

    def test_default_values(self):
        """Test default configuration values."""
        config = GlobalConfig()

        assert config.device == "auto"
        assert config.enable_torch_compile == True
        assert config.target_sample_rate == 24000
        assert config.default_nfe_step == 16
        assert config.default_cfg_strength == 2.0
        assert config.min_chunk_chars == 500
        assert config.max_chunk_chars == 2000
        assert config.default_vocoder == "vocos"

    def test_spanish_regional_defaults(self):
        """Test Spanish regional default values."""
        config = GlobalConfig()

        assert config.spanish_region == "neutral"
        assert config.auto_detect_region == False
        assert config.apply_regional_phonetics == True

    def test_from_env(self):
        """Test loading configuration from environment."""
        # Set environment variables
        os.environ['DEVICE'] = 'cuda'
        os.environ['DEFAULT_NFE_STEP'] = '32'
        os.environ['SPANISH_REGION'] = 'rioplatense'
        os.environ['AUTO_DETECT_REGION'] = 'true'

        config = GlobalConfig.from_env()

        assert config.device == 'cuda'
        assert config.default_nfe_step == 32
        assert config.spanish_region == 'rioplatense'
        assert config.auto_detect_region == True

        # Clean up
        del os.environ['DEVICE']
        del os.environ['DEFAULT_NFE_STEP']
        del os.environ['SPANISH_REGION']
        del os.environ['AUTO_DETECT_REGION']

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = GlobalConfig()
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert 'device' in config_dict
        assert 'target_sample_rate' in config_dict
        assert 'spanish_region' in config_dict

    def test_singleton_functions(self):
        """Test singleton get/set/reset functions."""
        # Reset to clean state
        reset_config()

        # Get default config
        config1 = get_config()
        assert config1.spanish_region == "neutral"

        # Create custom config
        custom_config = GlobalConfig(spanish_region="rioplatense", device="cpu")
        set_config(custom_config)

        # Get should return the same config
        config2 = get_config()
        assert config2.spanish_region == "rioplatense"
        assert config2.device == "cpu"

        # Reset
        reset_config()
        config3 = get_config()
        assert config3.spanish_region == "neutral"


class TestAudioData:
    """Test AudioData class."""

    def test_creation(self):
        """Test AudioData creation."""
        import torch

        waveform = torch.randn(1, 24000)
        audio_data = AudioData(waveform=waveform, sample_rate=24000)

        assert audio_data.sample_rate == 24000
        assert audio_data.waveform.shape == (1, 24000)

    def test_with_metadata(self):
        """Test AudioData with optional duration."""
        import torch

        waveform = torch.randn(1, 24000)
        # Test with explicit duration
        audio_data = AudioData(
            waveform=waveform,
            sample_rate=24000,
            duration=1.0
        )

        assert audio_data.duration == 1.0


class TestInferenceConfig:
    """Test InferenceConfig class."""

    def test_default_values(self):
        """Test default inference configuration."""
        config = InferenceConfig()

        assert config.nfe_step == 16
        assert config.cfg_strength == 2.0
        assert config.speed == 1.0
        assert config.seed == -1

    def test_custom_values(self):
        """Test custom inference configuration."""
        config = InferenceConfig(
            nfe_step=32,
            cfg_strength=3.0,
            speed=1.2,
            seed=42
        )

        assert config.nfe_step == 32
        assert config.cfg_strength == 3.0
        assert config.speed == 1.2
        assert config.seed == 42


class TestAudioProcessingConfig:
    """Test AudioProcessingConfig class."""

    def test_default_values(self):
        """Test default audio processing configuration."""
        config = AudioProcessingConfig()

        assert config.target_sample_rate == 24000
        assert config.n_mel_channels == 100
        assert config.normalize_output == True
        assert config.remove_dc_offset == True

    def test_custom_values(self):
        """Test custom audio processing configuration."""
        config = AudioProcessingConfig(
            target_sample_rate=16000,
            n_mel_channels=80,
            normalize_output=False,
            remove_dc_offset=False
        )

        assert config.target_sample_rate == 16000
        assert config.n_mel_channels == 80
        assert config.normalize_output == False
        assert config.remove_dc_offset == False


class TestConfigIntegration:
    """Test configuration integration."""

    def test_global_config_affects_inference(self):
        """Test that global config can be used for inference."""
        reset_config()

        # Set global config
        custom = GlobalConfig(
            default_nfe_step=32,
            default_cfg_strength=3.0,
            spanish_region="mexican"
        )
        set_config(custom)

        # Get config
        config = get_config()

        # Create inference config from global
        inference = InferenceConfig(
            nfe_step=config.default_nfe_step,
            cfg_strength=config.default_cfg_strength
        )

        assert inference.nfe_step == 32
        assert inference.cfg_strength == 3.0

        reset_config()

    def test_audio_config_from_global(self):
        """Test creating audio config from global."""
        reset_config()

        config = get_config()

        audio_config = AudioProcessingConfig(
            target_sample_rate=config.target_sample_rate
        )

        assert audio_config.target_sample_rate == 24000

        reset_config()


def run_tests():
    """Run all tests."""
    test_classes = [
        TestGlobalConfig,
        TestAudioData,
        TestInferenceConfig,
        TestAudioProcessingConfig,
        TestConfigIntegration,
    ]

    total = 0
    passed = 0
    failed = 0

    for test_class in test_classes:
        print(f"\n{'='*60}")
        print(f"Testing {test_class.__name__}")
        print('='*60)

        instance = test_class()
        methods = [m for m in dir(instance) if m.startswith('test_')]

        for method_name in methods:
            total += 1
            try:
                method = getattr(instance, method_name)
                method()
                print(f"✓ {method_name}")
                passed += 1
            except AssertionError as e:
                print(f"✗ {method_name}: {e}")
                failed += 1
            except Exception as e:
                print(f"✗ {method_name}: ERROR: {e}")
                failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} passed, {failed}/{total} failed")
    print('='*60)

    return failed == 0


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
