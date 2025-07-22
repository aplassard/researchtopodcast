"""OpenAI LLM client."""

import httpx
from .base import ChatMessage
from .models import ModelID


class OpenAIClient:
    """OpenAI API client."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.name = "openai"
        self._total_cost = 0.0
        
    async def chat(self, messages: list[ChatMessage], model: ModelID = ModelID.OPENAI_GPT_4O_MINI, **kwargs) -> str:
        """Send chat messages to OpenAI."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": model.value,
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
            **kwargs
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            # Track cost (simplified)
            if "usage" in data:
                self._total_cost += 0.001  # Placeholder cost calculation
                
            return content
    
    def cost(self) -> float:
        """Get cumulative cost."""
        return self._total_cost
