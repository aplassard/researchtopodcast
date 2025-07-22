"""Podcast generation endpoints."""

import asyncio
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ...llm_client import LLMClient
from ...script_engine import ScriptPlanner, ScriptFormatter
from ...script_engine.planner import ScriptMode
from ...speech import GoogleTTSEngine, Script
from ...utils import DocumentLoader
from ...settings import settings
from ..dependencies import get_llm_client, get_tts_engine

router = APIRouter(prefix="/podcast", tags=["podcast"])

# In-memory storage for job status (in production, use Redis or database)
job_storage: Dict[str, Dict[str, Any]] = {}


class PodcastRequest(BaseModel):
    """Podcast generation request."""
    mode: ScriptMode = ScriptMode.SINGLE_LLM_MULTI_SPEAKER
    duration: int = 300
    title: Optional[str] = None


class PodcastResponse(BaseModel):
    """Podcast generation response."""
    job_id: str
    status: str
    message: str


class JobStatus(BaseModel):
    """Job status response."""
    job_id: str
    status: str
    progress: float
    message: str
    download_url: Optional[str] = None
    error: Optional[str] = None


@router.post("/", response_model=PodcastResponse)
async def create_podcast(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    mode: ScriptMode = ScriptMode.SINGLE_LLM_MULTI_SPEAKER,
    duration: int = 300,
    title: Optional[str] = None,
    llm_client: LLMClient = Depends(get_llm_client),
    tts_engine: GoogleTTSEngine = Depends(get_tts_engine),
):
    """Create a podcast from uploaded document."""
    
    # Validate file type
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )
    
    allowed_extensions = {".pdf", ".txt", ".md", ".html", ".htm"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_ext}"
        )
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Initialize job status
    job_storage[job_id] = {
        "status": "queued",
        "progress": 0.0,
        "message": "Job queued",
        "download_url": None,
        "error": None,
    }
    
    # Start background task
    background_tasks.add_task(
        process_podcast_job,
        job_id=job_id,
        file_content=await file.read(),
        filename=file.filename,
        mode=mode,
        duration=duration,
        title=title,
        llm_client=llm_client,
        tts_engine=tts_engine,
    )
    
    return PodcastResponse(
        job_id=job_id,
        status="queued",
        message="Podcast generation started"
    )


@router.get("/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get job status."""
    if job_id not in job_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    job_data = job_storage[job_id]
    return JobStatus(job_id=job_id, **job_data)


@router.get("/{job_id}/download")
async def download_podcast(job_id: str):
    """Download generated podcast."""
    if job_id not in job_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    job_data = job_storage[job_id]
    if job_data["status"] != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job not completed"
        )
    
    audio_path = Path(settings.podgen_temp_dir) / job_id / "episode.mp3"
    if not audio_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )
    
    return FileResponse(
        path=audio_path,
        media_type="audio/mpeg",
        filename=f"podcast_{job_id}.mp3"
    )


@router.get("/voices/", response_model=list)
async def list_voices(tts_engine: GoogleTTSEngine = Depends(get_tts_engine)):
    """List available TTS voices."""
    return await tts_engine.list_voices()


async def process_podcast_job(
    job_id: str,
    file_content: bytes,
    filename: str,
    mode: ScriptMode,
    duration: int,
    title: Optional[str],
    llm_client: LLMClient,
    tts_engine: GoogleTTSEngine,
):
    """Process podcast generation job."""
    
    try:
        # Update status
        job_storage[job_id].update({
            "status": "processing",
            "progress": 0.1,
            "message": "Loading document..."
        })
        
        # Save uploaded file
        job_dir = Path(settings.podgen_temp_dir) / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        
        input_path = job_dir / filename
        with open(input_path, 'wb') as f:
            f.write(file_content)
        
        # Load document content
        loader = DocumentLoader()
        content = await loader.load(input_path)
        
        job_storage[job_id].update({
            "progress": 0.3,
            "message": "Generating script..."
        })
        
        # Generate script
        planner = ScriptPlanner(llm_client)
        script_data = await planner.generate_script(
            content=content,
            mode=mode,
            duration_sec=duration,
            title=title
        )
        
        job_storage[job_id].update({
            "progress": 0.6,
            "message": "Saving script..."
        })
        
        # Save script
        formatter = ScriptFormatter()
        script_path = job_dir / "episode.podcast.yaml"
        formatter.save_script(script_data, script_path)
        
        job_storage[job_id].update({
            "progress": 0.8,
            "message": "Synthesizing audio..."
        })
        
        # Synthesize audio
        script = Script(**script_data)
        audio_path = job_dir / "episode.mp3"
        await tts_engine.synthesize(script, audio_path)
        
        # Complete
        job_storage[job_id].update({
            "status": "completed",
            "progress": 1.0,
            "message": "Podcast generated successfully",
            "download_url": f"/v1/podcast/{job_id}/download"
        })
        
    except Exception as e:
        job_storage[job_id].update({
            "status": "failed",
            "progress": 0.0,
            "message": "Generation failed",
            "error": str(e)
        })
