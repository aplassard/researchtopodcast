"""Tests for CLI."""

import pytest
from pathlib import Path
import tempfile
from typer.testing import CliRunner

from researchtopodcast.cli.cli import app
from researchtopodcast.utils import DocumentLoader


def test_cli_help():
    """Test CLI help command."""
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "research2podcast" in result.stdout


@pytest.mark.asyncio
async def test_document_loader_text():
    """Test document loader with text file."""
    loader = DocumentLoader()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test content")
        f.flush()
        
        content = await loader.load(Path(f.name))
        assert content == "Test content"


@pytest.mark.asyncio
async def test_document_loader_markdown():
    """Test document loader with markdown file."""
    loader = DocumentLoader()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("# Test\n\nMarkdown content")
        f.flush()
        
        content = await loader.load(Path(f.name))
        assert "# Test" in content
        assert "Markdown content" in content


@pytest.mark.asyncio
async def test_document_loader_nonexistent():
    """Test document loader with nonexistent file."""
    loader = DocumentLoader()
    
    with pytest.raises(FileNotFoundError):
        await loader.load(Path("nonexistent.txt"))
