"""
File upload endpoints for custom reference audio.

Handles TTS generation with uploaded reference audio files.
"""

import asyncio
import uuid
import json
import logging
from typing import Dict, List

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks

from ..models import TTSRequest, TTSResponse, MultiStyleRequest
from ..state import api_state
from ..config import TEMP_DIR
from ..tts_processor import tts_processor

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/tts/upload", response_model=TTSResponse)
async def text_to_speech_with_upload(
    request: str = Form(...), ref_audio: UploadFile = File(..., description="Reference audio file"), background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Generate speech from text using uploaded reference audio.

    This endpoint accepts custom reference audio and processes TTS in the background.

    Args:
        request: JSON string with TTS request parameters
        ref_audio: Uploaded reference audio file
        background_tasks: FastAPI background task manager

    Returns:
        Task information for tracking generation progress
    """
    task_id = str(uuid.uuid4())

    # Parse JSON request from form data
    try:
        request_data = json.loads(request)
        tts_request = TTSRequest(**request_data)
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=422, detail=f"Invalid request format: {str(e)}")

    # Save uploaded reference audio
    ref_audio_path = f"{TEMP_DIR}/ref_audio_{task_id}.wav"
    with open(ref_audio_path, "wb") as f:
        content = await ref_audio.read()
        f.write(content)

    # Initialize task
    api_state.create_task(task_id, message="Starting TTS generation")

    # Start background processing
    background_tasks.add_task(process_tts_request, task_id, tts_request, ref_audio_path)

    return TTSResponse(task_id=task_id, status="processing", message="TTS generation started")


@router.post("/tts/file", response_model=TTSResponse)
async def text_to_speech_from_file(
    model: str = Form(default="F5-TTS"),
    ref_text: str = Form(default=""),
    remove_silence: bool = Form(default=False),
    speed: float = Form(default=1.0),
    ref_audio: UploadFile = File(...),
    gen_text_file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Generate speech from text file using reference audio.

    This endpoint accepts both text file and reference audio for batch processing.

    Args:
        model: Model to use
        ref_text: Reference text
        remove_silence: Remove silence flag
        speed: Speech speed
        ref_audio: Reference audio file
        gen_text_file: Text file with content to synthesize
        background_tasks: FastAPI background task manager

    Returns:
        Task information for tracking generation progress
    """
    task_id = str(uuid.uuid4())

    # Save uploaded files
    ref_audio_path = f"{TEMP_DIR}/ref_audio_{task_id}.wav"
    gen_text_path = f"{TEMP_DIR}/gen_text_{task_id}.txt"

    with open(ref_audio_path, "wb") as f:
        content = await ref_audio.read()
        f.write(content)

    with open(gen_text_path, "wb") as f:
        content = await gen_text_file.read()
        f.write(content)

    # Read text content
    with open(gen_text_path, "r", encoding="utf-8") as f:
        gen_text = f.read()

    request = TTSRequest(model=model, ref_text=ref_text, gen_text=gen_text, remove_silence=remove_silence, speed=speed)

    # Initialize task
    api_state.create_task(task_id, message="Starting TTS generation from file")

    # Start background processing
    background_tasks.add_task(process_tts_request, task_id, request, ref_audio_path)

    return TTSResponse(task_id=task_id, status="processing", message="TTS generation from file started")


@router.post("/tts/multi-style", response_model=TTSResponse)
async def multi_style_tts(
    request: MultiStyleRequest,
    ref_audio: UploadFile = File(..., description="Main reference audio"),
    voice_files: List[UploadFile] = File(..., description="Additional voice files"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Generate multi-style speech with different voices.

    This endpoint supports multiple voice styles within a single generation.

    Args:
        request: Multi-style request with voice markers
        ref_audio: Main reference audio
        voice_files: Additional voice files for different styles
        background_tasks: FastAPI background task manager

    Returns:
        Task information for tracking generation progress
    """
    task_id = str(uuid.uuid4())

    # Save main reference audio
    ref_audio_path = f"{TEMP_DIR}/ref_audio_{task_id}.wav"
    with open(ref_audio_path, "wb") as f:
        content = await ref_audio.read()
        f.write(content)

    # Save voice files
    voice_paths = {}
    for i, voice_file in enumerate(voice_files):
        voice_path = f"{TEMP_DIR}/voice_{task_id}_{i}.wav"
        with open(voice_path, "wb") as f:
            content = await voice_file.read()
            f.write(content)
        # Map to voice names (assuming order matches request.voices keys)
        voice_names = list(request.voices.keys())
        if i < len(voice_names):
            voice_paths[voice_names[i]] = voice_path

    # Initialize task
    api_state.create_task(task_id, message="Starting multi-style TTS generation")

    # Start background processing
    background_tasks.add_task(process_multi_style_request, task_id, request, ref_audio_path, voice_paths)

    return TTSResponse(task_id=task_id, status="processing", message="Multi-style TTS generation started")


# Background processing functions


async def process_tts_request(task_id: str, request: TTSRequest, ref_audio_path: str):
    """
    Process TTS request in background.

    Args:
        task_id: Unique task identifier
        request: TTS request parameters
        ref_audio_path: Path to reference audio file
    """
    try:
        # Update task status
        api_state.update_task(task_id, message="Getting model...")

        # Get model from cache
        try:
            f5tts_instance = api_state.get_model(request.model)
        except KeyError:
            api_state.fail_task(task_id, f"Model {request.model} not loaded")
            return

        # Update task status
        api_state.update_task(task_id, message="Processing audio...")

        # Generate output path
        output_path = f"{TEMP_DIR}/output_{task_id}.wav"

        # Process TTS
        def run_inference():
            # Calculate adjustments for short texts
            adjusted_speed, fix_duration = tts_processor.calculate_short_text_adjustments(
                request.gen_text, request.speed
            )

            wav, sr, spect = f5tts_instance.infer(
                ref_file=ref_audio_path,
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

        # Run inference in executor
        await asyncio.get_event_loop().run_in_executor(None, run_inference)

        # Store audio file reference
        api_state.store_audio(task_id, output_path)

        # Update task completion
        api_state.complete_task(
            task_id, message="TTS generation completed successfully", result={"audio_url": f"/audio/{task_id}", "output_path": output_path}
        )

    except Exception as e:
        logger.error(f"Error processing TTS request {task_id}: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        api_state.fail_task(task_id, f"TTS generation failed: {str(e)}")


async def process_multi_style_request(task_id: str, request: MultiStyleRequest, ref_audio_path: str, voice_paths: Dict[str, str]):
    """
    Process multi-style TTS request in background.

    Args:
        task_id: Unique task identifier
        request: Multi-style request parameters
        ref_audio_path: Path to main reference audio
        voice_paths: Dictionary mapping voice names to audio file paths
    """
    try:
        # Update task status
        api_state.update_task(task_id, message="Processing multi-style TTS...")

        # Get model from cache
        try:
            f5tts_instance = api_state.get_model(request.model)
        except KeyError:
            api_state.fail_task(task_id, f"Model {request.model} not loaded")
            return

        output_path = f"{TEMP_DIR}/multi_output_{task_id}.wav"

        # Calculate adjustments for short texts
        text_length = len(request.gen_text)
        adjusted_speed = 1.0
        fix_duration = None

        if text_length < 15:
            adjusted_speed = 0.85
            fix_duration = 8.0
            logger.info(f"Short text detected ({text_length} chars): adjusted_speed={adjusted_speed:.2f}, fix_duration={fix_duration}s")
        elif text_length < 30:
            adjusted_speed = 0.95
            fix_duration = 7.0
            logger.info(f"Medium-short text detected ({text_length} chars): adjusted_speed={adjusted_speed:.2f}, fix_duration={fix_duration}s")

        # Process multi-style TTS (simplified implementation)
        # In a full implementation, you'd parse voice markers and switch voices
        def run_inference():
            wav, sr, spect = f5tts_instance.infer(
                ref_file=ref_audio_path,
                ref_text="",  # Auto-transcribe
                gen_text=request.gen_text,
                target_rms=0.1,
                speed=adjusted_speed,
                nfe_step=32,
                cfg_strength=2.0,
                sway_sampling_coef=-1.0,
                remove_silence=request.remove_silence,
                fix_duration=fix_duration,
            )

            # Save audio file
            tts_processor.save_audio(wav, sr, output_path)
            return wav, sr, spect

        await asyncio.get_event_loop().run_in_executor(None, run_inference)

        # Store audio file reference
        api_state.store_audio(task_id, output_path)

        # Update task completion
        api_state.complete_task(
            task_id,
            message="Multi-style TTS generation completed successfully",
            result={"audio_url": f"/audio/{task_id}", "output_path": output_path},
        )

    except Exception as e:
        logger.error(f"Error processing multi-style TTS request {task_id}: {e}")
        api_state.fail_task(task_id, f"Multi-style TTS generation failed: {str(e)}")
