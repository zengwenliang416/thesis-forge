from __future__ import annotations

import ast
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import docforge.bibliography.bibtex as bibliography_bibtex_module
import docforge.bibliography.engine as bibliography_engine_module
import docforge.bibliography.formatter as bibliography_formatter_module
import docforge.cli as cli_module
import docforge.core.compiler as compiler_module
import docforge.core.math as math_module
import docforge.core.model as model_module
import docforge.core.parser_backend as parser_backend_module
import docforge.core.parser_markdown_it as parser_markdown_it_module
import docforge.core.render_plan as render_plan_module
import docforge.presentation as presentation_module
import docforge.renderers.docx.renderer as docx_renderer_module
import docforge.templates.model as template_model_module
import docforge.ui.controller as ui_controller_module
import docforge.ui.filesystem as ui_filesystem_module
import docforge.ui.models as ui_models_module
import docforge.ui.tasks as ui_tasks_module

FORBIDDEN_IMPORT_PREFIXES = (
    "docx",
    "lxml",
    "docforge.ai",
    "docforge.renderers",
    "docforge.templates",
    "docforge.ui",
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


def _typescript_import_sources(module_path: Path) -> set[str]:
    content = module_path.read_text(encoding="utf-8")
    return {
        source.lower()
        for source in re.findall(
            r"""(?:from\s+|import\s*(?:\(\s*)?)["']([^"']+)["']""",
            content,
        )
    }


def _python_branch_expressions(module_path: Path) -> tuple[str, ...]:
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    expressions: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.IfExp, ast.While)):
            expressions.append(ast.unparse(node.test))
        elif isinstance(node, ast.Match):
            expressions.append(ast.unparse(node.subject))
    return tuple(expressions)


def test_domain_and_parser_backend_do_not_import_forbidden_layers():
    for module in (
        model_module,
        parser_backend_module,
        parser_markdown_it_module,
    ):
        imports = _import_names(Path(module.__file__))
        forbidden = {
            name
            for name in imports
            if any(name == prefix or name.startswith(f"{prefix}.") for prefix in FORBIDDEN_IMPORT_PREFIXES)
        }
        assert forbidden == set()


def test_parser_does_not_branch_on_project_profiles_or_templates():
    for module in (parser_backend_module, parser_markdown_it_module):
        branches = "\n".join(
            _python_branch_expressions(Path(module.__file__))
        ).lower()
        assert "document.type" not in branches
        assert "academic" not in branches
        assert "template_id" not in branches


def test_render_plan_is_renderer_neutral_and_docx_renderer_does_not_import_parser():
    for module in (compiler_module, math_module, render_plan_module):
        imports = _import_names(Path(module.__file__))
        assert not {"docx", "lxml"} & imports
        assert not any(
            name == "docforge.renderers"
            or name.startswith("docforge.renderers.")
            for name in imports
        )

    renderer_imports = _import_names(Path(docx_renderer_module.__file__))
    assert "docforge.core.parser" not in renderer_imports

    render_plan_source = Path(render_plan_module.__file__).read_text(encoding="utf-8")
    assert "TFAbstract" not in render_plan_source
    assert "w:pStyle" not in render_plan_source


def test_template_model_is_renderer_neutral():
    imports = _import_names(Path(template_model_module.__file__))
    forbidden = {
        name
        for name in imports
        if name in {"docx", "lxml"}
        or name.startswith(("docx.", "lxml.", "docforge.renderers."))
    }
    assert forbidden == set()


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
            or name.startswith(("docx.", "lxml.", "docforge.renderers."))
        }
        assert forbidden == set()


def test_cli_delegates_core_flows_to_application_services():
    imports = _import_names(Path(cli_module.__file__))

    assert "docforge.application" in imports
    assert not {
        "docforge.core.compiler",
        "docforge.core.parser",
        "docforge.core.validator",
        "docforge.renderers.docx",
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

import docforge.ui

forbidden = {
    "docx",
    "lxml",
    "docforge.application.services",
    "docforge.core.compiler",
    "docforge.core.parser",
    "docforge.renderers.docx",
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


def test_preview_presentation_and_frontend_modules_do_not_import_renderers():
    preview_module = Path(presentation_module.__file__).parent / "preview.py"
    assert preview_module.is_file()
    python_imports = _import_names(preview_module)
    assert not {
        "docx",
        "lxml",
        "docforge.renderers",
        "docforge.renderers.docx",
    } & python_imports

    project_root = Path(__file__).resolve().parents[1]
    frontend_paths = [
        project_root / "frontend" / "src" / "state" / "preview.ts",
        project_root / "frontend" / "src" / "components" / "PreviewPanels.tsx",
    ]
    forbidden_prefixes = (
        "docx",
        "lxml",
        "docforge.renderers",
        "docforge.core.compiler",
        "docforge.core.parser",
        "docforge.core.validator",
        "@tauri-apps",
        "../transport/web",
        "../transport/tauri",
    )
    for path in frontend_paths:
        assert path.is_file()
        imports = _typescript_import_sources(path)
        assert not any(
            source == prefix or source.startswith(f"{prefix}/")
            for source in imports
            for prefix in forbidden_prefixes
        )
