"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    client = AsyncMock()
    client.name = "mock-llm"
    client.chat.return_value = "Mock response"
    return client


@pytest.fixture
def mock_speech_engine():
    """Mock speech engine for testing."""
    engine = AsyncMock()
    engine.synthesize.return_value = b"mock audio data"
    return engine


@pytest.fixture
def sample_script_data():
    """Sample script data for testing."""
    return {
        "meta": {
            "title": "Test Episode",
            "duration_sec": 300,
            "created": "2025-01-20T12:00:00Z"
        },
        "hosts": [
            {
                "name": "Dr. Ada",
                "persona": "Expert host",
                "voice_id": "en-US-Standard-A"
            }
        ],
        "segments": [
            {
                "speaker": "Dr. Ada",
                "text": "Welcome to our test episode."
            }
        ]
    }
