# Quality Review: 001-preview-font-adaptation

## Verdict

approved

## Separation Of Concerns

- Installed-font discovery, alias resolution and disposable package adaptation remain inside `application/pdf_preview.py`, while renderer-owned package restoration remains in `application/office_refresh.py`.
- Core, Parser, Compiler, RenderPlan, Renderer and frontend remain independent of platform font discovery. The existing public `PdfPreviewExporter.export()` and document refresher contracts are unchanged.
- XML parsing is used only to identify exact WordprocessingML elements and attributes; byte-level replacement preserves unrelated XML formatting and document text.

## Component Cohesion / Coupling

- `_installed_font_families()` is a bounded, failure-safe probe; `preview_font_aliases()` is a pure resolver when installed families are injected; `_adapt_docx_font_aliases()` owns one preview-only ZIP transformation.
- `_PackagePart`, `_read_package_parts()` and `_restore_package_parts()` form a cohesive safe-refresh helper set and preserve both content and `ZipInfo` metadata for renderer-owned parts.
- No duplicate platform-font logic or cross-layer service was introduced.

## Test Quality

- Reviewer-executed `tests/test_pdf_preview.py`: `29 passed`. Coverage includes probe command failure/timeout/non-zero exit, localized family aliases, partial and empty candidates, macOS/Windows/Linux branches, exact WordprocessingML attributes, foreign namespace lookalikes, source bytes, ZIP metadata, binary resources, disposable cleanup, timeout cleanup, invalid PDF and previous-output preservation.
- Reviewer-executed refresh selection: `19 passed, 52 deselected`. Coverage includes mutation restoration, deleted renderer-owned parts and invalid ZIP rollback.
- Reviewer-executed counterexamples confirmed that a foreign namespace remains unchanged, a corrupt refreshed package returns `False` and restores original bytes, and deleted renderer-owned parts are reinserted.
- A fresh real LibreOffice conversion independently exercised the complete DOCX path and reproduced source immutability, valid PDF output and expected Chinese font embedding.

## Error Handling

- Font probe `OSError`, timeout/subprocess failure and non-zero exit safely return no candidates, causing direct source-DOCX conversion.
- Malformed XML is left unchanged rather than partially rewritten.
- Adaptation/conversion errors remain contained by the best-effort exporter; invalid or missing PDFs are not published and previous valid PDFs are preserved.
- `BadZipFile` during refresh restoration is now caught and the original DOCX bytes are restored. The reviewer reproduced this behavior directly.

## Reuse / Duplication

- Existing executable discovery, isolated LibreOffice profile, process ownership, PDF validation and atomic output replacement are reused.
- Font probing, alias policy and OOXML rewriting each have one implementation used by production and tests. No unnecessary shared ZIP abstraction was introduced between preview adaptation and refresh restoration.

## Complexity Delta

- The namespace-aware byte replacement is more complex than the rejected regex-only implementation, but the added complexity is bounded and necessary to preserve non-target XML bytes while enforcing exact namespace semantics.
- Refresh restoration now handles modified, deleted and corrupt package states without changing the surrounding build flow. The state space is closed by focused regression tests.
- No new dependency, public configuration, persistent state or architectural layer was added.

## Acceptance Assertions Verified

- A1 - verified and satisfied through code inspection, focused tests, direct failure-path counterexamples and an independent real LibreOffice conversion that preserved the source DOCX bytes and produced a validated PDF.

## Required Fixes

- None for task 001.
