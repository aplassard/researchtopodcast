"""Model definitions and configurations."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class ModelProvider(Enum):
    """LLM providers."""
    OPENROUTER = "openrouter"
    OPENAI = "openai"


@dataclass
class ModelConfig:
    """Configuration for an LLM model."""
    id: str
    provider: ModelProvider
    context_length: int
    input_cost_per_1k: float  # USD per 1K input tokens
    output_cost_per_1k: float  # USD per 1K output tokens
    description: str


class SupportedModels(Enum):
    """Supported LLM models with their configurations."""
    
    # OpenRouter models
    GPT_4O_MINI = ModelConfig(
        id="openai/gpt-4o-mini",
        provider=ModelProvider.OPENROUTER,
        context_length=128000,
        input_cost_per_1k=0.00015,
        output_cost_per_1k=0.0006,
        description="OpenAI GPT-4o Mini via OpenRouter"
    )
    
    DEEPSEEK_CODER = ModelConfig(
        id="deepseek/deepseek-coder",
        provider=ModelProvider.OPENROUTER,
        context_length=16384,
        input_cost_per_1k=0.00014,
        output_cost_per_1k=0.00028,
        description="DeepSeek Coder via OpenRouter"
    )
    
    # OpenAI direct models
    OPENAI_GPT_4O_MINI = ModelConfig(
        id="gpt-4o-mini",
        provider=ModelProvider.OPENAI,
        context_length=128000,
        input_cost_per_1k=0.00015,
        output_cost_per_1k=0.0006,
        description="OpenAI GPT-4o Mini (direct)"
    )
    
    OPENAI_GPT_4O = ModelConfig(
        id="gpt-4o",
        provider=ModelProvider.OPENAI,
        context_length=128000,
        input_cost_per_1k=0.005,
        output_cost_per_1k=0.015,
        description="OpenAI GPT-4o (direct)"
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
