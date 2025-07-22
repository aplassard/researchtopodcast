"""Command-line interface."""

import asyncio
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..settings import settings
from ..llm_client import OpenRouterClient, OpenAIClient
from ..script_engine import ScriptPlanner, ScriptFormatter
from ..script_engine.planner import ScriptMode
from ..speech import GoogleTTSEngine, Script
from ..utils import DocumentLoader

app = typer.Typer(name="research2podcast", help="Transform documents into podcasts")
console = Console()


@app.command()
def generate(
    input_path: str = typer.Option(..., "--input", "-i", help="Input document path"),
    mode: ScriptMode = typer.Option(ScriptMode.SINGLE_LLM_MULTI_SPEAKER, "--mode", "-m", help="Generation mode"),
    duration: int = typer.Option(300, "--duration", "-d", help="Target duration in seconds"),
    output_dir: str = typer.Option("./output", "--out", "-o", help="Output directory"),
    openrouter_api_key: Optional[str] = typer.Option(None, "--openrouter-api-key", help="OpenRouter API key"),
    openai_api_key: Optional[str] = typer.Option(None, "--openai-api-key", help="OpenAI API key"),
):
    """Generate a podcast from a document."""
    asyncio.run(_generate_async(
        input_path=input_path,
        mode=mode,
        duration=duration,
        output_dir=output_dir,
        openrouter_api_key=openrouter_api_key,
        openai_api_key=openai_api_key,
    ))


async def _generate_async(
    input_path: str,
    mode: ScriptMode,
    duration: int,
    output_dir: str,
    openrouter_api_key: Optional[str],
    openai_api_key: Optional[str],
):
    """Async implementation of generate command."""
    
    # Override settings with CLI args if provided
    if openrouter_api_key:
        settings.openrouter_api_key = openrouter_api_key
    if openai_api_key:
        settings.openai_api_key = openai_api_key
    
    # Check for LLM configuration
    if not settings.has_llm_config:
        console.print("[red]Error: No LLM API key configured. Set OPENROUTER_API_KEY or OPENAI_API_KEY.[/red]")
        raise typer.Exit(1)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # Load document
        task = progress.add_task("Loading document...", total=None)
        loader = DocumentLoader()
        content = await loader.load(Path(input_path))
        progress.update(task, description="Document loaded ✓")
        
        # Initialize LLM client
        progress.update(task, description="Initializing LLM client...")
        if settings.openrouter_api_key:
            llm_client = OpenRouterClient(
                api_key=settings.openrouter_api_key,
                base_url=settings.openrouter_base_url
            )
        else:
            llm_client = OpenAIClient(api_key=settings.openai_api_key)
        
        # Generate script
        progress.update(task, description="Generating script...")
        planner = ScriptPlanner(llm_client)
        script_data = await planner.generate_script(
            content=content,
            mode=mode,
            duration_sec=duration
        )
        
        # Save script
        progress.update(task, description="Saving script...")
        formatter = ScriptFormatter()
        script_path = output_path / "episode01.podcast.yaml"
        formatter.save_script(script_data, script_path)
        
        # Synthesize audio
        progress.update(task, description="Synthesizing audio...")
        tts_engine = GoogleTTSEngine(settings.google_tts_key)
        script = Script(**script_data)
        audio_path = output_path / "episode01.mp3"
        await tts_engine.synthesize(script, audio_path)
        
        progress.update(task, description="Complete ✓")
    
    console.print(f"\n[green]✓ Podcast generated successfully![/green]")
    console.print(f"Script: {script_path}")
    console.print(f"Audio: {audio_path}")
    console.print(f"Duration: {duration} seconds")
    console.print(f"Cost: ${llm_client.cost():.4f}")


@app.command()
def list_voices():
    """List available TTS voices."""
    asyncio.run(_list_voices_async())


async def _list_voices_async():
    """Async implementation of list-voices command."""
    tts_engine = GoogleTTSEngine(settings.google_tts_key)
    voices = await tts_engine.list_voices()
    
    console.print("\n[bold]Available TTS Voices:[/bold]")
    for voice in voices:
        console.print(f"  {voice['name']} ({voice['language']}, {voice['gender']})")


@app.command()
def play(audio_path: str):
    """Play an audio file."""
    import subprocess
    import sys
    
    path = Path(audio_path)
    if not path.exists():
        console.print(f"[red]Error: File not found: {audio_path}[/red]")
        raise typer.Exit(1)
    
    # Try to play with system default player
    try:
        if sys.platform == "darwin":  # macOS
            subprocess.run(["open", str(path)])
        elif sys.platform == "linux":  # Linux
            subprocess.run(["xdg-open", str(path)])
        elif sys.platform == "win32":  # Windows
            subprocess.run(["start", str(path)], shell=True)
        else:
            console.print(f"[yellow]Cannot auto-play on this platform. Please open: {path}[/yellow]")
    except Exception as e:
        console.print(f"[red]Error playing file: {e}[/red]")


@app.command()
def serve():
    """Start the FastAPI + React development server."""
    console.print("[blue]Starting development server...[/blue]")
    console.print("This would run: docker compose up")
    console.print("API: http://localhost:8000")
    console.print("Frontend: http://localhost:5173")


if __name__ == "__main__":
    app()
