"""FastAPI application main module."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import podcast
from ..settings import settings

app = FastAPI(
    title="Research2Podcast API",
    description="Transform documents into conversational podcasts",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(podcast.router, prefix="/v1")

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Research2Podcast API",
        "version": "0.1.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "llm_configured": settings.has_llm_config,
        "tts_configured": bool(settings.google_tts_key)
    }
