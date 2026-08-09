# Spec Review: 004-toc-styles

## Verdict

approved

The current implementation and tests satisfy the task 004 TOC style boundary.
The review is based on the task packet, parent requirements and acceptance
contract, prototype handoff, current allowed implementation diff, source
inspection, saved-package XML assertions, system-executed validation records,
and the reviewer-executed focused checks below.

## Missing Requirements

None found within tasks 4.1-4.6.

- `TocLevelSpec` defaults to `0pt` first-line indentation and dot leaders,
  rejects non-positive page-number tabs with the exact field path, and keeps
  the accepted policy shape to `level1`-`level3` with the closed leader enum
  (`src/thesis_forge/templates/model.py:192-209`; `tests/test_template.py:771-879`).
- `configure_toc_styles()` creates or updates stable package style IDs
  `TOC1`, `TOC2` and `TOC3`, uses the current section printable width as the
  deterministic omitted-tab fallback, and delegates common font, indentation,
  spacing and line-spacing translation to `apply_paragraph_style()`
  (`src/thesis_forge/renderers/docx/styles.py:226-361,364-468`).
- All six leader policies are mapped and asserted against Word OOXML tokens;
  `em` page-number tabs use the effective TOC-level size rather than a global
  12pt assumption (`tests/test_docx_renderer.py:446-593`).
- `template.toc is None` leaves the legacy TOC styles untouched. The existing
  renderer and field helper still emit a real TOC complex field with
  `begin/instr/separate/end`, a dirty begin, and `w:updateFields=true`; no
  static TOC entries are rendered (`tests/test_docx_renderer.py:396-444,595-617`;
  `src/thesis_forge/renderers/docx/renderer.py:179-190,225-226`;
  `src/thesis_forge/renderers/docx/fields.py:33-59,91-97`).

## Extra Behavior

None found in the allowed implementation and test diff. The renderer and
field call paths were preserved without unrelated production changes.

## Misunderstood Requirements

None found. Package style IDs are checked as `TOC1`-`TOC3`, not inferred from
localized Word display names. The default-level tab is a deterministic
printable-width fallback, while explicit tab values and all leader values remain
template-controlled.

## Cannot Verify From Diff

- Word or WPS recalculation and sensory layout review are client-owned and are
  intentionally outside this task's scope.
- Change-wide acceptance assertions beyond the TOC slice, including the full
  P0 build and later school-template/Office handoff work, are not claimed here.
- The final handoff contract probe was not rerun after this review write because
  the user interrupted the command; this does not change the direct task
  evidence or the verdict.

## Acceptance Assertions Verified

- A2: Verified only for the TOC-related compatibility scope: a template with
  `toc=None` keeps the legacy TOC style definitions unchanged while preserving
  the real TOC field. Broader change-wide legacy compatibility is not claimed.
- A4: Verified `TOC1`-`TOC3` package style IDs, configured indentation and
  spacing, right-aligned page-number tabs, the printable-width fallback, all
  six leader OOXML tokens, effective-size `em` tabs, and the updateable TOC
  complex field with dirty/update-on-open settings.

## Required Fixes

The approved task has no remaining spec correction; its real TOC and style
requirements are directly covered.

## Independent Validation

- `.venv/bin/python -m pytest tests/test_template.py tests/test_docx_renderer.py -k 'toc or style' -q`
  -> `34 passed, 61 deselected in 1.36s`.
- `.venv/bin/ruff check .`
  -> `All checks passed!`.
- `git diff --check`
  -> exit 0 with no output.
- `development/validation-log.jsonl` contains matching task 004
  `attestation: "system-executed"` records for the focused suite, Ruff and
  diff check.
- CodeGraph evidence `ev-msh7we5o` matches
  `development:task-004-toc-styles`; `codegraph/status.json` and
  `codegraph/guard-report.json` both report `ok: true`, with no task evidence
  blockers.
