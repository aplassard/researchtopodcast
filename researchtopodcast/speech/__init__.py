"""Speech synthesis package."""

from .base import SpeechEngine, Script
from .google import GoogleTTSEngine

__all__ = ["SpeechEngine", "Script", "GoogleTTSEngine"]
