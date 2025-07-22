"""Application settings and configuration."""

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
    openrouter_api_key: str | None = Field(None, description="OpenRouter API key")
    openrouter_base_url: str = Field(
        "https://openrouter.ai/api/v1", 
        description="OpenRouter base URL"
    )
    openai_api_key: str | None = Field(None, description="OpenAI API key")
    
    # TTS Configuration
    google_tts_key: str | None = Field(None, description="Google Cloud TTS credentials")
    
    # Generation Settings
    podgen_max_tokens: int = Field(4096, description="Max tokens per LLM call")
    podgen_temp_dir: str = Field("./output", description="Output directory")
    
    # Development/Testing
    mock_mode: bool = Field(False, description="Enable mock mode for testing")
    
    @property
    def has_llm_config(self) -> bool:
        """Check if LLM configuration is available."""
        return bool(self.openrouter_api_key or self.openai_api_key)
    
    @property
    def has_tts_config(self) -> bool:
        """Check if TTS configuration is available."""
        return bool(self.google_tts_key)


# Global settings instance
settings = Settings()
