# Task Report: 005-template-profiles

## Status

DONE

Items 5.1 through 5.5 are implemented in the current checkout. Independent
spec and quality re-reviews approved the final Task 005 slice. Change-level
acceptance remains owned by Task 008 and the SpecNav verification lifecycle.

## Files Changed

- `src/docforge/templates/bindings.py`
- `src/docforge/templates/model.py`
- `src/docforge/templates/__init__.py`
- `src/docforge/core/compiler.py`
- `src/docforge/core/validator.py`
- `src/docforge/core/render_plan.py`
- `src/docforge/presentation/metadata.py`
- `src/docforge/presentation/preview.py`
- `src/docforge/presentation/review.py`
- `templates/base/docforge-standard.yaml`
- `templates/schools/example-university/2026.yaml`
- `templates/schools/hunan-university-of-technology/master-2026.yaml`
- `templates/schools/project-proposal/2026.yaml`
- `tests/templates/test_metadata_bindings.py`
- `tests/compiler/test_template_profiles.py`
- `tests/core/test_manifest_resource_validation.py`
- `tests/test_distribution.py`
- `pyproject.toml`
- `scripts/verify_distribution.py`

## What Changed

- Added typed template binding paths for common metadata and the optional
  academic profile. Template cover items now own `required` and `join_with`
  behavior.
- Preserved manifest metadata as typed `metadata`, `academic`, and `render`
  binding data instead of flattening it into the obsolete academic dictionary.
- Replaced fixed cover fields with generic `CoverInstruction.bindings`; the
  compiler resolves declared bindings before RenderPlan construction and the
  renderer remains profile-agnostic.
- Added the bundled `docforge-standard` template with neutral styles and no
  university, degree, advisor, student, or completion placeholders.
- Migrated repository-owned academic templates to typed `academic.*` and
  `metadata.*` bindings with template-scoped required fields.
- Expanded wheel distribution checks to require all five bundled template YAML
  files.

## Review Fixes Applied

- `QR-001`: Optional empty bindings are filtered before `CoverInstruction`
  construction, and a RenderPlan-level regression asserts that absent optional
  metadata does not enter the plan.
- `QR-002`: Removed the legacy `("thesis.title", "author.name")` validator
  default. Required metadata is neutral by default and template declarations
  provide template-scoped diagnostics.
- `QR-003`: Generic title bindings use a shared `metadata.title` required group
  with locale-aware selection and fallback; an English-only project is
  validated and resolved successfully.
- `QR-004`: Isolated wheel verification now runs `inspect`, `validate`, `review`,
  and `build` for both `docforge-general` and `docforge-academic`, including
  visible DOCX text assertions.
- `QR-005`: `compile_document()` raises `MissingRequiredBindingError` before
  creating a partial cover when a required template binding is absent.
- `QR-006`: Binding paths, labels, and formatting policy are covered by the
  central metadata registry and a legal-path/presentation parity regression.

## TDD Evidence

- `tests/templates/test_metadata_bindings.py` covers common values, multiple
  authors, keywords, optional academic data, and template-owned requirements.
- `tests/compiler/test_template_profiles.py` compares general and academic
  RenderPlans and inspects visible DOCX text for fabricated academic content.
- `tests/core/test_manifest_resource_validation.py` covers active
  `docforge.yaml` and `document.md` manifest metadata injection.
- `tests/test_distribution.py` covers package contents, runtime requirements,
  obsolete package rejection, isolated launcher behavior, and distribution
  verification.

## Verification Commands

- `PYTHONPATH=src .venv/bin/python -m pytest tests/templates tests/compiler tests/project tests/core/test_manifest_resource_validation.py tests/test_distribution.py -q`
  -> `147 passed in 23.08s`.
- `.venv/bin/ruff check src/docforge/templates src/docforge/core/compiler.py src/docforge/core/validator.py src/docforge/core/render_plan.py src/docforge/project tests/templates tests/compiler tests/project tests/core/test_manifest_resource_validation.py tests/test_distribution.py scripts/verify_distribution.py`
  -> `All checks passed`.
- `.venv/bin/python -m build --no-isolation --outdir <temporary-directory>` followed
  by `PYTHONPATH=src .venv/bin/python scripts/verify_distribution.py
  --dist-dir <temporary-directory>`
  -> `docforge-0.1.0` wheel/sdist built successfully; `ok: true`; the wheel
  contained 93 files; isolated no-network installation passed both general and
  academic fixture flows, including inspect, validate, review, build, Review
  artifact checks, and visible DOCX text checks.
- `git diff --check` over the Task 005 implementation and tests
  -> passed.

## Current Review State

- `spec-review.md` independently approved A2, A3, and the Task 005 slice of A7
  after replaying the focused tests and isolated distribution verification.
- `quality-review.md` independently closed QR-001 through QR-006 and approved
  the final separation, binding, validation, and package behavior.

## Concerns

- The active runtime resolver intentionally remains the strongly typed YAML
  model under `src/docforge/templates/model.py`. The separate
  `src/docforge/templates/v2` package pipeline is not an active runtime
  resolver for this change and was not bridged with a compatibility layer.
- A7 is evidenced only for the Task 005 template/compiler/RenderPlan and
  renderer-neutral segment. Cancellation and atomic-output lifecycle evidence
  remain owned by the broader runtime and verification tasks.

## Scope Deviations

- The task packet named template/compiler/project paths, while the active
  implementation boundary is `src/docforge/core`; compiler, validator, and
  RenderPlan changes there were required to resolve bindings before plan
  construction.
- `src/docforge/presentation/{metadata,preview,review}.py`,
  `scripts/verify_distribution.py`, `tests/test_distribution.py`, and
  `pyproject.toml` were touched to establish presentation parity and packaged
  `docforge-standard` coverage. These changes add no parser or renderer
  document-type branch and no compatibility alias.
- These deviations are recorded for controller ownership review rather than
  silently treated as part of the original packet allowlist.

## Follow-up Needed

- Full change-level distribution, repository facticity, and six-domain
  verification remain owned by Tasks 007 and 008.

## Adjudication

The authoritative schema boundary remains the current runtime template model.
No legacy/v2 compatibility adapter was added because the change explicitly
forbids preserving obsolete paths. The context maps this task's direct
acceptance contribution to A2, A3, and the Task 005 slice of A7; it does not
claim closure of those change-level assertions.
