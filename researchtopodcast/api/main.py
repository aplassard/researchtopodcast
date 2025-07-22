"""FastAPI application for Research2Podcast."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routers import podcast
from .dependencies import validate_api_config
from ..settings import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Research2Podcast API")
    try:
        validate_api_config()
        logger.info("API configuration validated")
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Research2Podcast API")


app = FastAPI(
    title="Research2Podcast API",
    description="Transform documents into conversational podcasts",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
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
        "has_llm_config": settings.has_llm_config,
        "has_tts_config": bool(settings.google_tts_key)
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
