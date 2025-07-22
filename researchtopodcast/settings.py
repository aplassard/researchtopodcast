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
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openai_api_key: str | None = None
    
    # TTS Configuration
    google_tts_key: str | None = None
    
    # Generation Configuration
    podgen_max_tokens: int = 4096
    podgen_temp_dir: str = "./output"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    @property
    def has_llm_config(self) -> bool:
        """Check if LLM configuration is available."""
        return bool(self.openrouter_api_key or self.openai_api_key)


settings = Settings()
