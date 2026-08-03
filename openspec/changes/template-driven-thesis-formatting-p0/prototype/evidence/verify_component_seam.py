from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
PROTOTYPE = ROOT / "openspec/changes/template-driven-thesis-formatting-p0/prototype"


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def has_forbidden_import(path: Path) -> bool:
    forbidden = ("docx", "lxml", "thesis_forge.renderers")
    return any(
        module == prefix or module.startswith(f"{prefix}.")
        for module in imported_modules(path)
        for prefix in forbidden
    )


def main() -> int:
    manifest = json.loads(
        (PROTOTYPE / "prototype-manifest.json").read_text(encoding="utf-8")
    )
    component_map = (PROTOTYPE / manifest["entry"]).read_text(encoding="utf-8")
    question = (PROTOTYPE / "question.md").read_text(encoding="utf-8")

    source_checks = {
        "parser_is_renderer_neutral": not has_forbidden_import(
            ROOT / "src/thesis_forge/core/parser.py"
        ),
        "domain_is_renderer_neutral": not has_forbidden_import(
            ROOT / "src/thesis_forge/core/model.py"
        ),
        "render_plan_is_renderer_neutral": not has_forbidden_import(
            ROOT / "src/thesis_forge/core/render_plan.py"
        ),
        "template_model_is_renderer_neutral": not has_forbidden_import(
            ROOT / "src/thesis_forge/templates/model.py"
        ),
        "compiler_uses_template_and_render_plan": (
            "thesis_forge.templates.model"
            in imported_modules(ROOT / "src/thesis_forge/core/compiler.py")
            and "render_plan"
            in imported_modules(ROOT / "src/thesis_forge/core/compiler.py")
        ),
        "docx_renderer_owns_word_dependencies": any(
            module == "docx" or module.startswith("docx.")
            for module in imported_modules(
                ROOT / "src/thesis_forge/renderers/docx/renderer.py"
            )
        ),
    }
    contract_checks = {
        "branch_is_component_seam": manifest["type"] == "component-seam",
        "variant_is_named": manifest.get("variant") == "policy-role-docx-seam-v1",
        "entry_exists": (PROTOTYPE / manifest["entry"]).is_file(),
        "question_has_no_placeholder": "<decision-required>" not in question,
        "map_has_no_placeholder": "<decision-required>" not in component_map,
        "map_names_common_policy": "ParagraphStyleSpec" in component_map,
        "map_names_renderer_neutral_role": "ParagraphRole" in component_map,
        "map_names_shared_translator": "ParagraphStyleTranslator" in component_map,
        "map_defines_compatibility": "## Compatibility Boundary" in component_map,
        "map_defines_forbidden_dependencies": "## Forbidden Dependencies"
        in component_map,
        "map_defines_promotion_tests": "## Promotion Tests" in component_map,
    }
    checks = {**source_checks, **contract_checks}
    result = {
        "ok": all(checks.values()),
        "variant": manifest.get("variant"),
        "entry": manifest["entry"],
        "checks": checks,
        "inspected_sources": [
            "src/thesis_forge/core/parser.py",
            "src/thesis_forge/core/model.py",
            "src/thesis_forge/core/render_plan.py",
            "src/thesis_forge/core/compiler.py",
            "src/thesis_forge/templates/model.py",
            "src/thesis_forge/renderers/docx/renderer.py",
        ],
        "production_files_modified": False,
    }
    output = PROTOTYPE / "evidence/component-seam-verification.json"
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
