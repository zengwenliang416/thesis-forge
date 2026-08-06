# Task Report: 003-semantic-roles

## Status

DONE

## Files Changed

- `src/thesis_forge/core/render_plan.py`
- `src/thesis_forge/core/compiler.py`
- `src/thesis_forge/renderers/docx/styles.py`
- `src/thesis_forge/renderers/docx/renderer.py`
- `tests/test_compiler.py`
- `tests/test_render_plan.py`
- `tests/test_docx_renderer.py`
- `tests/test_architecture.py`
- `tests/test_acceptance.py`
- `openspec/changes/template-driven-thesis-formatting-p0/codegraph/claims-map.json`
- `openspec/changes/template-driven-thesis-formatting-p0/codegraph/evidence.jsonl`
- `openspec/changes/template-driven-thesis-formatting-p0/codegraph/evidence-index.json`

## What Changed

- Added the closed renderer-neutral `ParagraphRole` contract and compatible
  heading/paragraph instruction defaults and payloads.
- Added a private compile-scoped semantic context that recognizes Chinese and
  English abstracts, TOC, bibliography, acknowledgements and achievements from
  stable level-1 heading IDs.
- Preserved abstract context across nested H2-H9 headings and exited only at
  the next H1 boundary.
- Supported both current `chap:` IDs and the existing complete-template bare
  `references`, `acknowledgements` and `achievements` IDs.
- Restricted Chinese and English keyword recognition to paragraph-start labels
  inside the matching abstract while preserving original text and inline runs.
- Added deterministic template policy lookup. Semantic title roles use their
  corresponding Heading style as the Word base; body, keyword and bibliography
  entry roles use Normal. Partial policies inherit omitted properties and
  explicit false values override inherited pagination.
- Added a conversion-only inherited font-size input for partial semantic
  policies that omit `size` but use `em` indentation, spacing or fixed line
  spacing. The conversion base comes from the effective Heading or body style
  without emitting an unintended child font-size override.
- Bound abstract, keyword, TOC, bibliography and special-section roles to
  stable internal Word styles through the task 002 translator.
- Updated the complete-example acceptance assertion so semantic abstract
  titles are recognized as headings instead of requiring direct `Heading*`
  `w:pStyle` values.

## TDD Evidence

- Initial collection failed because `ParagraphRole` and
  `resolve_paragraph_style()` did not exist.
- The first implementation passed 72 focused tests and exposed one stale
  acceptance assertion that still required `Heading1` for abstract titles.
- Independent quality review found three silent semantic degradations: nested
  headings exited abstract context, partial semantic titles inherited from
  Normal, and existing bare special-section IDs were not recognized.
- Added failing regressions for all three findings before fixing them.
- Package tests now assert stable `w:pStyle` values for Chinese/English
  abstract titles, bodies and keywords, TOC, bibliography, acknowledgements
  and achievements.
- The partial-title package test proves `w:basedOn="Heading1"`, inherited
  heading properties, absence of unintended body font/size overrides and an
  explicit `w:pageBreakBefore w:val="0"` override.
- Partial title and body package tests prove omitted sizes still resolve `em`
  values from the effective Heading or Normal/body size, including indentation,
  spacing and fixed line spacing.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_compiler.py tests/test_render_plan.py tests/test_docx_renderer.py tests/test_architecture.py tests/test_acceptance.py -q`
  -> `79 passed in 11.43s`.
- `.venv/bin/python -m pytest -q` -> `321 passed in 45.20s`.
- `.venv/bin/ruff check .` -> `All checks passed`.
- `git diff --check` -> passed.
- CodeGraph evidence `ev-mscv2ik1`, `ev-mscv2zpb` and final review-fix
  evidence `ev-mscvniyw`, `ev-mscvzqsv` match
  `development:task-003-semantic-roles`.

## Concerns

- TOC level styles and tab leaders remain task 004.
- Citation superscript and bibliography entry presentation remain task 005.
- Full offline CLI, normalized OOXML determinism and Office sensory review
  remain tasks 007-008.

## Scope Deviations

- `tests/test_acceptance.py` was added to the task allowlist because its
  complete-example heading assertion encoded the superseded assumption that
  abstract headings must directly use `Heading*` styles. The change now checks
  the required semantic style IDs without changing source or runtime behavior.

## Follow-up Needed

- Task 004 should reuse `toc.title` and the shared translator for TOC 1-3.
- Task 005 should reuse `bibliography.entry` for generated bibliography
  paragraphs and add citation presentation.

## Adjudication

Tasks 3.1-3.7 are complete at the semantic-role boundary. A3 and A7 are proven
for this slice; A8 is proven for renderer constants, dependency direction and
compile determinism, while broader command/package evidence remains downstream.
