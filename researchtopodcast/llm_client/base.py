"""Base classes and interfaces for LLM clients."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Protocol, Dict, Any
from enum import Enum


class MessageRole(Enum):
    """Chat message roles."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class ChatMessage:
    """A single chat message."""
    role: MessageRole
    content: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format."""
        return {
            "role": self.role.value,
            "content": self.content
        }


@dataclass
class LLMUsage:
    """Token usage information."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: Optional[float] = None


@dataclass
class LLMResponse:
    """Response from an LLM."""
    content: str
    usage: Optional[LLMUsage] = None
    model: Optional[str] = None
    finish_reason: Optional[str] = None


class LLMClient(Protocol):
    """Protocol for LLM clients."""
    
    @property
    def name(self) -> str:
        """Client name for identification."""
        ...
    
    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> LLMResponse:
        """Send chat messages and get response."""
        ...
    
    def estimate_cost(self, usage: LLMUsage, model: str) -> float:
        """Estimate cost for token usage."""
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
        """Client name for identification."""
        pass
    
    @abstractmethod
    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> LLMResponse:
        """Send chat messages and get response."""
        pass
    
    @abstractmethod
    def estimate_cost(self, usage: LLMUsage, model: str) -> float:
        """Estimate cost for token usage."""
        pass
    
    @property
    def total_usage(self) -> LLMUsage:
        """Get cumulative usage statistics."""
        return self._total_usage
    
    def _update_usage(self, usage: LLMUsage) -> None:
        """Update cumulative usage statistics."""
        self._total_usage.prompt_tokens += usage.prompt_tokens
        self._total_usage.completion_tokens += usage.completion_tokens
        self._total_usage.total_tokens += usage.total_tokens
        if usage.estimated_cost:
            if self._total_usage.estimated_cost is None:
                self._total_usage.estimated_cost = 0.0
            self._total_usage.estimated_cost += usage.estimated_cost
