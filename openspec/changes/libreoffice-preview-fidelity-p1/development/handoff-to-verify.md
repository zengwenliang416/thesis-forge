# Development Handoff To Verify: libreoffice-preview-fidelity-p1

## Implemented Slices

- `001-preview-font-adaptation`
- `002-heading-color-verification`

## Files Changed

- Application PDF preview font detection/adaptation and Office refresh package
  preservation.
- Example university Heading 1/2/3 template policy.
- Focused model, OOXML, failure-path and acceptance tests.
- Current DOCX/PDF audit artifacts and SpecNav development evidence.

## Requirements Covered

- macOS-only installed-family-gated aliases for LibreOffice preview conversion.
- Strict WordprocessingML font attribute rewriting in a disposable DOCX.
- Source DOCX immutability, isolated profile cleanup, timeout/process cleanup,
  PDF validation, previous-output retention and atomic publication.
- Formal DOCX preservation of `宋体`, `黑体` and explicit black Heading 1/2/3.
- Complete PDF font, page, text and package audit.

## Prototype Decisions Implemented

- Implemented approved `macos-temporary-font-alias-v1`.
- `宋体` uses the verified `Source Han Serif SC` LibreOffice alias only when a
  compatible Songti family is installed; `黑体` uses `PingFang SC` only when a
  compatible Heiti/PingFang family is installed.
- Formal DOCX names remain authoritative and unchanged.

## Components Created / Reused / Extracted

- Created pure installed-font and alias-resolution seams plus one strict
  conversion-only DOCX package adapter.
- Reused `LibreOfficePdfPreviewExporter`, LibreOffice process ownership, PDF
  validation and atomic output helpers.
- Extended the existing safe Office refresh seam to restore renderer-owned
  package parts and roll back invalid packages.

## API / Data Flow Changes

- Internal preview flow is now `formal DOCX -> optional disposable adapted
  DOCX -> LibreOffice -> validated atomic PDF`.
- Public CLI, Web, Tauri, sidecar and build result contracts are unchanged.
- No new network, database, account, UI or persistent configuration surface.

## Tests Added

- Font probe success/failure, partial/empty candidates and non-macOS behavior.
- Exact WordprocessingML attributes, non-target namespace lookalikes, text and
  binary resource preservation.
- Refresh mutation, deletion and invalid ZIP rollback.
- Heading 1/2/3 model and OOXML black/font/theme assertions.

## Local Validation

- Affected Python suite: `254 passed`; full Python: `475 passed`.
- Ruff, pip check, strict OpenSpec and diff check passed.
- PDF embeds `STSongti-SC-Regular` and `PingFangSC-Semibold`, excludes Arial
  Unicode MS, is 7-page A4, text-extractable and qpdf-clean.
- Formal DOCX SHA-256:
  `b358ea9ea98be1d14cb0f56cf772af747325936ddfe266efdfd8abb5d2210a3d`.
- Preview PDF SHA-256:
  `724b58606a62367dd81312dccd769acd9b21aecc7222fd973f4eb8922e739279`.
- Frontend `81 passed`, typecheck/lint passed; Rust protocol `26 passed` and
  cargo check passed.
- macOS distribution verifier returned `ok:true`; arm64 app was installed at
  `/Applications/ThesisForge.app` and byte-compared without launching.

## Known Risks

- LibreOffice/font family resolution may change across future OS or Office
  versions; unavailable candidates safely fall back to the source DOCX.
- Windows/Linux branches are covered by behavior tests but not target-native
  LibreOffice execution in this macOS run.
- The local app is unsigned and not notarized.
- LibreOffice and WPS/Word pagination is not claimed to be pixel-identical.

## Items Requiring Six-Domain Verification

- Bind A1-A3 to signed validation receipts from a clean reviewed Git snapshot.
- Re-run static/unit/redteam/E2E evidence from that reviewed snapshot.
- User sensory: open the installed app, load
  `examples/complete-thesis/thesis.md`, select the example template, wait for
  `LibreOffice PDF`, and compare body font, black Heading 1/2/3 and TOC with
  the formal DOCX in WPS.
