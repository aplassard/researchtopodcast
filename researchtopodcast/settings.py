"""Configuration settings for the research2podcast application."""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
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
    google_tts_key: Optional[str] = Field(None, description="Google TTS API key")
    
    # Generation Settings
    podgen_max_tokens: int = Field(4096, description="Max tokens per LLM call")
    podgen_temp_dir: Path = Field(
        Path("./output"),
        description="Output directory for generated files"
    )
    
    # API Settings
    api_host: str = Field("0.0.0.0", description="API host")
    api_port: int = Field(8000, description="API port")

    def model_post_init(self, __context) -> None:
        """Ensure output directory exists."""
        self.podgen_temp_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
