"""
F5-TTS REST API Entry Point.

This is the main entry point for the F5-TTS REST API server. It creates and runs
the FastAPI application using the modular API implementation.

The API has been refactored into a modular structure:
    - src/f5_tts/rest_api/app.py: FastAPI app creation and startup
    - src/f5_tts/rest_api/models.py: Pydantic request/response models
    - src/f5_tts/rest_api/state.py: Global state management
    - src/f5_tts/rest_api/config.py: Configuration settings
    - src/f5_tts/rest_api/enhancements.py: Enhancement processing
    - src/f5_tts/rest_api/tts_processor.py: TTS generation logic
    - src/f5_tts/rest_api/routes/: API endpoint handlers

Usage:
    # Development mode
    python f5_tts_api.py

    # Production mode with gunicorn
    gunicorn f5_tts_api:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

    # Docker
    docker build -t spanish-f5-tts .
    docker run --gpus all -p 8000:8000 spanish-f5-tts
"""

import sys
import logging

# Add src to path for imports
sys.path.append("src")

from f5_tts.rest_api import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Create the FastAPI application
app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
