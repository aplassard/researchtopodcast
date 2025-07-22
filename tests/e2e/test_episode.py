"""End-to-end test for podcast generation."""

import pytest
import asyncio
from pathlib import Path
import shutil
import os
from unittest.mock import patch, MagicMock

from researchtopodcast.cli.cli import app
from researchtopodcast.settings import settings
from typer.testing import CliRunner


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def sample_document(tmp_path):
    """Create a sample document for testing."""
    doc_path = tmp_path / "sample.md"
    
    content = """# Test Document

This is a sample document for testing the researchtopodcast system.
It contains several paragraphs about artificial intelligence and machine learning.

## Introduction

AI is transforming many industries. Machine learning algorithms can analyze
large datasets to find patterns and make predictions.

## Technical Details

The transformer architecture uses self-attention mechanisms to process
sequences in parallel, making it much faster than previous approaches.

## Conclusion

Generative AI has made remarkable progress in recent years. Models like
GPT-4 can generate high-quality text that is difficult to distinguish
from human writing."""
    
    doc_path.write_text(content)
    return doc_path


@pytest.fixture(autouse=True)
def setup_test_environment(tmp_path, monkeypatch):
    """Setup test environment with temporary output directory."""
    temp_output = tmp_path / "output"
    temp_output.mkdir()
    
    # Use monkeypatch to avoid modifying global settings
    monkeypatch.setattr(settings, "podgen_temp_dir", str(temp_output))
    
    # Create temporary data directory
    temp_data = tmp_path / "data"
    temp_data.mkdir()
    
    yield


@pytest.mark.e2e
def test_end_to_end_podcast_generation(runner, sample_document):
    """Test complete podcast generation from document to audio."""
    with patch('researchtopodcast.cli.cli.get_llm_client') as mock_get_llm, \
         patch('researchtopodcast.cli.cli.get_speech_engine') as mock_get_speech:
        
        # Mock LLM
        mock_client = AsyncMock()
        mock_client.chat.return_value = "Mock LLM response"
        mock_get_llm.return_value = mock_client
        
        # Mock TTS
        mock_engine = AsyncMock()
        mock_engine.synthesize.return_value = Path("/tmp/episode.mp3")
        mock_get_speech.return_value = mock_engine
        
        output_dir = Path(settings.podgen_temp_dir) / "e2e_test"
        
        result = runner.invoke(app, [
            "generate",
            "--input", str(sample_document),
            "--duration", "150",
            "--mode", "solo",
            "--out", str(output_dir),
            "--title", "E2E Test Episode"
        ])
    
    assert result.exit_code == 0, f"CLI command failed with output: {result.output}"
    
    assert output_dir.exists()
    assert (output_dir / "script.podcast.yaml").exists()
    assert (output_dir / "episode.mp3").exists()
    
    # Verify script content
    from researchtopodcast.script_engine.formatter import ScriptFormatter
    formatter = ScriptFormatter()
    script = formatter.load_from_file(script_file)
    
    assert script.meta.title == "E2E Test Episode"
    assert script.meta.duration_sec == 150
    assert script.meta.mode == "solo"
    assert len(script.hosts) >= 1
    assert len(script.segments) >= 1


@pytest.mark.e2e
def test_end_to_end_multi_speaker(runner, sample_document):
    """Test end-to-end generation with multi-speaker mode."""
    with patch('researchtopodcast.cli.cli.get_llm_client') as mock_get_llm, \
         patch('researchtopodcast.cli.cli.get_speech_engine') as mock_get_speech:
        
        mock_client = AsyncMock()
        mock_client.chat.return_value = "Mock LLM response"
        mock_get_llm.return_value = mock_client
        
        mock_engine = AsyncMock()
        mock_engine.synthesize.return_value = Path("/tmp/episode.mp3")
        mock_get_speech.return_value = mock_engine
        
        output_dir = Path(settings.podgen_temp_dir) / "multi_speaker"
        
        result = runner.invoke(app, [
            "generate",
            "--input", str(sample_document),
            "--duration", "120",
            "--mode", "single-llm",
            "--out", str(output_dir),
            "--title", "Multi-Speaker Test"
        ])
    
    assert result.exit_code == 0, f"CLI command failed: {result.output}"
    
    assert output_dir.exists()
    assert (output_dir / "script.podcast.yaml").exists()
    
    from researchtopodcast.script_engine.formatter import ScriptFormatter
    formatter = ScriptFormatter()
    script = formatter.load_from_file(script_file)
    
    # Should have multiple hosts in multi-llm mode
    assert len(script.hosts) >= 2
    
    # Speakers should match the hosts
    host_names = {host.name for host in script.hosts}
    for segment in script.segments:
        assert segment.speaker in host_names


