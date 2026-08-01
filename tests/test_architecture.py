from __future__ import annotations

import ast
import subprocess
import sys
import tomllib
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
import thesis_forge.ui.controller as ui_controller_module
import thesis_forge.ui.filesystem as ui_filesystem_module
import thesis_forge.ui.models as ui_models_module
import thesis_forge.ui.tasks as ui_tasks_module

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


def test_headless_ui_controller_and_models_avoid_qt_docx_and_xml_imports():
    forbidden_prefixes = ("PySide6", "docx", "lxml")

    for module in (
        ui_controller_module,
        ui_filesystem_module,
        ui_models_module,
        ui_tasks_module,
    ):
        imports = _import_names(Path(module.__file__))
        forbidden = {
            name
            for name in imports
            if any(
                name == prefix or name.startswith(f"{prefix}.")
                for prefix in forbidden_prefixes
            )
        }
        assert forbidden == set()


def test_python_package_does_not_declare_qt_product_dependencies():
    project_root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject["project"]
    dependency_groups = [project.get("dependencies", [])]
    dependency_groups.extend(project.get("optional-dependencies", {}).values())

    normalized_dependencies = {
        dependency.split(";", 1)[0].strip().lower()
        for group in dependency_groups
        for dependency in group
    }

    assert not any(
        dependency.startswith(("pyside", "pyqt"))
        for dependency in normalized_dependencies
    )


def test_importing_headless_ui_does_not_load_application_or_rendering_stack():
    script = """
import json
import sys

import thesis_forge.ui

forbidden = {
    "docx",
    "lxml",
    "thesis_forge.application.services",
    "thesis_forge.core.compiler",
    "thesis_forge.core.parser",
    "thesis_forge.renderers.docx",
}
loaded = sorted(name for name in forbidden if name in sys.modules)
print(json.dumps(loaded))
raise SystemExit(bool(loaded))
"""

    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout or result.stderr
