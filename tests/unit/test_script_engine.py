"""Tests for script engine."""

import pytest
from unittest.mock import AsyncMock
from pathlib import Path
import tempfile

from researchtopodcast.script_engine import Persona, ScriptPlanner, ScriptFormatter
from researchtopodcast.script_engine.planner import ScriptMode


@pytest.mark.asyncio
async def test_script_planner_generate_solo(mock_llm_client):
    """Test solo script generation."""
    mock_llm_client.chat.side_effect = [
        "Test Episode Title",  # Title generation
        "Alex: Welcome to our podcast about AI.\nAlex: This is fascinating research."  # Script
    ]
    
    planner = ScriptPlanner(mock_llm_client)
    script = await planner.generate_script(
        content="AI research content",
        mode=ScriptMode.SOLO,
        duration_sec=300
    )
    
    assert script["meta"]["title"] == "Test Episode Title"
    assert script["meta"]["duration_sec"] == 300
    assert len(script["hosts"]) == 1
    assert script["hosts"][0]["name"] == "Alex"
    assert len(script["segments"]) == 2


@pytest.mark.asyncio
async def test_script_planner_generate_multi_speaker(mock_llm_client):
    """Test multi-speaker script generation."""
    mock_llm_client.chat.side_effect = [
        "Multi-Speaker Episode",
        "Dr. Ada: Welcome everyone.\nBen: Thanks Ada, what's this about?\nDr. Ada: Let me explain."
    ]
    
    planner = ScriptPlanner(mock_llm_client)
    script = await planner.generate_script(
        content="Research content",
        mode=ScriptMode.SINGLE_LLM_MULTI_SPEAKER,
        duration_sec=300
    )
    
    assert len(script["hosts"]) == 2
    assert script["hosts"][0]["name"] == "Dr. Ada"
    assert script["hosts"][1]["name"] == "Ben"
    assert len(script["segments"]) == 3


def test_script_formatter():
    """Test script formatter."""
    formatter = ScriptFormatter()
    
    script_data = {
        "meta": {"title": "Test", "duration_sec": 300},
        "hosts": [{"name": "Alex", "persona": "Host", "voice_id": "voice1"}],
        "segments": [{"speaker": "Alex", "text": "Hello"}]
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.podcast.yaml"
        formatter.save_script(script_data, output_path)
        
        assert output_path.exists()
        
        loaded_data = formatter.load_script(output_path)
        assert loaded_data["meta"]["title"] == "Test"
        assert len(loaded_data["segments"]) == 1


def test_persona():
    """Test Persona dataclass."""
    persona = Persona(
        name="Test Host",
        persona="Test description",
        voice_id="test-voice"
    )
    
    assert persona.name == "Test Host"
    assert persona.persona == "Test description"
    assert persona.voice_id == "test-voice"
