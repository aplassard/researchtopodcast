"""Command-line interface for research2podcast."""

import typer
from rich.console import Console

app = typer.Typer(help="Transform documents into conversational podcasts")
console = Console()


@app.command()
def generate(
    input_path: str = typer.Option(..., "--input", help="Input document path"),
    duration: int = typer.Option(300, "--duration", help="Target duration in seconds"),
    mode: str = typer.Option("solo", "--mode", help="Podcast mode: solo, single-llm, multi-agent"),
    output_dir: str = typer.Option("./output", "--out", help="Output directory"),
) -> None:
    """Generate a podcast from a document."""
    console.print(f"[green]Generating podcast from {input_path}[/green]")
    console.print(f"Mode: {mode}, Duration: {duration}s, Output: {output_dir}")
    # TODO: Implement actual generation logic
    console.print("[yellow]Generation not yet implemented[/yellow]")


@app.command()
def list_voices() -> None:
    """List available TTS voices."""
    console.print("[green]Available TTS voices:[/green]")
    # TODO: Implement voice listing
    console.print("[yellow]Voice listing not yet implemented[/yellow]")


@app.command()
def serve() -> None:
    """Start the web interface."""
    console.print("[green]Starting web interface...[/green]")
    # TODO: Implement server startup
    console.print("[yellow]Web interface not yet implemented[/yellow]")


if __name__ == "__main__":
    app()
