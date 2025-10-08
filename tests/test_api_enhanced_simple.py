"""Test enhanced API endpoints - simplified version."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Test without TestClient - just validate the enhancements are imported correctly


def test_imports():
    """Test that all enhancement modules can be imported."""
    # Import the API module
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "f5_tts_api",
        Path(__file__).parent.parent / "f5_tts_api.py"
    )
    f5_tts_api = importlib.util.module_from_spec(spec)

    # This will fail if imports are broken
    spec.loader.exec_module(f5_tts_api)

    # Verify the app exists
    assert hasattr(f5_tts_api, 'app')

    # Verify enhancement modules were imported
    # Note: These are imported as functions, not classes
    assert hasattr(f5_tts_api, 'normalize_spanish_text')
    assert hasattr(f5_tts_api, 'analyze_spanish_prosody')
    assert hasattr(f5_tts_api, 'analyze_breath_pauses')
    assert hasattr(f5_tts_api, 'AudioQualityAnalyzer')
    assert hasattr(f5_tts_api, 'get_adaptive_nfe_step')
    assert hasattr(f5_tts_api, 'get_adaptive_crossfade_duration')


def test_request_models():
    """Test that request models have enhancement fields."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "f5_tts_api",
        Path(__file__).parent.parent / "f5_tts_api.py"
    )
    f5_tts_api = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(f5_tts_api)

    TTSRequest = f5_tts_api.TTSRequest

    # Create a request with enhancement fields
    request = TTSRequest(
        gen_text="Test",
        ref_text="",
        normalize_text=True,
        analyze_prosody=True,
        analyze_breath_pauses=True,
        adaptive_nfe=True,
        adaptive_crossfade=True,
        check_audio_quality=True
    )

    assert request.normalize_text == True
    assert request.analyze_prosody == True
    assert request.analyze_breath_pauses == True
    assert request.adaptive_nfe == True
    assert request.adaptive_crossfade == True
    assert request.check_audio_quality == True
    assert request.cross_fade_duration == 0.8  # Updated default


def test_analysis_request():
    """Test AnalysisRequest model."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "f5_tts_api",
        Path(__file__).parent.parent / "f5_tts_api.py"
    )
    f5_tts_api = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(f5_tts_api)

    AnalysisRequest = f5_tts_api.AnalysisRequest

    request = AnalysisRequest(
        text="¿Tienes 25 euros?",
        normalize_text=True,
        analyze_prosody=True,
        analyze_breath_pauses=True
    )

    assert request.text == "¿Tienes 25 euros?"
    assert request.normalize_text == True


def test_enhancement_features_work():
    """Test that enhancement features actually work."""
    from f5_tts.text import (
        normalize_spanish_text,
        analyze_spanish_prosody,
        analyze_breath_pauses
    )
    from f5_tts.core import get_adaptive_nfe_step, get_adaptive_crossfade_duration

    # Test normalization
    normalized = normalize_spanish_text("Tengo 25 euros")
    assert "veinticinco" in normalized

    # Test prosody
    prosody = analyze_spanish_prosody("¿Cómo estás?")
    assert len(prosody.markers) > 0

    # Test breath analysis
    breath = analyze_breath_pauses("Primero. Segundo. Tercero.")
    assert len(breath.pauses) > 0

    # Test adaptive NFE
    nfe = get_adaptive_nfe_step("¿Cómo estás? ¡Muy bien!", 16)
    assert nfe >= 16

    # Test adaptive crossfade
    crossfade = get_adaptive_crossfade_duration()
    assert 0.4 <= crossfade <= 1.2


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
