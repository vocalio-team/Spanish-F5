"""
Tests for the modular API components.

Tests the individual modules extracted from the monolithic f5_tts_api.py.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import torch
import numpy as np

from f5_tts.rest_api.models import TTSRequest, TTSResponse, TaskStatus, AnalysisRequest
from f5_tts.rest_api.state import APIState
from f5_tts.rest_api.tts_processor import TTSProcessor
from f5_tts.rest_api.enhancements import EnhancementProcessor


class TestAPIModels:
    """Test Pydantic models."""

    def test_tts_request_defaults(self):
        """Test TTSRequest with default values."""
        request = TTSRequest(ref_text="", gen_text="Hola mundo")

        assert request.model == "F5-TTS"
        assert request.gen_text == "Hola mundo"
        assert request.speed == 1.0
        assert request.nfe_step == 16
        assert request.normalize_text is True
        assert request.adaptive_nfe is True

    def test_tts_request_custom_values(self):
        """Test TTSRequest with custom values."""
        request = TTSRequest(
            model="E2-TTS",
            ref_text="Reference",
            gen_text="Test text",
            speed=0.8,
            nfe_step=32,
            normalize_text=False,
        )

        assert request.model == "E2-TTS"
        assert request.speed == 0.8
        assert request.nfe_step == 32
        assert request.normalize_text is False

    def test_tts_response(self):
        """Test TTSResponse model."""
        response = TTSResponse(task_id="123", status="completed", message="Success", audio_url="/audio/123")

        assert response.task_id == "123"
        assert response.status == "completed"
        assert response.audio_url == "/audio/123"

    def test_task_status(self):
        """Test TaskStatus model."""
        task = TaskStatus(
            task_id="456", status="processing", message="In progress", created_at=datetime.now().isoformat()
        )

        assert task.task_id == "456"
        assert task.status == "processing"
        assert task.completed_at is None

    def test_analysis_request(self):
        """Test AnalysisRequest model."""
        request = AnalysisRequest(text="Test text", normalize_text=True, analyze_prosody=True)

        assert request.text == "Test text"
        assert request.normalize_text is True
        assert request.analyze_prosody is True


class TestAPIState:
    """Test state management."""

    def test_initialization(self):
        """Test APIState initialization."""
        state = APIState()

        assert isinstance(state.models_cache, dict)
        assert isinstance(state.tasks, dict)
        assert isinstance(state.audio_files, dict)
        assert state.model_loading_status["loading"] is False

    def test_add_and_get_model(self):
        """Test adding and retrieving models."""
        state = APIState()
        mock_model = Mock()

        state.add_model("F5-TTS", mock_model)
        retrieved = state.get_model("F5-TTS")

        assert retrieved == mock_model
        assert "F5-TTS" in state.loaded_models

    def test_get_nonexistent_model(self):
        """Test retrieving non-existent model raises error."""
        state = APIState()

        with pytest.raises(KeyError):
            state.get_model("NonExistent")

    def test_create_task(self):
        """Test task creation."""
        state = APIState()

        task = state.create_task("task123", "Starting")

        assert task.task_id == "task123"
        assert task.status == "processing"
        assert task.message == "Starting"
        assert "task123" in state.tasks

    def test_update_task(self):
        """Test task update."""
        state = APIState()
        state.create_task("task123", "Starting")

        state.update_task("task123", status="completed", message="Done", result={"url": "/audio/123"})

        task = state.get_task("task123")
        assert task.status == "completed"
        assert task.message == "Done"
        assert task.result["url"] == "/audio/123"

    def test_complete_task(self):
        """Test completing a task."""
        state = APIState()
        state.create_task("task123", "Starting")

        state.complete_task("task123", "Success", {"audio_url": "/audio/123"})

        task = state.get_task("task123")
        assert task.status == "completed"
        assert task.completed_at is not None

    def test_fail_task(self):
        """Test failing a task."""
        state = APIState()
        state.create_task("task123", "Starting")

        state.fail_task("task123", "Error occurred")

        task = state.get_task("task123")
        assert task.status == "failed"
        assert task.message == "Error occurred"

    def test_store_and_get_audio(self):
        """Test audio file storage."""
        state = APIState()

        state.store_audio("task123", "/tmp/audio.wav")
        path = state.get_audio_path("task123")

        assert path == "/tmp/audio.wav"

    def test_delete_task(self):
        """Test task deletion."""
        state = APIState()
        state.create_task("task123", "Starting")
        state.store_audio("task123", "/tmp/audio.wav")

        state.delete_task("task123", cleanup_audio=False)

        with pytest.raises(KeyError):
            state.get_task("task123")


class TestTTSProcessor:
    """Test TTS processor."""

    def test_short_text_adjustments_very_short(self):
        """Test adjustments for very short text."""
        processor = TTSProcessor()

        adjusted_speed, fix_duration = processor.calculate_short_text_adjustments("Hola", 1.0)

        assert adjusted_speed < 1.0
        assert fix_duration == 12.0  # Updated: increased to prevent audio chopping

    def test_short_text_adjustments_medium(self):
        """Test adjustments for medium-short text."""
        processor = TTSProcessor()

        adjusted_speed, fix_duration = processor.calculate_short_text_adjustments("Hola mundo, ¿cómo estás?", 1.0)

        assert adjusted_speed < 1.0
        assert fix_duration == 9.0  # Updated: increased to prevent audio chopping

    def test_normal_text_no_adjustments(self):
        """Test no adjustments for normal length text."""
        processor = TTSProcessor()

        adjusted_speed, fix_duration = processor.calculate_short_text_adjustments(
            "Este es un texto de longitud normal que no necesita ajustes.", 1.0
        )

        assert adjusted_speed == 1.0
        assert fix_duration is None

    @patch("torchaudio.save")
    def test_save_audio_tensor(self, mock_save):
        """Test saving audio from torch tensor."""
        processor = TTSProcessor()
        wav = torch.randn(1, 24000)

        processor.save_audio(wav, 24000, "/tmp/test.wav")

        mock_save.assert_called_once()

    @patch("torchaudio.save")
    def test_save_audio_numpy(self, mock_save):
        """Test saving audio from numpy array."""
        processor = TTSProcessor()
        wav = np.random.randn(24000)

        processor.save_audio(wav, 24000, "/tmp/test.wav")

        mock_save.assert_called_once()


class TestEnhancementProcessor:
    """Test enhancement processor."""

    def test_initialization(self):
        """Test EnhancementProcessor initialization."""
        processor = EnhancementProcessor()

        assert processor.quality_analyzer is not None

    @patch("f5_tts.rest_api.enhancements.normalize_spanish_text")
    def test_normalize_text(self, mock_normalize):
        """Test text normalization."""
        processor = EnhancementProcessor()
        mock_normalize.return_value = "texto normalizado"

        result = processor._normalize_text("texto 123")

        assert result == "texto normalizado"
        mock_normalize.assert_called_once_with("texto 123")

    @patch("f5_tts.rest_api.enhancements.normalize_spanish_text")
    def test_normalize_text_error_handling(self, mock_normalize):
        """Test text normalization error handling."""
        processor = EnhancementProcessor()
        mock_normalize.side_effect = Exception("Normalization error")

        result = processor._normalize_text("texto")

        # Should return original text on error
        assert result == "texto"

    def test_adaptive_nfe_default(self):
        """Test adaptive NFE with default fallback."""
        processor = EnhancementProcessor()

        result = processor._get_adaptive_nfe("Simple text", 16)

        assert isinstance(result, int)
        assert result > 0

    def test_adaptive_crossfade_default(self):
        """Test adaptive crossfade with default fallback (requires text parameter now)."""
        processor = EnhancementProcessor()

        # Test with normal-length text
        result = processor._get_adaptive_crossfade(0.8, "This is a normal length text for testing")

        assert isinstance(result, float)
        assert result > 0

    @patch("f5_tts.rest_api.enhancements.analyze_spanish_prosody")
    def test_analyze_prosody_success(self, mock_analyze):
        """Test prosody analysis."""
        processor = EnhancementProcessor()

        # Mock prosody analysis result
        mock_result = Mock()
        mock_result.markers = []
        mock_result.sentence_boundaries = [0, 10]
        mock_result.breath_points = [5]
        mock_result.marked_text = "test"
        mock_analyze.return_value = mock_result

        result = processor._analyze_prosody("Test text")

        assert result is not None
        assert "sentence_count" in result
        assert result["sentence_count"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
