"""Application settings and configuration."""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # LLM Configuration
    openrouter_api_key: Optional[str] = Field(None, description="OpenRouter API key")
    openrouter_base_url: str = Field(
        "https://openrouter.ai/api/v1", 
        description="OpenRouter base URL"
    )
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    
    # TTS Configuration
    google_tts_key: Optional[str] = Field(None, description="Google TTS credentials")
    
    # Generation Configuration
    podgen_max_tokens: int = Field(4096, description="Max tokens per LLM call")
    podgen_temp_dir: str = Field("./output", description="Output directory")
    
    # Application Configuration
    debug: bool = Field(False, description="Debug mode")
    log_level: str = Field("INFO", description="Log level")


# Global settings instance
settings = Settings()
