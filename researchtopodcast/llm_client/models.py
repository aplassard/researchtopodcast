"""Model definitions and configurations."""

from enum import Enum


class ModelID(str, Enum):
    """Supported model identifiers."""
    
    # OpenRouter models
    GPT_4O_MINI = "openai/gpt-4o-mini"
    GPT_4O = "openai/gpt-4o"
    DEEPSEEK_CODER = "deepseek/deepseek-coder"
    CLAUDE_3_HAIKU = "anthropic/claude-3-haiku"
    
    # OpenAI models (direct)
    OPENAI_GPT_4O_MINI = "gpt-4o-mini"
    OPENAI_GPT_4O = "gpt-4o"


# Default models for different use cases
DEFAULT_MODELS = {
    "orchestrator": ModelID.GPT_4O_MINI,
    "researcher": ModelID.DEEPSEEK_CODER,
    "fallback": ModelID.OPENAI_GPT_4O_MINI,
}


# Model pricing (per 1K tokens) - approximate
MODEL_PRICING = {
    ModelID.GPT_4O_MINI: {"input": 0.00015, "output": 0.0006},
    ModelID.GPT_4O: {"input": 0.005, "output": 0.015},
    ModelID.DEEPSEEK_CODER: {"input": 0.00014, "output": 0.00028},
    ModelID.CLAUDE_3_HAIKU: {"input": 0.00025, "output": 0.00125},
    ModelID.OPENAI_GPT_4O_MINI: {"input": 0.00015, "output": 0.0006},
    ModelID.OPENAI_GPT_4O: {"input": 0.005, "output": 0.015},
}
