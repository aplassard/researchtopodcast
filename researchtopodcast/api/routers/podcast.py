"""Podcast generation API endpoints."""

import asyncio
import uuid
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import logging

from ...settings import settings
from ...script_engine import ScriptPlanner, ScriptFormatter, PodcastMode
from ...llm_client import LLMClient
from ...speech import SpeechEngine
from ..dependencies import get_llm_client, get_speech_engine, validate_api_config

logger = logging.getLogger(__name__)

router = APIRouter(tags=["podcast"])

# In-memory storage for job status (use Redis/DB in production)
job_status: Dict[str, Dict] = {}


class PodcastRequest(BaseModel):
    """Request model for podcast generation."""
    content: str = Field(..., description="Document content to convert")
    mode: str = Field("solo", description="Podcast mode: solo, single-llm, multi-agent")
    duration: int = Field(300, ge=30, le=1800, description="Target duration in seconds")
    title: Optional[str] = Field(None, description="Custom podcast title")


class PodcastResponse(BaseModel):
    """Response model for podcast generation."""
    job_id: str
    status: str
    message: str


class JobStatus(BaseModel):
    """Job status response model."""
    job_id: str
    status: str  # pending, processing, completed, failed
    progress: float  # 0.0 to 1.0
    message: str
    download_url: Optional[str] = None
    script_url: Optional[str] = None
    error: Optional[str] = None


class VoiceInfo(BaseModel):
    """Voice information model."""
    name: str
    language_codes: List[str]
    ssml_gender: str
    natural_sample_rate_hertz: int


@router.post("/podcast", response_model=PodcastResponse)
async def create_podcast(
    request: PodcastRequest,
    background_tasks: BackgroundTasks,
    llm_client: LLMClient = Depends(get_llm_client),
    speech_engine: SpeechEngine = Depends(get_speech_engine)
):
    """Generate a podcast from content."""
    
    # Validate configuration
    validate_api_config()
    
    # Validate mode
    mode_map = {
        "solo": PodcastMode.SOLO,
        "single-llm": PodcastMode.SINGLE_LLM,
        "multi-agent": PodcastMode.MULTI_AGENT
    }
    
    if request.mode not in mode_map:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode: {request.mode}. Use: solo, single-llm, multi-agent"
        )
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Initialize job status
    job_status[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0.0,
        "message": "Job queued for processing",
        "download_url": None,
        "script_url": None,
        "error": None
    }
    
    # Start background task
    background_tasks.add_task(
        generate_podcast_task,
        job_id,
        request,
        mode_map[request.mode],
        llm_client,
        speech_engine
    )
    
    return PodcastResponse(
        job_id=job_id,
        status="pending",
        message="Podcast generation started"
    )


@router.get("/podcast/{job_id}", response_model=JobStatus)
async def get_podcast_status(job_id: str):
    """Get podcast generation status."""
    
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatus(**job_status[job_id])


@router.get("/podcast/{job_id}/download")
async def download_podcast(job_id: str):
    """Download generated podcast audio."""
    
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    status = job_status[job_id]
    if status["status"] != "completed":
        raise HTTPException(status_code=400, detail="Podcast not ready for download")
    
    if not status["download_url"]:
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    audio_path = Path(status["download_url"])
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        path=str(audio_path),
        media_type="audio/mpeg",
        filename=f"podcast_{job_id}.mp3"
    )


@router.get("/podcast/{job_id}/script")
async def download_script(job_id: str):
    """Download generated podcast script."""
    
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    status = job_status[job_id]
    if status["status"] != "completed":
        raise HTTPException(status_code=400, detail="Script not ready for download")
    
    if not status["script_url"]:
        raise HTTPException(status_code=404, detail="Script file not found")
    
    script_path = Path(status["script_url"])
    if not script_path.exists():
        raise HTTPException(status_code=404, detail="Script file not found")
    
    return FileResponse(
        path=str(script_path),
        media_type="application/x-yaml",
        filename=f"script_{job_id}.podcast.yaml"
    )


@router.get("/voices", response_model=List[VoiceInfo])
async def list_voices(
    speech_engine: SpeechEngine = Depends(get_speech_engine)
):
    """List available TTS voices."""
    
    try:
        voices = await speech_engine.list_voices()
        return [VoiceInfo(**voice) for voice in voices]
    except Exception as e:
        logger.error(f"Error listing voices: {e}")
        raise HTTPException(status_code=500, detail="Error listing voices")


async def generate_podcast_task(
    job_id: str,
    request: PodcastRequest,
    mode: PodcastMode,
    llm_client: LLMClient,
    speech_engine: SpeechEngine
):
    """Background task to generate podcast."""
    
    try:
        # Update status
        job_status[job_id].update({
            "status": "processing",
            "progress": 0.1,
            "message": "Generating script..."
        })
        
        # Generate script
        planner = ScriptPlanner(llm_client)
        script = await planner.generate_script(
            content=request.content,
            mode=mode,
            target_duration=request.duration,
            title=request.title
        )
        
        # Update progress
        job_status[job_id].update({
            "progress": 0.5,
            "message": "Script generated, synthesizing audio..."
        })
        
        # Create output directory
        output_dir = Path(settings.podgen_temp_dir) / job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save script
        script_file = output_dir / "script.podcast.yaml"
        formatter = ScriptFormatter()
        formatter.save_to_file(script, script_file)
        
        # Update progress
        job_status[job_id].update({
            "progress": 0.7,
            "message": "Synthesizing audio..."
        })
        
        # Synthesize audio
        audio_file = output_dir / "episode.mp3"
        final_audio = await speech_engine.synthesize(script, audio_file)
        
        # Update completion status
        job_status[job_id].update({
            "status": "completed",
            "progress": 1.0,
            "message": "Podcast generation completed",
            "download_url": str(final_audio),
            "script_url": str(script_file)
        })
        
        logger.info(f"Podcast generation completed for job {job_id}")
        
    except Exception as e:
        logger.error(f"Error generating podcast for job {job_id}: {e}")
        job_status[job_id].update({
            "status": "failed",
            "progress": 0.0,
            "message": "Podcast generation failed",
            "error": str(e)
        })
