from __future__ import annotations

import ast
from pathlib import Path

import thesis_forge.bibliography.bibtex as bibliography_bibtex_module
import thesis_forge.bibliography.engine as bibliography_engine_module
import thesis_forge.bibliography.formatter as bibliography_formatter_module
import thesis_forge.cli as cli_module
import thesis_forge.core.compiler as compiler_module
import thesis_forge.core.math as math_module
import thesis_forge.core.model as model_module
import thesis_forge.core.parser as parser_module
import thesis_forge.core.render_plan as render_plan_module
import thesis_forge.renderers.docx.renderer as docx_renderer_module

FORBIDDEN_IMPORT_PREFIXES = (
    "docx",
    "lxml",
    "thesis_forge.ai",
    "thesis_forge.renderers",
    "thesis_forge.templates",
    "thesis_forge.ui",
)


def _import_names(module_path: Path) -> set[str]:
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_domain_and_parser_do_not_import_forbidden_layers():
    for module in (model_module, parser_module):
        imports = _import_names(Path(module.__file__))
        forbidden = {
            name
            for name in imports
            if any(name == prefix or name.startswith(f"{prefix}.") for prefix in FORBIDDEN_IMPORT_PREFIXES)
        }
        assert forbidden == set()


def test_render_plan_is_renderer_neutral_and_docx_renderer_does_not_import_parser():
    for module in (compiler_module, math_module, render_plan_module):
        imports = _import_names(Path(module.__file__))
        assert not {"docx", "lxml"} & imports

    renderer_imports = _import_names(Path(docx_renderer_module.__file__))
    assert "thesis_forge.core.parser" not in renderer_imports


def test_bibliography_subsystem_does_not_import_docx_xml_or_renderer_layers():
    for module in (
        bibliography_engine_module,
        bibliography_bibtex_module,
        bibliography_formatter_module,
    ):
        imports = _import_names(Path(module.__file__))
        forbidden = {
            name
            for name in imports
            if name in {"docx", "lxml"}
            or name.startswith(("docx.", "lxml.", "thesis_forge.renderers."))
        }
        assert forbidden == set()


def test_cli_delegates_core_flows_to_application_services():
    imports = _import_names(Path(cli_module.__file__))

    assert "thesis_forge.application" in imports
    assert not {
        "thesis_forge.core.compiler",
        "thesis_forge.core.parser",
        "thesis_forge.core.validator",
        "thesis_forge.renderers.docx",
    } & imports
