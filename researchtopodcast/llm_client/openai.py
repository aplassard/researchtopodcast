"""OpenAI LLM client implementation."""

import httpx
import logging
from typing import List, Optional

from .base import BaseLLMClient, ChatMessage, LLMResponse, LLMUsage
from .models import get_model_config, ModelProvider

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """OpenAI API client."""
    
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        super().__init__(api_key, base_url)
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=60.0
        )
    
    @property
    def name(self) -> str:
        return "OpenAI"
    
    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> LLMResponse:
        """Send chat completion request to OpenAI."""
        
        payload = {
            "model": model,
            "messages": [msg.to_dict() for msg in messages],
        }
        
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if temperature is not None:
            payload["temperature"] = temperature
        
        # Add any additional kwargs
        payload.update(kwargs)
        
        logger.debug(f"Sending request to OpenAI: {model}")
        
        try:
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Extract response content
            content = data["choices"][0]["message"]["content"]
            finish_reason = data["choices"][0].get("finish_reason")
            
            # Extract usage information
            usage_data = data.get("usage", {})
            usage = LLMUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0)
            )
            
            # Estimate cost
            usage.estimated_cost = self.estimate_cost(usage, model)
            
            # Update cumulative usage
            self._update_usage(usage)
            
            logger.debug(f"OpenAI response: {usage.total_tokens} tokens, ${usage.estimated_cost:.4f}")
            
            return LLMResponse(
                content=content,
                usage=usage,
                model=model,
                finish_reason=finish_reason
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenAI API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"OpenAI request failed: {e}")
            raise
    
    def estimate_cost(self, usage: LLMUsage, model: str) -> float:
        """Estimate cost based on token usage."""
        config = get_model_config(model)
        if not config:
            logger.warning(f"Unknown model for cost estimation: {model}")
            return 0.0
        
        input_cost = (usage.prompt_tokens / 1000) * config.input_cost_per_1k
        output_cost = (usage.completion_tokens / 1000) * config.output_cost_per_1k
        
        return input_cost + output_cost
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
