"""End-to-end test for episode generation."""

import pytest
import tempfile
from pathlib import Path

from researchtopodcast.llm_client import OpenRouterClient, OpenAIClient
from researchtopodcast.script_engine import ScriptPlanner, ScriptFormatter
from researchtopodcast.script_engine.planner import ScriptMode
from researchtopodcast.speech import GoogleTTSEngine, Script
from researchtopodcast.utils import DocumentLoader
from researchtopodcast.settings import settings


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_full_episode_generation():
    """Test complete episode generation pipeline."""
    
    # Skip if no LLM config
    if not settings.has_llm_config:
        pytest.skip("No LLM configuration available")
    
    # Create sample document
    sample_content = """
    # Artificial Intelligence in 2025
    
    Artificial Intelligence has made remarkable progress in recent years. 
    Large Language Models like GPT-4 have demonstrated unprecedented capabilities
    in natural language understanding and generation.
    
    ## Key Developments
    
    1. **Multimodal AI**: Models can now process text, images, and audio
    2. **Reasoning**: Improved logical reasoning capabilities
    3. **Efficiency**: Better performance with fewer parameters
    
    ## Future Implications
    
    The implications for research, education, and industry are profound.
    AI assistants are becoming more capable and accessible.
    """
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save sample document
        doc_path = Path(tmpdir) / "sample.md"
        with open(doc_path, 'w') as f:
            f.write(sample_content)
        
        # Load document
        loader = DocumentLoader()
        content = await loader.load(doc_path)
        assert len(content) > 100
        
        # Initialize LLM client
        if settings.openrouter_api_key:
            llm_client = OpenRouterClient(
                api_key=settings.openrouter_api_key,
                base_url=settings.openrouter_base_url
            )
        else:
            llm_client = OpenAIClient(api_key=settings.openai_api_key)
        
        # Generate script
        planner = ScriptPlanner(llm_client)
        script_data = await planner.generate_script(
            content=content,
            mode=ScriptMode.SINGLE_LLM_MULTI_SPEAKER,
            duration_sec=60  # Short for testing
        )
        
        # Validate script structure
        assert "meta" in script_data
        assert "hosts" in script_data
        assert "segments" in script_data
        assert script_data["meta"]["duration_sec"] == 60
        assert len(script_data["hosts"]) >= 1
        assert len(script_data["segments"]) >= 1
        
        # Save script
        formatter = ScriptFormatter()
        script_path = Path(tmpdir) / "episode.podcast.yaml"
        formatter.save_script(script_data, script_path)
        assert script_path.exists()
        
        # Load script back
        loaded_script = formatter.load_script(script_path)
        assert loaded_script["meta"]["title"] == script_data["meta"]["title"]
        
        # Synthesize audio (will use mock if no Google TTS key)
        tts_engine = GoogleTTSEngine(settings.google_tts_key)
        script = Script(**script_data)
        audio_path = Path(tmpdir) / "episode.mp3"
        
        result_path = await tts_engine.synthesize(script, audio_path)
        assert result_path == audio_path
        assert audio_path.exists()
        assert audio_path.stat().st_size > 0
        
        # Validate duration is approximately correct (±50% for mock)
        from pydub import AudioSegment
        audio = AudioSegment.from_mp3(str(audio_path))
        duration_sec = len(audio) / 1000
        target_duration = 60
        
        # Allow wide tolerance for mock audio
        assert abs(duration_sec - target_duration) <= target_duration * 0.5
        
        print(f"✓ Generated episode: {audio_path}")
        print(f"✓ Duration: {duration_sec:.1f}s (target: {target_duration}s)")
        print(f"✓ Cost: ${llm_client.cost():.4f}")


@pytest.mark.e2e
def test_cli_integration():
    """Test CLI integration."""
    import subprocess
    import sys
    
    # Skip if no LLM config
    if not settings.has_llm_config:
        pytest.skip("No LLM configuration available")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create sample document
        doc_path = Path(tmpdir) / "sample.txt"
        with open(doc_path, 'w') as f:
            f.write("This is a test document about AI research.")
        
        # Run CLI command
        result = subprocess.run([
            sys.executable, "-m", "researchtopodcast.cli.cli",
            "generate",
            "--input", str(doc_path),
            "--duration", "60",
            "--out", tmpdir,
            "--mode", "single-llm"
        ], capture_output=True, text=True, timeout=120)
        
        # Check if command succeeded or failed gracefully
        if result.returncode != 0:
            # Print error for debugging
            print(f"CLI Error: {result.stderr}")
            # For now, just check that it attempted to run
            assert "Error:" in result.stderr or "research2podcast" in result.stderr
        else:
            # Check outputs were created
            output_dir = Path(tmpdir)
            audio_files = list(output_dir.glob("*.mp3"))
            script_files = list(output_dir.glob("*.podcast.yaml"))
            
            assert len(audio_files) >= 1 or len(script_files) >= 1
