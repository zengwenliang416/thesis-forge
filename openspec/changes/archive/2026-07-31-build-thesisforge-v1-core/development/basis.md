# Development Basis: build-thesisforge-v1-core

## Approved Outcome

Build the deterministic, offline-first ThesisForge V1 compiler in Python 3.11+.
The production path remains:

```text
Markdown -> ThesisDocument -> Validation -> Template -> Compiler -> RenderPlan -> DOCX
```

The current change delivers the CLI/compiler core. Production PySide6 UI, Web
services, databases, accounts and mandatory AI integrations remain out of scope.

## Requirements Reference

- `openspec/changes/build-thesisforge-v1-core/requirements.md`
- `openspec/changes/build-thesisforge-v1-core/acceptance.md`
- `openspec/changes/build-thesisforge-v1-core/acceptance.json`
- `openspec/changes/build-thesisforge-v1-core/spec-map.json`
- `openspec/changes/build-thesisforge-v1-core/component-impact-map.json`
- `openspec/specs/ui-design/design.md`
- `openspec/specs/system-architecture/design.md`
- `openspec/specs/frontend-backend-data-flow/design.md`
- `openspec/specs/component-architecture/design.md`

## Prototype Reference

- `openspec/changes/build-thesisforge-v1-core/prototype/artifact/index.html`
- `openspec/changes/build-thesisforge-v1-core/prototype/handoff.md`
- `openspec/changes/build-thesisforge-v1-core/prototype/decision.json`
- `openspec/changes/build-thesisforge-v1-core/prototype/verifier-report.json`

## Handoff Reference

The approved HTML artifact is a review-only interaction specification for a
future PySide6 desktop adapter. It is not a production runtime and must not be
copied into the Python compiler. Development may reuse approved terminology,
workflow names and state semantics only.

## Implementation Basis

- Python 3.11+ is the sole required runtime.
- Domain objects remain dataclasses with no Word implementation objects.
- User-authored YAML is validated through Pydantic and PyYAML.
- CLI commands use Typer and Rich but delegate to testable application services.
- DOCX high-level operations use python-docx; unsupported Word objects use
  focused lxml/OOXML helpers under `src/thesis_forge/renderers/docx/`.
- citeproc-py may be an optional bibliography backend, but offline contracts and
  GB/T golden fixtures cannot depend on network access.
- pytest, OOXML package assertions and Ruff are required executable evidence.
- Build output is written through a temporary file and atomically replaces only
  the explicit output path after package validation.

## Component Architecture Constraint

Parser and Domain cannot import Template, Renderer, `docx`, `lxml`, UI or AI.
Compiler cannot expose python-docx objects. Renderer cannot parse Markdown,
calculate school policy or hard-code a school profile. Shared numbering,
bookmark, reference, unit, font, resource, citation and OOXML behavior must be
implemented once behind focused services or helpers.

## Delivery Strategy

Development proceeds through the user-visible vertical slices in `tasks.md`.
Each closed slice requires direct test evidence, a task report, an independent
spec review, an independent quality review and validation ledger entries. No
advanced Word feature may be represented by placeholder text or an image when
the acceptance contract requires a real OOXML object.
