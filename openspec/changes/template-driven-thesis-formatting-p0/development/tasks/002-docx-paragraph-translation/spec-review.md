# Spec Review: 002-docx-paragraph-translation

## Verdict

approved

The actual renderer diff, direct OOXML assertions and independently rerun
tests force approval for tasks 2.1-2.7 at the shared DOCX paragraph
translation boundary.

Reviewer-executed current-worktree evidence:

- `.venv/bin/python -m pytest tests/test_docx_renderer.py tests/test_template.py -q`
  -> `78 passed in 1.05s`
- `.venv/bin/python -m pytest -q` -> `308 passed in 14.79s`
- `.venv/bin/ruff check .` -> `All checks passed`
- `git diff --check` -> passed
- Final CodeGraph evidence `ev-mscqnesn` is matched to
  `development:task-002-docx-paragraph-translation` and identifies the shared
  translator, body absolute-size validation, single-spacing XML and stable
  style package round trip.

The matching `78` focused / `308` full / Ruff / diff-check results are also
recorded in `validation-log.jsonl` with `attestation: "system-executed"`.

## Missing Requirements

- None within tasks 2.1-2.7.
- Task 2.1 is satisfied by the typed `apply_paragraph_style()` path for both
  `ParagraphStyle` and concrete `Paragraph` targets. It applies font, size,
  bold, italic, alignment, left/right/first-line/hanging indentation,
  before/after spacing, fixed/multiple/single line spacing and all required
  pagination properties.
- Task 2.2 is satisfied by explicit translation of `w:widowControl`,
  `w:keepNext`, `w:keepLines`, `w:pageBreakBefore`, `w:outlineLvl` and
  `w:snapToGrid`, including explicit false values. Focused XML assertions
  verify both enabled and disabled forms.
- Task 2.3 is satisfied. Paragraph-relative `em` lengths use the resolved
  target policy size, and a relative heading size is first resolved against
  the body fallback size. Tests prove 15 pt paragraph `em` conversion and a
  1.5 em heading over a 10 pt body base without a global 12 pt assumption.
  `BodySpec` now rejects `body.size: em` at template-validation time with the
  exact `body.size` error path, so the root fallback can never be ambiguous.
- Task 2.4 is satisfied because `configure_styles()` routes Normal and every
  configured Heading 1-3 through `apply_paragraph_style()`. Heading-level XML
  tests prove all three levels use their own target sizes.
- Task 2.5 is satisfied by the closed `PARAGRAPH_STYLE_NAMES` registry and
  `ensure_paragraph_style()`. All supported semantic roles produce stable,
  idempotent internal style IDs based on Normal; unsupported arbitrary Word
  style IDs are rejected, and no template field accepts a Word style ID. A
  package round-trip test proves the stable style is saved in `styles.xml`,
  referenced through paragraph `w:pStyle`, and remains resolvable after
  reopening with python-docx.
- Task 2.6 is satisfied by direct `styles.xml` and paragraph XML assertions for
  fonts, size, emphasis, alignment, indentation, spacing, line rules,
  pagination, outline, grid and stable style IDs. Single spacing is explicitly
  asserted as Word's quantized `w:lineRule="auto"` / `w:line="240"` form.
- Task 2.7 is satisfied at this slice's boundary. Two templates applied to the
  same `ThesisDocument` produce different Normal style XML while preserving
  the same ordered body text. The production diff is confined to DOCX style
  and font translation, so it does not alter Compiler semantic instructions.

## Extra Behavior

- `apply_font()` now accepts an absent font policy and an explicit `em_size_pt`
  base. This is necessary for partial paragraph policies and relative target
  sizes; existing callers retain the previous 12 pt default when they do not
  supply a base.
- `BodySpec` now rejects relative root font sizes because no deterministic
  absolute base exists for Normal. `src/thesis_forge/templates/model.py` is
  explicitly included in the final task brief/context allowlist.
- `ensure_paragraph_style()` creates semantic named styles on demand rather
  than adding every unused semantic style to every document. Role selection
  remains correctly deferred to task 003.

## Misunderstood Requirements

- None found.
- Optional paragraph properties are deliberately skipped when `None`; they are
  not assigned as `None` to python-docx. This preserves built-in Heading
  properties such as `keepNext`, `keepLines` and existing outline behavior.
- Explicit false values are not treated as omissions. The generated XML uses
  `w:val="0"` where required.
- Stable Word style IDs are renderer-owned implementation details selected by
  closed semantic roles, not template-configurable identifiers.

## Cannot Verify From Diff

- A3 semantic role recognition and binding to the stable internal styles
  remain deferred to task 003.
- TOC tab/leader behavior, bibliography presentation and header/footer
  paragraph use of the translator remain deferred to tasks 004-006.
- A8 is only partially evidenced here: renderer source contains no
  school-specific names, fonts or dimensions, and the two-template test
  preserves this slice's text semantics. Complete offline core-command
  execution, repeated-build determinism and broader semantic equivalence for
  numbering, references and bookmarks remain deferred to tasks 007-008.
- A9 complete P0 package validation and A10 Word/WPS sensory evidence remain
  deferred to tasks 007-008.
- The report's initial red TDD narrative is not present as a system-executed
  validation-log entry and was not used as approval evidence.

## Acceptance Assertions Verified

- A1: task 001 proves YAML/model validation, while this diff emits the complete
  body paragraph policy into Normal and heading pagination into Heading
  styles. Direct XML assertions cover fonts, indentation, spacing, exact line
  spacing, quantized single spacing, alignment, widow control, keep properties,
  page break, outline and grid values.
- A2: all current templates continue to pass, Normal retains the legacy
  required translation, and omitted optional Heading fields leave built-in
  `keepNext` and `keepLines` XML intact. The full regression suite passes.

## Required Fixes

- None blocking task 002 approval.
