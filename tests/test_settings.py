"""Tests for application settings."""

from triage.settings import Settings, get_settings


def test_default_settings_creation() -> None:
    """Settings should be creatable with defaults."""
    settings = Settings()
    assert settings.app_env == "development"
    assert settings.random_seed == 42
    assert settings.model_name == "tfidf_lr"
    assert settings.api_port == 8000


def test_is_production_false_by_default() -> None:
    """is_production should be False in development mode."""
    settings = Settings()
    assert settings.is_production is False


def test_is_production_true_when_set() -> None:
    """is_production should be True when app_env is 'production'."""
    settings = Settings(app_env="production")
    assert settings.is_production is True


def test_get_settings_returns_settings_instance() -> None:
    """get_settings() should return a Settings instance."""
    settings = get_settings()
    assert isinstance(settings, Settings)


def test_model_dir_is_path() -> None:
    """model_dir should be a Path object."""
    from pathlib import Path

    settings = Settings()
    assert isinstance(settings.model_dir, Path)
