# Spec Review: 006-local-citations-and-bibliography

## Verdict

approved

The previous blocker is closed. `docs/BIBLIOGRAPHY_SPEC.md:74-92` now matches
the current compiler contract in `src/thesis_forge/core/compiler.py:549-604`:
citation ordinals are assigned by first rendered occurrence, footnote
citations expand at the first `FootnoteReference`, and only unattached
registered citations fall back to stable registration order afterward. I
independently reran the footnote-order, reused-context and DOCX bibliography
targeted tests plus the full task-006 focused suite, and the current checkout
supports approval.

## Missing Requirements

| Task | Result | Independent verification |
| --- | --- | --- |
| 6.1 | satisfied | `tests/test_bibliography.py:20-37` proves local BibTeX loading into normalized records for the supported V1 types, and `tests/test_bibliography.py:63-103` proves malformed input, duplicate keys, unsupported types and missing required fields fail structurally. |
| 6.2 | satisfied | `tests/test_validator.py:300-327` proves validation loads the configured local bibliography, reports `missing-citation` at the citation source line, and stores the loaded database on `ValidationContext`. `src/thesis_forge/core/validator.py:465-481` resets derived bibliography state per run, and `tests/test_validator.py:368-395` proves stale bibliography state is cleared when the same context is reused with changed rules. |
| 6.3 | satisfied | `tests/test_bibliography.py:40-60` proves deterministic `format_citation()` and `format_bibliography()` interfaces against the reviewed golden fixture. `tests/test_compiler.py:158-174` proves grouped inline citations preserve source key order while bibliography entries follow ordinal order. |
| 6.4 | satisfied | `tests/test_bibliography.py:40-60` locks the GB/T 7714-2025 V1 output contract to `tests/fixtures/bibliography/gbt7714-v1.{bib,json}`. The formatter remains explicitly limited to the documented V1 subset, matching `docs/BIBLIOGRAPHY_SPEC.md:47-68`. |
| 6.5 | satisfied | `tests/test_parser.py:180-197` proves `::: bibliography` parses to a renderer-neutral `BibliographyBlock`. `src/thesis_forge/core/compiler.py:517-546` builds typed `BibliographyInstruction` entries from resolved records and ordinals, while `tests/test_compiler.py:177-194` proves bibliography auto-appends when no marker is present. `tests/test_architecture.py:48-70` proves render-plan/core/bibliography layers remain free of DOCX/XML imports. |
| 6.6 | satisfied | `src/thesis_forge/renderers/docx/renderer.py:40-107` renders citation runs via `item.text` and bibliography entries as ordinary paragraphs. `tests/test_docx_renderer.py:746-808` proves resolved citation text appears in body and footnote XML, raw `[@key]` markup is absent, and bibliography entries render as editable DOCX paragraphs. |

## Extra Behavior

- No out-of-scope product behavior is visible in the reviewed task surface.
  The bibliography pipeline stays local, deterministic and renderer-neutral.
- The current bibliography spec no longer drifts from implementation. The new
  `Citation Ordering` section in `docs/BIBLIOGRAPHY_SPEC.md:74-92` explicitly
  describes footnote-reference expansion and the post-traversal fallback for
  unattached registered citations, which is the exact behavior implemented by
  `src/thesis_forge/core/compiler.py:549-604` and exercised by
  `tests/test_compiler.py:197-242`.

## Misunderstood Requirements

- None remain in the current checkout.
- The prior doc-only misunderstanding has been corrected: bibliography order is
  still first-use order, but citation ordinal assignment is now documented as
  first actual render position rather than raw `ThesisDocument.citations`
  registration order.
- The reused-context validator fix is also present and verified:
  `active_context.bibliography_database = None` runs before rule execution in
  `src/thesis_forge/core/validator.py:465-481`, and the regression test at
  `tests/test_validator.py:368-395` proves the stale-state case.

## Cannot Verify From Diff

- The repository remains entirely untracked, so Git cannot provide a historical
  task-scoped diff or independently prove the implementer's claimed RED/GREEN
  sequence. This review is therefore based on current files plus independently
  rerun tests.
- I did not reopen the recorded LibreOffice artifact or rely on prior
  validation-log narratives for approval.
- Change-level acceptance items outside this slice remain out of scope for this
  re-review: `A5`, `A6`, `A7`, and `A9`.

## Acceptance Assertions Verified

- `A1`: Within the task-006 surface, bibliography loading/formatting stays
  local and offline by construction (`docs/BIBLIOGRAPHY_SPEC.md:1-16`), the
  bibliography subsystem and parser/domain layers import no AI, DOCX renderer
  or XML implementation modules (`tests/test_architecture.py:16-70`), and the
  focused CLI/test suite passed (`tests/test_cli.py` included in the 75-test
  run).
- `A2`: Parser and domain stay renderer-neutral. `tests/test_parser.py:58-197`
  proves the bibliography config, citations, footnote citations and
  `BibliographyBlock` semantic objects are produced, while
  `tests/test_architecture.py:37-45` proves parser/domain do not import
  forbidden DOCX/renderer/AI layers.
- `A3`: `tests/test_validator.py:300-365` proves structural
  `missing-citation` and `invalid-bibliography` diagnostics with stable line,
  target and error-type details, and no noisy missing-key report when the
  bibliography itself is invalid.
- `A4`: `src/thesis_forge/core/compiler.py:517-604` resolves citation ordinals
  and bibliography entries before rendering. `tests/test_compiler.py:158-242`
  proves deterministic grouped citation text, referenced-only bibliography
  order, marker/append behavior and first-rendered footnote citation ordering.
- `A8`: I independently reran targeted regression tests for footnote ordering,
  reused validation context and DOCX output (`3 passed`), the focused task-006
  suite (`75 passed`), `ruff check .`, `pip check`, and `git diff --check`.
  Architecture tests enforce bibliography/core neutrality, and DOCX tests
  inspect XML content rather than file existence alone.

## Required Fixes

- None for task 006.

## Reviewer Checks

- `.venv/bin/python -m pytest tests/test_compiler.py::test_compile_document_orders_footnote_citation_at_reference_position tests/test_validator.py::test_reused_validation_context_clears_stale_bibliography_when_rules_change tests/test_docx_renderer.py::test_docx_renderer_writes_resolved_body_footnote_and_bibliography_text`
  -> `3 passed in 0.54s`.
- `.venv/bin/python -m pytest tests/test_bibliography.py tests/test_validator.py tests/test_parser.py tests/test_compiler.py tests/test_render_plan.py tests/test_docx_renderer.py tests/test_cli.py tests/test_architecture.py`
  -> `75 passed in 1.93s`.
- `.venv/bin/ruff check .` -> `All checks passed!`.
- `.venv/bin/python -m pip check` -> `No broken requirements found.` (with a
  non-blocking local pip cache permission warning).
- `git diff --check` -> passed.
