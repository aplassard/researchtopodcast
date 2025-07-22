"""Tests for LLM client functionality."""

import pytest
from unittest.mock import AsyncMock, patch

from researchtopodcast.llm_client.base import ChatMessage
from researchtopodcast.llm_client.models import ModelID
from researchtopodcast.llm_client.openrouter import OpenRouterClient
from researchtopodcast.llm_client.openai import OpenAIClient


class TestChatMessage:
    """Test ChatMessage functionality."""
    
    def test_chat_message_creation(self):
        """Test creating a chat message."""
        message = ChatMessage(role="user", content="Hello")
        assert message.role == "user"
        assert message.content == "Hello"


class TestOpenRouterClient:
    """Test OpenRouter client functionality."""
    
    def test_client_creation_with_api_key(self):
        """Test creating client with API key."""
        client = OpenRouterClient(api_key="test-key")
        assert client.name == "openrouter"
        assert client.api_key == "test-key"
    
    def test_client_creation_without_api_key(self):
        """Test creating client without API key raises error."""
        with pytest.raises(ValueError, match="OpenRouter API key is required"):
            OpenRouterClient(api_key=None)
    
    @pytest.mark.asyncio
    async def test_chat_request(self):
        """Test making a chat request."""
        client = OpenRouterClient(api_key="test-key")
        
        # Mock the HTTP response
        mock_response_data = {
            "choices": [
                {"message": {"content": "Test response"}}
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5
            }
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            messages = [ChatMessage(role="user", content="Hello")]
            response = await client.chat(messages)
            
            assert response == "Test response"
            assert client.cost() > 0  # Should have tracked some cost


class TestOpenAIClient:
    """Test OpenAI client functionality."""
    
    def test_client_creation_with_api_key(self):
        """Test creating client with API key."""
        client = OpenAIClient(api_key="test-key")
        assert client.name == "openai"
        assert client.api_key == "test-key"
    
    def test_client_creation_without_api_key(self):
        """Test creating client without API key raises error."""
        with pytest.raises(ValueError, match="OpenAI API key is required"):
            OpenAIClient(api_key=None)
