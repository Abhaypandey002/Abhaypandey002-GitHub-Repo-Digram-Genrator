from __future__ import annotations

import json
import logging
import random
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional

import networkx as nx

from core.config import get_settings
from graphs.build_dependency_graph import build_dependency_graph
from graphs.c4_builder import build_c4_mermaid
from parsers.javascript_parser import JavaScriptFileSummary, parse_javascript_file
from parsers.python_parser import PythonFileSummary, parse_python_file
from services.git_clone import RepoMetadata, ensure_cloned, fetch_repo_metadata
from services.llm import LocalLLM

LOGGER = logging.getLogger(__name__)
settings = get_settings()

random.seed(42)


class RepoInfo(dict):
    pass


class DiagramPayload(dict):
    pass


class SummaryPayload(dict):
    pass


class LimitsPayload(dict):
    pass


class AnalysisResult(dict):
    repo: RepoInfo
    diagrams: DiagramPayload
    summaries: SummaryPayload
    limits: LimitsPayload


CACHE_FILENAME = "result.json"


def load_cached_result(sha: str) -> Optional[AnalysisResult]:
    cache_path = settings.cache_root
    for owner_dir in cache_path.iterdir():
        sha_dir = owner_dir / sha
        if sha_dir.exists():
            result_path = sha_dir / CACHE_FILENAME
            if result_path.exists():
                with result_path.open("r", encoding="utf-8") as handle:
                    data = json.load(handle)
                return AnalysisResult(data)
    return None


def analyze_repository(repo_url: str) -> AnalysisResult:
    metadata = fetch_repo_metadata(repo_url)
    cached = load_cached_result(metadata.sha)
    if cached:
        LOGGER.info("Returning cached result for %s", metadata.sha)
        return cached

    repo_path = ensure_cloned(repo_url, metadata)
    log_path = settings.log_dir / f"{metadata.sha}.log"
    handler = logging.FileHandler(log_path)
    handler.setLevel(logging.INFO)
    LOGGER.addHandler(handler)

    try:
        result = _analyze_path(repo_path, metadata)
    finally:
        LOGGER.removeHandler(handler)
        handler.close()

    cache_dir = metadata.cache_dir
    (cache_dir).mkdir(parents=True, exist_ok=True)
    result_path = cache_dir / CACHE_FILENAME
    with result_path.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)

    return AnalysisResult(result)


def _analyze_path(repo_path: Path, metadata: RepoMetadata) -> AnalysisResult:
    python_summaries: List[PythonFileSummary] = []
    js_summaries: List[JavaScriptFileSummary] = []
    languages = Counter()

    for path in sorted(repo_path.rglob("*")):
        if path.is_dir():
            continue
        rel_path = path.relative_to(repo_path).as_posix()
        suffix = path.suffix.lower()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if suffix == ".py":
            summary = parse_python_file(rel_path, text)
            python_summaries.append(summary)
            languages["python"] += 1
        elif suffix in {".js", ".jsx", ".ts"}:
            summary = parse_javascript_file(rel_path, text)
            js_summaries.append(summary)
            languages["javascript"] += 1
        else:
            languages[suffix.lstrip(".") or "other"] += 1

    dep_graph = build_dependency_graph(python_summaries, js_summaries, settings.max_nodes)
    dependency_mermaid = _graph_to_mermaid(dep_graph)
    c4_mermaid, module_structure = build_c4_mermaid(python_summaries, js_summaries)
    routes_mermaid = _routes_mermaid(python_summaries, js_summaries)
    db_mermaid = _db_mermaid(python_summaries)

    languages_percent = _language_percentages(languages)

    summaries = _summaries(metadata, python_summaries, js_summaries, dep_graph)

    limits = {
        "file_count_scanned": sum(languages.values()),
        "files_sampled_for_llm": min(settings.max_files_for_llm, len(python_summaries) + len(js_summaries)),
        "max_nodes": settings.max_nodes,
    }

    result: AnalysisResult = AnalysisResult(
        {
            "repo": {
                "name": f"{metadata.owner}/{metadata.name}",
                "default_branch": metadata.default_branch,
                "sha": metadata.sha,
                "languages": languages_percent,
            },
            "diagrams": {
                "c4_modules_mermaid": c4_mermaid,
                "dependencies_mermaid": dependency_mermaid,
                "routes_mermaid": routes_mermaid,
                "db_mermaid": db_mermaid,
            },
            "summaries": summaries,
            "modules": module_structure,
            "limits": limits,
        }
    )
    return result


def _graph_to_mermaid(graph: nx.DiGraph) -> str:
    lines = ["graph LR"]
    for source, target in sorted(graph.edges()):
        source_id = _safe_id(source)
        target_id = _safe_id(target)
        lines.append(f"    {source_id}[{source}] --> {target_id}[{target}]")
    if len(lines) == 1:
        lines.append("    Empty[No dependencies detected]")
    return "\n".join(lines)


def _safe_id(value: str) -> str:
    return value.replace("/", "_").replace(".", "_").replace("-", "_")


def _routes_mermaid(
    python_summaries: List[PythonFileSummary],
    js_summaries: List[JavaScriptFileSummary],
) -> str:
    lines = ["graph TD"]
    nodes_added = False
    for summary in python_summaries:
        for route in summary.routes:
            node_id = _safe_id(route)
            lines.append(f"    Client((Client)) --> {node_id}[{route}]")
            nodes_added = True
    for summary in js_summaries:
        for route in summary.routes:
            node_id = _safe_id(route)
            lines.append(f"    Client((Client)) --> {node_id}[{route}]")
            nodes_added = True
    if not nodes_added:
        lines.append("    NoRoutes[No routes detected]")
    return "\n".join(lines)


def _db_mermaid(python_summaries: List[PythonFileSummary]) -> str:
    lines = ["erDiagram"]
    nodes_added = False
    for summary in python_summaries:
        for model in summary.orm_models:
            node = model.replace(" ", "")
            lines.append(f"    {node} {{\n        string id\n    }}")
            nodes_added = True
    if not nodes_added:
        lines.append("    NONE {\n        string placeholder\n    }")
    return "\n".join(lines)


def _language_percentages(counter: Counter[str]) -> Dict[str, int]:
    total = sum(counter.values())
    if total == 0:
        return {}
    return {lang: int((count / total) * 100) for lang, count in counter.items()}


def _summaries(
    metadata: RepoMetadata,
    python_summaries: List[PythonFileSummary],
    js_summaries: List[JavaScriptFileSummary],
    dep_graph: nx.DiGraph,
) -> SummaryPayload:
    llm = LocalLLM()
    focus_modules: List[Dict[str, str]] = []
    centrality = nx.degree_centrality(dep_graph) if dep_graph.number_of_nodes() else {}
    top_modules = sorted(centrality.items(), key=lambda item: item[1], reverse=True)[:3]
    for module, score in top_modules:
        context = f"Module {module} has centrality {score:.2f}."
        description = llm.summarize_module(module, context)
        focus_modules.append({
            "module": module,
            "why": f"degree centrality {score:.2f}",
            "notes": description or "LLM unavailable",
        })

    repo_context = (
        f"Repository {metadata.owner}/{metadata.name} with {len(python_summaries)} Python files "
        f"and {len(js_summaries)} JavaScript files."
    )
    high_level = llm.summarize_repo(repo_context)
    if not high_level:
        high_level = [
            "Summaries unavailable (LLM offline).",
            "Diagrams and static analysis are still provided.",
        ]

    return SummaryPayload({"high_level": high_level, "focus_modules": focus_modules})
