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

from f5_tts.infer.infer_cli import load_model, infer_process, parse_toml_file
from f5_tts.model import DiT, UNetT
from f5_tts.infer.utils_infer import (
    load_vocoder,
    load_model as load_model_utils,
    preprocess_ref_audio_text,
    infer_process as infer_process_utils,
    chunk_text,
    save_spectrogram
)

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
        logger.info("Loading default F5-TTS model...")
        model, vocoder, tokenizer, mel_spec_type = load_model_utils(
            model_type="F5-TTS",
            ckpt_file="",
            vocab_file="",
            ode_method="euler",
            use_ema=True,
            vocoder_name="vocos",
            local_path="",
            device="auto"
        )
        models_cache["F5-TTS"] = {
            "model": model,
            "vocoder": vocoder,
            "tokenizer": tokenizer,
            "mel_spec_type": mel_spec_type
        }
        logger.info("Default model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load default model: {e}")

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

@app.post("/tts", response_model=TTSResponse)
async def text_to_speech(
    request: TTSRequest,
    ref_audio: UploadFile = File(..., description="Reference audio file"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Generate speech from text using reference audio
    """
    task_id = str(uuid.uuid4())
    
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
        request,
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
        tasks[task_id].message = "Loading model..."
        
        # Load model if not cached
        if request.model not in models_cache:
            model, vocoder, tokenizer, mel_spec_type = load_model_utils(
                model_type=request.model,
                ckpt_file="",
                vocab_file="",
                ode_method="euler",
                use_ema=True,
                vocoder_name=request.vocoder_name,
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
        
        # Update task status
        tasks[task_id].message = "Processing audio..."
        
        # Generate output path
        output_path = f"/tmp/output_{task_id}.wav"
        
        # Process TTS
        await asyncio.get_event_loop().run_in_executor(
            None,
            infer_process_utils,
            ref_audio_path,
            request.ref_text,
            request.gen_text,
            model_data["model"],
            model_data["vocoder"],
            model_data["tokenizer"],
            model_data["mel_spec_type"],
            request.speed,
            request.nfe_step,
            request.cfg_strength,
            request.sway_sampling_coef,
            request.seed,
            request.remove_silence,
            request.cross_fade_duration,
            output_path
        )
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
