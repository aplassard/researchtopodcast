"""FastAPI dependencies."""

from fastapi import Depends, HTTPException, status

from ..settings import settings
from ..llm_client import OpenRouterClient, OpenAIClient
from ..speech import GoogleTTSEngine


def get_llm_client():
    """Get LLM client dependency."""
    if not settings.has_llm_config:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No LLM API key configured"
        )
    
    if settings.openrouter_api_key:
        return OpenRouterClient(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url
        )
    else:
        return OpenAIClient(api_key=settings.openai_api_key)


def get_tts_engine():
    """Get TTS engine dependency."""
    return GoogleTTSEngine(settings.google_tts_key)
