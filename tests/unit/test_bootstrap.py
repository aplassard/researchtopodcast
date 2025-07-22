"""Test basic project bootstrap functionality."""

import pytest
from researchtopodcast import __version__
from researchtopodcast.settings import Settings


def test_version():
    """Test that version is defined."""
    assert __version__ == "0.1.0"


def test_settings_creation():
    """Test that settings can be created."""
    settings = Settings()
    assert settings.podgen_max_tokens == 4096
    assert settings.api_port == 8000


def test_settings_with_env_override(monkeypatch):
    """Test that environment variables override defaults."""
    monkeypatch.setenv("PODGEN_MAX_TOKENS", "2048")
    monkeypatch.setenv("API_PORT", "9000")
    
    settings = Settings()
    assert settings.podgen_max_tokens == 2048
    assert settings.api_port == 9000
