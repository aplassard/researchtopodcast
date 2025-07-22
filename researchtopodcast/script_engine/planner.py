"""Script planning and generation."""

from enum import Enum
from typing import List, Dict, Any
from datetime import datetime

from ..llm_client import LLMClient, ChatMessage
from .persona import Persona, SOLO_PERSONAS, MULTI_SPEAKER_PERSONAS, MULTI_AGENT_PERSONAS


class ScriptMode(str, Enum):
    """Script generation modes."""
    SOLO = "solo"
    SINGLE_LLM_MULTI_SPEAKER = "single-llm"
    MULTI_AGENT_MULTI_SPEAKER = "multi-agent"


class ScriptPlanner:
    """Plans and generates podcast scripts."""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        
    async def generate_script(
        self,
        content: str,
        mode: ScriptMode = ScriptMode.SINGLE_LLM_MULTI_SPEAKER,
        duration_sec: int = 300,
        title: str | None = None
    ) -> Dict[str, Any]:
        """Generate a podcast script from content."""
        
        # Choose personas based on mode
        if mode == ScriptMode.SOLO:
            personas = SOLO_PERSONAS
        elif mode == ScriptMode.SINGLE_LLM_MULTI_SPEAKER:
            personas = MULTI_SPEAKER_PERSONAS
        else:  # MULTI_AGENT_MULTI_SPEAKER
            personas = MULTI_AGENT_PERSONAS
            
        # Estimate words needed (150 words per minute)
        target_words = int(duration_sec * 150 / 60)
        
        # Generate title if not provided
        if not title:
            title = await self._generate_title(content)
            
        # Generate script content
        if mode == ScriptMode.MULTI_AGENT_MULTI_SPEAKER:
            segments = await self._generate_multi_agent_script(content, personas, target_words)
        else:
            segments = await self._generate_single_llm_script(content, personas, target_words, mode)
            
        return {
            "meta": {
                "title": title,
                "duration_sec": duration_sec,
                "created": datetime.utcnow().isoformat() + "Z"
            },
            "hosts": [
                {
                    "name": persona.name,
                    "persona": persona.persona,
                    "voice_id": persona.voice_id
                }
                for persona in personas
            ],
            "segments": segments
        }
    
    async def _generate_title(self, content: str) -> str:
        """Generate a title for the podcast episode."""
        messages = [
            ChatMessage(
                role="system",
                content="You are a podcast title generator. Create engaging, concise titles for academic/technical content."
            ),
            ChatMessage(
                role="user",
                content=f"Generate a compelling podcast episode title for this content:\n\n{content[:1000]}..."
            )
        ]
        
        title = await self.llm_client.chat(messages, max_tokens=50)
        return title.strip().strip('"')
    
    async def _generate_single_llm_script(
        self,
        content: str,
        personas: List[Persona],
        target_words: int,
        mode: ScriptMode
    ) -> List[Dict[str, str]]:
        """Generate script using a single LLM."""
        
        if mode == ScriptMode.SOLO:
            system_prompt = f"""You are creating a solo podcast script. The host is {personas[0].name} ({personas[0].persona}).
            
Create a {target_words}-word script that transforms the given content into an engaging 5-minute podcast episode.
Format as alternating speaker segments. Use natural, conversational language.

Return ONLY the dialogue in this format:
SPEAKER: [dialogue text]
SPEAKER: [dialogue text]"""
        else:
            host_descriptions = "\n".join([f"- {p.name}: {p.persona}" for p in personas])
            system_prompt = f"""You are creating a multi-speaker podcast script with these hosts:
{host_descriptions}

Create a {target_words}-word conversational script that transforms the given content into an engaging 5-minute podcast episode.
The hosts should have natural banter, with {personas[1].name} asking questions and {personas[0].name} providing expert insights.

Return ONLY the dialogue in this format:
SPEAKER: [dialogue text]
SPEAKER: [dialogue text]"""
        
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=f"Content to transform:\n\n{content}")
        ]
        
        script_text = await self.llm_client.chat(messages, max_tokens=2000)
        return self._parse_script_segments(script_text)
    
    async def _generate_multi_agent_script(
        self,
        content: str,
        personas: List[Persona],
        target_words: int
    ) -> List[Dict[str, str]]:
        """Generate script using multiple LLM agents."""
        
        # For now, use single LLM approach but with more sophisticated prompting
        # In a full implementation, this would coordinate multiple LLM calls
        host_descriptions = "\n".join([f"- {p.name}: {p.persona}" for p in personas])
        system_prompt = f"""You are an orchestrator creating a multi-speaker podcast script with these hosts:
{host_descriptions}

Create a {target_words}-word conversational script with rich reasoning and fact-checking.
{personas[2].name} should occasionally interject with additional context or corrections.

Return ONLY the dialogue in this format:
SPEAKER: [dialogue text]
SPEAKER: [dialogue text]"""
        
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=f"Content to transform:\n\n{content}")
        ]
        
        script_text = await self.llm_client.chat(messages, max_tokens=2500)
        return self._parse_script_segments(script_text)
    
    def _parse_script_segments(self, script_text: str) -> List[Dict[str, str]]:
        """Parse script text into segments."""
        segments = []
        lines = script_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' in line and line:
                speaker, text = line.split(':', 1)
                segments.append({
                    "speaker": speaker.strip(),
                    "text": text.strip()
                })
        
        return segments
