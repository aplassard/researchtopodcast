"""Base LLM client interface."""

from dataclasses import dataclass
from typing import Protocol


@dataclass
class ChatMessage:
    """A chat message."""
    role: str  # "system", "user", "assistant"
    content: str


class LLMClient(Protocol):
    """Protocol for LLM clients."""
    
    name: str
    
    async def chat(self, messages: list[ChatMessage], **kwargs) -> str:
        """Send chat messages and get response."""
        ...
    
    def cost(self) -> float:
        """Get cumulative cost in USD."""
        ...
