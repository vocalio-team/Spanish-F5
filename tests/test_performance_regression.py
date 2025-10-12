"""
Performance Regression Tests

These tests verify that code changes don't degrade performance or quality
beyond acceptable thresholds defined in PERFORMANCE_BASELINE.md.

Run with: pytest tests/test_performance_regression.py -v
"""

import json
import pytest
import torch
import time
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from f5_tts.api import F5TTS
from f5_tts.text import analyze_spanish_prosody, process_spanish_text
from f5_tts.audio import AudioQualityAnalyzer


# Load baseline from baseline_quick.json
BASELINE_PATH = Path(__file__).parent.parent / "baseline_quick.json"


def load_baseline():
    """Load baseline metrics from file."""
    if not BASELINE_PATH.exists():
        pytest.skip(f"Baseline file not found at {BASELINE_PATH}. Run benchmark_quick.py first.")

    with open(BASELINE_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def baseline():
    """Fixture to load baseline metrics."""
    return load_baseline()


@pytest.fixture(scope="module")
def f5tts_model():
    """Fixture to load F5TTS model (reused across tests)."""
    device = "cuda" if torch.cuda.is_available() else "cpu"

    model = F5TTS(
        model_type="F5-TTS",
        ckpt_file="models/Spanish/model_1250000.safetensors",
        vocab_file="models/Spanish/vocab.txt",
        ode_method="euler",
        use_ema=True,
        vocoder_name="vocos",
        device=device,
    )

    return model


class TestAudioQualityRegression:
    """Test that audio quality doesn't regress."""

    def test_audio_quality_score_regression(self, baseline, f5tts_model):
        """
        Test that overall audio quality score doesn't drop below threshold.

        Baseline: 96.3/100
        Threshold: > 94.0 (2-point degradation tolerance)
        """
        # Generate audio
        wav, sr, _ = f5tts_model.infer(
            ref_file="ref_audio/short.wav",
            ref_text="",
            gen_text="Esta es una prueba de calidad de audio.",
            target_rms=0.1,
            speed=1.0,
            nfe_step=16,
        )

        # Analyze quality
        quality_analyzer = AudioQualityAnalyzer()
        if not isinstance(wav, torch.Tensor):
            wav = torch.from_numpy(wav)
        quality_metrics = quality_analyzer.analyze(wav, sr)

        current_score = float(quality_metrics.overall_score)
        baseline_score = baseline["quality"]["audio_quality"]["overall_score"]
        threshold = 94.0

        print(f"\n  Current: {current_score:.1f}, Baseline: {baseline_score:.1f}, Threshold: {threshold:.1f}")

        assert current_score >= threshold, (
            f"Audio quality score ({current_score:.1f}) dropped below threshold ({threshold:.1f}). "
            f"Baseline was {baseline_score:.1f}."
        )

    def test_snr_regression(self, baseline, f5tts_model):
        """
        Test that SNR doesn't drop below threshold.

        Baseline: 73.2dB
        Threshold: > 70.0dB
        """
        # Generate audio
        wav, sr, _ = f5tts_model.infer(
            ref_file="ref_audio/short.wav",
            ref_text="",
            gen_text="Prueba de relación señal-ruido.",
            target_rms=0.1,
            speed=1.0,
            nfe_step=16,
        )

        # Analyze quality
        quality_analyzer = AudioQualityAnalyzer()
        if not isinstance(wav, torch.Tensor):
            wav = torch.from_numpy(wav)
        quality_metrics = quality_analyzer.analyze(wav, sr)

        current_snr = float(quality_metrics.snr_db)
        baseline_snr = baseline["quality"]["audio_quality"]["snr_db"]
        threshold = 70.0

        print(f"\n  Current: {current_snr:.1f}dB, Baseline: {baseline_snr:.1f}dB, Threshold: {threshold:.1f}dB")

        assert current_snr >= threshold, (
            f"SNR ({current_snr:.1f}dB) dropped below threshold ({threshold:.1f}dB). "
            f"Baseline was {baseline_snr:.1f}dB."
        )

    def test_clipping_regression(self, baseline, f5tts_model):
        """
        Test that clipping rate stays below threshold.

        Baseline: 0.0%
        Threshold: < 0.1%
        """
        # Generate audio
        wav, sr, _ = f5tts_model.infer(
            ref_file="ref_audio/short.wav",
            ref_text="",
            gen_text="Prueba de recorte de audio.",
            target_rms=0.1,
            speed=1.0,
            nfe_step=16,
        )

        # Analyze quality
        quality_analyzer = AudioQualityAnalyzer()
        if not isinstance(wav, torch.Tensor):
            wav = torch.from_numpy(wav)
        quality_metrics = quality_analyzer.analyze(wav, sr)

        current_clipping = float(quality_metrics.clipping_rate)
        baseline_clipping = baseline["quality"]["audio_quality"]["clipping_rate"]
        threshold = 0.001  # 0.1%

        print(f"\n  Current: {current_clipping:.4f}, Baseline: {baseline_clipping:.4f}, Threshold: {threshold:.4f}")

        assert current_clipping <= threshold, (
            f"Clipping rate ({current_clipping:.4f}) exceeded threshold ({threshold:.4f}). "
            f"Baseline was {baseline_clipping:.4f}."
        )


class TestProsodyRegression:
    """Test that prosody detection doesn't regress."""

    def test_question_detection_regression(self, baseline):
        """
        Test that question detection still works.

        Baseline: 100% (1/1 detected)
        Threshold: Must detect question marker
        """
        text = "¿Cómo estás hoy?"
        prosody_analysis = analyze_spanish_prosody(text)

        markers_detected = len(prosody_analysis.markers)
        baseline_markers = baseline["quality"]["prosody_detection"]["question"]["markers_detected"]

        print(f"\n  Current: {markers_detected} markers, Baseline: {baseline_markers} markers")

        assert markers_detected > 0, (
            f"Question detection failed. Expected at least 1 marker, got {markers_detected}."
        )

    def test_exclamation_detection_regression(self, baseline):
        """
        Test that exclamation detection still works.

        Baseline: 100% (1/1 detected)
        Threshold: Must detect exclamation marker
        """
        text = "¡Qué hermoso día!"
        prosody_analysis = analyze_spanish_prosody(text)

        markers_detected = len(prosody_analysis.markers)
        baseline_markers = baseline["quality"]["prosody_detection"]["exclamation"]["markers_detected"]

        print(f"\n  Current: {markers_detected} markers, Baseline: {baseline_markers} markers")

        assert markers_detected > 0, (
            f"Exclamation detection failed. Expected at least 1 marker, got {markers_detected}."
        )


class TestRegionalProcessingRegression:
    """Test that regional processing doesn't regress."""

    def test_prosodic_profile_applied(self, baseline):
        """
        Test that prosodic profile is still applied for regional processing.

        Baseline: True (profile applied)
        """
        result = process_spanish_text(
            "Che boludo, ¿vos querés tomar unos mates?",
            region="rioplatense"
        )

        # Handle both dict and object returns
        if isinstance(result, dict):
            has_profile = result.get("prosodic_profile") is not None
        else:
            has_profile = result.prosodic_profile is not None

        baseline_has_profile = baseline["quality"]["regional_processing"]["has_prosodic_profile"]

        print(f"\n  Current: {has_profile}, Baseline: {baseline_has_profile}")

        assert has_profile, "Prosodic profile not applied in regional processing."


class TestPerformanceRegression:
    """Test that performance doesn't significantly regress (latency)."""

    @pytest.mark.skipif(
        not torch.cuda.is_available(),
        reason="Performance regression tests require CUDA for consistent timing"
    )
    def test_latency_regression_short_text(self, baseline, f5tts_model):
        """
        Test that short text latency doesn't significantly increase.

        Baseline: 9.33s (CPU)
        Threshold: < 12.0s (CPU) - 30% degradation tolerance

        Note: Skipped on CPU due to high variance. Run on GPU for consistent results.
        """
        text = "¿Cómo estás hoy?"

        # Warmup
        for _ in range(2):
            f5tts_model.infer(
                ref_file="ref_audio/short.wav",
                ref_text="",
                gen_text=text,
                target_rms=0.1,
                speed=1.0,
                nfe_step=16,
            )

        # Measure
        start = time.time()
        f5tts_model.infer(
            ref_file="ref_audio/short.wav",
            ref_text="",
            gen_text=text,
            target_rms=0.1,
            speed=1.0,
            nfe_step=16,
        )
        latency = time.time() - start

        baseline_latency = baseline["performance"]["latency"]["short"]["latency_seconds"]
        threshold = 12.0

        print(f"\n  Current: {latency:.2f}s, Baseline: {baseline_latency:.2f}s, Threshold: {threshold:.2f}s")

        assert latency <= threshold, (
            f"Latency ({latency:.2f}s) exceeded threshold ({threshold:.2f}s). "
            f"Baseline was {baseline_latency:.2f}s."
        )

    def test_model_load_time_reasonable(self, baseline):
        """
        Test that model load time is reasonable (not a regression test, just sanity check).

        Baseline: 2.73s
        Threshold: < 10.0s (very generous)
        """
        device = "cuda" if torch.cuda.is_available() else "cpu"

        start = time.time()
        model = F5TTS(
            model_type="F5-TTS",
            ckpt_file="models/Spanish/model_1250000.safetensors",
            vocab_file="models/Spanish/vocab.txt",
            ode_method="euler",
            use_ema=True,
            vocoder_name="vocos",
            device=device,
        )
        load_time = time.time() - start

        baseline_load_time = baseline["performance"]["model_load_time_seconds"]
        threshold = 10.0

        print(f"\n  Current: {load_time:.2f}s, Baseline: {baseline_load_time:.2f}s, Threshold: {threshold:.2f}s")

        assert load_time <= threshold, (
            f"Model load time ({load_time:.2f}s) exceeded threshold ({threshold:.2f}s). "
            f"Baseline was {baseline_load_time:.2f}s."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
