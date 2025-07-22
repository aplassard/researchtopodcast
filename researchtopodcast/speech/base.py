"""Base classes for speech synthesis."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Protocol
from ..script_engine import Script


class SpeechEngine(Protocol):
    """Protocol for speech synthesis engines."""
    
    async def synthesize(self, script: Script, output_path: Path, **kwargs) -> Path:
        """Synthesize script to audio file."""
        ...
    
    async def list_voices(self) -> List[dict]:
        """List available voices."""
        ...


class BaseSpeechEngine(ABC):
    """Abstract base class for speech engines."""
    
    @abstractmethod
    async def synthesize(self, script: Script, output_path: Path, **kwargs) -> Path:
        """Synthesize script to audio file."""
        pass
    
    @abstractmethod
    async def list_voices(self) -> List[dict]:
        """List available voices."""
        pass
