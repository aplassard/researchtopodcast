"""Google Cloud Text-to-Speech integration."""

import asyncio
from pathlib import Path
from typing import List, Dict, Any
import tempfile
import os

try:
    from google.cloud import texttospeech
    GOOGLE_TTS_AVAILABLE = True
except ImportError:
    GOOGLE_TTS_AVAILABLE = False

from pydub import AudioSegment

from .base import Script


class GoogleTTSEngine:
    """Google Cloud Text-to-Speech engine."""
    
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self._client = None
        
        if api_key and GOOGLE_TTS_AVAILABLE:
            # Set up Google Cloud credentials
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = api_key
            self._client = texttospeech.TextToSpeechClient()
    
    async def synthesize(self, script: Script, output_path: Path, **kwargs) -> Path:
        """Synthesize script to audio file."""
        if not self._client:
            # Return mock audio for testing
            return await self._create_mock_audio(script, output_path)
        
        audio_segments = []
        
        for segment in script.segments:
            # Find voice for speaker
            voice_id = self._get_voice_for_speaker(segment["speaker"], script.hosts)
            
            # Synthesize segment
            audio_data = await self._synthesize_text(segment["text"], voice_id)
            
            # Convert to AudioSegment
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_file.write(audio_data)
                tmp_path = tmp_file.name
            
            try:
                audio_segment = AudioSegment.from_wav(tmp_path)
                audio_segments.append(audio_segment)
            finally:
                os.unlink(tmp_path)
        
        # Combine all segments
        combined_audio = sum(audio_segments, AudioSegment.empty())
        
        # Export to output path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        combined_audio.export(str(output_path), format="mp3")
        
        return output_path
    
    async def _synthesize_text(self, text: str, voice_id: str) -> bytes:
        """Synthesize text with given voice."""
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name=voice_id
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16
        )
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            self._client.synthesize_speech,
            synthesis_input,
            voice,
            audio_config
        )
        
        return response.audio_content
    
    def _get_voice_for_speaker(self, speaker_name: str, hosts: List[Dict[str, str]]) -> str:
        """Get voice ID for speaker."""
        for host in hosts:
            if host["name"] == speaker_name:
                return host["voice_id"]
        return "en-US-Standard-A"  # Default voice
    
    async def _create_mock_audio(self, script: Script, output_path: Path) -> Path:
        """Create mock audio file for testing."""
        # Create a short silent audio file
        duration_ms = script.meta.get("duration_sec", 300) * 1000
        silent_audio = AudioSegment.silent(duration=duration_ms)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        silent_audio.export(str(output_path), format="mp3")
        
        return output_path
    
    async def list_voices(self) -> List[Dict[str, str]]:
        """List available voices."""
        if not self._client:
            # Return mock voices for testing
            return [
                {"name": "en-US-Standard-A", "language": "en-US", "gender": "FEMALE"},
                {"name": "en-US-Standard-B", "language": "en-US", "gender": "MALE"},
                {"name": "en-US-Standard-C", "language": "en-US", "gender": "FEMALE"},
            ]
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            self._client.list_voices
        )
        
        voices = []
        for voice in response.voices:
            voices.append({
                "name": voice.name,
                "language": voice.language_codes[0] if voice.language_codes else "unknown",
                "gender": voice.ssml_gender.name
            })
        
        return voices
