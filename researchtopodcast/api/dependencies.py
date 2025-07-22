"""FastAPI dependencies."""

from typing import Generator
from fastapi import Depends, HTTPException, status

from ..llm_client import OpenRouterClient, OpenAIClient, LLMClient
from ..speech import GoogleTTSEngine, MockTTSEngine, SpeechEngine
from ..settings import settings


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
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No LLM API key configured"
        )


def get_speech_engine() -> SpeechEngine:
    """Get configured speech engine."""
    if settings.google_tts_key:
        return GoogleTTSEngine(credentials_path=settings.google_tts_key)
    else:
        return MockTTSEngine()
