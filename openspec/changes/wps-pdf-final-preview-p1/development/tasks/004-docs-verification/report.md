# Task Report: 004-docs-verification

## Status

DONE_WITH_CONCERNS

## Files Changed

- `docs/ARCHITECTURE.md`
- `docs/MAINTENANCE.md`
- `docs/USER_MANUAL.md`
- `output/verification/wps-pdf-final-preview-p1/*`
- lifecycle evidence under this change

## What Changed

- Documented structural versus final-layout preview, LibreOffice/WPS labels,
  `.preview.pdf`, stale semantics and runtime-specific recovery.
- Built the complete HUT DOCX and a real LibreOffice PDF through the production
  exporter seam.
- Inspected all 12 rendered pages and recorded package, PDF, hash and cleanup
  evidence.

## TDD Evidence

- Full Python, frontend, Rust, HTTP, E2E, Ruff, OpenSpec and diff checks passed.
- Browser sensory checked desktop and 390px final-layout empty states.
- Real PDF page images cover cover, abstracts, TOC, body, figure/table/equation,
  bibliography, acknowledgements and appendix without clipping.

## Verification Commands

- DOCX package validation -> passed.
- `qpdf --check` -> no syntax or stream errors.
- PDF metadata -> LibreOffice `26.2.3.2`, 12 A4 pages.
- DOCX SHA-256:
  `542e399890ac4f13f4b1562e40acb292357b5c4466e1504deaa9e11c478350fa`.
- PDF SHA-256:
  `417e9af14f6529b87597c5b249029baaaf1fdca564afd2e4bb8bded9ef02664d`.

## Concerns

- No exact WPS-exported PDF was available in the current run. LibreOffice
  output is not claimed to be WPS-equivalent.
- Native Windows and packaged macOS sensory remain verification gates.

## Scope Deviations

- None recorded.

## Follow-up Needed

- Open an exact WPS-exported PDF through the picker and compare it page by page
  in the right viewer during sensory verification.

## Adjudication

Automated and LibreOffice development evidence is complete. Independent review
must decide whether the exact WPS comparison is a development blocker or a
six-domain sensory item.
