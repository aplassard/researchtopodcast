"""Tests for speech synthesis."""

import pytest
from pathlib import Path
import tempfile

from researchtopodcast.speech import Script, GoogleTTSEngine


@pytest.mark.asyncio
async def test_google_tts_mock_synthesis():
    """Test Google TTS with mock (no API key)."""
    engine = GoogleTTSEngine()
    
    script = Script(
        meta={"title": "Test", "duration_sec": 10},
        hosts=[{"name": "Alex", "voice_id": "en-US-Standard-A"}],
        segments=[{"speaker": "Alex", "text": "Hello world"}]
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.mp3"
        result_path = await engine.synthesize(script, output_path)
        
        assert result_path == output_path
        assert output_path.exists()
        assert output_path.stat().st_size > 0


@pytest.mark.asyncio
async def test_google_tts_list_voices():
    """Test listing voices."""
    engine = GoogleTTSEngine()
    voices = await engine.list_voices()
    
    assert len(voices) > 0
    assert all("name" in voice for voice in voices)
    assert all("language" in voice for voice in voices)


def test_script_dataclass():
    """Test Script dataclass."""
    script = Script(
        meta={"title": "Test"},
        hosts=[{"name": "Host"}],
        segments=[{"speaker": "Host", "text": "Hello"}]
    )
    
    assert script.meta["title"] == "Test"
    assert len(script.hosts) == 1
    assert len(script.segments) == 1
