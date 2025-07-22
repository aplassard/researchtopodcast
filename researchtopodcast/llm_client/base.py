"""Base classes and interfaces for LLM clients."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class ChatMessage(BaseModel):
    """A single chat message."""
    role: str  # "system", "user", "assistant"
    content: str


class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this LLM client."""
        pass
    
    @abstractmethod
    async def chat(
        self, 
        messages: List[ChatMessage], 
        **kwargs: Any
    ) -> str:
        """Send chat messages and return the response."""
        pass
    
    @abstractmethod
    def cost(self) -> float:
        """Return the cumulative cost of API calls."""
        pass
