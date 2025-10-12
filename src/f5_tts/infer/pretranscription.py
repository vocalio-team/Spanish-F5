"""
Pre-transcription utilities for reference audio.

This module provides functions to load pre-transcribed reference audio text,
eliminating the 7-8s Whisper transcription overhead on first inference.
"""

import json
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def load_pretranscribed_text(audio_path: str) -> Optional[str]:
    """
    Load pre-transcribed text for a reference audio file.

    Looks for a .json file with the same name as the audio file containing
    pre-transcribed text. If found, returns the transcription, otherwise None.

    Args:
        audio_path: Path to reference audio file

    Returns:
        Pre-transcribed text if available, None otherwise

    Example:
        >>> text = load_pretranscribed_text("ref_audio/short.wav")
        >>> if text:
        ...     print(f"Using pre-transcribed text: {text}")
        ... else:
        ...     print("No pre-transcription found, will transcribe dynamically")
    """
    audio_path = Path(audio_path)
    json_path = audio_path.with_suffix('.json')

    if not json_path.exists():
        return None

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        transcription = data.get('transcription', '').strip()

        if transcription:
            logger.info(f"✓ Loaded pre-transcribed text from {json_path.name} (saved ~5-7s)")
            return transcription
        else:
            logger.warning(f"Pre-transcription file {json_path} exists but has empty transcription")
            return None

    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse pre-transcription file {json_path}: {e}")
        return None
    except Exception as e:
        logger.warning(f"Error loading pre-transcription file {json_path}: {e}")
        return None


def has_pretranscription(audio_path: str) -> bool:
    """
    Check if a pre-transcription exists for an audio file.

    Args:
        audio_path: Path to reference audio file

    Returns:
        True if pre-transcription exists, False otherwise
    """
    audio_path = Path(audio_path)
    json_path = audio_path.with_suffix('.json')
    return json_path.exists()


def get_pretranscription_metadata(audio_path: str) -> Optional[dict]:
    """
    Get full metadata from a pre-transcription file.

    Args:
        audio_path: Path to reference audio file

    Returns:
        Dictionary with metadata (transcription, duration, model, etc.) or None
    """
    audio_path = Path(audio_path)
    json_path = audio_path.with_suffix('.json')

    if not json_path.exists():
        return None

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Error loading pre-transcription metadata from {json_path}: {e}")
        return None