@pytest.mark.e2e
def test_end_to_end_with_missing_keys(runner, sample_document):
    """Test end-to-end with mocked LLM and TTS (no real API keys needed)."""
    with patch('researchtopodcast.cli.cli.get_llm_client') as mock_get_llm, \
         patch('researchtopodcast.cli.cli.get_speech_engine') as mock_get_speech:
        
        mock_client = AsyncMock()
        mock_client.chat.return_value = "Mock LLM response"
        mock_get_llm.return_value = mock_client
        
        mock_engine = AsyncMock()
        mock_engine.synthesize.return_value = Path("/tmp/episode.mp3")
        mock_get_speech.return_value = mock_engine
        
        output_dir = Path(settings.podgen_temp_dir) / "mocked_test"
        
        result = runner.invoke(app, [
            "generate",
            "--input", str(sample_document),
            "--duration", "60",
            "--mode", "solo",
            "--out", str(output_dir),
            "--title", "Mocked Test Episode"
        ])
    
    assert result.exit_code == 0, f"CLI command failed: {result.output}"
    
    assert output_dir.exists()
    assert (output_dir / "script.podcast.yaml").exists()


@pytest.mark.e2e
def test_cli_help_command(runner):
    """Test that the CLI help command works."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Transform documents into conversational podcasts" in result.output
    assert "generate" in result.output
    assert "list-voices" in result.output
    assert "serve" in result.output


@pytest.mark.e2e
def test_list_voices_command(runner):
    """Test the list-voices command."""
    result = runner.invoke(app, ["list-voices"])
    # Should not fail, even if no real TTS key is available
    # (it will use mock engine)
    assert result.exit_code == 0
    # Output should mention available voices
    assert "Available TTS voices" in result.output


@pytest.mark.e2e
def test_serve_command(runner):
    """Test the serve command (without actually starting the server)."""
    with patch('researchtopodcast.cli.cli.get_llm_client'), \
         patch('researchtopodcast.cli.cli.get_speech_engine'), \
         patch('researchtopodcast.cli.cli.uvicorn.run') as mock_run:
        
        result = runner.invoke(app, ["serve"])
        
        assert result.exit_code == 0
        mock_run.assert_called_once()


@pytest.mark.e2e
def test_generate_with_nonexistent_file(runner):
    """Test generating with a nonexistent input file."""
    result = runner.invoke(app, [
        "generate",
        "--input", "nonexistent.txt",
        "--duration", "60"
    ])
    
    # Should fail with exit code 1
    assert result.exit_code == 1
    # Should mention file not found
    assert "Input file not found" in result.output


@pytest.mark.e2e
def test_generate_with_empty_file(runner, tmp_path):
    """Test generating with an empty input file."""
    # Create an empty file
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("")
    
    result = runner.invoke(app, [
        "generate",
        "--input", str(empty_file),
        "--duration", "60"
    ])
    
    # Should fail
    assert result.exit_code == 1
    assert "Input file is empty" in result.output


@pytest.mark.e2e
def test_generate_with_invalid_mode(runner, sample_document):
    """Test generating with an invalid mode."""
    result = runner.invoke(app, [
        "generate",
        "--input", str(sample_document),
        "--duration", "60",
        "--mode", "invalid-mode"
    ])
    
    # Should fail
    assert result.exit_code == 1
    assert "Invalid mode" in result.output


@pytest.mark.e2e
def test_generate_with_custom_output_dir(runner, sample_document, tmp_path):
    """Test generating with a custom output directory."""
    with patch('researchtopodcast.cli.cli.get_llm_client') as mock_get_llm, \
         patch('researchtopodcast.cli.cli.get_speech_engine') as mock_get_speech:
        
        mock_client = AsyncMock()
        mock_client.chat.return_value = "Mock LLM response"
        mock_get_llm.return_value = mock_client
        
        mock_engine = AsyncMock()
        mock_engine.synthesize.return_value = tmp_path / "episode.mp3"
        mock_get_speech.return_value = mock_engine
        
        custom_dir = tmp_path / "custom_output"
        
        result = runner.invoke(app, [
            "generate",
            "--input", str(sample_document),
            "--duration", "60",
            "--mode", "solo",
            "--out", str(custom_dir),
            "--title", "Custom Output Test"
        ])
    
    assert result.exit_code == 0
    assert custom_dir.exists()
    assert (custom_dir / "script.podcast.yaml").exists()
    assert (custom_dir / "episode.mp3").exists()


def test_end_to_end_podcast_generation_api():
    """Test the complete API workflow."""
    # This test would require a running server and is typically
    # run in a separate environment, but we can outline the steps:
    pass
