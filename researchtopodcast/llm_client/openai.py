"""OpenAI LLM client implementation."""

import httpx
from typing import List

from ..settings import settings
from .base import BaseLLMClient, ChatMessage
from .models import ModelID, MODEL_PRICING


class OpenAIClient(BaseLLMClient):
    """OpenAI API client."""
    
    def __init__(self, api_key: str | None = None):
        super().__init__()
        self.api_key = api_key or settings.openai_api_key
        self.base_url = "https://api.openai.com/v1"
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
    
    @property
    def name(self) -> str:
        return "openai"
    
    async def chat(self, messages: List[ChatMessage], **kwargs) -> str:
        """Send chat request to OpenAI."""
        
        model = kwargs.get("model", ModelID.OPENAI_GPT_4O_MINI)
        max_tokens = kwargs.get("max_tokens", settings.podgen_max_tokens)
        temperature = kwargs.get("temperature", 0.7)
        
        # Convert messages to API format
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        payload = {
            "model": model.value,
            "messages": api_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=60.0,
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract response content
            content = data["choices"][0]["message"]["content"]
            
            # Calculate and track cost
            usage = data.get("usage", {})
            if usage and model in MODEL_PRICING:
                pricing = MODEL_PRICING[model]
                input_cost = (usage.get("prompt_tokens", 0) / 1000) * pricing["input"]
                output_cost = (usage.get("completion_tokens", 0) / 1000) * pricing["output"]
                self._add_cost(input_cost + output_cost)
            
            return content
