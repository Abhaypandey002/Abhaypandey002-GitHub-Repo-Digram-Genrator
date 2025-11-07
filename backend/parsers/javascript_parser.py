from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List

from tree_sitter import Node, Parser
from tree_sitter_languages import get_language


JS_LANGUAGE = get_language("javascript")
JS_PARSER = Parser()
JS_PARSER.set_language(JS_LANGUAGE)


@dataclass
class JavaScriptFileSummary:
    path: str
    imports: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    routes: List[str] = field(default_factory=list)


def _node_text(node: Node, source: bytes) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="ignore")


def _walk(node: Node) -> Iterable[Node]:
    yield node
    for child in node.children:
        yield from _walk(child)


def parse_javascript_file(path: str, content: str) -> JavaScriptFileSummary:
    source = content.encode("utf-8")
    tree = JS_PARSER.parse(source)
    summary = JavaScriptFileSummary(path=path)
    imports: List[str] = []
    functions: List[str] = []
    routes: List[str] = []

    for node in _walk(tree.root_node):
        if node.type in {"import_statement", "require_call"}:
            imports.append(_node_text(node, source).strip())
        elif node.type == "function_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                functions.append(_node_text(name_node, source))
        elif node.type == "call_expression":
            call_text = _node_text(node, source)
            if any(call_text.startswith(prefix) for prefix in ("app.", "router.", "express.Router().", "server.")):
                if any(http in call_text for http in (".get(", ".post(", ".put(", ".delete(", ".patch(")):
                    routes.append(call_text)
    summary.imports = sorted(set(imports))
    summary.functions = sorted(set(functions))
    summary.routes = sorted(routes)
    return summary
