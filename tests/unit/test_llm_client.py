"""Unit tests for LLM client functionality."""

import pytest
from unittest.mock import AsyncMock, patch
from researchtopodcast.llm_client.base import ChatMessage
from researchtopodcast.llm_client.openrouter import OpenRouterClient
from researchtopodcast.llm_client.models import ModelID


@pytest.fixture
def mock_openrouter_response():
    """Mock OpenRouter API response."""
    return {
        "choices": [
            {
                "message": {
                    "content": "This is a test response from the LLM."
                }
            }
        ],
        "usage": {
            "total_tokens": 100
        }
    }


@pytest.mark.asyncio
async def test_openrouter_client_chat(mock_openrouter_response):
    """Test OpenRouter client chat functionality."""
    with patch("researchtopodcast.settings.settings") as mock_settings:
        mock_settings.openrouter_api_key = "test-key"
        mock_settings.openrouter_base_url = "https://test.api.com/v1"
        mock_settings.podgen_max_tokens = 4096
        
        client = OpenRouterClient(ModelID.GPT_4O_MINI)
        
        with patch("httpx.AsyncClient") as mock_http:
            mock_response = AsyncMock()
            mock_response.json.return_value = mock_openrouter_response
            mock_response.raise_for_status.return_value = None
            
            mock_http.return_value.__aenter__.return_value.post.return_value = mock_response
            
            messages = [
                ChatMessage(role="user", content="Hello, world!")
            ]
            
            result = await client.chat(messages)
            
            assert result == "This is a test response from the LLM."
            assert client.cost() > 0  # Should track some cost


def test_openrouter_client_name():
    """Test OpenRouter client name property."""
    with patch("researchtopodcast.settings.settings") as mock_settings:
        mock_settings.openrouter_api_key = "test-key"
        
        client = OpenRouterClient(ModelID.GPT_4O_MINI)
        assert client.name == "OpenRouter(openrouter/gpt-4o-mini)"


def test_openrouter_client_missing_key():
    """Test OpenRouter client raises error without API key."""
    with patch("researchtopodcast.settings.settings") as mock_settings:
        mock_settings.openrouter_api_key = None
        
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY is required"):
            OpenRouterClient()
