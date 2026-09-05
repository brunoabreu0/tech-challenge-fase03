"""Application settings loaded from environment variables via pydantic-settings."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the medical triage system.

    Values are loaded from environment variables or a .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # General
    app_env: str = Field(default="development")
    random_seed: int = Field(default=42)

    # Data paths
    data_raw_dir: Path = Field(default=Path("data/raw"))
    data_processed_dir: Path = Field(default=Path("data/processed"))
    model_dir: Path = Field(default=Path("models"))

    # Model selection
    model_name: str = Field(default="tfidf_lr", description="tfidf_lr | onnx")

    # API
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_log_level: str = Field(default="info")

    @property
    def is_production(self) -> bool:
        """Return True when running in production mode."""
        return self.app_env == "production"


def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
