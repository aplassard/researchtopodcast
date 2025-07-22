"""OpenRouter LLM client implementation."""

import httpx
import logging
from typing import Any, Dict, List, Optional

from .base import BaseLLMClient, ChatMessage, LLMResponse, LLMUsage
from .models import get_model_config

logger = logging.getLogger(__name__)


class OpenRouterClient(BaseLLMClient):
    """OpenRouter API client."""
    
    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        super().__init__(api_key, base_url)
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/yourusername/researchtopodcast",
            "X-Title": "Research2Podcast"
        }
    
    @property
    def name(self) -> str:
        return "OpenRouter"
    
    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any
    ) -> LLMResponse:
        """Send chat messages to OpenRouter API."""
        
        # Convert messages to API format
        api_messages = [msg.to_dict() for msg in messages]
        
        payload = {
            "model": model,
            "messages": api_messages,
            "temperature": temperature or 0.7,
            **kwargs
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        logger.debug(f"Sending request to OpenRouter: {model}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract response content
            content = data["choices"][0]["message"]["content"]
            
            # Extract usage statistics
            usage_data = data.get("usage", {})
            usage = LLMUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
                cost_usd=self.estimate_cost(
                    LLMUsage(
                        usage_data.get("prompt_tokens", 0),
                        usage_data.get("completion_tokens", 0),
                        usage_data.get("total_tokens", 0)
                    ),
                    model
                )
            )
            
            # Update total usage
            self._update_usage(usage)
            
            return LLMResponse(
                content=content,
                usage=usage,
                model=model
            )
    
    def estimate_cost(self, usage: LLMUsage, model: str) -> float:
        """Calculate cost for OpenRouter models."""
        model_config = get_model_config(model)
        if not model_config:
            # Default rates if model not found
            prompt_rate = 0.0015
            completion_rate = 0.002
        else:
            prompt_rate = model_config.cost_per_1m_prompt_tokens
            completion_rate = model_config.cost_per_1m_completion_tokens
        
        cost = (
            usage.prompt_tokens * prompt_rate +
            usage.completion_tokens * completion_rate
        ) / 1_000_000
        
        return round(cost, 6)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
