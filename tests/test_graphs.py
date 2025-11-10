import networkx as nx

from graphs.build_dependency_graph import build_dependency_graph
from parsers.javascript_parser import JavaScriptFileSummary
from parsers.python_parser import PythonFileSummary


def test_dependency_graph_limits_nodes():
    python_summaries = [
        PythonFileSummary(path=f"module_{i}.py", imports=["import os"], classes=[], functions=[], routes=[], orm_models=[])
        for i in range(5)
    ]
    js_summaries = [
        JavaScriptFileSummary(path=f"module_{i}.js", imports=["import http from 'http'"])
        for i in range(5)
    ]
    graph = build_dependency_graph(python_summaries, js_summaries, max_nodes=4)
    assert graph.number_of_nodes() <= 4
