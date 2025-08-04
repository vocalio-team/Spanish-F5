from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import tempfile
import os
import asyncio
import uuid
from pathlib import Path
import logging
from datetime import datetime
import json

# Import F5-TTS modules
import sys
sys.path.append('src')

# Use the F5TTS API class to avoid argparse conflicts
from f5_tts.api import F5TTS
from f5_tts.model import DiT, UNetT
from f5_tts.infer.utils_infer import (
    load_vocoder,
    preprocess_ref_audio_text,
    infer_process,
    chunk_text,
    save_spectrogram,
    load_model,
    remove_silence_for_generated_wav,
    target_sample_rate,
    hop_length
)
import torchaudio
import torch
from importlib import files

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    cross_fade_duration: float = Field(default=0.15, description="Cross-fade duration for chunks")
    nfe_step: int = Field(default=32, description="Number of function evaluations")
    cfg_strength: float = Field(default=2.0, description="Classifier-free guidance strength")
    sway_sampling_coef: float = Field(default=-1.0, description="Sway sampling coefficient")
    seed: int = Field(default=-1, description="Random seed (-1 for random)")
    vocoder_name: str = Field(default="vocos", description="Vocoder to use")
    output_format: str = Field(default="wav", description="Output audio format")

class TTSResponse(BaseModel):
    task_id: str
    status: str
    message: str
    audio_url: Optional[str] = None
    duration: Optional[float] = None

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
        else:
            device = "cpu"
            logger.info("CUDA not available, using CPU")
        
        # Use the F5TTS class with explicit local model paths
        # Don't use local_path for vocoder, let it download from HF
        f5tts = F5TTS(
            model_type="F5-TTS",
            ckpt_file="/app/models/F5TTS_Base/model_1200000.safetensors",
            vocab_file="",
            ode_method="euler",
            use_ema=True,
            vocoder_name="vocos",
            local_path=None,  # Let vocoder download from HF
            device=device
        )
        models_cache["F5-TTS"] = f5tts
        
        # Also load E2-TTS model
        logger.info("Loading E2-TTS model...")
        e2tts = F5TTS(
            model_type="E2-TTS",
            ckpt_file="/app/models/E2TTS_Base/model_1200000.safetensors",
            vocab_file="",
            ode_method="euler",
            use_ema=True,
            vocoder_name="vocos",
            local_path=None,  # Let vocoder download from HF
            device=device
        )
        models_cache["E2-TTS"] = e2tts
        
        model_loading_status["loading"] = False
        model_loading_status["loaded"] = True
        logger.info("All models loaded successfully")
    except Exception as e:
        model_loading_status["loading"] = False
        model_loading_status["error"] = str(e)
        logger.error(f"Failed to load default model: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "F5-TTS REST API",
        "version": "1.0.0",
        "endpoints": {
            "tts": "/tts",
            "tts_file": "/tts/file",
            "multi_style": "/tts/multi-style",
            "status": "/tasks/{task_id}",
            "models": "/models",
            "health": "/health"
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
    Generate speech from text using default reference audio - Real-time response
    """
    try:
        # Use default reference audio
        ref_audio_path = "ref_audio/default.wav"
        logger.info("Real-time TTS generation with default ref_audio")
        
        # Get model from cache
        if request.model not in models_cache:
            raise HTTPException(status_code=400, detail=f"Model {request.model} not loaded")
        
        f5tts_instance = models_cache[request.model]
        
        # Generate unique filename for output
        output_filename = f"tts_{uuid.uuid4().hex}.wav"
        output_path = f"/tmp/{output_filename}"
        
        # Process TTS synchronously
        def run_inference():
            wav, sr, spect = f5tts_instance.infer(
                ref_file=ref_audio_path,
                ref_text=request.ref_text,
                gen_text=request.gen_text,
                target_rms=0.1,
                cross_fade_duration=request.cross_fade_duration,
                nfe_step=request.nfe_step,
                cfg_strength=request.cfg_strength,
                sway_sampling_coef=request.sway_sampling_coef,
                speed=request.speed,
                seed=request.seed,
                remove_silence=request.remove_silence,
                file_wave=output_path
            )
            return wav, sr, spect
        
        # Run inference in executor to avoid blocking
        await asyncio.get_event_loop().run_in_executor(None, run_inference)
        
        # Return the audio file directly
        return FileResponse(
            output_path,
            media_type="audio/wav",
            filename=output_filename,
            headers={"Content-Disposition": f"attachment; filename={output_filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error in real-time TTS: {e}")
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
        # Use default reference audio
        ref_audio_path = "ref_audio/default.wav"
        logger.info("Real-time streaming TTS generation with default ref_audio")
        
        # Get model from cache
        if request.model not in models_cache:
            raise HTTPException(status_code=400, detail=f"Model {request.model} not loaded")
        
        f5tts_instance = models_cache[request.model]
        
        # Generate unique filename for output
        output_filename = f"tts_{uuid.uuid4().hex}.wav"
        output_path = f"/tmp/{output_filename}"
        
        # Process TTS synchronously
        def run_inference():
            wav, sr, spect = f5tts_instance.infer(
                ref_file=ref_audio_path,
                ref_text=request.ref_text,
                gen_text=request.gen_text,
                target_rms=0.1,
                cross_fade_duration=request.cross_fade_duration,
                nfe_step=request.nfe_step,
                cfg_strength=request.cfg_strength,
                sway_sampling_coef=request.sway_sampling_coef,
                speed=request.speed,
                seed=request.seed,
                remove_silence=request.remove_silence,
                file_wave=output_path
            )
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
            except:
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
        
        # Process TTS using F5TTS instance
        def run_inference():
            wav, sr, spect = f5tts_instance.infer(
                ref_file=ref_audio_path,
                ref_text=request.ref_text,
                gen_text=request.gen_text,
                target_rms=0.1,
                cross_fade_duration=request.cross_fade_duration,
                nfe_step=request.nfe_step,
                cfg_strength=request.cfg_strength,
                sway_sampling_coef=request.sway_sampling_coef,
                speed=request.speed,
                seed=request.seed,
                remove_silence=request.remove_silence,
                file_wave=output_path
            )
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
        
        # Load model if not cached
        if request.model not in models_cache:
            model, vocoder, tokenizer, mel_spec_type = load_model_utils(
                model_type=request.model,
                ckpt_file="",
                vocab_file="",
                ode_method="euler",
                use_ema=True,
                vocoder_name="vocos",
                local_path="",
                device="auto"
            )
            models_cache[request.model] = {
                "model": model,
                "vocoder": vocoder,
                "tokenizer": tokenizer,
                "mel_spec_type": mel_spec_type
            }
        
        model_data = models_cache[request.model]
        output_path = f"/tmp/multi_output_{task_id}.wav"
        
        # Process multi-style TTS (simplified implementation)
        # In a full implementation, you'd parse voice markers and switch voices
        await asyncio.get_event_loop().run_in_executor(
            None,
            infer_process_utils,
            ref_audio_path,
            "",  # Auto-transcribe
            request.gen_text,
            model_data["model"],
            model_data["vocoder"],
            model_data["tokenizer"],
            model_data["mel_spec_type"],
            1.0,  # speed
            32,   # nfe_step
            2.0,  # cfg_strength
            -1.0, # sway_sampling_coef
            -1,   # seed
            request.remove_silence,
            0.15, # cross_fade_duration
            output_path
        )
        
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

# Utility functions
def load_model_utils(model_type="F5-TTS", ckpt_file="", vocab_file="", ode_method="euler", use_ema=True, vocoder_name="vocos", local_path="", device="auto"):
    """Load model and vocoder for TTS inference"""
    
    # Determine device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Model configurations
    if model_type == "F5-TTS":
        model_cls = DiT
        model_cfg = dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4)
        if ckpt_file == "":
            ckpt_file = str(files("f5_tts").joinpath("infer/examples/ckpts/F5TTS_Base/model_1200000.safetensors"))
    elif model_type == "E2-TTS":
        model_cls = UNetT
        model_cfg = dict(dim=1024, depth=24, heads=16, ff_mult=4)
        if ckpt_file == "":
            ckpt_file = str(files("f5_tts").joinpath("infer/examples/ckpts/E2TTS_Base/model_1200000.safetensors"))
    
    # Load model
    model = load_model(
        model_cls, model_cfg, ckpt_file, vocab_file=vocab_file,
        ode_method=ode_method, use_ema=use_ema, device=device
    )
    
    # Load vocoder
    vocoder = load_vocoder(vocoder_name, device=device)
    
    return model, vocoder, "custom", "vocos"

def infer_process_utils(
    ref_audio_path, ref_text, gen_text, model, vocoder, tokenizer, mel_spec_type,
    speed, nfe_step, cfg_strength, sway_sampling_coef, seed, remove_silence, cross_fade_duration, output_path
):
    """Process TTS inference and save to file"""
    
    # Set seed if specified
    if seed != -1:
        torch.manual_seed(seed)
    
    # Process reference audio and text
    ref_audio, ref_text = preprocess_ref_audio_text(ref_audio_path, ref_text)
    
    # Generate audio
    final_wave, sample_rate = infer_process(
        ref_audio=ref_audio,
        ref_text=ref_text,
        gen_text=gen_text,
        model_obj=model,
        vocoder=vocoder,
        speed=speed,
        nfe_step=nfe_step,
        cfg_strength=cfg_strength,
        sway_sampling_coef=sway_sampling_coef,
        cross_fade_duration=cross_fade_duration
    )
    
    # Save audio file
    torchaudio.save(output_path, final_wave.unsqueeze(0).cpu(), sample_rate)
    
    return output_path

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
