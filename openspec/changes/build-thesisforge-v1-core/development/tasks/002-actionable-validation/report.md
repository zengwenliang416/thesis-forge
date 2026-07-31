# Task Report: 002-actionable-validation

## Status

DONE

## Files Changed

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

## What Changed

- Added composable `ValidationContext` rules while preserving
  `validate_document(document)` compatibility.
- Added deterministic diagnostics for required metadata, empty documents,
  stable ID prefixes, duplicates, references, heading jumps, images,
  bibliography configuration, templates, required styles and resource escapes.
- Added structured `ValidationIssue.details`; core diagnostics remain
  presentation-neutral while CLI renders Chinese user copy.
- Replaced untyped template dictionaries with strict Pydantic models for
  lengths, pages, paragraphs, headings, captions, numbering, figures, tables,
  equations, sections, headers/footers, page numbers and citations.
- Added field-specific template loading errors, malformed-YAML handling and
  `.yaml`/`.yml` explicit-path enforcement.
- Added deterministic template resolution by explicit path or Front Matter ID,
  independent of process cwd, with project-template priority and packaged
  fallback templates.
- Added resource-root enforcement for image and bibliography paths.
- Added stable CLI `Severity`, `Code`, `Line`, `Target` and `Message` output
  with warning-only exit 0, validation-error exit 1 and source-error exit 2.
- Packaged the two current built-in YAML templates without AppleDouble files.
- Updated template and Markdown resource specifications and corrected the
  example compiler pipeline.

## TDD Evidence

- Initial focused collection failed because `ValidationContext`,
  `TemplateLoadError` and resolver APIs did not exist.
- Review-driven red tests reproduced cwd-dependent template lookup, malformed
  YAML misclassification, bibliography configuration omission and resource
  path escapes before fixes.
- A CLI regression test exposed Rich table truncation of stable code/target
  fields; rendering was made deterministic at a fixed width.
- Final focused Validator/Template/CLI suite passed all 26 tests.
- Final full suite passed all 35 tests.

## Verification Commands

- `.venv/bin/python -m pytest` -> `35 passed in 1.83s`.
- `.venv/bin/ruff check .` -> `All checks passed!`.
- `.venv/bin/python -m pip check` -> `No broken requirements found.`
- Repository-external validate invocation from `/tmp` -> no structural issues.
- `python -m pip wheel . --no-deps` -> wheel built successfully.
- Final wheel SHA-256:
  `1d79184cde6778f40271eb7d86d62f5a420d1d8c438b68112534de9d88038f16`.
- Wheel archive contains both `template_data` YAML files and no `._*` entries.
- Isolated wheel import path pointed to the temporary installation and
  validated a `/tmp` thesis by packaged template ID successfully.
- `git diff --check` -> no whitespace errors.
- SpecNav development entry contract -> `ok:true`.
- CodeGraph development claim -> matched with no blockers.

## Concerns

- Individual BibTeX citation-key existence remains intentionally owned by task
  006, which introduces the bibliography loader. This slice validates missing
  bibliography configuration/files and missing citation template coverage.
- Template application to `RenderPlan` and DOCX remains owned by task 003.

## Scope Deviations

- `pyproject.toml` was added to the allowed set after independent review proved
  metadata template IDs would fail in installed wheels without packaged
  template data.
- `docs/MARKDOWN_SPEC.md` was added to document the resource-root behavior
  introduced by the acceptance red-team path-escape requirement.

## Follow-up Needed

- Task 003 must pass the resolved typed template into Compiler/RenderPlan.
- Task 006 must load BibTeX and add per-key citation diagnostics through the
  existing `ValidationContext`.

## Adjudication

Both independent reviews returned `approved` after all required fixes. Deferred
items map to explicit downstream tasks and do not block this vertical slice.
