# Prototype Handoff: libreoffice-preview-fidelity-p1

## Approved Branch Variant

- Branch: `logic-state`
- Variant: `macos-temporary-font-alias-v1`
- User approval: continue using and optimize LibreOffice on August 13, 2026.

## Flow

- Source/published DOCX remains unchanged.
- macOS conversion creates a disposable package copy.
- Exact OOXML font-name attributes map `宋体` to `Source Han Serif SC` and `黑体` to
  `PingFang SC`.
- LibreOffice converts only the disposable copy.
- Non-macOS conversion uses the source DOCX without macOS aliases.
- Adaptation or conversion failure leaves DOCX success and any prior PDF intact.

## Components To Create

- Pure platform alias resolver.
- Safe disposable DOCX package adapter.

## Components To Reuse

- `LibreOfficePdfPreviewExporter`
- executable discovery
- isolated profile
- bounded Office process ownership
- PDF validation and atomic replacement

## Extraction Targets

- Keep platform alias selection as one pure application utility.
- Keep DOCX package adaptation in one preview-only helper.
- Reuse the existing isolated Office process and atomic PDF publication path.

## API Contracts

- Existing `PdfPreviewExporter.export(docx_path, pdf_path) -> PdfPreviewArtifact | None`.
- Internal `preview_font_aliases(platform) -> mapping`.
- Internal disposable package adapter returning an adapted path owned by the conversion profile.

## Data Flows

- Published or temporary DOCX -> optional macOS disposable font adaptation -> LibreOffice PDF.
- Valid PDF -> signature validation -> atomic preview replacement.
- Adaptation/conversion failure -> preview unavailable while DOCX remains authoritative.

## State Behavior

- Loading: the current PDF remains visible while a new conversion runs.
- Ready: the validated PDF is published with the existing `LibreOffice PDF` label.
- Error: adaptation or conversion failure does not replace a previous valid PDF.
- Disabled: missing LibreOffice still disables automatic PDF only.
- Platform: macOS uses the approved aliases; Windows and Linux convert the original DOCX.

## Theme And Locale Policy

- Theme support: `light-only`; no UI change.
- Theme toggle: intentionally omitted.
- Internationalization: disabled.
- Product copy locale: fixed `zh-CN`.
- Locale switcher: intentionally omitted.

## Out Of Scope Items

- New UI controls or font settings.
- Bundled proprietary or open-source CJK font binaries.
- Changes to published DOCX font names.
- WPS/Word automation or cross-engine pixel-equality claims.

## Required Tests

- Exact attribute replacement without replacing thesis text.
- macOS, Windows, and Linux alias selection.
- Input DOCX byte preservation and adapted-copy cleanup.
- Existing timeout, invalid PDF, and previous-output preservation.
- Complete-thesis PDF font and page-count audit.
- Heading 1/2/3 explicit black OOXML.

## Open Risks

- LibreOffice remains a different layout engine from WPS/Word.
- macOS system font aliases may change in a future OS release; failure remains best-effort.
