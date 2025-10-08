"""Crossfading algorithms for smooth audio transitions."""

import numpy as np
from enum import Enum


class CrossfadeType(Enum):
    """Available crossfade algorithms."""
    LINEAR = "linear"
    EQUAL_POWER = "equal_power"
    RAISED_COSINE = "raised_cosine"


class EqualPowerCrossfader:
    """
    Equal-power crossfading maintains constant perceived loudness.
    Industry standard for audio mixing.
    """

    def crossfade(
        self,
        audio1: np.ndarray,
        audio2: np.ndarray,
        duration: float,
        sample_rate: int
    ) -> np.ndarray:
        """
        Crossfade two audio segments using equal-power curves.

        Args:
            audio1: First audio segment
            audio2: Second audio segment
            duration: Crossfade duration in seconds
            sample_rate: Audio sample rate

        Returns:
            Crossfaded audio segment
        """
        cross_fade_samples = int(duration * sample_rate)
        cross_fade_samples = min(cross_fade_samples, len(audio1), len(audio2))

        if cross_fade_samples <= 0:
            return np.concatenate([audio1, audio2])

        # Extract overlapping regions
        overlap1 = audio1[-cross_fade_samples:]
        overlap2 = audio2[:cross_fade_samples]

        # Equal-power curves using cosine
        t = np.linspace(0, 1, cross_fade_samples)
        fade_out = np.cos(t * np.pi / 2)  # Smooth fade out
        fade_in = np.sin(t * np.pi / 2)   # Smooth fade in

        # Mix with equal power
        crossfaded = overlap1 * fade_out + overlap2 * fade_in

        # Combine segments
        return np.concatenate([
            audio1[:-cross_fade_samples],
            crossfaded,
            audio2[cross_fade_samples:]
        ])


class RaisedCosineCrossfader:
    """Raised cosine (Hann window) crossfading."""

    def crossfade(
        self,
        audio1: np.ndarray,
        audio2: np.ndarray,
        duration: float,
        sample_rate: int
    ) -> np.ndarray:
        """Crossfade using raised cosine curves."""
        cross_fade_samples = int(duration * sample_rate)
        cross_fade_samples = min(cross_fade_samples, len(audio1), len(audio2))

        if cross_fade_samples <= 0:
            return np.concatenate([audio1, audio2])

        overlap1 = audio1[-cross_fade_samples:]
        overlap2 = audio2[:cross_fade_samples]

        # Raised cosine curves
        fade_curve = np.sin(np.linspace(0, np.pi / 2, cross_fade_samples)) ** 2
        fade_out = 1 - fade_curve
        fade_in = fade_curve

        crossfaded = overlap1 * fade_out + overlap2 * fade_in

        return np.concatenate([
            audio1[:-cross_fade_samples],
            crossfaded,
            audio2[cross_fade_samples:]
        ])


class LinearCrossfader:
    """Simple linear crossfading (not recommended for audio)."""

    def crossfade(
        self,
        audio1: np.ndarray,
        audio2: np.ndarray,
        duration: float,
        sample_rate: int
    ) -> np.ndarray:
        """Crossfade using linear curves."""
        cross_fade_samples = int(duration * sample_rate)
        cross_fade_samples = min(cross_fade_samples, len(audio1), len(audio2))

        if cross_fade_samples <= 0:
            return np.concatenate([audio1, audio2])

        overlap1 = audio1[-cross_fade_samples:]
        overlap2 = audio2[:cross_fade_samples]

        fade_out = np.linspace(1, 0, cross_fade_samples)
        fade_in = np.linspace(0, 1, cross_fade_samples)

        crossfaded = overlap1 * fade_out + overlap2 * fade_in

        return np.concatenate([
            audio1[:-cross_fade_samples],
            crossfaded,
            audio2[cross_fade_samples:]
        ])


def get_crossfader(crossfade_type: CrossfadeType = CrossfadeType.EQUAL_POWER):
    """Factory function to get a crossfader instance."""
    crossfaders = {
        CrossfadeType.EQUAL_POWER: EqualPowerCrossfader,
        CrossfadeType.RAISED_COSINE: RaisedCosineCrossfader,
        CrossfadeType.LINEAR: LinearCrossfader,
    }
    return crossfaders[crossfade_type]()


def apply_edge_fades(
    audio: np.ndarray,
    fade_duration: float,
    sample_rate: int
) -> np.ndarray:
    """
    Apply gentle fade-in/out at audio edges to prevent discontinuities.

    Args:
        audio: Audio waveform
        fade_duration: Fade duration in seconds
        sample_rate: Audio sample rate

    Returns:
        Audio with edge fades applied
    """
    edge_fade_samples = int(fade_duration * sample_rate)

    if len(audio) <= 2 * edge_fade_samples:
        return audio

    result = audio.copy()

    # Fade in at start
    fade_in_curve = np.linspace(0, 1, edge_fade_samples)
    result[:edge_fade_samples] *= fade_in_curve

    # Fade out at end
    fade_out_curve = np.linspace(1, 0, edge_fade_samples)
    result[-edge_fade_samples:] *= fade_out_curve

    return result
