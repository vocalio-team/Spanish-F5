"""
State management for F5-TTS REST API.

This module manages global state including model cache, task storage, and vocoder cache.
"""

from typing import Dict, Any
from datetime import datetime
import logging

from .models import TaskStatus

logger = logging.getLogger(__name__)


class APIState:
    """Global state manager for the API."""

    def __init__(self):
        """Initialize empty state containers."""
        # Model storage
        self.models_cache: Dict[str, Any] = {}
        self.vocoder_cache: Dict[str, Any] = {}
        self.model_loading_status = {"loading": False, "loaded": False, "error": None}

        # Task storage (in production, use Redis or database)
        self.tasks: Dict[str, TaskStatus] = {}
        self.audio_files: Dict[str, str] = {}

    def get_model(self, model_name: str) -> Any:
        """
        Get a loaded model by name.

        Args:
            model_name: Name of the model (e.g., "F5-TTS", "E2-TTS")

        Returns:
            The model instance

        Raises:
            KeyError: If model is not loaded
        """
        if model_name not in self.models_cache:
            raise KeyError(f"Model {model_name} not loaded")
        return self.models_cache[model_name]

    def add_model(self, model_name: str, model: Any) -> None:
        """
        Add a model to the cache.

        Args:
            model_name: Name of the model
            model: Model instance
        """
        self.models_cache[model_name] = model
        logger.info(f"Added model {model_name} to cache")

    def get_task(self, task_id: str) -> TaskStatus:
        """
        Get task status by ID.

        Args:
            task_id: Task identifier

        Returns:
            Task status object

        Raises:
            KeyError: If task not found
        """
        if task_id not in self.tasks:
            raise KeyError(f"Task {task_id} not found")
        return self.tasks[task_id]

    def create_task(self, task_id: str, message: str = "Task created") -> TaskStatus:
        """
        Create a new task.

        Args:
            task_id: Unique task identifier
            message: Initial task message

        Returns:
            Created task status object
        """
        task = TaskStatus(
            task_id=task_id,
            status="processing",
            message=message,
            created_at=datetime.now().isoformat(),
        )
        self.tasks[task_id] = task
        return task

    def update_task(
        self, task_id: str, status: str = None, message: str = None, result: Dict[str, Any] = None
    ) -> None:
        """
        Update an existing task.

        Args:
            task_id: Task identifier
            status: New status
            message: New message
            result: Task result data
        """
        if task_id not in self.tasks:
            raise KeyError(f"Task {task_id} not found")

        task = self.tasks[task_id]
        if status:
            task.status = status
        if message:
            task.message = message
        if result:
            task.result = result

        if status in ["completed", "failed"]:
            task.completed_at = datetime.now().isoformat()

    def complete_task(self, task_id: str, message: str, result: Dict[str, Any]) -> None:
        """
        Mark a task as completed.

        Args:
            task_id: Task identifier
            message: Completion message
            result: Task result data
        """
        self.update_task(task_id, status="completed", message=message, result=result)

    def fail_task(self, task_id: str, error_message: str) -> None:
        """
        Mark a task as failed.

        Args:
            task_id: Task identifier
            error_message: Error description
        """
        self.update_task(task_id, status="failed", message=error_message)

    def store_audio(self, task_id: str, audio_path: str) -> None:
        """
        Store reference to generated audio file.

        Args:
            task_id: Task identifier
            audio_path: Path to audio file
        """
        self.audio_files[task_id] = audio_path

    def get_audio_path(self, task_id: str) -> str:
        """
        Get audio file path by task ID.

        Args:
            task_id: Task identifier

        Returns:
            Path to audio file

        Raises:
            KeyError: If audio file not found
        """
        if task_id not in self.audio_files:
            raise KeyError(f"Audio file for task {task_id} not found")
        return self.audio_files[task_id]

    def delete_task(self, task_id: str, cleanup_audio: bool = True) -> None:
        """
        Delete a task and optionally its audio file.

        Args:
            task_id: Task identifier
            cleanup_audio: Whether to delete associated audio file
        """
        import os

        if task_id in self.tasks:
            del self.tasks[task_id]

        if cleanup_audio and task_id in self.audio_files:
            audio_path = self.audio_files[task_id]
            if os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                    logger.info(f"Deleted audio file: {audio_path}")
                except OSError as e:
                    logger.warning(f"Failed to delete audio file {audio_path}: {e}")
            del self.audio_files[task_id]

    @property
    def loaded_models(self) -> list:
        """Get list of loaded model names."""
        return list(self.models_cache.keys())


# Global state instance
api_state = APIState()
