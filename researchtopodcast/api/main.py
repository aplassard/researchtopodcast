"""FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import podcast
from ..settings import settings

app = FastAPI(
    title="Research to Podcast API",
    description="Transform documents into conversational podcasts",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(podcast.router, prefix="/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Research to Podcast API", "version": "0.1.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "has_llm_config": settings.has_llm_config,
        "has_tts_config": bool(settings.google_tts_key),
    }
