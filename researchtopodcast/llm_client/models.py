"""Model definitions and enums for supported LLM models."""

from enum import Enum


class ModelID(str, Enum):
    """Supported model identifiers."""
    
    # OpenRouter models
    GPT_4O_MINI = "openrouter/gpt-4o-mini"
    DEEPSEEK_CODER = "openrouter/deepseek-coder"
    
    # OpenAI models (fallback)
    GPT_4O_MINI_OPENAI = "gpt-4o-mini"
    GPT_4_TURBO = "gpt-4-turbo"
