# Development Handoff To Verify: automatic-docx-toc-refresh-p1

## Implemented Slices

- `001-toc-field-structure`
- `002-libreoffice-refresh`
- `003-build-finalization-verification`

## Files Changed

- Renderer TOC paragraph/field structure and OOXML tests.
- Application Office refresher, finalization orchestration and safety tests.
- Template specification and change-local lifecycle evidence.

## Requirements Covered

- Standalone styled TOC title and following real editable field.
- Optional macOS/Linux/Windows LibreOffice discovery and isolated refresh.
- Missing, failed and timed-out refresh fallback.
- Post-refresh package validation and atomic replacement.
- Complete HUT TOC materialization and Office sensory review.
- Template-controlled front-matter Roman numeral case with HUT configured as
  `roman-upper`.

## Prototype Decisions Implemented

- The title and field have independent lifecycles.
- Office layout work remains outside Renderer and the deterministic compiler.
- The shared `build_service` owns the optional finalization seam.

## Components Created / Reused / Extracted

- Created `DocumentRefresher` and `LibreOfficeDocumentRefresher`.
- Reused TOC field, bookmark, package-validation and atomic-output helpers.
- Centralized UNO, process discovery and Win32 Job Object ownership in one
  application module.

## API / Data Flow Changes

- `ApplicationDependencies` now injects `document_refresher`.
- `FLOW-BUILD` is now render temporary -> optional refresh -> validate package
  -> cancellation check -> atomic replace.
- Public CLI, Web, Tauri and `BuildResult` contracts are unchanged.

## Tests Added

- Cross-platform discovery and UNO Python capability tests.
- Headless profile/pipe, timeout, restoration and process-tree tests.
- Build order, corruption, cancellation and previous-output tests.
- Exact TOC title, bookmark, outline and field OOXML tests.
- HUT template and complete-build assertions for `w:pgNumType upperRoman`.

## Local Validation

- `416 passed` full pytest.
- Full Ruff and diff checks passed.
- Real LibreOffice 26.2.3.2 HUT build produced 19 TOC entries and a valid DOCX.
- Final DOCX SHA-256 is
  `46307a81fe19b853c5e6fc8c4ae3227cf62699303b46aeb56aca9a72584b407d`.
- LibreOffice PDF showed a populated TOC with `I/II/III`; WPS loaded a
  byte-identical Downloads copy and exposed the expected populated navigation
  hierarchy. No residual LibreOffice process or temporary profile remained.

## Known Risks

- Windows and Linux LibreOffice runtime paths are not target-native tested in
  this change.
- LibreOffice and WPS paginate the sample differently, as allowed by scope.
- WPS required a byte-identical Downloads copy because its file picker did not
  resolve the canonical `/Volumes/...` path.
- WPS retained an older unsaved tab during the final uppercase retest, so the
  final same-SHA WPS evidence is the new tab and populated navigation hierarchy;
  exact `I/II/III` rendering is independently covered by OOXML and the final
  LibreOffice PDF.

## Items Requiring Six-Domain Verification

- Confirm assertion-to-evidence bindings for `A1`-`A3`.
- Re-run static/unit/redteam/e2e/sensory evidence from the committed state.
- Treat native Windows LibreOffice behavior as an explicit residual platform
  risk until a target-native verification run exists.
