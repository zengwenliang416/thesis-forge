from __future__ import annotations

import ast
from pathlib import Path

PARSER_PATH = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "thesis_forge"
    / "core"
    / "parser.py"
)
MARKDOWN_IT_PARSER_PATH = PARSER_PATH.with_name("parser_markdown_it.py")


def _parser_imports(tree: ast.Module) -> set[str]:
    return {
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.level == 1
        and node.module == "parser"
        for alias in node.names
    }


def test_markdown_v2_uses_public_parser_primitives() -> None:
    markdown_it_tree = ast.parse(MARKDOWN_IT_PARSER_PATH.read_text(encoding="utf-8"))
    parser_tree = ast.parse(PARSER_PATH.read_text(encoding="utf-8"))

    imported = _parser_imports(markdown_it_tree)
    assert {
        "bibliography_config",
        "parse_container",
        "parse_front_matter",
        "parse_inline_content",
    } <= imported
    assert not any(name.startswith("_") for name in imported)

    definitions = {
        node.name
        for node in parser_tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert {
        "bibliography_config",
        "parse_container",
        "parse_front_matter",
        "parse_inline_content",
    } <= definitions
