"""Main CLI application using Typer."""

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..settings import settings
from ..llm_client.openrouter import OpenRouterClient
from ..llm_client.openai import OpenAIClient
from ..script_engine.planner import ScriptPlanner
from ..script_engine.persona import PodcastMode
from ..script_engine.formatter import ScriptFormatter
from ..speech.google import GoogleTTSEngine

app = typer.Typer(
    name="research2podcast",
    help="Transform research documents into conversational podcasts.",
    no_args_is_help=True,
)
console = Console()


def get_llm_client():
    """Get configured LLM client."""
    if settings.openrouter_api_key:
        return OpenRouterClient()
    elif settings.openai_api_key:
        return OpenAIClient()
    else:
        console.print("[red]Error: No LLM API key configured.[/red]")
        console.print("Set OPENROUTER_API_KEY or OPENAI_API_KEY environment variable.")
        raise typer.Exit(1)


@app.command()
def generate(
    input_file: Path = typer.Argument(..., help="Input document (PDF/Markdown/HTML)"),
    mode: PodcastMode = typer.Option(PodcastMode.SINGLE_LLM, help="Podcast generation mode"),
    duration: int = typer.Option(300, help="Target duration in seconds"),
    output: Path = typer.Option(Path("./output"), help="Output directory"),
    title: Optional[str] = typer.Option(None, help="Episode title"),
):
    """Generate a podcast from a document."""
    asyncio.run(_generate_async(input_file, mode, duration, output, title))


async def _generate_async(
    input_file: Path,
    mode: PodcastMode,
    duration: int,
    output: Path,
    title: Optional[str],
):
    """Async implementation of generate command."""
    
    if not input_file.exists():
        console.print(f"[red]Error: Input file {input_file} not found.[/red]")
        raise typer.Exit(1)
    
    # Read input content (simplified - would need proper document parsing)
    content = input_file.read_text(encoding="utf-8")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # Generate script
        task1 = progress.add_task("Generating script...", total=None)
        
        llm_client = get_llm_client()
        planner = ScriptPlanner(llm_client)
        
        script_data = await planner.generate_script(
            content=content,
            mode=mode,
            duration_sec=duration,
            title=title or input_file.stem,
        )
        
        progress.update(task1, description="Script generated ✓")
        
        # Save script
        task2 = progress.add_task("Saving script...", total=None)
        
        formatter = ScriptFormatter()
        script = formatter.format_script(script_data)
        
        output.mkdir(parents=True, exist_ok=True)
        script_path = output / f"{input_file.stem}.podcast.yaml"
        formatter.save_script(script, script_path)
        
        progress.update(task2, description="Script saved ✓")
        
        # Generate audio
        task3 = progress.add_task("Synthesizing audio...", total=None)
        
        tts_engine = GoogleTTSEngine()
        audio_path = output / f"{input_file.stem}.mp3"
        
        await tts_engine.synthesize(script, audio_path)
        
        progress.update(task3, description="Audio generated ✓")
    
    console.print(f"\n[green]✓ Podcast generated successfully![/green]")
    console.print(f"Script: {script_path}")
    console.print(f"Audio: {audio_path}")
    console.print(f"Cost: ${llm_client.cost():.4f}")


@app.command()
def list_voices():
    """List available TTS voices."""
    asyncio.run(_list_voices_async())


async def _list_voices_async():
    """Async implementation of list-voices command."""
    tts_engine = GoogleTTSEngine()
    voices = await tts_engine.list_voices()
    
    console.print("\n[bold]Available TTS Voices:[/bold]")
    for voice in voices:
        console.print(f"  {voice.id} - {voice.language} ({voice.gender})")


@app.command()
def serve(
    host: str = typer.Option("localhost", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
):
    """Start the web interface."""
    try:
        import uvicorn
        from ..api.main import app as api_app
        
        console.print(f"Starting web interface at http://{host}:{port}")
        uvicorn.run(api_app, host=host, port=port)
    except ImportError:
        console.print("[red]Error: FastAPI/Uvicorn not available for web interface.[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
