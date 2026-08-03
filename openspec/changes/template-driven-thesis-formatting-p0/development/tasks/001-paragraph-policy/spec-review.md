# Spec Review: 001-paragraph-policy

## Verdict

approved

The latest diff and direct reviewer execution force approval for task 001 at
the Template Model boundary. Tasks 1.1-1.7 are implemented within the updated
allowlist, and the previous validation, normalization, test-coverage and scope
blockers are resolved.

Reviewer-executed current-worktree evidence:

- `.venv/bin/python -m pytest tests/test_template.py tests/test_architecture.py -q`
  -> `49 passed in 0.91s`
- `.venv/bin/python -m pytest -q` -> `288 passed in 11.95s`
- `.venv/bin/ruff check .` -> `All checks passed`
- `git diff --check` -> passed

The matching `49` focused / `288` full / Ruff / diff-check results are also
recorded in `validation-log.jsonl` with `attestation: "system-executed"`.

## Missing Requirements

- None within tasks 1.1-1.7.
- Task 1.1 is satisfied by the closed, renderer-neutral
  `ParagraphStyleSpec`, covering font, size, emphasis, alignment, all required
  indentation and spacing properties, pagination controls, outline level and
  grid alignment.
- Task 1.2 is satisfied by exact line-spacing combination checks, a
  field-level `hanging_indent` validator for contradictory indentation,
  bounded outline levels and closed Pydantic literals. Tests assert exact
  error paths for fixed, multiple and single spacing, indentation and an
  invalid TOC enum.
- Task 1.3 is satisfied by `BodySpec` and `HeadingLevelSpec` inheriting the
  common paragraph contract. Schema assertions prove the legacy required
  fields and defaults remain intact.
- Task 1.4 is satisfied by strong semantic, TOC, bibliography, citation,
  page-geometry, border, header/footer-variant and page-number display models.
  TOC and bibliography title/entry styles have one canonical owner rather than
  duplicate semantic-style fields. The PAGE/NUMPAGES conflict is enforced by a
  parsed-model `SectionSpec` after-validator, so both YAML loading and direct
  construction with already validated child models use the same invariant.
- Task 1.5 is satisfied by presence-aware legacy normalization using
  `model_fields_set`, one-way legacy-to-variant defaults, explicit rejection of
  ambiguous mixed declarations, and compatibility defaults for page-number
  display.
- Task 1.6 is satisfied by current built-in, minimal legacy, complete P0,
  inheritance, unknown-field, indentation, line-spacing, enum, border-path,
  mixed-policy and all six enabled PAGE/NUMPAGES variant tests, plus the
  disabled-variant exception and direct validated-submodel construction
  regression.
- Task 1.7 is satisfied at this task's boundary: direct source inspection and
  architecture tests show no `docx`, `lxml`, renderer dependency, raw OOXML,
  Word style ID input or school-specific renderer constant in the Template
  Model.

## Extra Behavior

- `LengthSpec.__str__` now preserves integral trailing zeroes such as `20pt`
  and `150mm`. This is required for correct round-tripping of the newly tested
  policy lengths and has direct parameterized regression coverage.
- The new policy classes are exported from
  `src/thesis_forge/templates/__init__.py`. Both `brief.md` and `context.json`
  now explicitly include that file in the task allowlist, so this is no longer
  a scope deviation.

## Misunderstood Requirements

- None remaining.
- `SectionSpec` now treats disabled page numbering as a section-level
  invariant and reports the complete
  `sections.<role>.<header|footer>.<default|first|even>.page_number` path for
  complete YAML input. Because validation runs after child parsing, callers
  cannot bypass the invariant by constructing `SectionSpec` from
  `HeaderFooterSpec` and `PageNumberSpec` instances.
- `HeaderFooterSpec` now distinguishes explicit legacy fields from omitted
  defaults. Explicit false/empty legacy values cannot be silently overwritten
  by new variants.
- New variant policies intentionally do not project back into fields consumed
  by the legacy Renderer. This prevents partial activation before tasks
  002-006 and preserves the task's stated renderer boundary.

## Cannot Verify From Diff

- A1 DOCX style emission remains deferred to task 002. This task verifies the
  complete YAML/model policy and validation portion only.
- A3 semantic role resolution and rendered abstract/keyword styles remain
  deferred to task 003.
- A4 TOC style/tab/leader OOXML remains deferred to task 004.
- A5 citation superscript and bibliography OOXML remain deferred to task 005.
- A6 first/default/even relationships, borders, distances and PAGE/NUMPAGES
  emission remain deferred to task 006.
- A7 compiler role resolution and complete RenderPlan neutrality remain
  deferred to task 003. Only the Template Model architecture boundary is
  verified here.
- A8 renderer-constant inspection, offline command execution and repeated-build
  determinism remain deferred to tasks 007-008. Only the Template Model
  boundary is verified here.
- A9 and A10 complete DOCX package and Word/WPS evidence remain deferred to
  tasks 007-008.
- The reported initial red TDD run and CodeGraph claim match are not recorded
  as system-executed validation-log entries and were not required for this
  approval.

## Acceptance Assertions Verified

- A2: every current built-in template loads, a minimal legacy-shaped template
  remains valid, inherited body/heading requirements and defaults are asserted,
  legacy header/footer fields normalize one-way without changing the fields
  consumed by the existing Renderer, citation remains inline by default, and
  the current system-attested and independently rerun focused/full suites pass.

## Required Fixes

- None blocking task 001 approval.
