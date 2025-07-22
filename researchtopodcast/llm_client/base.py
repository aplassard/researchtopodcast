"""Base classes and interfaces for LLM clients."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol
from enum import Enum


class MessageRole(Enum):
    """Message roles for chat conversations."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class ChatMessage:
    """A single chat message."""
    role: str
    content: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format for API calls."""
        return {"role": self.role, "content": self.content}


@dataclass
class LLMUsage:
    """Usage statistics for LLM calls."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float = 0.0


@dataclass
class LLMResponse:
    """Response from LLM including usage stats."""
    content: str
    usage: LLMUsage
    model: str


class LLMClient(Protocol):
    """Protocol for LLM clients."""
    
    @property
    def name(self) -> str:
        """Client name for logging."""
        ...
    
    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any
    ) -> LLMResponse:
        """Send chat messages and get response."""
        ...
    
    def estimate_cost(self, usage: LLMUsage, model: str) -> float:
        """Estimate cost for the given usage."""
        ...


class BaseLLMClient(ABC):
    """Base implementation for LLM clients."""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url
        self._total_usage = LLMUsage(0, 0, 0, 0.0)
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Client name for logging."""
        pass
    
    @abstractmethod
    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any
    ) -> LLMResponse:
        """Send chat messages and get response."""
        pass
    
    @abstractmethod
    def estimate_cost(self, usage: LLMUsage, model: str) -> float:
        """Estimate cost for the given usage."""
        pass
    
    @property
    def total_usage(self) -> LLMUsage:
        """Get total usage across all calls."""
        return self._total_usage
    
    def _update_usage(self, usage: LLMUsage) -> None:
        """Update total usage statistics."""
        self._total_usage.prompt_tokens += usage.prompt_tokens
        self._total_usage.completion_tokens += usage.completion_tokens
        self._total_usage.total_tokens += usage.total_tokens
        self._total_usage.cost_usd += usage.cost_usd
