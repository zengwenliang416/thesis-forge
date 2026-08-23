from __future__ import annotations

import ast
from pathlib import Path

from thesis_forge.core.parser_markdown_it import _build_markdown_it

PARSER_SUPPORT_PATH = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "thesis_forge"
    / "core"
    / "parser_support.py"
)
MARKDOWN_IT_PARSER_PATH = PARSER_SUPPORT_PATH.with_name("parser_markdown_it.py")


def _parser_imports(tree: ast.Module) -> set[str]:
    return {
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.level == 1
        and node.module == "parser_support"
        for alias in node.names
    }


def test_markdown_v2_uses_public_parser_primitives() -> None:
    markdown_it_tree = ast.parse(MARKDOWN_IT_PARSER_PATH.read_text(encoding="utf-8"))
    parser_support_tree = ast.parse(PARSER_SUPPORT_PATH.read_text(encoding="utf-8"))

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
        for node in parser_support_tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert {
        "bibliography_config",
        "parse_container",
        "parse_front_matter",
        "parse_inline_content",
    } <= definitions


def test_markdown_v2_enables_default_commonmark_gfm_rules() -> None:
    markdown_it_tree = ast.parse(MARKDOWN_IT_PARSER_PATH.read_text(encoding="utf-8"))
    build = next(
        node
        for node in markdown_it_tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_build_markdown_it"
    )
    constructors = [
        node
        for node in ast.walk(build)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "MarkdownIt"
    ]
    assert len(constructors) == 1
    assert constructors[0].args[0].value == "default"
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "disable"
        for node in ast.walk(build)
    )

    md = _build_markdown_it()
    assert {
        "table",
        "code",
        "fence",
        "blockquote",
        "hr",
        "lheading",
        "reference",
    } <= set(md.block.ruler.get_active_rules())
    assert {
        "backticks",
        "emphasis",
        "link",
        "image",
    } <= set(md.inline.ruler.get_active_rules())
