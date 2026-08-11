# Task Report: 003-build-finalization-verification

## Status

DONE

## Files Changed

- `src/thesis_forge/application/services.py`
- `src/thesis_forge/application/office_refresh.py`
- `src/thesis_forge/renderers/docx/renderer.py`
- `tests/conftest.py`
- `tests/test_application_services.py`
- `tests/test_docx_renderer.py`
- `tests/test_acceptance.py`
- `templates/schools/hunan-university-of-technology/master-2026.yaml`
- `docs/TEMPLATE_SPEC.md`
- lifecycle evidence under this change

## What Changed

- Extended `FLOW-BUILD` to render a temporary DOCX, optionally refresh it,
  validate the post-refresh package and atomically replace the final output.
- Kept optional refresh failure non-fatal by restoring the Renderer output.
  A corrupt successful refresh still fails mandatory package validation and
  preserves the prior final output.
- Documented template-style versus Office-layout responsibilities and the
  three runtime environment variables.
- Documented the existing `roman-lower` / `roman-upper` template parameter and
  configured HUT front matter as `roman-upper`.
- Rebuilt the complete HUT thesis with LibreOffice and materialized 19 editable
  TOC entries and page numbers.

## TDD Evidence

- OOXML tests prove independent title/field paragraphs, `outlineLvl=9`, stable
  bookmark, field characters, dirty marker and update-fields fallback.
- Application tests prove `render -> refresh -> validate -> replace`, optional
  failure restoration, corrupt output rejection, cancellation boundaries and
  prior-output preservation.
- The full suite covers CLI, Web adapter, Tauri sidecar contracts and shared
  application service callers.
- Acceptance tests prove the HUT template renders `w:pgNumType
  w:fmt="upperRoman"` while existing renderer tests retain `lowerRoman`
  coverage.

## Verification Commands

- `.venv/bin/python -m pytest` -> `416 passed`.
- `.venv/bin/ruff check .` -> `All checks passed`.
- Real build:
  `THESISFORGE_OFFICE_REFRESH=1 .venv/bin/thesisforge build examples/complete-thesis/thesis.md -o output/verification/automatic-docx-toc-refresh-p1/hut-toc-refreshed.docx --template templates/schools/hunan-university-of-technology/master-2026.yaml`
  -> success.
- DOCX inspection -> valid package, 19 TOC entries, field
  `TOC \f \o "1-3" \h`, one title `目录`, title outline level `9`, bookmark
  `tf_toc_index`, section page formats `decimal / upperRoman / decimal`, and
  SHA-256
  `46307a81fe19b853c5e6fc8c4ae3227cf62699303b46aeb56aca9a72584b407d`.
- LibreOffice PDF sensory review -> visible 12-page output with a populated TOC
  and uppercase front-matter entries/footer `I/II/III`.
- WPS sensory review -> a byte-identical uniquely named Downloads copy opened
  in a new tab and exposed the expected populated navigation hierarchy. The
  final uppercase glyphs are independently confirmed by OOXML and the final PDF.

## Concerns

- WPS could not open the canonical `/Volumes/...` path through its own file
  picker, but opened the byte-identical Downloads copy. This is an existing WPS
  path-access issue, not a DOCX package failure.
- WPS retained an older unsaved tab during the final uppercase retest, so a
  clean single-tab screenshot of the final TOC page was not captured.
- Windows and Linux LibreOffice behavior still needs target-native release
  verification.

## Scope Deviations

- None recorded.

## Follow-up Needed

- Run the native Windows LibreOffice acceptance gate before release.

## Adjudication

Approved against tasks 2.4-3.4 and acceptance assertions `A1`, `A2` and `A3`.
