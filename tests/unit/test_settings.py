"""Test application settings."""

import os
import pytest
from researchtopodcast.settings import Settings


def test_settings_defaults():
    """Test default settings values."""
    settings = Settings()
    
    assert settings.openrouter_base_url == "https://openrouter.ai/api/v1"
    assert settings.podgen_max_tokens == 4096
    assert settings.podgen_temp_dir == "./output"
    assert settings.api_host == "0.0.0.0"
    assert settings.api_port == 8000


def test_settings_from_env(monkeypatch):
    """Test settings loaded from environment variables."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("PODGEN_MAX_TOKENS", "2048")
    
    settings = Settings()
    
    assert settings.openrouter_api_key == "test-key"
    assert settings.podgen_max_tokens == 2048


def test_has_llm_config():
    """Test LLM configuration detection."""
    # No keys
    settings = Settings()
    assert not settings.has_llm_config
    
    # OpenRouter key
    settings = Settings(openrouter_api_key="test-key")
    assert settings.has_llm_config
    
    # OpenAI key
    settings = Settings(openai_api_key="test-key")
    assert settings.has_llm_config
