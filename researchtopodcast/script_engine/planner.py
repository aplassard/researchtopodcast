"""Script planning and generation engine."""

import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

from ..llm_client import LLMClient, ChatMessage, SupportedModels, ModelProvider
from ..settings import settings
from .persona import Script, ScriptMetadata, Host, Segment, PodcastMode, PERSONA_TEMPLATES

logger = logging.getLogger(__name__)


class ScriptPlanner:
    """Plans and generates podcast scripts from input documents."""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
    
    async def generate_script(
        self,
        content: str,
        mode: PodcastMode,
        target_duration: int = 300,
        title: Optional[str] = None,
        source_document: Optional[str] = None,
        custom_hosts: Optional[List[Host]] = None
    ) -> Script:
        """Generate a complete podcast script from content."""
        
        logger.info(f"Generating {mode.value} script, target duration: {target_duration}s")
        
        # Use custom hosts or default templates
        hosts = custom_hosts or PERSONA_TEMPLATES[mode].copy()
        
        # Generate title if not provided
        if not title:
            title = await self._generate_title(content)
        
        # Create metadata
        metadata = ScriptMetadata(
            title=title,
            duration_sec=target_duration,
            mode=mode,
            source_document=source_document
        )
        
        # Generate segments based on mode
        if mode == PodcastMode.SOLO:
            segments = await self._generate_solo_script(content, hosts[0], target_duration)
        elif mode == PodcastMode.SINGLE_LLM:
            segments = await self._generate_single_llm_script(content, hosts, target_duration)
        elif mode == PodcastMode.MULTI_AGENT:
            segments = await self._generate_multi_agent_script(content, hosts, target_duration)
        else:
            raise ValueError(f"Unsupported mode: {mode}")
        
        script = Script(meta=metadata, hosts=hosts, segments=segments)
        
        # Adjust timing if needed
        script = await self._adjust_timing(script, target_duration)
        
        logger.info(f"Generated script: {len(segments)} segments, ~{script.estimated_duration_seconds:.1f}s")
        return script
    
    async def _generate_title(self, content: str) -> str:
        """Generate an engaging title from content."""
        prompt = f"""
You are a podcast title generator. Create an engaging, concise title for a 5-minute podcast episode based on this content.

Content summary:
{content[:500]}...

Requirements:
- Maximum 8 words
- Engaging and descriptive
- Suitable for a general audience
- No quotation marks in response

Title:
"""
        
        messages = [ChatMessage(role="user", content=prompt)]
        response = await self.llm_client.chat(
            messages=messages,
            model=self._get_default_model(),
            max_tokens=100,
            temperature=0.7
        )
        
        # Clean up the title
        title = response.content.strip().strip('"').strip("'")
        return title
    
    async def _generate_solo_script(self, content: str, host: Host, target_duration: int) -> List[Segment]:
        """Generate solo narration script."""
        target_words = int(target_duration * 150 / 60)  # 150 words per minute
        
        prompt = f"""
You are {host.name}, a podcast host. {host.persona}

Transform this content into an engaging {target_duration}-second solo podcast narration.

Content:
{content}

Requirements:
- Conversational, engaging tone
- Approximately {target_words} words ({target_duration} seconds at 150 words/minute)
- Break into natural paragraphs for pacing
- Include smooth transitions
- Make complex topics accessible
- No speaker labels needed (solo narration)

Begin the narration:
"""
        
        messages = [ChatMessage(role="user", content=prompt)]
        response = await self.llm_client.chat(
            messages=messages,
            model=self._get_default_model(),
            max_tokens=settings.podgen_max_tokens,
            temperature=0.7
        )
        
        # Parse the response into segments
        segments = self._parse_solo_response(response.content, host.name)
        return segments
    
    async def _generate_single_llm_script(self, content: str, hosts: List[Host], target_duration: int) -> List[Segment]:
        """Generate multi-speaker script using single LLM."""
        target_words = int(target_duration * 150 / 60)
        
        host_descriptions = "\n".join([f"{host.name}: {host.persona}" for host in hosts])
        
        prompt = f"""
You are creating a {target_duration}-second podcast conversation between these hosts:

{host_descriptions}

Transform this content into a natural conversation:

{content}

Requirements:
- Approximately {target_words} words total ({target_duration} seconds at 150 words/minute)
- Natural back-and-forth dialogue
- Each speaker should have multiple turns
- Use format: "Speaker Name: dialogue text"
- Include questions, explanations, and reactions
- Make complex topics accessible through conversation
- Maintain engaging pace and flow

Begin the conversation:
"""
        
        messages = [ChatMessage(role="user", content=prompt)]
        response = await self.llm_client.chat(
            messages=messages,
            model=self._get_default_model(),
            max_tokens=settings.podgen_max_tokens,
            temperature=0.8
        )
        
        # Parse the response into segments
        segments = self._parse_multi_speaker_response(response.content, hosts)
        return segments
    
    async def _generate_multi_agent_script(self, content: str, hosts: List[Host], target_duration: int) -> List[Segment]:
        """Generate script using multiple specialized agents."""
        # For now, use single LLM approach but with more specialized prompts
        # TODO: Implement true multi-agent orchestration
        return await self._generate_single_llm_script(content, hosts, target_duration)
    
    def _parse_solo_response(self, response: str, speaker_name: str) -> List[Segment]:
        """Parse solo narration response into segments."""
        # Split into natural segments (paragraphs)
        paragraphs = [p.strip() for p in response.split('\n\n') if p.strip()]
        
        segments = []
        for paragraph in paragraphs:
            if paragraph:
                segments.append(Segment(speaker=speaker_name, text=paragraph))
        
        return segments
    
    def _parse_multi_speaker_response(self, response: str, hosts: List[Host]) -> List[Segment]:
        """Parse multi-speaker response into segments."""
        segments = []
        host_names = {host.name for host in hosts}
        
        lines = response.split('\n')
        current_speaker = None
        current_text = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts with a speaker name
            speaker_found = None
            for name in host_names:
                if line.startswith(f"{name}:"):
                    speaker_found = name
                    text = line[len(name)+1:].strip()
                    break
            
            if speaker_found:
                # Save previous segment if exists
                if current_speaker and current_text:
                    segments.append(Segment(
                        speaker=current_speaker,
                        text=' '.join(current_text)
                    ))
                
                # Start new segment
                current_speaker = speaker_found
                current_text = [text] if text else []
            else:
                # Continue current segment
                if current_speaker:
                    current_text.append(line)
        
        # Save final segment
        if current_speaker and current_text:
            segments.append(Segment(
                speaker=current_speaker,
                text=' '.join(current_text)
            ))
        
        return segments
    
    async def _adjust_timing(self, script: Script, target_duration: int) -> Script:
        """Adjust script timing to match target duration."""
        current_duration = script.estimated_duration_seconds
        target_tolerance = target_duration * 0.05  # 5% tolerance
        
        if abs(current_duration - target_duration) <= target_tolerance:
            return script  # Already within tolerance
        
        # If too long, trim segments
        if current_duration > target_duration:
            return await self._trim_script(script, target_duration)
        
        # If too short, return as-is for now
        return script
    
    async def _trim_script(self, script: Script, target_duration: int) -> Script:
        """Trim script to fit target duration."""
        # Simple approach: remove segments from the end
        segments = script.segments.copy()
        while segments:
            current_duration = sum(s.estimated_duration_seconds for s in segments)
            if current_duration <= target_duration:
                break
            segments.pop()
        
        return Script(meta=script.meta, hosts=script.hosts, segments=segments)
    
    def _get_default_model(self) -> str:
        """Get the default model for script generation."""
        if settings.openrouter_api_key:
            return "openai/gpt-4o-mini"
        elif settings.openai_api_key:
            return "gpt-4o-mini"
        else:
            raise ValueError("No LLM API key configured")
