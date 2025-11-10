from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List

from tree_sitter import Node, Parser
from tree_sitter_languages import get_language


PY_LANGUAGE = get_language("python")
PY_PARSER = Parser()
PY_PARSER.set_language(PY_LANGUAGE)


@dataclass
class PythonFileSummary:
    path: str
    imports: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    routes: List[str] = field(default_factory=list)
    orm_models: List[str] = field(default_factory=list)


def _node_text(node: Node, source: bytes) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="ignore")


def _walk(node: Node) -> Iterable[Node]:
    yield node
    for child in node.children:
        yield from _walk(child)


def parse_python_file(path: str, content: str) -> PythonFileSummary:
    source = content.encode("utf-8")
    tree = PY_PARSER.parse(source)
    summary = PythonFileSummary(path=path)
    classes: List[str] = []
    functions: List[str] = []
    imports: List[str] = []
    routes: List[str] = []
    orm_models: List[str] = []

    for node in _walk(tree.root_node):
        if node.type in {"import_statement", "import_from_statement"}:
            text = _node_text(node, source)
            imports.append(text.strip())
        elif node.type == "class_definition":
            name = _node_text(node.child_by_field_name("name"), source)
            bases = []
            inheritance = node.child_by_field_name("superclass")
            if inheritance is not None:
                bases.append(_node_text(inheritance, source))
            classes.append(name)
            if any(base.lower().endswith("model") for base in bases) or "Base" in "".join(bases):
                orm_models.append(name)
        elif node.type == "function_definition":
            name = _node_text(node.child_by_field_name("name"), source)
            functions.append(name)
            decorators = [child for child in node.children if child.type == "decorator"]
            for decorator in decorators:
                call = decorator.child_by_field_name("call")
                if call is None:
                    continue
                call_text = _node_text(call, source)
                if call_text.startswith(("app.", "router.", "api.", "bp.")) and "(" in call_text:
                    routes.append(f"{call_text} -> {name}")
    summary.classes = sorted(set(classes))
    summary.functions = sorted(set(functions))
    summary.imports = sorted(set(imports))
    summary.routes = sorted(routes)
    summary.orm_models = sorted(set(orm_models))
    return summary
