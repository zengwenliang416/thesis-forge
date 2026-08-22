from __future__ import annotations

import ast
import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRODUCTION = ROOT / "src" / "thesis_forge"
LEGACY_IMPLEMENTATION = PRODUCTION / "core" / "parser.py"


def _imports_legacy_parser(node: ast.AST) -> bool:
    if isinstance(node, ast.Import):
        return any(
            alias.name in {"core.parser", "thesis_forge.core.parser"}
            for alias in node.names
        )
    if not isinstance(node, ast.ImportFrom):
        return False
    if node.level and node.module == "parser":
        return True
    return node.module in {"core.parser", "thesis_forge.core.parser"}


def test_production_modules_do_not_import_legacy_parser() -> None:
    offenders: list[str] = []
    for path in sorted(PRODUCTION.rglob("*.py")):
        if path == LEGACY_IMPLEMENTATION:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if any(_imports_legacy_parser(node) for node in ast.walk(tree)):
            offenders.append(str(path.relative_to(ROOT)))

    assert offenders == []


def test_core_public_surface_exposes_only_canonical_parser_entry() -> None:
    core = importlib.import_module("thesis_forge.core")

    assert not hasattr(core, "parse_markdown")
    assert not hasattr(core, "parse_markdown_text")
    assert core.ParseError.__module__ == "thesis_forge.core.parser_support"
    backend = core.create_parser_backend()
    assert type(backend) is core.MarkdownItParserBackend
