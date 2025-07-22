"""Supported LLM models and their configurations."""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional


class ModelProvider(Enum):
    """LLM providers."""
    OPENROUTER = "openrouter"
    OPENAI = "openai"


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    id: str
    provider: ModelProvider
    max_tokens: int
    cost_per_1m_prompt_tokens: float
    cost_per_1m_completion_tokens: float
    context_window: int


class SupportedModels(Enum):
    """Supported LLM models with their configurations."""
    
    # OpenRouter models
    GPT_4O_MINI = ModelConfig(
        id="openai/gpt-4o-mini",
        provider=ModelProvider.OPENROUTER,
        max_tokens=16384,
        cost_per_1m_prompt_tokens=0.15,
        cost_per_1m_completion_tokens=0.60,
        context_window=128000
    )
    
    DEEPSEEK_CODER = ModelConfig(
        id="deepseek/deepseek-coder",
        provider=ModelProvider.OPENROUTER,
        max_tokens=4096,
        cost_per_1m_prompt_tokens=0.14,
        cost_per_1m_completion_tokens=0.28,
        context_window=16384
    )
    
    # OpenAI models (fallback)
    OPENAI_GPT_4O_MINI = ModelConfig(
        id="gpt-4o-mini",
        provider=ModelProvider.OPENAI,
        max_tokens=16384,
        cost_per_1m_prompt_tokens=0.15,
        cost_per_1m_completion_tokens=0.60,
        context_window=128000
    )


def get_model_config(model_id: str) -> Optional[ModelConfig]:
    """Get model configuration by ID."""
    for model in SupportedModels:
        if model.value.id == model_id:
            return model.value
    return None


def get_models_by_provider(provider: ModelProvider) -> Dict[str, ModelConfig]:
    """Get all models for a specific provider."""
    return {
        model.value.id: model.value
        for model in SupportedModels
        if model.value.provider == provider
    }
