from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from parsers.javascript_parser import JavaScriptFileSummary
from parsers.python_parser import PythonFileSummary


def build_c4_mermaid(
    python_summaries: Iterable[PythonFileSummary],
    javascript_summaries: Iterable[JavaScriptFileSummary],
) -> Tuple[str, Dict[str, List[str]]]:
    containers: dict[str, set[str]] = defaultdict(set)
    for summary in python_summaries:
        module = str(Path(summary.path).parent) or "."
        containers[module].add(Path(summary.path).name)
    for summary in javascript_summaries:
        module = str(Path(summary.path).parent) or "."
        containers[module].add(Path(summary.path).name)

    lines = ["graph TD"]
    for module in sorted(containers):
        safe_id = module.replace("/", "_").replace(".", "_") or "root"
        lines.append(f"    {safe_id}[{module}]")
        for file_name in sorted(containers[module]):
            file_id = f"{safe_id}_{file_name.replace('.', '_')}"
            lines.append(f"    {safe_id} --> {file_id}[{file_name}]")
    if len(lines) == 1:
        lines.append("    Empty[No modules detected]")
    structure = {module: sorted(files) for module, files in containers.items()}
    return "\n".join(lines), structure
