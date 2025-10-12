"""
Backend Integration for F5-TTS and Whisper Services

This module provides a simple client for the backend to access GPU inference services.
"""

import asyncio
import httpx
from typing import Optional, Literal
from pathlib import Path


class GPUInferenceClient:
    """Client for F5-TTS and Whisper GPU services."""

    def __init__(
        self,
        f5_tts_url: str,
        whisper_url: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialize the GPU inference client.

        Args:
            f5_tts_url: Base URL for F5-TTS service (ALB endpoint)
            whisper_url: Base URL for Whisper service (optional, same ALB different port)
            timeout: Request timeout in seconds
        """
        self.f5_tts_url = f5_tts_url.rstrip('/')
        self.whisper_url = whisper_url.rstrip('/') if whisper_url else None
        self.timeout = timeout

    async def generate_speech(
        self,
        text: str,
        region: Literal["rioplatense", "colombian", "mexican", "chilean", "caribbean", "andean", "auto"] = "rioplatense",
        nfe_step: int = 16,
        speed: float = 1.0,
        output_path: Optional[Path] = None
    ) -> bytes:
        """
        Generate Spanish speech from text using F5-TTS.

        Args:
            text: Text to synthesize (Spanish)
            region: Regional accent variant (auto-detects from slang if "auto")
            nfe_step: Number of inference steps (8-32, higher=better quality but slower)
            speed: Speech speed multiplier (0.5-2.0)
            output_path: Optional path to save the WAV file

        Returns:
            WAV audio bytes (24kHz, mono)

        Example:
            >>> client = GPUInferenceClient("http://alb-url.amazonaws.com")
            >>> audio = await client.generate_speech(
            ...     "Che boludo, ¿cómo andás?",
            ...     region="rioplatense"
            ... )
            >>> # audio is WAV bytes, ready to stream or save
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.f5_tts_url}/tts",
                json={
                    "text": text,
                    "region": region,
                    "nfe_step": nfe_step,
                    "speed": speed
                }
            )
            response.raise_for_status()

            audio_bytes = response.content

            # Optionally save to file
            if output_path:
                output_path.write_bytes(audio_bytes)

            return audio_bytes

    async def analyze_text(
        self,
        text: str,
        region: str = "auto"
    ) -> dict:
        """
        Analyze Spanish text for regional features without generating audio.

        Args:
            text: Text to analyze
            region: Region to analyze for (or "auto" to detect)

        Returns:
            Analysis result with detected region, slang markers, prosodic profile

        Example:
            >>> result = await client.analyze_text("Che boludo, vení acá")
            >>> print(result["detected_region"])  # "rioplatense"
            >>> print(result["slang_markers"])     # ["che", "boludo", "vení"]
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.f5_tts_url}/analyze",
                json={
                    "text": text,
                    "region": region
                }
            )
            response.raise_for_status()
            return response.json()

    async def health_check(self) -> dict:
        """
        Check F5-TTS service health.

        Returns:
            Health status dict with models_loaded, timestamp, etc.
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.f5_tts_url}/health")
            response.raise_for_status()
            return response.json()

    async def transcribe_audio(
        self,
        audio_file: Path,
        language: str = "es"
    ) -> dict:
        """
        Transcribe audio to text using Whisper (when available).

        Args:
            audio_file: Path to audio file
            language: Language code (default: "es" for Spanish)

        Returns:
            Transcription result with text and metadata

        Note: Requires Whisper service to be deployed
        """
        if not self.whisper_url:
            raise ValueError("Whisper URL not configured")

        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(audio_file, 'rb') as f:
                files = {'file': f}
                data = {'language': language}
                response = await client.post(
                    f"{self.whisper_url}/transcribe",
                    files=files,
                    data=data
                )
            response.raise_for_status()
            return response.json()


# FastAPI Integration Example
# ---------------------------

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Initialize client with ALB URL (get from CloudFormation outputs)
# ALB_URL will be available after deployment completes
tts_client = GPUInferenceClient(
    f5_tts_url="http://<ALB-URL>",  # Replace with actual ALB DNS
    # whisper_url="http://<ALB-URL>:9000"  # When Whisper is deployed
)


