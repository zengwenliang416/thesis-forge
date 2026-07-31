# Task Brief: 001-offline-thesis-inspection

## Goal

A contributor can reproduce the local Python development environment, and a
thesis author can run `thesisforge inspect` offline to see every V1 semantic
object, stable ID, source location, cross-reference and citation without
creating output files.

## Parent Artifacts

- `openspec/changes/build-thesisforge-v1-core/requirements.md`
- `openspec/changes/build-thesisforge-v1-core/acceptance.md`
- `openspec/changes/build-thesisforge-v1-core/acceptance.json`
- `openspec/changes/build-thesisforge-v1-core/spec-map.json`
- `openspec/changes/build-thesisforge-v1-core/component-impact-map.json`
- `openspec/changes/build-thesisforge-v1-core/prototype/handoff.md`

## Vertical Slice

From a clean local Python environment, parse one thesis containing Front Matter,
headings, paragraphs, lists, figures, tables, equations, algorithms, listings,
footnotes, citations and cross-references, then expose their deterministic
structure through the offline `inspect` command.

## In Scope

- Initialize Git without removing or rewriting existing scaffold files.
- Create `.venv`, install `.[dev]`, and keep generated/local files out of source
  and test discovery.
- Add import-boundary tests for Parser and Domain.
- Extend renderer-neutral domain objects for lists, footnotes, inline content
  and bibliography configuration.
- Add stable referencable-ID prefix utilities.
- Refactor deterministic parser helpers and parse every V1 semantic object.
- Preserve source locations and inline reference/citation ordering.
- Expand `inspect` output, parser tests and `docs/MARKDOWN_SPEC.md`.
- Record project-local `pytest` and `ruff` baseline evidence.

## Out Of Scope

- ValidationContext, template-schema expansion and template resolution.
- Typed RenderPlan transition, numbering resolution and DOCX rendering changes.
- Citation formatting, GB/T bibliography rendering and production PySide6 UI.
- Network access, API keys, databases, Web APIs and prototype code promotion.

## Files Allowed

- `.gitignore`
- `pyproject.toml`
- `src/thesis_forge/core/__init__.py`
- `src/thesis_forge/core/model.py`
- `src/thesis_forge/core/ids.py`
- `src/thesis_forge/core/parser.py`
- `src/thesis_forge/cli.py`
- `tests/test_architecture.py`
- `tests/test_cli.py`
- `tests/test_parser.py`
- `docs/MARKDOWN_SPEC.md`

## Interfaces / Seams

- Preserve `parse_markdown(path) -> ThesisDocument`.
- Preserve renderer-neutral dataclasses and `ThesisDocument.index_by_id()`.
- Keep CLI serialization in `cli.py`; Parser returns domain objects only.
- Stable ID utilities may be reused later by Validator and Compiler.

## Components To Create

- Renderer-neutral list and footnote domain types.
- Stable ID-prefix utility under `src/thesis_forge/core/ids.py`.
- Architecture import-boundary test.

## Components To Reuse

- Existing `ThesisDocument`, `SourceLocation`, block and inline dataclasses.
- Existing Front Matter, heading, paragraph, semantic-container and inline
  reference parsing entry points.
- Existing Typer/Rich `inspect` command adapter.

## Components To Extract

- Container collection and conversion helpers from the parser loop.
- Inline reference/citation extraction that preserves offsets and order.
- Stable referencable-ID prefix rules shared by later validation/compiler work.

## API / Data Flow Contracts

- Input: one local UTF-8 Markdown path and local YAML Front Matter.
- Processing: local file read -> deterministic Parser -> `ThesisDocument` ->
  JSON-compatible inspect projection.
- Output: stdout only; no DOCX, temporary file, source mutation or network call.
- Parse failures identify the source line and do not produce output files.

## State / Error / Empty / Loading Behavior

- Loading: CLI performs a bounded synchronous local read; no fake progress state.
- Empty: an empty Markdown file produces an inspectable empty document.
- Error: malformed Front Matter, unclosed containers and unreadable files fail
  with a precise non-zero CLI result.
- Disabled: no inspect capability depends on UI, AI or network availability.
- Permission: operating-system read denial is surfaced without privilege
  escalation or writes.

## TDD Requirement

- Write or update focused behavior tests before or alongside implementation.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_parser.py tests/test_architecture.py tests/test_cli.py`
- `.venv/bin/ruff check src/thesis_forge/core src/thesis_forge/cli.py tests/test_parser.py tests/test_architecture.py tests/test_cli.py`
- `.venv/bin/thesisforge inspect examples/bachelor-thesis/thesis.md`
- `OPENSPEC_TELEMETRY=0 node /Users/wenliang_zeng/.codex/plugins/cache/specnav-marketplace/specnav-development/0.3.0/scripts/development-contract.js --mode entry --json`

## Stop Conditions

- Scope lock mismatch.
- Missing product, architecture, data-flow, or component decision.
- Component duplication that should be extracted.
- Any Parser or Domain dependency on DOCX, Template, Renderer, UI or AI.
- A syntax decision not represented in `docs/MARKDOWN_SPEC.md`.
- A proposed task removal or merge without explicit user approval.

## Unsafe Assumptions

- Do not assume existing Parser behavior is correct without tests.
- Do not infer final figure/table/equation numbering during parsing.
- Do not treat an installed global pytest or Ruff as project-local evidence.
- Do not delete AppleDouble files as part of this slice; ignore them
  deterministically.
