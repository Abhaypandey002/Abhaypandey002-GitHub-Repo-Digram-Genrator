from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application configuration settings."""

    cache_root: Path = Field(default_factory=lambda: Path(os.getenv("REPO_DIAGRAMMER_CACHE", ".cache")))
    llm_model: str = Field(default_factory=lambda: os.getenv("LLM_MODEL", "llama3.1:8b"))
    ollama_endpoint: str = Field(default_factory=lambda: os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434"))
    max_nodes: int = 40
    max_files_for_llm: int = 20
    log_dir: Path | None = None

    class Config:
        frozen = True


_SETTINGS: Optional[Settings] = None


def get_settings() -> Settings:
    global _SETTINGS
    if _SETTINGS is None:
        settings = Settings()
        cache_root = settings.cache_root
        cache_root.mkdir(parents=True, exist_ok=True)
        log_dir = cache_root / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        _SETTINGS = settings.copy(update={"log_dir": log_dir})
    return _SETTINGS
