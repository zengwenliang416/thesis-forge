# Spec Review: 005-equations-references-and-page-structure

## Verdict

approved

The latest final checkout satisfies the task contract. Approval is based on
current source and tests, independently rerun checks, direct inspection of the
v3 DOCX/PDF artifacts, and the latest `attestation: "system-executed"`
validation records. The final quality-review fixes are present and verified.

## Missing Requirements

| Task | Result | Independent verification |
| --- | --- | --- |
| 5.1 | satisfied | `core/math.py` defines the renderer-neutral `MathConverter`, semantic math nodes and typed conversion errors. `docs/MATH_SPEC.md` documents the exact V1 subset and explicit unsupported/malformed behavior. |
| 5.2 | satisfied | Supported LaTeX becomes editable `m:oMath` structures for fractions, radicals, scripts, sums, functions and accents. Equation numbering uses a real SEQ field; the matching bookmark encloses only the resolved number field after the OMML object. Unsupported matrix LaTeX fails through the CLI with exit code 2, no traceback and no fallback output. |
| 5.3 | satisfied | `fields.py` owns the complete begin/instruction/separate/result/end construction, dirty state and the target-neutral `reference_field_runs()` helper. `bookmarks.py` remains the single bookmark implementation. Tests verify field ordering, dirty state, REF instruction generation and bookmark pairing/ranges. |
| 5.4 | satisfied | Figure/table/equation captions use Compiler-supplied sequence instructions and real SEQ fields. Body references call `add_reference_field()`, which delegates to `reference_field_runs()`; footnote references directly extend the same `reference_field_runs()` output. Both targets therefore share one REF implementation and retain Compiler-supplied bookmark/result values. |
| 5.5 | satisfied | A real TOC field is emitted for heading levels 1-3 and `word/settings.xml` contains `w:updateFields w:val="true"`. |
| 5.6 | satisfied | The DOCX contains a real `word/footnotes.xml` part, reserved IDs `-1` and `0`, stable positive definition/reference IDs, the required content type and relationship, body `w:footnoteReference`, and a complete REF field inside footnote content. Nested footnotes fail explicitly. |
| 5.7 | satisfied | Compiler emits explicit cover/front-matter/main transitions. Renderer creates section properties, start types, header/footer parts and relationships, Roman/decimal page formats, restart-at-one and PAGE/NUMPAGES fields. The disabled regression config includes non-empty header/footer text, but the later parts remain empty, unlinked from the prior section and free of inherited text or page fields. `format: none` emits no PAGE/NUMPAGES field. |
| 5.8 | satisfied | Focused ZIP/XML tests inspect OMML node types, all field structures, bookmark ranges, footnote package data, section properties, page formats/restarts, header/footer relationships, disabled inheritance, update-on-open and typed error behavior. The current complete suite passes 72 tests. |

## Extra Behavior

- No unauthorized file is identified. All report-declared changed files are in
  the current `context.json.allowed_files`; `errors.py` and `inlines.py` remain
  explicitly authorized, and all allowed/test paths exist.
- Wrapping low-level `AttributeError`, `KeyError`, `TypeError` and `ValueError`
  as capability-specific `DocxRenderError` is within the declared typed DOCX
  error boundary. `MathConversionError` is caught first and re-raised
  unchanged, preserving the explicit unsupported/malformed math contract.
- No Parser syntax, Domain Word implementation detail, Template schema,
  bibliography, atomic-output, production UI, network, account or AI behavior
  was found in the reviewed task surface.

## Misunderstood Requirements

- None remain. Disabled header/footer means that configured text is ignored
  while an empty non-inheriting later-section part may be materialized to
  suppress Word inheritance. Current `sections.py` and the focused regression
  test implement that exact brief clause.
- The shared REF requirement is implemented at the field-run level rather than
  by duplicating instruction strings in body and footnote renderers.
- Generic low-level `ValueError` is an implementation failure to normalize;
  `MathConversionError`, although it subclasses `ValueError`, is an intentional
  user-facing conversion result and remains explicit because of exception
  ordering in `DocxRenderer.render()`.

## Cannot Verify From Diff

- The repository remains entirely untracked, so Git cannot reconstruct a
  historical task-scoped diff or prove which files changed during task 005.
  Current-file inspection confirms that the report-declared set is within the
  current allowlist and exposes no current scope violation.
- Word and WPS were not opened interactively. The recorded and present
  LibreOffice artifact is a three-page A4 PDF, and an independent headless
  conversion also produced a three-page A4 PDF.
- LibreOffice PDF output is not byte-stable across independent conversions:
  the original system-executed v3 PDF matches the recorded SHA-256
  `f0bcda6f0d545c094e03fbfa92caa18cefff61ee03bf8a573f0c17e11666c073`,
  while the independent re-conversion produced a different binary hash with
  the same three-page A4 result. PDF byte determinism is not a task 005
  requirement.
- CodeGraph evidence `ev-ms8d5azt` is available through the latest
  system-executed validation record and reports no blockers with all five
  development claims verified. Current source was independently re-read
  through CodeGraph and matched the reviewed section, shared REF and typed
  error paths.

## Acceptance Assertions Verified

- `A4`: Current Compiler source and tests verify deterministic chapter-aware
  numbering, sequence instructions, bookmark names, resolved reference
  targets, citation order, positive footnote IDs, TOC placement and explicit
  section transitions before rendering. RenderPlan remains renderer-neutral.
- `A5`: Direct tests and independent v3 package inspection verify real TOC,
  SEQ, body REF, footnote REF, bookmarks, PAGE, NUMPAGES, OMML, footnote,
  section, header and footer structures. The review DOCX contains 23 valid
  parts, three sections, one editable OMML object, three SEQ fields, two body
  REF fields, one footnote REF field, update-on-open, two header parts and two
  footer parts; python-docx reload succeeds.
- `A8`: Independently rerun checks passed: 72 pytest tests, Ruff, pip dependency
  check and `git diff --check`. Architecture tests preserve Parser/Domain/Core
  neutrality, and focused tests inspect package/XML structures rather than
  relying on file existence.

## Required Fixes

- None for task 005.

## Reviewer Checks

- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider`
  -> `72 passed in 3.21s`.
- Focused final quality-fix tests -> `5 passed`.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/ruff check .` -> passed.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pip check` -> passed.
- `git diff --check` -> passed.
- Low-level exception probe -> `ValueError` became
  `DocxRenderError(capability="equation")`; `UnsupportedMathError` remained the
  original exception type.
- `/tmp/thesisforge-005-v3.docx` SHA-256 ->
  `43d7e4ecc92028b61a11a1a2ca29ff05042b891cabc1fffb17a966e9ab67a3e6`.
- `/tmp/thesisforge-005-review-v3/review.docx` SHA-256 ->
  `8a215964850bd005e9f01f9f8e568a5f87a77cbb8153fa765974c899c1de5ddf`;
  ZIP integrity, OOXML inspection and python-docx reload passed.
- `/private/tmp/thesisforge-005-review-v3/pdf/review.pdf` SHA-256 ->
  `f0bcda6f0d545c094e03fbfa92caa18cefff61ee03bf8a573f0c17e11666c073`;
  `pdfinfo` reports three A4 pages.
- SpecNav development entry -> `ok:true`, no blockers or warnings.
