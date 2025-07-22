"""Base LLM client interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Protocol


@dataclass
class ChatMessage:
    """Chat message for LLM conversation."""
    role: str  # "user", "assistant", "system"
    content: str


class LLMClient(Protocol):
    """Protocol for LLM clients."""
    
    name: str
    
    async def chat(self, messages: List[ChatMessage], **kwargs) -> str:
        """Send chat messages and get response."""
        ...
    
    def cost(self) -> float:
        """Get cumulative cost of API calls."""
        ...


class BaseLLMClient(ABC):
    """Base implementation for LLM clients."""
    
    def __init__(self):
        self._total_cost = 0.0
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Client name."""
        pass
    
    @abstractmethod
    async def chat(self, messages: List[ChatMessage], **kwargs) -> str:
        """Send chat messages and get response."""
        pass
    
    def cost(self) -> float:
        """Get cumulative cost of API calls."""
        return self._total_cost
    
    def _add_cost(self, cost: float) -> None:
        """Add to cumulative cost."""
        self._total_cost += cost
