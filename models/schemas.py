# models/schemas.py
from __future__ import annotations
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class RepoMeta(BaseModel):
    name: str
    default_branch: str
    sha: str
    languages: Dict[str, int] = Field(default_factory=dict)

class Diagrams(BaseModel):
    c4_modules_mermaid: Optional[str] = None
    dependencies_mermaid: Optional[str] = None
    routes_mermaid: Optional[str] = None
    db_mermaid: Optional[str] = None

class FocusModule(BaseModel):
    module: str
    why: str
    notes: Optional[str] = None

class Summaries(BaseModel):
    high_level: List[str] = Field(default_factory=list)
    focus_modules: List[FocusModule] = Field(default_factory=list)

class Limits(BaseModel):
    file_count_scanned: int
    files_sampled_for_llm: int
    max_nodes: int

class AnalysisResult(BaseModel):
    repo: RepoMeta
    diagrams: Diagrams
    summaries: Summaries
    limits: Limits
    notices: Optional[List[str]] = None
