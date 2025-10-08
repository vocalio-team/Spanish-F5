"""Reference audio quality detection and scoring for TTS."""

import numpy as np
import torch
import torchaudio
from dataclasses import dataclass
from typing import Tuple, List, Dict
from enum import Enum


class QualityLevel(Enum):
    """Audio quality levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNACCEPTABLE = "unacceptable"


@dataclass
class QualityMetrics:
    """Audio quality metrics."""
    overall_score: float  # 0-100
    quality_level: QualityLevel
    snr_db: float  # Signal-to-noise ratio
    clipping_rate: float  # Percentage of clipped samples
    silence_ratio: float  # Percentage of silence
    dynamic_range_db: float  # Dynamic range
    spectral_flatness: float  # Spectral flatness (0-1)
    issues: List[str]  # List of detected issues
    recommendations: List[str]  # Suggestions for improvement


class AudioQualityAnalyzer:
    """Analyze reference audio quality for TTS."""

    # Quality thresholds
    SNR_EXCELLENT = 35.0  # dB
    SNR_GOOD = 25.0
    SNR_FAIR = 15.0
    SNR_POOR = 10.0

    CLIPPING_ACCEPTABLE = 0.001  # 0.1%
    CLIPPING_FAIR = 0.01  # 1%
    CLIPPING_POOR = 0.05  # 5%

    SILENCE_ACCEPTABLE = 0.3  # 30%
    SILENCE_FAIR = 0.5  # 50%
    SILENCE_POOR = 0.7  # 70%

    DR_EXCELLENT = 40.0  # dB
    DR_GOOD = 30.0
    DR_FAIR = 20.0
    DR_POOR = 15.0

    def __init__(self, sample_rate: int = 24000):
        """
        Initialize quality analyzer.

        Args:
            sample_rate: Target sample rate for analysis
        """
        self.sample_rate = sample_rate

    def analyze(self, audio: torch.Tensor, sr: int) -> QualityMetrics:
        """
        Analyze audio quality.

        Args:
            audio: Audio waveform (1D tensor)
            sr: Sample rate

        Returns:
            Quality metrics with score and recommendations
        """
        # Ensure audio is 1D
        if audio.dim() > 1:
            audio = audio.squeeze()

        # Resample if needed
        if sr != self.sample_rate:
            audio = torchaudio.functional.resample(audio, sr, self.sample_rate)

        # Convert to numpy for analysis
        audio_np = audio.cpu().numpy()

        # Calculate metrics
        snr_db = self._calculate_snr(audio_np)
        clipping_rate = self._calculate_clipping_rate(audio_np)
        silence_ratio = self._calculate_silence_ratio(audio_np)
        dynamic_range_db = self._calculate_dynamic_range(audio_np)
        spectral_flatness = self._calculate_spectral_flatness(audio_np)

        # Detect issues and generate recommendations
        issues = []
        recommendations = []

        # SNR analysis
        if snr_db < self.SNR_POOR:
            issues.append(f"Very low SNR ({snr_db:.1f} dB) - noisy audio")
            recommendations.append("Record in a quieter environment or use noise reduction")
        elif snr_db < self.SNR_FAIR:
            issues.append(f"Low SNR ({snr_db:.1f} dB) - noticeable background noise")
            recommendations.append("Reduce background noise if possible")

        # Clipping analysis
        if clipping_rate > self.CLIPPING_POOR:
            issues.append(f"Severe clipping ({clipping_rate*100:.1f}%) - distorted audio")
            recommendations.append("Reduce recording volume to prevent clipping")
        elif clipping_rate > self.CLIPPING_FAIR:
            issues.append(f"Moderate clipping ({clipping_rate*100:.1f}%)")
            recommendations.append("Lower input gain slightly")

        # Silence analysis
        if silence_ratio > self.SILENCE_POOR:
            issues.append(f"Too much silence ({silence_ratio*100:.0f}%)")
            recommendations.append("Trim excessive silence from beginning/end")
        elif silence_ratio > self.SILENCE_FAIR:
            issues.append(f"High silence ratio ({silence_ratio*100:.0f}%)")
            recommendations.append("Consider trimming some silence")

        # Dynamic range analysis
        if dynamic_range_db < self.DR_POOR:
            issues.append(f"Very low dynamic range ({dynamic_range_db:.1f} dB)")
            recommendations.append("Audio may be over-compressed or too quiet")
        elif dynamic_range_db < self.DR_FAIR:
            issues.append(f"Low dynamic range ({dynamic_range_db:.1f} dB)")

        # Spectral flatness (voice quality indicator)
        if spectral_flatness > 0.5:
            issues.append(f"High spectral flatness - may not be clear speech")
            recommendations.append("Ensure audio contains clear, natural speech")

        # Calculate overall score (0-100)
        score_components = {
            'snr': self._score_snr(snr_db),
            'clipping': self._score_clipping(clipping_rate),
            'silence': self._score_silence(silence_ratio),
            'dynamic_range': self._score_dynamic_range(dynamic_range_db),
            'spectral': self._score_spectral_flatness(spectral_flatness),
        }

        # Weighted average
        weights = {
            'snr': 0.35,
            'clipping': 0.25,
            'silence': 0.15,
            'dynamic_range': 0.15,
            'spectral': 0.10,
        }

        overall_score = sum(score_components[k] * weights[k] for k in weights.keys())

        # Determine quality level
        if overall_score >= 85:
            quality_level = QualityLevel.EXCELLENT
        elif overall_score >= 70:
            quality_level = QualityLevel.GOOD
        elif overall_score >= 50:
            quality_level = QualityLevel.FAIR
        elif overall_score >= 30:
            quality_level = QualityLevel.POOR
        else:
            quality_level = QualityLevel.UNACCEPTABLE

        # Add general recommendations based on quality level
        if quality_level in [QualityLevel.POOR, QualityLevel.UNACCEPTABLE]:
            recommendations.insert(0, "⚠️ Audio quality is too low for good TTS results")
            recommendations.append("Consider re-recording with better equipment or conditions")

        return QualityMetrics(
            overall_score=overall_score,
            quality_level=quality_level,
            snr_db=snr_db,
            clipping_rate=clipping_rate,
            silence_ratio=silence_ratio,
            dynamic_range_db=dynamic_range_db,
            spectral_flatness=spectral_flatness,
            issues=issues,
            recommendations=recommendations,
        )

    def _calculate_snr(self, audio: np.ndarray) -> float:
        """Calculate signal-to-noise ratio."""
        # Simple energy-based SNR estimation
        # Assumes noise floor is in quietest 10% of frames

        # Frame the audio (25ms frames)
        frame_length = int(0.025 * self.sample_rate)
        hop_length = frame_length // 2

        frames = []
        for i in range(0, len(audio) - frame_length, hop_length):
            frame = audio[i:i+frame_length]
            frames.append(np.sqrt(np.mean(frame**2)))  # RMS

        frames = np.array(frames)

        # Sort by energy
        sorted_frames = np.sort(frames)

        # Noise estimate: average of quietest 10%
        noise_count = max(1, len(sorted_frames) // 10)
        noise_level = np.mean(sorted_frames[:noise_count])

        # Signal estimate: average of loudest 50%
        signal_count = len(sorted_frames) // 2
        signal_level = np.mean(sorted_frames[-signal_count:])

        # Avoid division by zero
        if noise_level < 1e-10:
            noise_level = 1e-10

        snr = 20 * np.log10(signal_level / noise_level)

        return float(snr)

    def _calculate_clipping_rate(self, audio: np.ndarray) -> float:
        """Calculate percentage of clipped samples."""
        # Samples near -1.0 or +1.0 are clipped
        threshold = 0.99
        clipped = np.sum(np.abs(audio) > threshold)
        return clipped / len(audio)

    def _calculate_silence_ratio(self, audio: np.ndarray) -> float:
        """Calculate percentage of silence."""
        # Simple energy-based silence detection
        frame_length = int(0.025 * self.sample_rate)
        hop_length = frame_length // 2

        silent_frames = 0
        total_frames = 0

        for i in range(0, len(audio) - frame_length, hop_length):
            frame = audio[i:i+frame_length]
            rms = np.sqrt(np.mean(frame**2))

            # Silence threshold (adaptive based on max amplitude)
            max_amplitude = np.max(np.abs(audio))
            silence_threshold = max_amplitude * 0.02  # 2% of max

            if rms < silence_threshold:
                silent_frames += 1
            total_frames += 1

        if total_frames == 0:
            return 0.0

        return silent_frames / total_frames

    def _calculate_dynamic_range(self, audio: np.ndarray) -> float:
        """Calculate dynamic range in dB."""
        # Frame-based RMS
        frame_length = int(0.025 * self.sample_rate)
        hop_length = frame_length // 2

        rms_values = []
        for i in range(0, len(audio) - frame_length, hop_length):
            frame = audio[i:i+frame_length]
            rms = np.sqrt(np.mean(frame**2))
            if rms > 1e-10:  # Avoid log of zero
                rms_values.append(rms)

        if not rms_values:
            return 0.0

        # Dynamic range: difference between loudest and quietest frames
        max_rms = np.max(rms_values)
        # Use 5th percentile instead of minimum to avoid outliers
        min_rms = np.percentile(rms_values, 5)

        if min_rms < 1e-10:
            min_rms = 1e-10

        dr = 20 * np.log10(max_rms / min_rms)

        return float(dr)

    def _calculate_spectral_flatness(self, audio: np.ndarray) -> float:
        """Calculate spectral flatness (measure of noisiness)."""
        # Compute FFT
        n_fft = 2048
        hop_length = n_fft // 2

        flatness_values = []

        for i in range(0, len(audio) - n_fft, hop_length):
            frame = audio[i:i+n_fft]
            spectrum = np.abs(np.fft.rfft(frame))

            # Avoid log of zero
            spectrum = spectrum + 1e-10

            # Spectral flatness: geometric mean / arithmetic mean
            geometric_mean = np.exp(np.mean(np.log(spectrum)))
            arithmetic_mean = np.mean(spectrum)

            flatness = geometric_mean / arithmetic_mean
            flatness_values.append(flatness)

        return float(np.mean(flatness_values))

    def _score_snr(self, snr_db: float) -> float:
        """Score SNR (0-100)."""
        if snr_db >= self.SNR_EXCELLENT:
            return 100.0
        elif snr_db >= self.SNR_GOOD:
            # Linear interpolation
            return 75 + 25 * (snr_db - self.SNR_GOOD) / (self.SNR_EXCELLENT - self.SNR_GOOD)
        elif snr_db >= self.SNR_FAIR:
            return 50 + 25 * (snr_db - self.SNR_FAIR) / (self.SNR_GOOD - self.SNR_FAIR)
        elif snr_db >= self.SNR_POOR:
            return 25 + 25 * (snr_db - self.SNR_POOR) / (self.SNR_FAIR - self.SNR_POOR)
        else:
            return max(0, 25 * snr_db / self.SNR_POOR)

    def _score_clipping(self, clipping_rate: float) -> float:
        """Score clipping rate (0-100)."""
        if clipping_rate <= self.CLIPPING_ACCEPTABLE:
            return 100.0
        elif clipping_rate <= self.CLIPPING_FAIR:
            return 75 - 25 * (clipping_rate - self.CLIPPING_ACCEPTABLE) / (self.CLIPPING_FAIR - self.CLIPPING_ACCEPTABLE)
        elif clipping_rate <= self.CLIPPING_POOR:
            return 50 - 25 * (clipping_rate - self.CLIPPING_FAIR) / (self.CLIPPING_POOR - self.CLIPPING_FAIR)
        else:
            return max(0, 50 * (1 - clipping_rate))

    def _score_silence(self, silence_ratio: float) -> float:
        """Score silence ratio (0-100)."""
        if silence_ratio <= self.SILENCE_ACCEPTABLE:
            return 100.0
        elif silence_ratio <= self.SILENCE_FAIR:
            return 75 - 25 * (silence_ratio - self.SILENCE_ACCEPTABLE) / (self.SILENCE_FAIR - self.SILENCE_ACCEPTABLE)
        elif silence_ratio <= self.SILENCE_POOR:
            return 50 - 25 * (silence_ratio - self.SILENCE_FAIR) / (self.SILENCE_POOR - self.SILENCE_FAIR)
        else:
            return max(0, 50 * (1 - silence_ratio))

    def _score_dynamic_range(self, dr_db: float) -> float:
        """Score dynamic range (0-100)."""
        if dr_db >= self.DR_EXCELLENT:
            return 100.0
        elif dr_db >= self.DR_GOOD:
            return 75 + 25 * (dr_db - self.DR_GOOD) / (self.DR_EXCELLENT - self.DR_GOOD)
        elif dr_db >= self.DR_FAIR:
            return 50 + 25 * (dr_db - self.DR_FAIR) / (self.DR_GOOD - self.DR_FAIR)
        elif dr_db >= self.DR_POOR:
            return 25 + 25 * (dr_db - self.DR_POOR) / (self.DR_FAIR - self.DR_POOR)
        else:
            return max(0, 25 * dr_db / self.DR_POOR)

    def _score_spectral_flatness(self, flatness: float) -> float:
        """Score spectral flatness (0-100)."""
        # Lower flatness is better for speech (more harmonic structure)
        if flatness <= 0.1:
            return 100.0
        elif flatness <= 0.3:
            return 75 - 25 * (flatness - 0.1) / 0.2
        elif flatness <= 0.5:
            return 50 - 25 * (flatness - 0.3) / 0.2
        else:
            return max(0, 50 * (1 - flatness))


def analyze_audio_quality(audio_path: str) -> QualityMetrics:
    """
    Convenience function to analyze audio quality from file.

    Args:
        audio_path: Path to audio file

    Returns:
        Quality metrics
    """
    audio, sr = torchaudio.load(audio_path)
    analyzer = AudioQualityAnalyzer(sample_rate=sr)
    return analyzer.analyze(audio[0], sr)


def print_quality_report(metrics: QualityMetrics):
    """
    Print formatted quality report.

    Args:
        metrics: Quality metrics to display
    """
    print("=" * 60)
    print("AUDIO QUALITY REPORT")
    print("=" * 60)
    print()

    # Overall score with color coding
    quality_emoji = {
        QualityLevel.EXCELLENT: "🟢",
        QualityLevel.GOOD: "🟢",
        QualityLevel.FAIR: "🟡",
        QualityLevel.POOR: "🟠",
        QualityLevel.UNACCEPTABLE: "🔴",
    }

    emoji = quality_emoji[metrics.quality_level]
    print(f"{emoji} Overall Quality: {metrics.quality_level.value.upper()}")
    print(f"   Score: {metrics.overall_score:.1f}/100")
    print()

    # Detailed metrics
    print("Detailed Metrics:")
    print(f"  • SNR: {metrics.snr_db:.1f} dB")
    print(f"  • Clipping: {metrics.clipping_rate*100:.2f}%")
    print(f"  • Silence: {metrics.silence_ratio*100:.1f}%")
    print(f"  • Dynamic Range: {metrics.dynamic_range_db:.1f} dB")
    print(f"  • Spectral Flatness: {metrics.spectral_flatness:.3f}")
    print()

    # Issues
    if metrics.issues:
        print("⚠️  Issues Detected:")
        for issue in metrics.issues:
            print(f"  • {issue}")
        print()

    # Recommendations
    if metrics.recommendations:
        print("💡 Recommendations:")
        for rec in metrics.recommendations:
            print(f"  • {rec}")
        print()

    print("=" * 60)
