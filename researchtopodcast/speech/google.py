"""Google Cloud Text-to-Speech implementation."""

import asyncio
import logging
from pathlib import Path
from typing import List, Optional
from google.cloud import texttospeech
from pydub import AudioSegment
import io

from .base import BaseSpeechEngine
from ..script_engine import Script
from ..settings import settings

logger = logging.getLogger(__name__)


class GoogleTTSEngine(BaseSpeechEngine):
    """Google Cloud Text-to-Speech engine."""
    
    def __init__(self, credentials_path: Optional[str] = None):
        self.credentials_path = credentials_path
        self._client = None
    
    @property
    def client(self) -> texttospeech.TextToSpeechClient:
        """Get or create TTS client."""
        if self._client is None:
            if self.credentials_path:
                self._client = texttospeech.TextToSpeechClient.from_service_account_file(
                    self.credentials_path
                )
            else:
                # Use default credentials (environment variable)
                self._client = texttospeech.TextToSpeechClient()
        return self._client
    
    async def synthesize(self, script: Script, output_path: Path, **kwargs) -> Path:
        """Synthesize script to audio file."""
        logger.info(f"Synthesizing script to {output_path}")
        
        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Synthesize each segment
        audio_segments = []
        
        for i, segment in enumerate(script.segments):
            logger.debug(f"Synthesizing segment {i+1}/{len(script.segments)}: {segment.speaker}")
            
            # Get voice for this speaker
            host = script.get_host_by_name(segment.speaker)
            if not host:
                raise ValueError(f"Host not found for speaker: {segment.speaker}")
            
            # Synthesize this segment
            audio_data = await self._synthesize_segment(segment.text, host.voice_id)
            
            # Convert to AudioSegment
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
            audio_segments.append(audio_segment)
            
            # Add small pause between speakers (except for same speaker)
            if i < len(script.segments) - 1:
                next_segment = script.segments[i + 1]
                if next_segment.speaker != segment.speaker:
                    # Add 500ms pause between different speakers
                    pause = AudioSegment.silent(duration=500)
                    audio_segments.append(pause)
        
        # Combine all segments
        final_audio = sum(audio_segments)
        
        # Export to file
        if output_path.suffix.lower() == '.mp3':
            final_audio.export(str(output_path), format="mp3")
        elif output_path.suffix.lower() == '.wav':
            final_audio.export(str(output_path), format="wav")
        else:
            # Default to MP3
            output_path = output_path.with_suffix('.mp3')
            final_audio.export(str(output_path), format="mp3")
        
        logger.info(f"Synthesis complete: {output_path}")
        return output_path
    
    async def _synthesize_segment(self, text: str, voice_id: str) -> bytes:
        """Synthesize a single text segment."""
        # Parse voice_id (format: "en-US-Standard-A")
        parts = voice_id.split('-')
        if len(parts) >= 3:
            language_code = f"{parts[0]}-{parts[1]}"
            voice_name = voice_id
        else:
            language_code = "en-US"
            voice_name = "en-US-Standard-A"
        
        # Set up synthesis input
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # Configure voice
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_name
        )
        
        # Configure audio
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.0
        )
        
        # Run synthesis in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            self.client.synthesize_speech,
            {
                "input": synthesis_input,
                "voice": voice,
                "audio_config": audio_config
            }
        )
        
        return response.audio_content
    
    async def list_voices(self) -> List[dict]:
        """List available voices."""
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            self.client.list_voices
        )
        
        voices = []
        for voice in response.voices:
            voices.append({
                "name": voice.name,
                "language_codes": list(voice.language_codes),
                "ssml_gender": voice.ssml_gender.name,
                "natural_sample_rate_hertz": voice.natural_sample_rate_hertz
            })
        
        return voices


class MockTTSEngine(BaseSpeechEngine):
    """Mock TTS engine for testing."""
    
    async def synthesize(self, script: Script, output_path: Path, **kwargs) -> Path:
        """Create a mock audio file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create a simple audio file with silence
        duration_ms = int(script.estimated_duration_seconds * 1000)
        silence = AudioSegment.silent(duration=duration_ms)
        
        if output_path.suffix.lower() == '.mp3':
            silence.export(str(output_path), format="mp3")
        else:
            output_path = output_path.with_suffix('.mp3')
            silence.export(str(output_path), format="mp3")
        
        return output_path
    
    async def list_voices(self) -> List[dict]:
        """Return mock voice list."""
        return [
            {
                "name": "en-US-Standard-A",
                "language_codes": ["en-US"],
                "ssml_gender": "FEMALE",
                "natural_sample_rate_hertz": 24000
            },
            {
                "name": "en-US-Standard-B",
                "language_codes": ["en-US"],
                "ssml_gender": "MALE",
                "natural_sample_rate_hertz": 24000
            },
            {
                "name": "en-US-Standard-C",
                "language_codes": ["en-US"],
                "ssml_gender": "FEMALE",
                "natural_sample_rate_hertz": 24000
            }
        ]
