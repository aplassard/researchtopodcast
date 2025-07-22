"""Tests for LLM client."""

import pytest
from unittest.mock import AsyncMock, patch
import httpx

from researchtopodcast.llm_client import ChatMessage, OpenRouterClient, OpenAIClient, ModelID


@pytest.mark.asyncio
async def test_openrouter_client_chat():
    """Test OpenRouter client chat."""
    client = OpenRouterClient("test-key")
    
    mock_response = {
        "choices": [{"message": {"content": "Test response"}}],
        "usage": {"total_tokens": 100}
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value.__aenter__.return_value
        mock_instance.post.return_value.json.return_value = mock_response
        mock_instance.post.return_value.raise_for_status.return_value = None
        
        messages = [ChatMessage(role="user", content="Hello")]
        response = await client.chat(messages)
        
        assert response == "Test response"
        assert client.cost() > 0


@pytest.mark.asyncio
async def test_openai_client_chat():
    """Test OpenAI client chat."""
    client = OpenAIClient("test-key")
    
    mock_response = {
        "choices": [{"message": {"content": "Test response"}}],
        "usage": {"total_tokens": 100}
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value.__aenter__.return_value
        mock_instance.post.return_value.json.return_value = mock_response
        mock_instance.post.return_value.raise_for_status.return_value = None
        
        messages = [ChatMessage(role="user", content="Hello")]
        response = await client.chat(messages)
        
        assert response == "Test response"
        assert client.cost() > 0


def test_chat_message():
    """Test ChatMessage dataclass."""
    msg = ChatMessage(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"
