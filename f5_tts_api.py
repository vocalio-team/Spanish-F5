from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import os
import asyncio
import uuid
import logging
from datetime import datetime
import json

# Import F5-TTS modules
import sys
sys.path.append('src')

# Use the F5TTS API class to avoid argparse conflicts
from f5_tts.api import F5TTS
import torchaudio
import torch

# Import enhancement modules
from f5_tts.text import (
    normalize_spanish_text,
    analyze_spanish_prosody,
    analyze_breath_pauses
)
from f5_tts.audio import AudioQualityAnalyzer, QualityLevel
from f5_tts.core import get_adaptive_nfe_step, get_adaptive_crossfade_duration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Performance optimization flags
ENABLE_TORCH_COMPILE = os.getenv("ENABLE_TORCH_COMPILE", "true").lower() == "true"
ENABLE_CUDNN_BENCHMARK = os.getenv("ENABLE_CUDNN_BENCHMARK", "true").lower() == "true"
TORCH_MATMUL_PRECISION = os.getenv("TORCH_MATMUL_PRECISION", "high")  # "high" or "highest"

app = FastAPI(
    title="F5-TTS REST API",
    description="REST API for F5-TTS Text-to-Speech inference operations",
    version="1.0.0"
)

# Global model storage
models_cache = {}
vocoder_cache = {}
model_loading_status = {"loading": False, "loaded": False, "error": None}

# Request/Response Models
class TTSRequest(BaseModel):
    model: str = Field(default="F5-TTS", description="Model to use: F5-TTS or E2-TTS")
    ref_text: str = Field(description="Reference text (leave empty for auto-transcription)")
    gen_text: str = Field(description="Text to generate speech for")
    remove_silence: bool = Field(default=False, description="Remove silence from output")
    speed: float = Field(default=1.0, description="Speech speed multiplier")
    cross_fade_duration: float = Field(default=0.8, description="Cross-fade duration for chunks (0.8s for smoother audio)")
    nfe_step: int = Field(default=16, description="Number of function evaluations (lower = faster, default was 32)")
    cfg_strength: float = Field(default=2.0, description="Classifier-free guidance strength")
    sway_sampling_coef: float = Field(default=-1.0, description="Sway sampling coefficient")
    seed: int = Field(default=-1, description="Random seed (-1 for random)")
    vocoder_name: str = Field(default="vocos", description="Vocoder to use")
    output_format: str = Field(default="wav", description="Output audio format")
    use_fp16: bool = Field(default=True, description="Use FP16/BF16 for faster inference (recommended)")

    # Enhancement features (Phase 1-4 improvements)
    normalize_text: bool = Field(default=True, description="Apply Spanish text normalization (numbers, dates, etc.)")
    analyze_prosody: bool = Field(default=True, description="Analyze and enhance prosody (questions, exclamations, etc.)")
    analyze_breath_pauses: bool = Field(default=True, description="Analyze breath and pause patterns")
    adaptive_nfe: bool = Field(default=True, description="Automatically adjust NFE steps based on text complexity")
    adaptive_crossfade: bool = Field(default=True, description="Automatically adjust crossfade duration based on audio characteristics")
    check_audio_quality: bool = Field(default=True, description="Check reference audio quality and provide warnings")

class TTSResponse(BaseModel):
    task_id: str
    status: str
    message: str
    audio_url: Optional[str] = None
    duration: Optional[float] = None

    # Enhancement metadata
    normalized_text: Optional[str] = None
    prosody_analysis: Optional[Dict[str, Any]] = None
    breath_analysis: Optional[Dict[str, Any]] = None
    audio_quality: Optional[Dict[str, Any]] = None
    nfe_step_used: Optional[int] = None
    crossfade_duration_used: Optional[float] = None

class TaskStatus(BaseModel):
    task_id: str
    status: str
    progress: Optional[float] = None
    message: str
    result: Optional[Dict[str, Any]] = None
    created_at: str
    completed_at: Optional[str] = None

