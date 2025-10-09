"""
Task management endpoints.

Handles task status queries, audio file retrieval, and task cleanup.
"""

import os
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..models import TaskStatus
from ..state import api_state

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """
    Get the status of a TTS generation task.

    Args:
        task_id: Unique task identifier

    Returns:
        Task status information

    Raises:
        HTTPException: If task not found
    """
    try:
        return api_state.get_task(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")


@router.get("/audio/{task_id}")
async def get_audio(task_id: str):
    """
    Download generated audio file.

    Args:
        task_id: Unique task identifier

    Returns:
        Audio file response

    Raises:
        HTTPException: If audio file not found
    """
    try:
        audio_path = api_state.get_audio_path(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Audio file not found")

    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found on disk")

    return FileResponse(audio_path, media_type="audio/wav", filename=f"generated_audio_{task_id}.wav")


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """
    Delete a task and its associated files.

    Args:
        task_id: Unique task identifier

    Returns:
        Success message
    """
    api_state.delete_task(task_id, cleanup_audio=True)
    return {"message": f"Task {task_id} deleted successfully"}
