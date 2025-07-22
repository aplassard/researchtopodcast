"""Persona and script data models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum


class PodcastMode(Enum):
    """Supported podcast generation modes."""
    SOLO = "solo"
    SINGLE_LLM = "single-llm"
    MULTI_AGENT = "multi-agent"


@dataclass
class Host:
    """A podcast host with persona and voice configuration."""
    name: str
    persona: str
    voice_id: str
    
    def __post_init__(self):
        """Validate host configuration."""
        if not self.name.strip():
            raise ValueError("Host name cannot be empty")
        if not self.voice_id.strip():
            raise ValueError("Voice ID cannot be empty")


@dataclass
class Segment:
    """A single segment of podcast dialogue."""
    speaker: str
    text: str
    
    def __post_init__(self):
        """Validate segment."""
        if not self.speaker.strip():
            raise ValueError("Speaker cannot be empty")
        if not self.text.strip():
            raise ValueError("Segment text cannot be empty")
    
    @property
    def word_count(self) -> int:
        """Estimate word count for timing."""
        return len(self.text.split())
    
    @property
    def estimated_duration_seconds(self) -> float:
        """Estimate duration based on ~150 words per minute."""
        words_per_minute = 150
        return (self.word_count / words_per_minute) * 60


@dataclass
class ScriptMetadata:
    """Metadata for a podcast script."""
    title: str
    duration_sec: int
    created: datetime = field(default_factory=datetime.now)
    mode: PodcastMode = PodcastMode.SOLO
    source_document: Optional[str] = None
    
    def __post_init__(self):
        """Validate metadata."""
        if not self.title.strip():
            raise ValueError("Title cannot be empty")
        if self.duration_sec <= 0:
            raise ValueError("Duration must be positive")


@dataclass
class Script:
    """Complete podcast script with metadata, hosts, and segments."""
    meta: ScriptMetadata
    hosts: List[Host]
    segments: List[Segment]
    
    def __post_init__(self):
        """Validate script structure."""
        if not self.hosts:
            raise ValueError("Script must have at least one host")
        if not self.segments:
            raise ValueError("Script must have at least one segment")
        
        # Validate all speakers exist in hosts
        host_names = {host.name for host in self.hosts}
        for segment in self.segments:
            if segment.speaker not in host_names:
                raise ValueError(f"Speaker '{segment.speaker}' not found in hosts")
    
    @property
    def estimated_duration_seconds(self) -> float:
        """Calculate total estimated duration."""
        return sum(segment.estimated_duration_seconds for segment in self.segments)
    
    @property
    def total_words(self) -> int:
        """Calculate total word count."""
        return sum(segment.word_count for segment in self.segments)
    
    def get_host_by_name(self, name: str) -> Optional[Host]:
        """Get host by name."""
        for host in self.hosts:
            if host.name == name:
                return host
        return None


# Predefined persona templates
PERSONA_TEMPLATES = {
    PodcastMode.SOLO: [
        Host(
            name="Alex",
            persona="Professional narrator with a warm, engaging voice. Explains complex topics clearly and maintains listener interest.",
            voice_id="en-US-Standard-A"
        )
    ],
    
    PodcastMode.SINGLE_LLM: [
        Host(
            name="Dr. Ada",
            persona="Expert host—friendly, knowledgeable, and concise. Breaks down complex concepts into digestible explanations.",
            voice_id="en-US-Standard-A"
        ),
        Host(
            name="Ben",
            persona="Curious co-host—asks clarifying questions that listeners might have. Represents the educated layperson perspective.",
            voice_id="en-US-Standard-B"
        )
    ],
    
    PodcastMode.MULTI_AGENT: [
        Host(
            name="Dr. Ada",
            persona="Expert host—friendly, knowledgeable, and concise. Leads the discussion and provides authoritative explanations.",
            voice_id="en-US-Standard-A"
        ),
        Host(
            name="Ben",
            persona="Curious co-host—asks clarifying questions and provides the layperson perspective.",
            voice_id="en-US-Standard-B"
        ),
        Host(
            name="Chloe",
            persona="Fact-checker and researcher—provides additional context, verifies claims, and adds depth to the discussion.",
            voice_id="en-US-Standard-C"
        )
    ]
}