class MultiStyleRequest(BaseModel):
    model: str = Field(default="F5-TTS", description="Model to use")
    gen_text: str = Field(description="Text with voice markers like [main], [voice1], etc.")
    voices: Dict[str, Dict[str, str]] = Field(description="Voice configurations")
    remove_silence: bool = Field(default=True, description="Remove silence from output")
    output_format: str = Field(default="wav", description="Output audio format")

# Task storage (in production, use Redis or database)
tasks = {}
audio_files = {}

# Startup event to load default models
@app.on_event("startup")
async def startup_event():
    """Load default models on startup"""
    try:
        model_loading_status["loading"] = True
        logger.info("Loading default F5-TTS model...")
        
        # Detect the best available device
        import torch
        if torch.cuda.is_available():
            device = "cuda"
            logger.info("CUDA is available, using GPU")

            # Apply CUDA optimizations
            if ENABLE_CUDNN_BENCHMARK:
                torch.backends.cudnn.benchmark = True
                logger.info("Enabled cuDNN benchmark mode for optimal kernel selection")

            # Set matmul precision for faster computation
            torch.set_float32_matmul_precision(TORCH_MATMUL_PRECISION)
            logger.info(f"Set matmul precision to: {TORCH_MATMUL_PRECISION}")

            # Enable TF32 on Ampere+ GPUs for faster matmul
            if torch.cuda.get_device_properties(0).major >= 8:
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True
                logger.info("Enabled TF32 for Ampere+ GPU")
        else:
            device = "cpu"
            logger.info("CUDA not available, using CPU")

        # Use the F5TTS class with explicit local model paths
        # Don't use local_path for vocoder, let it download from HF
        f5tts = F5TTS(
            model_type="F5-TTS",
            ckpt_file="/app/models/Spanish/model_1200000.safetensors",
            vocab_file="/app/models/Spanish/vocab.txt",
            ode_method="euler",
            use_ema=True,
            vocoder_name="vocos",
            local_path=None,  # Let vocoder download from HF
            device=device
        )
        models_cache["F5-TTS"] = f5tts

        # Warmup inference to optimize CUDA kernels
        logger.info("Running warmup inference to optimize CUDA kernels...")
        try:
            warmup_wav, _, _ = f5tts.infer(
                ref_file="ref_audio/short.wav",
                ref_text="",
                gen_text="Hola",
                nfe_step=8,  # Use fewer steps for warmup
                speed=1.0,
                remove_silence=False
            )
            logger.info("Warmup inference completed successfully")
        except Exception as warmup_err:
            logger.warning(f"Warmup inference failed (non-critical): {warmup_err}")

        # E2-TTS model loading disabled (model architecture mismatch)
        # logger.info("Loading E2-TTS model...")
        # e2tts = F5TTS(
        #     model_type="E2-TTS",
        #     ckpt_file="/app/models/E2TTS_Base/model_1200000.safetensors",
        #     vocab_file="",
        #     ode_method="euler",
        #     use_ema=True,
        #     vocoder_name="vocos",
        #     local_path=None,  # Let vocoder download from HF
        #     device=device
        # )
        # models_cache["E2-TTS"] = e2tts

        model_loading_status["loading"] = False
        model_loading_status["loaded"] = True
        logger.info(f"Models loaded successfully: {list(models_cache.keys())}")
        
    except Exception as e:
        model_loading_status["loading"] = False
        model_loading_status["error"] = str(e)
        logger.error(f"Failed to load models: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "F5-TTS REST API - Enhanced with Spanish Quality Improvements",
        "version": "2.0.0",
        "enhancements": {
            "text_normalization": "Convert numbers, dates, times to spoken Spanish",
            "prosody_analysis": "Detect questions, exclamations, emphasis, pauses",
            "breath_pause_modeling": "Natural breathing and pause patterns",
            "adaptive_nfe": "Automatic quality optimization based on text complexity",
            "adaptive_crossfade": "Dynamic crossfade duration for smoother audio",
            "audio_quality_check": "Reference audio quality validation"
        },
        "endpoints": {
            "tts": {
                "path": "/tts",
                "description": "Generate speech with all enhancements enabled by default"
            },
            "tts_stream": {
                "path": "/tts/stream",
                "description": "Stream speech output"
            },
            "tts_upload": {
                "path": "/tts/upload",
                "description": "Upload custom reference audio"
            },
            "tts_file": {
                "path": "/tts/file",
                "description": "Generate from text file"
            },
            "analyze": {
                "path": "/analyze",
                "description": "Analyze text without generating speech"
            },
            "audio_quality": {
                "path": "/audio/quality",
                "description": "Check audio quality without TTS"
            },
            "status": {
                "path": "/tasks/{task_id}",
                "description": "Get task status"
            },
            "models": {
                "path": "/models",
                "description": "List available models"
            },
            "health": {
                "path": "/health",
                "description": "Health check"
            }
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "models_loaded": list(models_cache.keys()),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/models")
async def list_models():
    """List available models"""
    return {
        "available_models": ["F5-TTS", "E2-TTS"],
        "loaded_models": list(models_cache.keys()),
        "vocoders": ["vocos", "bigvgan"]
    }

@app.post("/tts")
async def text_to_speech(
    request: TTSRequest
):
    """
    Generate speech from text using default reference audio - Real-time response with enhancements
    """
    try:
        import time
        start_time = time.time()

        # Use shorter reference audio for faster inference
        ref_audio_path = "ref_audio/short.wav"

        # Get model from cache
        if request.model not in models_cache:
            raise HTTPException(status_code=400, detail=f"Model {request.model} not loaded")

        f5tts_instance = models_cache[request.model]

        # Enhancement metadata
        enhancement_metadata = {}
        processed_text = request.gen_text

        # 1. Check reference audio quality
        if request.check_audio_quality:
            try:
                audio, sr = torchaudio.load(ref_audio_path)
                quality_analyzer = AudioQualityAnalyzer()
                quality_metrics = quality_analyzer.analyze(audio, sr)

                enhancement_metadata["audio_quality"] = {
                    "overall_score": quality_metrics.overall_score,
                    "quality_level": quality_metrics.quality_level.value,
                    "snr_db": quality_metrics.snr_db,
                    "issues": quality_metrics.issues,
                    "recommendations": quality_metrics.recommendations
                }

                # Warn if quality is poor
                if quality_metrics.quality_level in [QualityLevel.POOR, QualityLevel.UNACCEPTABLE]:
                    logger.warning(f"Reference audio quality is {quality_metrics.quality_level.value}: {quality_metrics.issues}")
            except Exception as e:
                logger.warning(f"Audio quality check failed: {e}")

        # 2. Apply text normalization
        if request.normalize_text:
            try:
                processed_text = normalize_spanish_text(processed_text)
                enhancement_metadata["normalized_text"] = processed_text
                logger.info(f"Text normalized: {request.gen_text[:50]}... -> {processed_text[:50]}...")
            except Exception as e:
                logger.warning(f"Text normalization failed: {e}")

        # 3. Analyze prosody
        if request.analyze_prosody:
            try:
                prosody_analysis = analyze_spanish_prosody(processed_text)
                enhancement_metadata["prosody_analysis"] = {
                    "num_questions": sum(1 for m in prosody_analysis.markers if "QUESTION" in str(m.type)),
                    "num_exclamations": sum(1 for m in prosody_analysis.markers if "EXCLAMATION" in str(m.type)),
                    "num_pauses": sum(1 for m in prosody_analysis.markers if "PAUSE" in str(m.type)),
                    "sentence_count": len(prosody_analysis.sentence_boundaries),
                    "breath_points": len(prosody_analysis.breath_points),
                    "marked_text": prosody_analysis.marked_text
                }
                logger.info(f"Prosody analyzed: {len(prosody_analysis.markers)} markers detected")
            except Exception as e:
                logger.warning(f"Prosody analysis failed: {e}")

        # 4. Analyze breath and pauses
        if request.analyze_breath_pauses:
            try:
                breath_analysis = analyze_breath_pauses(processed_text)
                enhancement_metadata["breath_analysis"] = {
                    "total_pauses": len(breath_analysis.pauses),
                    "breath_points": len(breath_analysis.breath_points),
                    "avg_pause_interval": breath_analysis.avg_pause_interval,
                    "estimated_duration": breath_analysis.total_duration_estimate
                }
                logger.info(f"Breath analysis: {len(breath_analysis.pauses)} pauses, {len(breath_analysis.breath_points)} breath points")
            except Exception as e:
                logger.warning(f"Breath analysis failed: {e}")

        # 5. Adaptive NFE steps
        nfe_step = request.nfe_step
        if request.adaptive_nfe:
            try:
                nfe_step = get_adaptive_nfe_step(processed_text, request.nfe_step)
                enhancement_metadata["nfe_step_used"] = nfe_step
                logger.info(f"Adaptive NFE: {request.nfe_step} -> {nfe_step}")
            except Exception as e:
                logger.warning(f"Adaptive NFE failed: {e}")

        # 6. Adaptive crossfade duration
        crossfade_duration = request.cross_fade_duration
        if request.adaptive_crossfade:
            try:
                # Use default adaptive crossfade (will be refined per chunk in actual processing)
                crossfade_duration = get_adaptive_crossfade_duration()
                enhancement_metadata["crossfade_duration_used"] = crossfade_duration
                logger.info(f"Adaptive crossfade: {request.cross_fade_duration} -> {crossfade_duration}")
            except Exception as e:
                logger.warning(f"Adaptive crossfade failed: {e}")

        logger.info(f"Enhanced TTS: nfe_step={nfe_step}, crossfade={crossfade_duration:.2f}s, text_len={len(processed_text)}")

        # Generate unique filename for output
        output_filename = f"tts_{uuid.uuid4().hex}.wav"
        output_path = f"/tmp/{output_filename}"

        # Adjust parameters for very short texts to prevent audio chopping
        adjusted_speed = request.speed
        fix_duration = None

        # For very short texts (< 15 chars), slow down speech and pad text for better audio quality
        text_length = len(processed_text)
        if text_length < 15:
            # Slow down speed for better clarity (e.g., "Comida" becomes more natural)
            adjusted_speed = max(0.7, request.speed * 0.85)
            # Pad short text with pauses to get minimum 2 seconds of actual speech
            # Note: F5-TTS trims ref_audio from generated audio, so we need longer duration
            # Reference audio is ~6 seconds, so fix_duration needs to be ref_duration + desired_output
            fix_duration = 8.0  # 6s (ref) + 2s (desired output) = 8s total
            logger.info(f"Short text detected ({text_length} chars): adjusted_speed={adjusted_speed:.2f}, fix_duration={fix_duration}s")
        elif text_length < 30:
            # Slightly slower for short texts
            adjusted_speed = max(0.85, request.speed * 0.95)
            # Medium padding
            fix_duration = 7.0  # 6s (ref) + 1s (desired output) = 7s total
            logger.info(f"Medium-short text detected ({text_length} chars): adjusted_speed={adjusted_speed:.2f}, fix_duration={fix_duration}s")

        # Process TTS synchronously
        def run_inference():
            inference_start = time.time()
            logger.info("Starting enhanced TTS inference...")
            wav, sr, spect = f5tts_instance.infer(
                ref_file=ref_audio_path,
                ref_text=request.ref_text,
                gen_text=processed_text,  # Use enhanced text
                target_rms=0.1,
                cross_fade_duration=crossfade_duration,  # Use adaptive crossfade
                speed=adjusted_speed,  # Use adjusted speed for short texts
                nfe_step=nfe_step,  # Use adaptive NFE
                cfg_strength=request.cfg_strength,
                sway_sampling_coef=request.sway_sampling_coef,
                fix_duration=fix_duration  # Set minimum duration for short texts
            )
            inference_time = time.time() - inference_start
            logger.info(f"Enhanced TTS inference completed in {inference_time:.2f}s")

            # Save to file (convert numpy array to torch tensor if needed)
            if isinstance(wav, torch.Tensor):
                wav_tensor = wav
            else:
                wav_tensor = torch.from_numpy(wav)
            torchaudio.save(output_path, wav_tensor.unsqueeze(0).cpu(), sr)
            return wav, sr, spect

        # Run inference in executor to avoid blocking
        await asyncio.get_event_loop().run_in_executor(None, run_inference)

        total_time = time.time() - start_time
        logger.info(f"Total enhanced TTS generation time: {total_time:.2f}s")

        # Add enhancement metadata to response headers
        headers = {
            "Content-Disposition": f"attachment; filename={output_filename}",
            "X-Enhancement-Metadata": json.dumps(enhancement_metadata)
        }

        # Return the audio file directly
        return FileResponse(
            output_path,
            media_type="audio/wav",
            filename=output_filename,
            headers=headers
        )

    except Exception as e:
        logger.error(f"Error in enhanced TTS: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")

@app.post("/tts/stream")
async def text_to_speech_stream(
    request: TTSRequest
):
    """
    Generate speech from text and return audio as streaming response - Real-time
    """
    try:
        # Use shorter reference audio for faster inference
        ref_audio_path = "ref_audio/short.wav"
        logger.info("Real-time streaming TTS generation with short ref_audio")

        # Get model from cache
        if request.model not in models_cache:
            raise HTTPException(status_code=400, detail=f"Model {request.model} not loaded")

        f5tts_instance = models_cache[request.model]

        # Generate unique filename for output
        output_filename = f"tts_{uuid.uuid4().hex}.wav"
        output_path = f"/tmp/{output_filename}"

        # Adjust parameters for very short texts to prevent audio chopping
        adjusted_speed = request.speed
        fix_duration = None
        text_length = len(request.gen_text)

        if text_length < 15:
            adjusted_speed = max(0.7, request.speed * 0.85)
            fix_duration = 8.0  # 6s (ref) + 2s (output)
            logger.info(f"Short text detected ({text_length} chars): adjusted_speed={adjusted_speed:.2f}, fix_duration={fix_duration}s")
        elif text_length < 30:
            adjusted_speed = max(0.85, request.speed * 0.95)
            fix_duration = 7.0  # 6s (ref) + 1s (output)
            logger.info(f"Medium-short text detected ({text_length} chars): adjusted_speed={adjusted_speed:.2f}, fix_duration={fix_duration}s")

        # Process TTS synchronously
        def run_inference():
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
                fix_duration=fix_duration
            )
            # Save to file (convert numpy array to torch tensor if needed)
            if isinstance(wav, torch.Tensor):
                wav_tensor = wav
            else:
                wav_tensor = torch.from_numpy(wav)
            torchaudio.save(output_path, wav_tensor.unsqueeze(0).cpu(), sr)
            return wav, sr, spect

        # Run inference in executor to avoid blocking
        await asyncio.get_event_loop().run_in_executor(None, run_inference)

        # Stream the audio file
        def iterfile():
            with open(output_path, mode="rb") as file_like:
                yield from file_like
            # Clean up file after streaming
            try:
                os.unlink(output_path)
            except OSError:
                pass

        return StreamingResponse(
            iterfile(),
            media_type="audio/wav",
            headers={"Content-Disposition": f"inline; filename={output_filename}"}
        )

    except Exception as e:
        logger.error(f"Error in streaming TTS: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")

@app.post("/tts/upload", response_model=TTSResponse)
async def text_to_speech_with_upload(
    request: str = Form(...),
    ref_audio: UploadFile = File(..., description="Reference audio file"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Generate speech from text using uploaded or default reference audio
    """
    task_id = str(uuid.uuid4())
    
    # Parse JSON request from form data
    try:
        request_data = json.loads(request)
        tts_request = TTSRequest(**request_data)
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=422, detail=f"Invalid request format: {str(e)}")
    
    # Save uploaded reference audio
    ref_audio_path = f"/tmp/ref_audio_{task_id}.wav"
    with open(ref_audio_path, "wb") as f:
        content = await ref_audio.read()
        f.write(content)
    
    # Initialize task
    tasks[task_id] = TaskStatus(
        task_id=task_id,
        status="processing",
        message="Starting TTS generation",
        created_at=datetime.now().isoformat()
    )
    
    # Start background processing
    background_tasks.add_task(
        process_tts_request,
        task_id,
        tts_request,
        ref_audio_path
    )
    
    return TTSResponse(
        task_id=task_id,
        status="processing",
        message="TTS generation started"
    )

@app.post("/tts/file", response_model=TTSResponse)
async def text_to_speech_from_file(
    model: str = Form(default="F5-TTS"),
    ref_text: str = Form(default=""),
    remove_silence: bool = Form(default=False),
    speed: float = Form(default=1.0),
    ref_audio: UploadFile = File(...),
    gen_text_file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Generate speech from text file using reference audio
    """
    task_id = str(uuid.uuid4())
    
    # Save uploaded files
    ref_audio_path = f"/tmp/ref_audio_{task_id}.wav"
    gen_text_path = f"/tmp/gen_text_{task_id}.txt"
    
    with open(ref_audio_path, "wb") as f:
        content = await ref_audio.read()
        f.write(content)
    
    with open(gen_text_path, "wb") as f:
        content = await gen_text_file.read()
        f.write(content)
    
    # Read text content
    with open(gen_text_path, "r", encoding="utf-8") as f:
        gen_text = f.read()
    
    request = TTSRequest(
        model=model,
        ref_text=ref_text,
        gen_text=gen_text,
        remove_silence=remove_silence,
        speed=speed
    )
    
    # Initialize task
    tasks[task_id] = TaskStatus(
        task_id=task_id,
        status="processing",
        message="Starting TTS generation from file",
        created_at=datetime.now().isoformat()
    )
    
    # Start background processing
    background_tasks.add_task(
        process_tts_request,
        task_id,
        request,
        ref_audio_path
    )
    
    return TTSResponse(
        task_id=task_id,
        status="processing",
        message="TTS generation from file started"
    )

@app.post("/tts/multi-style", response_model=TTSResponse)
async def multi_style_tts(
    request: MultiStyleRequest,
    ref_audio: UploadFile = File(..., description="Main reference audio"),
    voice_files: List[UploadFile] = File(..., description="Additional voice files"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Generate multi-style speech with different voices
    """
    task_id = str(uuid.uuid4())
    
    # Save main reference audio
    ref_audio_path = f"/tmp/ref_audio_{task_id}.wav"
    with open(ref_audio_path, "wb") as f:
        content = await ref_audio.read()
        f.write(content)
    
    # Save voice files
    voice_paths = {}
    for i, voice_file in enumerate(voice_files):
        voice_path = f"/tmp/voice_{task_id}_{i}.wav"
        with open(voice_path, "wb") as f:
            content = await voice_file.read()
            f.write(content)
        # Map to voice names (assuming order matches request.voices keys)
        voice_names = list(request.voices.keys())
        if i < len(voice_names):
            voice_paths[voice_names[i]] = voice_path
    
    # Initialize task
    tasks[task_id] = TaskStatus(
        task_id=task_id,
        status="processing",
        message="Starting multi-style TTS generation",
        created_at=datetime.now().isoformat()
    )
    
    # Start background processing
    background_tasks.add_task(
        process_multi_style_request,
        task_id,
        request,
        ref_audio_path,
        voice_paths
    )
    
    return TTSResponse(
        task_id=task_id,
        status="processing",
        message="Multi-style TTS generation started"
    )

@app.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """
    Get the status of a TTS generation task
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return tasks[task_id]

@app.get("/audio/{task_id}")
async def get_audio(task_id: str):
    """
    Download generated audio file
    """
    if task_id not in audio_files:
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    audio_path = audio_files[task_id]
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found on disk")
    
    return FileResponse(
        audio_path,
        media_type="audio/wav",
        filename=f"generated_audio_{task_id}.wav"
    )

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """
    Delete a task and its associated files
    """
    if task_id in tasks:
        del tasks[task_id]

    if task_id in audio_files:
        audio_path = audio_files[task_id]
        if os.path.exists(audio_path):
            os.remove(audio_path)
        del audio_files[task_id]

    return {"message": f"Task {task_id} deleted successfully"}

# Analysis-only endpoints (no TTS generation)
class AnalysisRequest(BaseModel):
    text: str = Field(description="Text to analyze")
    normalize_text: bool = Field(default=True, description="Apply text normalization")
    analyze_prosody: bool = Field(default=True, description="Analyze prosody")
    analyze_breath_pauses: bool = Field(default=True, description="Analyze breath and pauses")

@app.post("/analyze")
async def analyze_text(request: AnalysisRequest):
    """
    Analyze text without generating speech - useful for preprocessing and validation
    """
    try:
        result = {
            "original_text": request.text,
            "normalized_text": None,
            "prosody_analysis": None,
            "breath_analysis": None
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
                            "intensity": str(m.intensity) if hasattr(m, 'intensity') else None
                        }
                        for m in prosody_analysis.markers
                    ],
                    "marked_text": prosody_analysis.marked_text,
                    "sentence_count": len(prosody_analysis.sentence_boundaries),
                    "breath_points": len(prosody_analysis.breath_points),
                    "stress_points": len(prosody_analysis.stress_points),
                    "pitch_contours": prosody_analysis.pitch_contours
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
                            "context": p.context
                        }
                        for p in breath_analysis.pauses
                    ],
                    "breath_points": breath_analysis.breath_points,
                    "avg_pause_interval": breath_analysis.avg_pause_interval,
                    "estimated_duration": breath_analysis.total_duration_estimate
                }
            except Exception as e:
                result["breath_error"] = str(e)

        return result

    except Exception as e:
        logger.error(f"Error in text analysis: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Text analysis failed: {str(e)}")

@app.post("/audio/quality")
async def check_audio_quality(
    audio_file: UploadFile = File(..., description="Audio file to analyze")
):
    """
    Check audio quality without performing TTS - useful for validating reference audio
    """
    try:
        # Save uploaded audio
        temp_path = f"/tmp/quality_check_{uuid.uuid4().hex}.wav"
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
                "spectral_flatness": quality_metrics.spectral_flatness
            },
            "issues": quality_metrics.issues,
            "recommendations": quality_metrics.recommendations
        }

    except Exception as e:
        logger.error(f"Error in audio quality check: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Audio quality check failed: {str(e)}")

