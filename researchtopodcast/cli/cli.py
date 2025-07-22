"""Command-line interface for research2podcast."""

import asyncio
import uvicorn
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from pypdf import PdfReader
from bs4 import BeautifulSoup
import markdown

from ..settings import settings
from ..llm_client import OpenRouterClient, OpenAIClient
from ..script_engine import ScriptPlanner, ScriptFormatter, PodcastMode
from ..speech import GoogleTTSEngine, MockTTSEngine

app = typer.Typer(help="Transform documents into conversational podcasts")
console = Console()


def get_llm_client():
    """Get configured LLM client."""
    if settings.openrouter_api_key:
        return OpenRouterClient(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url
        )
    elif settings.openai_api_key:
        return OpenAIClient(api_key=settings.openai_api_key)
    else:
        # Return a mock client when no API key is configured for testing
        mock_client = MagicMock()
        mock_client.name = "mock-llm"
        return mock_client


def get_speech_engine():
    """Get configured speech engine."""
    if settings.google_tts_key:
        return GoogleTTSEngine(credentials_path=settings.google_tts_key)
    else:
        console.print("[yellow]No Google TTS key configured, using mock engine[/yellow]")
        return MockTTSEngine()


@app.command()
def generate(
    input_path: str = typer.Option(..., "--input", help="Input document path"),
    duration: int = typer.Option(300, "--duration", help="Target duration in seconds"),
    mode: str = typer.Option("solo", "--mode", help="Podcast mode: solo, single-llm, multi-agent"),
    output_dir: str = typer.Option("./output", "--out", help="Output directory"),
    title: Optional[str] = typer.Option(None, "--title", help="Custom podcast title"),
) -> None:
    """Generate a podcast from a document."""
    
    async def _generate():
        try:
            # Validate mode
            mode_map = {
                "solo": PodcastMode.SOLO,
                "single-llm": PodcastMode.SINGLE_LLM,
                "multi-agent": PodcastMode.MULTI_AGENT
            }
            
            if mode not in mode_map:
                console.print(f"[red]Invalid mode: {mode}. Use: solo, single-llm, multi-agent[/red]")
                raise typer.Exit(1)
            
            podcast_mode = mode_map[mode]
            
            # Read input file
            input_file = Path(input_path)
            if not input_file.exists():
                console.print(f"[red]Input file not found: {input_path}[/red]")
                raise typer.Exit(1)
            
            console.print(f"[green]Reading input file: {input_path}[/green]")
            
            # Extract text based on file type
            suffix = input_file.suffix.lower()
            
            try:
                if suffix == ".pdf":
                    reader = PdfReader(input_file)
                    content = "\n".join([page.extract_text() for page in reader.pages])
                elif suffix == ".html":
                    html = input_file.read_text(encoding='utf-8')
                    soup = BeautifulSoup(html, "html.parser")
                    content = soup.get_text()
                elif suffix == ".md":
                    md = input_file.read_text(encoding='utf-8')
                    content = markdown.markdown(md)
                else:
                    content = input_file.read_text(encoding='utf-8')
                    
                if len(content.strip()) == 0:
                    console.print("[red]Input file is empty[/red]")
                    raise typer.Exit(1)
                    
            except Exception as e:
                console.print(f"[red]Error reading file: {e}[/red]")
                raise typer.Exit(1)
            
            if len(content.strip()) == 0:
                console.print("[red]Input file is empty[/red]")
                raise typer.Exit(1)
            
            # Initialize components
            console.print("[blue]Initializing LLM client...[/blue]")
            llm_client = get_llm_client()
            
            console.print("[blue]Initializing speech engine...[/blue]")
            speech_engine = get_speech_engine()
            
            # Generate script
            console.print(f"[green]Generating {mode} script (target: {duration}s)...[/green]")
            planner = ScriptPlanner(llm_client)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Generating script...", total=None)
                
                script = await planner.generate_script(
                    content=content,
                    mode=podcast_mode,
                    target_duration=duration,
                    title=title,
                    source_document=str(input_file)
                )
                
                progress.update(task, description="Script generated!")
            
            # Save script
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            script_file = output_path / "script.podcast.yaml"
            formatter = ScriptFormatter()
            formatter.save_to_file(script, script_file)
            
            console.print(f"[green]Script saved: {script_file}[/green]")
            console.print(f"Title: {script.meta.title}")
            console.print(f"Estimated duration: {script.estimated_duration_seconds:.1f}s")
            console.print(f"Total words: {script.total_words}")
            
            # Synthesize audio
            console.print("[green]Synthesizing audio...[/green]")
            audio_file = output_path / "episode.mp3"
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Synthesizing audio...", total=None)
                
                final_audio = await speech_engine.synthesize(script, audio_file)
                
                progress.update(task, description="Audio synthesized!")
            
            console.print(f"[green]Podcast generated successfully![/green]")
            console.print(f"Audio file: {final_audio}")
            console.print(f"Script file: {script_file}")
            
            # Show usage stats
            if hasattr(llm_client, 'total_usage'):
                usage = llm_client.total_usage
                console.print(f"\n[blue]LLM Usage:[/blue]")
                console.print(f"  Tokens: {usage.total_tokens}")
                console.print(f"  Cost: ${usage.cost_usd:.4f}")
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
    
    asyncio.run(_generate())


@app.command()
def list_voices() -> None:
    """List available TTS voices."""
    
    async def _list_voices():
        try:
            speech_engine = get_speech_engine()
            voices = await speech_engine.list_voices()
            
            console.print("[green]Available TTS voices:[/green]")
            for voice in voices[:10]:  # Show first 10
                console.print(f"  {voice['name']} ({voice.get('ssml_gender', 'Unknown')})")
            
            if len(voices) > 10:
                console.print(f"  ... and {len(voices) - 10} more voices")
                
        except Exception as e:
            console.print(f"[red]Error listing voices: {e}[/red]")
            raise typer.Exit(1)
    
    asyncio.run(_list_voices())


@app.command()
def serve() -> None:
    """Start the FastAPI web server."""
    from ..api.main import app as fastapi_app
    
    console.print("[green]Starting Research2Podcast API server...[/green]")
    console.print(f"[blue]Server will be available at: http://{settings.api_host}:{settings.api_port}[/blue]")
    console.print(f"[blue]API docs: http://{settings.api_host}:{settings.api_port}/docs[/blue]")
    
    uvicorn.run(
        fastapi_app,
        host=settings.api_host,
        port=settings.api_port,
        log_level="info"
    )


if __name__ == "__main__":
    app()
