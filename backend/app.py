from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.config import get_settings
from services.analyze import AnalysisResult, analyze_repository, load_cached_result

settings = get_settings()

app = FastAPI(title="Repo Diagrammer", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    repo_url: str


@app.on_event("startup")
def configure_logging() -> None:
    log_path = settings.log_dir / "app.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.FileHandler(log_path), logging.StreamHandler()],
    )


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/cache/{sha}")
def get_cached(sha: str) -> AnalysisResult:
    cached = load_cached_result(sha)
    if cached is None:
        raise HTTPException(status_code=404, detail="Cache miss")
    return cached


@app.post("/api/analyze", response_model=AnalysisResult)
def analyze(req: AnalyzeRequest) -> AnalysisResult:
    try:
        result = analyze_repository(req.repo_url)
        return result
    except ValueError as exc:  # validation errors
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:  # git missing etc.
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - fallback
        logging.exception("Analysis failed")
        raise HTTPException(status_code=500, detail="Analysis failed") from exc
