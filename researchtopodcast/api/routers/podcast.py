"""Podcast generation API endpoints."""

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from ..dependencies import get_llm_client, get_speech_engine
from ...script_engine import ScriptPlanner, ScriptFormatter, PodcastMode
from ...settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["podcast"])

# In-memory job storage (use Redis/database in production)
job_status: Dict[str, Dict] = {}


class PodcastRequest(BaseModel):
    """Request model for podcast generation."""
    content: str = Field(..., description="Document content to convert")
    mode: str = Field("solo", description="Podcast mode: solo, single-llm, multi-agent")
    duration: int = Field(300, ge=30, le=1800, description="Target duration in seconds")
    title: Optional[str] = Field(None, description="Custom podcast title")
    source_document: Optional[str] = Field(None, description="Source document name")


class PodcastResponse(BaseModel):
    """Response model for podcast generation."""
    job_id: str = Field(..., description="Job ID for tracking progress")
    status: str = Field(..., description="Job status")
    message: str = Field(..., description="Status message")


class JobStatus(BaseModel):
    """Job status response model."""
    job_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress: float = Field(0.0, ge=0.0, le=1.0)
    message: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    audio_url: Optional[str] = None
    script_url: Optional[str] = None
    error: Optional[str] = None
    usage: Optional[Dict] = None


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
    llm_client = Depends(get_llm_client),
    speech_engine = Depends(get_speech_engine)
):
    """Create a new podcast generation job."""
    
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
    
    podcast_mode = mode_map[request.mode]
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Initialize job status
    job_status[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0.0,
        "message": "Job created",
        "created_at": datetime.now(),
        "completed_at": None,
        "audio_url": None,
        "script_url": None,
        "error": None,
        "usage": None
    }
    
    # Start background task
    background_tasks.add_task(
        generate_podcast_task,
        job_id,
        request,
        podcast_mode,
        llm_client,
        speech_engine
    )
    
    return PodcastResponse(
        job_id=job_id,
        status="pending",
        message="Podcast generation started"
    )


@router.post("/podcast/upload", response_model=PodcastResponse)
async def create_podcast_from_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    mode: str = Form("solo"),
    duration: int = Form(300),
    title: Optional[str] = Form(None),
    llm_client = Depends(get_llm_client),
    speech_engine = Depends(get_speech_engine)
):
    """Create podcast from uploaded file."""
    
    # Read file content
    try:
        content = await file.read()
        text_content = content.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must be UTF-8 encoded text"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error reading file: {str(e)}"
        )
    
    # Create request object
    request = PodcastRequest(
        content=text_content,
        mode=mode,
        duration=duration,
        title=title,
        source_document=file.filename
    )
    
    # Use the same logic as create_podcast
    return await create_podcast(request, background_tasks, llm_client, speech_engine)


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
    
    job = job_status[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
    
    if not job["audio_url"]:
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    audio_path = Path(job["audio_url"])
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
    
    job = job_status[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
    
    if not job["script_url"]:
        raise HTTPException(status_code=404, detail="Script file not found")
    
    script_path = Path(job["script_url"])
    if not script_path.exists():
        raise HTTPException(status_code=404, detail="Script file not found")
    
    return FileResponse(
        path=str(script_path),
        media_type="application/x-yaml",
        filename=f"script_{job_id}.yaml"
    )


@router.get("/voices", response_model=List[VoiceInfo])
async def list_voices(speech_engine = Depends(get_speech_engine)):
    """List available TTS voices."""
    try:
        voices = await speech_engine.list_voices()
        return [VoiceInfo(**voice) for voice in voices]
    except Exception as e:
        logger.error(f"Error listing voices: {e}")
        raise HTTPException(status_code=500, detail="Error listing voices")


@router.delete("/podcast/{job_id}")
async def delete_podcast_job(job_id: str):
    """Delete a podcast job and its files."""
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = job_status[job_id]
    
    # Clean up files
    for url_key in ["audio_url", "script_url"]:
        if job[url_key]:
            try:
                Path(job[url_key]).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Error deleting file {job[url_key]}: {e}")
    
    # Remove from memory
    del job_status[job_id]
    
    return {"message": "Job deleted successfully"}


async def generate_podcast_task(
    job_id: str,
    request: PodcastRequest,
    mode: PodcastMode,
    llm_client,
    speech_engine
):
    """Background task to generate podcast."""
    
    try:
        # Update status
        job_status[job_id].update({
            "status": "processing",
            "progress": 0.1,
            "message": "Initializing script generation..."
        })
        
        # Generate script
        logger.info(f"Job {job_id}: Generating script")
        planner = ScriptPlanner(llm_client)
        
        script = await planner.generate_script(
            content=request.content,
            mode=mode,
            target_duration=request.duration,
            title=request.title,
            source_document=request.source_document
        )
        
        job_status[job_id].update({
            "progress": 0.5,
            "message": "Script generated, starting audio synthesis..."
        })
        
        # Save script
        output_dir = Path(settings.podgen_temp_dir) / job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        script_file = output_dir / "script.podcast.yaml"
        formatter = ScriptFormatter()
        formatter.save_to_file(script, script_file)
        
        # Synthesize audio
        logger.info(f"Job {job_id}: Synthesizing audio")
        audio_file = output_dir / "episode.mp3"
        
        final_audio = await speech_engine.synthesize(script, audio_file)
        
        # Get usage stats
        usage_stats = None
        if hasattr(llm_client, 'total_usage'):
            usage = llm_client.total_usage
            usage_stats = {
                "total_tokens": usage.total_tokens,
                "cost_usd": usage.cost_usd,
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens
            }
        
        # Update final status
        job_status[job_id].update({
            "status": "completed",
            "progress": 1.0,
            "message": "Podcast generated successfully",
            "completed_at": datetime.now(),
            "audio_url": str(final_audio),
            "script_url": str(script_file),
            "usage": usage_stats
        })
        
        logger.info(f"Job {job_id}: Completed successfully")
        
    except Exception as e:
        logger.error(f"Job {job_id}: Failed with error: {e}", exc_info=True)
        job_status[job_id].update({
            "status": "failed",
            "message": "Podcast generation failed",
            "completed_at": datetime.now(),
            "error": str(e)
        })
