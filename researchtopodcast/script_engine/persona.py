"""Host persona definitions."""

from dataclasses import dataclass
from typing import List


@dataclass
class Persona:
    """A podcast host persona."""
    name: str
    persona: str
    voice_id: str


# Default personas for different modes
SOLO_PERSONAS = [
    Persona(
        name="Alex",
        persona="Single narrator with news-reader style delivery",
        voice_id="en-US-Standard-A"
    )
]

MULTI_SPEAKER_PERSONAS = [
    Persona(
        name="Dr. Ada",
        persona="Expert host—friendly, concise, knowledgeable",
        voice_id="en-US-Standard-A"
    ),
    Persona(
        name="Ben",
        persona="Curious co-host—asks clarifying questions, represents the audience",
        voice_id="en-US-Standard-B"
    )
]

MULTI_AGENT_PERSONAS = [
    Persona(
        name="Dr. Ada",
        persona="Expert host—friendly, concise, knowledgeable",
        voice_id="en-US-Standard-A"
    ),
    Persona(
        name="Ben",
        persona="Curious co-host—asks clarifying questions",
        voice_id="en-US-Standard-B"
    ),
    Persona(
        name="Chloe",
        persona="Fact-checker—provides additional context and verification",
        voice_id="en-US-Standard-C"
    )
]
