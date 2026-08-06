# Task Report: 005-citations-bibliography

## Status

DONE

## Files Changed

- `src/thesis_forge/renderers/docx/inlines.py`
- `src/thesis_forge/renderers/docx/footnotes.py`
- `src/thesis_forge/renderers/docx/renderer.py`
- `tests/test_docx_renderer.py`
- `openspec/changes/template-driven-thesis-formatting-p0/codegraph/evidence.jsonl`
- `openspec/changes/template-driven-thesis-formatting-p0/codegraph/evidence-index.json`
- `openspec/changes/template-driven-thesis-formatting-p0/development/tasks/005-citations-bibliography/brief.md`
- `openspec/changes/template-driven-thesis-formatting-p0/development/tasks/005-citations-bibliography/context.json`

## What Changed

- Connected the existing `CitationSpec.presentation` policy to DOCX rendering
  without adding presentation state to `CitationRun` or bibliography records.
- Added one focused `citation_run_element()` helper that preserves the
  formatter-produced citation text and writes `w:vertAlign` only for
  `superscript` presentation.
- Reused the same citation helper for body, heading, list and footnote
  citations so one template does not produce inconsistent baseline behavior
  between `document.xml` and `footnotes.xml`.
- Preserved the legacy `inline` default by omitting `w:vertAlign` entirely.
- Verified that bibliography headings and generated entries continue through
  the existing semantic role resolver and shared paragraph translator.
- Proved configured bibliography title/entry fonts, stable style IDs, heading
  and body fallbacks, two-character hanging indentation, paragraph spacing and
  fixed line spacing in the saved DOCX package.
- Kept citation text, locator handling, first-use numbering, bibliography
  ordering and `Gbt7714Formatter` output unchanged.

## TDD Evidence

- The first citation-presentation test failed only for `superscript` because no
  `w:vertAlign` existed; `inline` and bibliography style assertions already
  passed.
- The first implementation made document citations pass, then the new
  compiler-to-footnote regression failed because `footnotes.xml` used an
  independent text-run helper.
- The task packet allowed-file list was expanded to include that discovered
  production seam, and both document and footnote paths were routed through
  the same citation OOXML helper.
- The final focused tests assert that only citation runs are superscript, body
  and footnote citation ordinals remain `[1]` and `[2]`, grouped locator text
  remains `[1,2, p. 12]`, and bibliography entry order remains deterministic.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_bibliography.py tests/test_compiler.py tests/test_docx_renderer.py -k 'citation or bibliography' -q`
  -> `18 passed, 64 deselected in 6.23s`.
- `.venv/bin/python -m pytest tests/test_bibliography.py tests/test_compiler.py tests/test_docx_renderer.py -q`
  -> `82 passed in 7.78s`.
- `.venv/bin/python -m pytest -q`
  -> `339 passed in 87.79s`.
- `.venv/bin/ruff check .`
  -> `All checks passed`.
- `git diff --check`
  -> passed.
- CodeGraph evidence `ev-mshalcs2` matches
  `development:task-005-citations-bibliography`.

## Concerns

- `CitationSpec.style` remains the existing bibliography-style identifier and
  is outside this presentation-only slice; no new formatter registry or CSL
  selection behavior was introduced.
- Full school-template configuration and Office/WPS sensory review remain
  tasks 007-008.

## Scope Deviations

- `src/thesis_forge/renderers/docx/footnotes.py` was added to the allowed files
  after a failing end-to-end test proved that footnote citations use a separate
  DOCX construction seam. This closes an in-scope presentation inconsistency;
  it does not change footnote data or numbering contracts.

## Follow-up Needed

- Task 007 should select the required citation presentation and bibliography
  paragraph policy in the HUT school template.

## Adjudication

Tasks 5.1-5.6 are implemented at the template-to-DOCX presentation boundary.
A5 is directly covered by saved-package `document.xml`, `footnotes.xml` and
`styles.xml` assertions. Both independent task reviews approved the slice.
