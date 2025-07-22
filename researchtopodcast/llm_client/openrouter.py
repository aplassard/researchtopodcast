"""OpenRouter LLM client implementation."""

import httpx
from typing import List, Dict, Any, Optional
from ..settings import settings
from .base import LLMClient, ChatMessage
from .models import ModelID


class OpenRouterClient(LLMClient):
    """OpenRouter API client."""
    
    def __init__(self, model: ModelID = ModelID.GPT_4O_MINI):
        self.model = model
        self.base_url = settings.openrouter_base_url
        self.api_key = settings.openrouter_api_key
        self._total_cost = 0.0
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is required")
    
    @property
    def name(self) -> str:
        return f"OpenRouter({self.model})"
    
    async def chat(
        self, 
        messages: List[ChatMessage], 
        **kwargs: Any
    ) -> str:
        """Send chat messages to OpenRouter API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        # Convert messages to API format
        api_messages = [
            {"role": msg.role, "content": msg.content} 
            for msg in messages
        ]
        
        payload = {
            "model": self.model.value,
            "messages": api_messages,
            "max_tokens": kwargs.get("max_tokens", settings.podgen_max_tokens),
            "temperature": kwargs.get("temperature", 0.7),
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Track usage costs (simplified)
            if "usage" in data:
                # Rough cost estimation - would need actual pricing
                tokens = data["usage"].get("total_tokens", 0)
                self._total_cost += tokens * 0.00001  # Placeholder rate
            
            return data["choices"][0]["message"]["content"]
    
    def cost(self) -> float:
        """Return cumulative cost."""
        return self._total_cost
