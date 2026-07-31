# Task Brief: 002-actionable-validation

## Goal

A thesis author can run `thesisforge validate` offline and receive complete,
deterministically ordered diagnostics for document, resource, bibliography and
template problems, with stable exit behavior.

## Parent Artifacts

- `openspec/changes/build-thesisforge-v1-core/requirements.md`
- `openspec/changes/build-thesisforge-v1-core/acceptance.md`
- `openspec/changes/build-thesisforge-v1-core/prototype/handoff.md`

## Vertical Slice

Implement `FLOW-VALIDATE` from CLI input through Parser, template resolution,
composable validation rules and the user-visible diagnostics table. The same
validation API remains reusable by `build` and the future PySide6 adapter.

## In Scope

- Preserve `validate_document(doc)` while adding a composable
  `ValidationContext`.
- Validate stable ID prefixes, duplicate IDs, reference targets, heading
  hierarchy, local images, required metadata and bibliography configuration.
- Reject figure and bibliography paths that escape the document resource root.
- Resolve a template from an explicit path or Front Matter `render.template_id`.
- Replace untyped template dictionaries with Pydantic models for headings,
  captions, numbering, sections, headers/footers, page numbers and citations.
- Validate explicit template lengths with field-specific errors.
- Validate template style coverage for semantic objects used by the document.
- Make diagnostics ordering and CLI exit behavior deterministic.
- Document every supported template field in `docs/TEMPLATE_SPEC.md`.

## Out Of Scope

- Parsing BibTeX records or checking individual citation keys; task 006 owns
  bibliography loading and key validation.
- Applying template styles in `RenderPlan` or DOCX; task 003 owns compilation
  and basic rendering.
- Figure/table rendering, OMML, Word fields, sections or bibliography output.
- Web services, persistent storage, accounts, AI or production desktop UI.

## Files Allowed

- `src/thesis_forge/core/__init__.py`
- `src/thesis_forge/core/model.py`
- `src/thesis_forge/core/validator.py`
- `src/thesis_forge/templates/__init__.py`
- `src/thesis_forge/templates/model.py`
- `src/thesis_forge/templates/resolver.py`
- `src/thesis_forge/cli.py`
- `pyproject.toml`
- `tests/test_validator.py`
- `tests/test_template.py`
- `tests/test_cli.py`
- `docs/TEMPLATE_SPEC.md`
- `docs/MARKDOWN_SPEC.md`
- `examples/bachelor-thesis/thesis.md`

## Interfaces / Seams

- `validate_document(doc, context=None) -> list[ValidationIssue]`
- `ValidationContext` owns rule composition and resolved template state.
- `load_template(path) -> ThesisTemplate`
- `resolve_template(explicit_path, template_id, search_roots) -> ResolvedTemplate`
- CLI owns presentation and exit codes; validation rules never print.

## Components To Create

- Typed template length, heading, caption, numbering, section, header/footer,
  page-number and citation models.
- Template resolver and typed template loading exceptions.
- Composable validation rule contract and `ValidationContext`.

## Components To Reuse

- `ThesisDocument`, `ValidationIssue` and source locations.
- Stable ID helpers from `core/ids.py`.
- Existing Parser and Typer/Rich CLI adapters.

## Components To Extract

- Unit parsing is centralized in the Template Model and must not be duplicated
  in Validator or future Renderer code.
- Diagnostic sorting is centralized in Validator.
- Template selection is centralized in `templates/resolver.py`.

## API / Data Flow Contracts

- Source Markdown and all referenced local resources are read-only.
- Explicit `--template` path takes precedence over Front Matter template ID.
- Missing or invalid templates become structured validation issues.
- Warning-only validation exits 0; any error exits 1; unreadable or malformed
  source input exits 2 without a traceback.
- No network access, API key or production output write is permitted.

## State / Error / Empty / Loading Behavior

- Loading: synchronous local reads with no hidden network access.
- Empty: empty documents and missing required metadata produce diagnostics.
- Error: all applicable validation issues are collected and sorted.
- Disabled: no AI, Renderer or output path is invoked by validation.
- Permission: unreadable source input is reported as exit 2; unreadable
  template/resource paths are structured validation errors.

## TDD Requirement

- Write or update focused behavior tests before or alongside implementation.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_validator.py tests/test_template.py tests/test_cli.py`
- `.venv/bin/python -m pytest`
- `.venv/bin/ruff check .`
- `.venv/bin/python -m pip check`
- `.venv/bin/thesisforge validate examples/bachelor-thesis/thesis.md`
- `git diff --check`
- SpecNav development entry and CodeGraph claim checks.

## Stop Conditions

- Scope lock mismatch.
- Missing product, architecture, data-flow, or component decision.
- Component duplication that should be extracted.
- Parser or Domain would need to import Template, Renderer, DOCX, UI or AI.
- Individual BibTeX key parsing would be required to satisfy this slice.

## Unsafe Assumptions

- Do not assume a template exists because an ID is present in Front Matter.
- Do not resolve template IDs from process cwd alone.
- Do not allow local resource paths to escape the document directory.
- Do not infer final citation keys without loading BibTeX in task 006.
- Do not treat warning diagnostics as fatal.
- Do not accept unitless explicit lengths.
