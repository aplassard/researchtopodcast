"""Dependency injection for FastAPI."""

from typing import Annotated
from fastapi import Depends, HTTPException

from ..settings import settings
from ..llm_client import LLMClient, OpenRouterClient, OpenAIClient
from ..speech import SpeechEngine, GoogleTTSEngine, MockTTSEngine


def get_llm_client() -> LLMClient:
    """Get configured LLM client."""
    if settings.openrouter_api_key:
        return OpenRouterClient(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url
        )
    elif settings.openai_api_key:
        return OpenAIClient(api_key=settings.openai_api_key)
    else:
        raise HTTPException(
            status_code=500,
            detail="No LLM API key configured. Set OPENROUTER_API_KEY or OPENAI_API_KEY."
        )


def get_speech_engine() -> SpeechEngine:
    """Get configured speech engine."""
    if settings.google_tts_key:
        return GoogleTTSEngine(credentials_path=settings.google_tts_key)
    else:
        return MockTTSEngine()


def validate_api_config():
    """Validate API configuration."""
    if not settings.has_llm_config:
        raise HTTPException(
            status_code=500,
            detail="LLM configuration required"
        )


# Type aliases for dependency injection
LLMClientDep = Annotated[LLMClient, Depends(get_llm_client)]
SpeechEngineDep = Annotated[SpeechEngine, Depends(get_speech_engine)]