class TTSRequest(BaseModel):
    text: str
    region: str = "rioplatense"
    nfe_step: int = 16
    speed: float = 1.0


class AnalysisRequest(BaseModel):
    text: str
    region: str = "auto"


@app.post("/api/tts/generate")
async def generate_tts(request: TTSRequest):
    """
    Generate Spanish TTS audio.

    Example:
        POST /api/tts/generate
        {
            "text": "Hola amigo, ¿cómo estás?",
            "region": "rioplatense",
            "nfe_step": 16,
            "speed": 1.0
        }

    Returns:
        WAV audio file (audio/wav)
    """
    try:
        audio_bytes = await tts_client.generate_speech(
            text=request.text,
            region=request.region,
            nfe_step=request.nfe_step,
            speed=request.speed
        )

        from fastapi.responses import Response
        return Response(
            content=audio_bytes,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename=speech.wav"
            }
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"TTS service error: {str(e)}")


@app.post("/api/tts/analyze")
async def analyze_text(request: AnalysisRequest):
    """
    Analyze Spanish text for regional features.

    Example:
        POST /api/tts/analyze
        {
            "text": "Che boludo, ¿cómo andás?",
            "region": "auto"
        }

    Returns:
        {
            "detected_region": "rioplatense",
            "slang_markers": ["che", "boludo", "andás"],
            "prosodic_profile": {
                "pace": "slow",
                "f0_range": [75, 340],
                "stress_pattern": "double_accentuation"
            }
        }
    """
    try:
        result = await tts_client.analyze_text(
            text=request.text,
            region=request.region
        )
        return result
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"Analysis service error: {str(e)}")


@app.get("/api/tts/health")
async def check_tts_health():
    """Check TTS service health."""
    try:
        health = await tts_client.health_check()
        return {
            "status": "healthy",
            "tts_service": health
        }
    except httpx.HTTPError:
        return {
            "status": "unhealthy",
            "tts_service": "unavailable"
        }


# Standalone Usage Example
# -------------------------

async def example_usage():
    """Example of using the TTS client directly."""

    # Initialize client
    client = GPUInferenceClient(
        f5_tts_url="http://unified-gpu-stack-alb-xyz.us-east-1.elb.amazonaws.com"
    )

    # Check health
    health = await client.health_check()
    print(f"TTS Service Status: {health['status']}")
    print(f"Models Loaded: {health['models_loaded']}")

    # Analyze text (fast, no audio generation)
    analysis = await client.analyze_text(
        "Che boludo, ¿vos querés tomar unos mates?",
        region="auto"
    )
    print(f"Detected Region: {analysis['detected_region']}")
    print(f"Slang Markers: {analysis['slang_markers']}")

    # Generate speech
    audio = await client.generate_speech(
        text="Hola amigo, ¿cómo estás hoy?",
        region="rioplatense",
        nfe_step=16,  # Fast inference
        speed=1.0,
        output_path=Path("output.wav")
    )
    print(f"Generated audio: {len(audio)} bytes")

    # For higher quality (slower)
    audio_hq = await client.generate_speech(
        text="Esta es una prueba de alta calidad",
        region="colombian",
        nfe_step=32,  # Higher quality
        speed=0.9,
        output_path=Path("output_hq.wav")
    )
    print(f"High-quality audio: {len(audio_hq)} bytes")


if __name__ == "__main__":
    # Run standalone example
    asyncio.run(example_usage())


# Environment Variables (for production)
# ---------------------------------------
"""
Add to your backend .env file:

# GPU Inference Services
F5_TTS_ENDPOINT=http://<ALB-DNS>
WHISPER_ENDPOINT=http://<ALB-DNS>:9000

# Service Settings
TTS_TIMEOUT=30
TTS_DEFAULT_REGION=rioplatense
TTS_DEFAULT_NFE_STEP=16

Then use:

import os

tts_client = GPUInferenceClient(
    f5_tts_url=os.getenv("F5_TTS_ENDPOINT"),
    whisper_url=os.getenv("WHISPER_ENDPOINT"),
    timeout=float(os.getenv("TTS_TIMEOUT", "30"))
)
"""
