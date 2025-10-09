"""
Main TTS generation endpoints.

Handles direct TTS generation and streaming responses.
"""

import asyncio
import uuid
import time
import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from ..models import TTSRequest
from ..state import api_state
from ..config import DEFAULT_REF_AUDIO_PATH, TEMP_DIR
from ..enhancements import enhancement_processor
from ..tts_processor import tts_processor
from ..audio_compression import audio_compressor

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/tts/formats")
async def list_audio_formats():
    """
    List available audio compression formats.

    Returns information about supported output formats including bitrates,
    MIME types, and descriptions.

    Returns:
        Dictionary with available formats and their properties
    """
    formats = audio_compressor.list_formats()
    return {
        "formats": formats,
        "default": "opus",
        "recommendation": "Use 'opus' for lowest bandwidth (best for poor network coverage)",
        "bandwidth_comparison": {
            "opus_32k": "~4 KB/s (32kbps) - Excellent voice quality, minimal bandwidth",
            "mp3_64k": "~8 KB/s (64kbps) - Good voice quality, moderate bandwidth",
            "wav": "~48 KB/s - Uncompressed, maximum bandwidth"
        }
    }


@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """
    Generate speech from text using default reference audio - Real-time response with enhancements.

    This endpoint applies all configured enhancements and returns the audio file directly.
    Enhancement metadata is included in the response headers.

    Args:
        request: TTS request with text and configuration

    Returns:
        Audio file with enhancement metadata in headers
    """
    try:
        start_time = time.time()

        # Get model from cache
        try:
            f5tts_instance = api_state.get_model(request.model)
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Model {request.model} not loaded")

        # Process enhancements
        processed_text, enhancement_metadata, nfe_step, crossfade_duration = (
            enhancement_processor.process_enhancements(request, DEFAULT_REF_AUDIO_PATH)
        )

        logger.info(
            f"Enhanced TTS: nfe_step={nfe_step}, crossfade={crossfade_duration:.2f}s, "
            f"text_len={len(processed_text)}"
        )

        # Generate unique filename for output
        output_filename = f"tts_{uuid.uuid4().hex}.wav"
        output_path = f"{TEMP_DIR}/{output_filename}"

        # Process TTS synchronously
        def run_inference():
            inference_start = time.time()
            logger.info("Starting enhanced TTS inference...")

            wav, sr, spect = tts_processor.generate_audio(
                f5tts_instance,
                DEFAULT_REF_AUDIO_PATH,
                processed_text,
                request,
                nfe_step,
                crossfade_duration,
            )

            inference_time = time.time() - inference_start
            logger.info(f"Enhanced TTS inference completed in {inference_time:.2f}s")

            # Save audio file
            tts_processor.save_audio(wav, sr, output_path)
            return wav, sr, spect

        # Run inference in executor to avoid blocking
        await asyncio.get_event_loop().run_in_executor(None, run_inference)

        total_time = time.time() - start_time
        logger.info(f"Total enhanced TTS generation time: {total_time:.2f}s")

        # Compress audio based on output format
        if request.output_format and request.output_format.lower() != "wav":
            compressed_path, mime_type, file_size = audio_compressor.compress(
                output_path,
                output_format=request.output_format.lower(),
                bitrate=request.output_bitrate,
                delete_source=True
            )
            output_path = compressed_path
            output_filename = output_filename.rsplit('.', 1)[0] + '.' + audio_compressor.get_format_info(request.output_format.lower())['extension']
            logger.info(f"Audio compressed to {request.output_format} ({file_size} bytes)")
        else:
            mime_type = "audio/wav"

        # Add enhancement metadata to response headers
        headers = {
            "Content-Disposition": f"attachment; filename={output_filename}",
            "X-Enhancement-Metadata": json.dumps(enhancement_metadata),
        }

        # Return the audio file directly
        return FileResponse(output_path, media_type=mime_type, filename=output_filename, headers=headers)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in enhanced TTS: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")


@router.post("/tts/stream")
async def text_to_speech_stream(request: TTSRequest):
    """
    Generate speech from text and return audio as streaming response - Real-time.

    This endpoint streams the generated audio back to the client without enhancement metadata.

    Args:
        request: TTS request with text and configuration

    Returns:
        Streaming audio response
    """
    try:
        logger.info("Real-time streaming TTS generation")

        # Get model from cache
        try:
            f5tts_instance = api_state.get_model(request.model)
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Model {request.model} not loaded")

        # Generate unique filename for output
        output_filename = f"tts_{uuid.uuid4().hex}.wav"
        output_path = f"{TEMP_DIR}/{output_filename}"

        # Process TTS synchronously (without full enhancements for speed)
        def run_inference():
            # Calculate adjustments for short texts
            adjusted_speed, fix_duration = tts_processor.calculate_short_text_adjustments(
                request.gen_text, request.speed
            )

            wav, sr, spect = f5tts_instance.infer(
                ref_file=DEFAULT_REF_AUDIO_PATH,
                ref_text=request.ref_text,
                gen_text=request.gen_text,
                target_rms=0.1,
                cross_fade_duration=request.cross_fade_duration,
                speed=adjusted_speed,
                nfe_step=request.nfe_step,
                cfg_strength=request.cfg_strength,
                sway_sampling_coef=request.sway_sampling_coef,
                fix_duration=fix_duration,
            )

            # Save audio file
            tts_processor.save_audio(wav, sr, output_path)
            return wav, sr, spect

        # Run inference in executor to avoid blocking
        await asyncio.get_event_loop().run_in_executor(None, run_inference)

        # Compress audio based on output format
        if request.output_format and request.output_format.lower() != "wav":
            compressed_path, mime_type, file_size = audio_compressor.compress(
                output_path,
                output_format=request.output_format.lower(),
                bitrate=request.output_bitrate,
                delete_source=True
            )
            output_path = compressed_path
            output_filename = output_filename.rsplit('.', 1)[0] + '.' + audio_compressor.get_format_info(request.output_format.lower())['extension']
            logger.info(f"Audio compressed to {request.output_format} ({file_size} bytes)")
        else:
            mime_type = "audio/wav"

        # Stream the audio file
        def iterfile():
            with open(output_path, mode="rb") as file_like:
                yield from file_like
            # Clean up file after streaming
            try:
                import os

                os.unlink(output_path)
            except OSError:
                pass

        return StreamingResponse(
            iterfile(), media_type=mime_type, headers={"Content-Disposition": f"inline; filename={output_filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in streaming TTS: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")