# Background processing functions
async def process_tts_request(task_id: str, request: TTSRequest, ref_audio_path: str):
    """
    Process TTS request in background
    """
    try:
        # Update task status
        tasks[task_id].status = "processing"
        tasks[task_id].message = "Getting model..."

        # Get model from cache
        if request.model not in models_cache:
            tasks[task_id].status = "failed"
            tasks[task_id].message = f"Model {request.model} not loaded"
            return

        f5tts_instance = models_cache[request.model]

        # Update task status
        tasks[task_id].message = "Processing audio..."

        # Generate output path
        output_path = f"/tmp/output_{task_id}.wav"

        # Adjust parameters for very short texts to prevent audio chopping
        adjusted_speed = request.speed
        fix_duration = None
        text_length = len(request.gen_text)

        if text_length < 15:
            adjusted_speed = max(0.7, request.speed * 0.85)
            fix_duration = 8.0  # 6s (ref) + 2s (output)
            logger.info(f"Short text detected ({text_length} chars): adjusted_speed={adjusted_speed:.2f}, fix_duration={fix_duration}s")
        elif text_length < 30:
            adjusted_speed = max(0.85, request.speed * 0.95)
            fix_duration = 7.0  # 6s (ref) + 1s (output)
            logger.info(f"Medium-short text detected ({text_length} chars): adjusted_speed={adjusted_speed:.2f}, fix_duration={fix_duration}s")

        # Process TTS
        def run_inference():
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
                fix_duration=fix_duration
            )
            # Save to file (convert numpy array to torch tensor if needed)
            if isinstance(wav, torch.Tensor):
                wav_tensor = wav
            else:
                wav_tensor = torch.from_numpy(wav)
            torchaudio.save(output_path, wav_tensor.unsqueeze(0).cpu(), sr)
            return wav, sr, spect

        # Run inference in executor
        await asyncio.get_event_loop().run_in_executor(None, run_inference)

        # Store audio file reference
        audio_files[task_id] = output_path

        # Update task completion
        tasks[task_id].status = "completed"
        tasks[task_id].message = "TTS generation completed successfully"
        tasks[task_id].completed_at = datetime.now().isoformat()
        tasks[task_id].result = {
            "audio_url": f"/audio/{task_id}",
            "output_path": output_path
        }

    except Exception as e:
        logger.error(f"Error processing TTS request {task_id}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        tasks[task_id].status = "failed"
        tasks[task_id].message = f"TTS generation failed: {str(e)}"
        tasks[task_id].completed_at = datetime.now().isoformat()

async def process_multi_style_request(
    task_id: str,
    request: MultiStyleRequest,
    ref_audio_path: str,
    voice_paths: Dict[str, str]
):
    """
    Process multi-style TTS request in background
    """
    try:
        # Update task status
        tasks[task_id].status = "processing"
        tasks[task_id].message = "Processing multi-style TTS..."

        # Get model from cache
        if request.model not in models_cache:
            tasks[task_id].status = "failed"
            tasks[task_id].message = f"Model {request.model} not loaded"
            return

        f5tts_instance = models_cache[request.model]
        output_path = f"/tmp/multi_output_{task_id}.wav"

        # Adjust parameters for very short texts to prevent audio chopping
        adjusted_speed = 1.0
        fix_duration = None
        text_length = len(request.gen_text)

        if text_length < 15:
            adjusted_speed = 0.85
            fix_duration = 8.0  # 6s (ref) + 2s (output)
            logger.info(f"Short text detected ({text_length} chars): adjusted_speed={adjusted_speed:.2f}, fix_duration={fix_duration}s")
        elif text_length < 30:
            adjusted_speed = 0.95
            fix_duration = 7.0  # 6s (ref) + 1s (output)
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
                fix_duration=fix_duration
            )
            # Save to file (convert numpy array to torch tensor if needed)
            if isinstance(wav, torch.Tensor):
                wav_tensor = wav
            else:
                wav_tensor = torch.from_numpy(wav)
            torchaudio.save(output_path, wav_tensor.unsqueeze(0).cpu(), sr)
            return wav, sr, spect

        await asyncio.get_event_loop().run_in_executor(None, run_inference)

        # Store audio file reference
        audio_files[task_id] = output_path

        # Update task completion
        tasks[task_id].status = "completed"
        tasks[task_id].message = "Multi-style TTS generation completed successfully"
        tasks[task_id].completed_at = datetime.now().isoformat()
        tasks[task_id].result = {
            "audio_url": f"/audio/{task_id}",
            "output_path": output_path
        }

    except Exception as e:
        logger.error(f"Error processing multi-style TTS request {task_id}: {e}")
        tasks[task_id].status = "failed"
        tasks[task_id].message = f"Multi-style TTS generation failed: {str(e)}"
        tasks[task_id].completed_at = datetime.now().isoformat()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
