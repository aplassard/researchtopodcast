"""Supported model IDs."""

from enum import Enum


class ModelID(str, Enum):
    """Supported model identifiers."""
    
    # OpenRouter models
    GPT_4O_MINI = "openai/gpt-4o-mini"
    DEEPSEEK_CODER = "deepseek/deepseek-coder"
    
    # OpenAI models
    OPENAI_GPT_4O_MINI = "gpt-4o-mini"
    OPENAI_GPT_4O = "gpt-4o"
