from __future__ import annotations

from typing import Iterable, List, Mapping

import networkx as nx

from parsers.javascript_parser import JavaScriptFileSummary
from parsers.python_parser import PythonFileSummary


def build_dependency_graph(
    python_summaries: Iterable[PythonFileSummary],
    javascript_summaries: Iterable[JavaScriptFileSummary],
    max_nodes: int,
) -> nx.DiGraph:
    graph = nx.DiGraph()

    for summary in python_summaries:
        graph.add_node(summary.path, language="python")
        for imp in summary.imports:
            target = _normalize_import(imp)
            if target:
                graph.add_edge(summary.path, target)

    for summary in javascript_summaries:
        graph.add_node(summary.path, language="javascript")
        for imp in summary.imports:
            target = _normalize_import(imp)
            if target:
                graph.add_edge(summary.path, target)

    if graph.number_of_nodes() <= max_nodes:
        return graph

    centrality = nx.degree_centrality(graph)
    top_nodes = sorted(centrality.items(), key=lambda item: item[1], reverse=True)[:max_nodes]
    keep = {node for node, _ in top_nodes}
    subgraph = graph.subgraph(keep).copy()
    return subgraph


def _normalize_import(raw: str) -> str | None:
    cleaned = raw.strip()
    if not cleaned:
        return None
    if "import" in cleaned:
        tokens = cleaned.replace(",", " ").split()
        if "from" in tokens and tokens.index("from") + 1 < len(tokens):
            return tokens[tokens.index("from") + 1]
        if "import" in tokens:
            idx = tokens.index("import")
            if idx + 1 < len(tokens):
                return tokens[idx + 1]
    if cleaned.startswith("require"):
        return cleaned
    return cleaned.split()[0]
