"""Base speech synthesis interface."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Protocol


@dataclass
class Script:
    """A podcast script."""
    meta: Dict[str, Any]
    hosts: List[Dict[str, str]]
    segments: List[Dict[str, str]]


class SpeechEngine(Protocol):
    """Protocol for speech synthesis engines."""
    
    async def synthesize(self, script: Script, output_path: Path, **kwargs) -> Path:
        """Synthesize script to audio file."""
        ...
    
    async def list_voices(self) -> List[Dict[str, str]]:
        """List available voices."""
        ...
