"""
Text and audio analysis endpoints.

Provides analysis capabilities without TTS generation.
"""

import os
import uuid
import logging

from fastapi import APIRouter, HTTPException, UploadFile, File
import torchaudio

from f5_tts.text import normalize_spanish_text, analyze_spanish_prosody, analyze_breath_pauses
from f5_tts.audio import AudioQualityAnalyzer

from ..models import AnalysisRequest
from ..config import TEMP_DIR

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/analyze")
async def analyze_text(request: AnalysisRequest):
    """
    Analyze text without generating speech - useful for preprocessing and validation.

    This endpoint applies configured text analysis including normalization, prosody,
    and breath patterns without performing TTS generation.

    Args:
        request: Analysis request with text and flags

    Returns:
        Dictionary with analysis results
    """
    try:
        result = {
            "original_text": request.text,
            "normalized_text": None,
            "prosody_analysis": None,
            "breath_analysis": None,
        }

        processed_text = request.text

        # 1. Text normalization
        if request.normalize_text:
            try:
                processed_text = normalize_spanish_text(processed_text)
                result["normalized_text"] = processed_text
            except Exception as e:
                result["normalization_error"] = str(e)

        # 2. Prosody analysis
        if request.analyze_prosody:
            try:
                prosody_analysis = analyze_spanish_prosody(processed_text)
                result["prosody_analysis"] = {
                    "markers": [
                        {
                            "type": str(m.type),
                            "position": m.position,
                            "text": m.text,
                            "intensity": str(m.intensity) if hasattr(m, "intensity") else None,
                        }
                        for m in prosody_analysis.markers
                    ],
                    "marked_text": prosody_analysis.marked_text,
                    "sentence_count": len(prosody_analysis.sentence_boundaries),
                    "breath_points": len(prosody_analysis.breath_points),
                    "stress_points": len(prosody_analysis.stress_points),
                    "pitch_contours": prosody_analysis.pitch_contours,
                }
            except Exception as e:
                result["prosody_error"] = str(e)

        # 3. Breath and pause analysis
        if request.analyze_breath_pauses:
            try:
                breath_analysis = analyze_breath_pauses(processed_text)
                result["breath_analysis"] = {
                    "pauses": [
                        {
                            "position": p.position,
                            "type": p.type.value,
                            "duration_ms": p.duration_ms,
                            "is_breath_point": p.is_breath_point,
                            "context": p.context,
                        }
                        for p in breath_analysis.pauses
                    ],
                    "breath_points": breath_analysis.breath_points,
                    "avg_pause_interval": breath_analysis.avg_pause_interval,
                    "estimated_duration": breath_analysis.total_duration_estimate,
                }
            except Exception as e:
                result["breath_error"] = str(e)

        return result

    except Exception as e:
        logger.error(f"Error in text analysis: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Text analysis failed: {str(e)}")


@router.post("/audio/quality")
async def check_audio_quality(audio_file: UploadFile = File(..., description="Audio file to analyze")):
    """
    Check audio quality without performing TTS - useful for validating reference audio.

    This endpoint analyzes audio file quality including SNR, clipping, dynamic range, etc.

    Args:
        audio_file: Audio file to analyze

    Returns:
        Dictionary with quality metrics and recommendations
    """
    try:
        # Save uploaded audio
        temp_path = f"{TEMP_DIR}/quality_check_{uuid.uuid4().hex}.wav"
        with open(temp_path, "wb") as f:
            content = await audio_file.read()
            f.write(content)

        # Load and analyze
        audio, sr = torchaudio.load(temp_path)
        quality_analyzer = AudioQualityAnalyzer()
        quality_metrics = quality_analyzer.analyze(audio, sr)

        # Clean up
        os.remove(temp_path)

        return {
            "filename": audio_file.filename,
            "overall_score": quality_metrics.overall_score,
            "quality_level": quality_metrics.quality_level.value,
            "metrics": {
                "snr_db": quality_metrics.snr_db,
                "clipping_rate": quality_metrics.clipping_rate,
                "silence_ratio": quality_metrics.silence_ratio,
                "dynamic_range_db": quality_metrics.dynamic_range_db,
                "spectral_flatness": quality_metrics.spectral_flatness,
            },
            "issues": quality_metrics.issues,
            "recommendations": quality_metrics.recommendations,
        }

    except Exception as e:
        logger.error(f"Error in audio quality check: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Audio quality check failed: {str(e)}")
