"""Tests for FastAPI application."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import tempfile
from pathlib import Path

from researchtopodcast.api.main import app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Research to Podcast API"


def test_health_endpoint(client):
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "has_llm_config" in data


@patch("researchtopodcast.api.dependencies.settings")
def test_podcast_endpoint_no_llm_config(mock_settings, client):
    """Test podcast endpoint without LLM config."""
    mock_settings.has_llm_config = False
    
    with tempfile.NamedTemporaryFile(suffix=".txt") as tmp_file:
        tmp_file.write(b"Test content")
        tmp_file.seek(0)
        
        response = client.post(
            "/v1/podcast/",
            files={"file": ("test.txt", tmp_file, "text/plain")},
        )
        
        assert response.status_code == 503


@patch("researchtopodcast.api.dependencies.settings")
def test_voices_endpoint(mock_settings, client):
    """Test voices endpoint."""
    mock_settings.google_tts_key = None
    
    with patch("researchtopodcast.speech.GoogleTTSEngine.list_voices") as mock_list_voices:
        mock_list_voices.return_value = [
            {"name": "en-US-Standard-A", "language": "en-US", "gender": "FEMALE"}
        ]
        
        response = client.get("/v1/podcast/voices/")
        assert response.status_code == 200
        voices = response.json()
        assert len(voices) > 0


def test_job_status_not_found(client):
    """Test job status for non-existent job."""
    response = client.get("/v1/podcast/nonexistent-job-id")
    assert response.status_code == 404
