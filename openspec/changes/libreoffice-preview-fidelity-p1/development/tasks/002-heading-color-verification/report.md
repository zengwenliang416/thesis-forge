# Task Report: 002-heading-color-verification

## Status

DONE

## Files Changed

- `templates/schools/example-university/2026.yaml`
- `tests/test_template.py`
- `tests/test_docx_renderer.py`
- `tests/test_acceptance.py`
- `output/verification/libreoffice-preview-fidelity-p1/*`
- `src-tauri/binaries/thesisforge-sidecar-aarch64-apple-darwin`
- `src-tauri/target/aarch64-apple-darwin/release/bundle/macos/ThesisForge.app`
- `/Applications/ThesisForge.app`

## What Changed

- Made Heading 1 and Heading 2 explicitly black and added a complete Heading 3
  policy with black `000000`, Chinese `黑体`, Times New Roman, 12pt and bold.
- Kept the missing-style acceptance case by creating a temporary template that
  intentionally omits Heading 3.
- Rebuilt the complete thesis DOCX and LibreOffice PDF, audited the formal DOCX
  styles and PDF fonts, rebuilt the arm64 sidecar and `.app`, and installed the
  byte-identical app into `/Applications`.

## TDD Evidence

- Template tests assert all three heading policies at the model boundary.
- DOCX tests inspect `word/styles.xml` for Heading 1/2/3 `黑体`, `000000`,
  boldness and absence of theme color modifiers.
- The combined affected suite passed `254` tests and the full Python suite
  passed `475` tests.

## Verification Commands

- `.venv/bin/python -m pytest -p no:cacheprovider
  tests/test_template.py tests/test_docx_renderer.py tests/test_pdf_preview.py
  tests/test_application_services.py tests/test_acceptance.py -q`
  -> `254 passed`.
- `.venv/bin/python -m pytest -p no:cacheprovider -q` -> `475 passed`.
- `pdffonts`, `pdfinfo`, `pdftotext`, and `qpdf --check` against
  `complete-thesis.preview.pdf` -> Songti/PingFang embedded, no Arial Unicode
  MS, 7 A4 pages, extractable text, and no PDF syntax/stream errors.
- Formal DOCX audit -> Normal `宋体`; Heading 1/2/3 `黑体` and `000000`;
  no `themeColor`; populated TOC content retained.
- Current hashes: DOCX
  `b358ea9ea98be1d14cb0f56cf772af747325936ddfe266efdfd8abb5d2210a3d`;
  PDF
  `724b58606a62367dd81312dccd769acd9b21aecc7222fd973f4eb8922e739279`;
  packaged sidecar
  `f1a613aa0ba290a53ff0b33a86d05c39804202dac24b08e22fb3525c7fc5517d`.
- Frontend -> `81 passed`, typecheck and lint passed.
- Rust protocol contract -> `26 passed`; `cargo check` passed.
- macOS distribution verifier -> `ok: true`; installed app executable,
  sidecar, Info.plist and resources match the built `.app`.

## Concerns

- The locally installed app is an unsigned development bundle. It is suitable
  for local testing but is not claimed to be Developer ID signed or notarized.
- No automated or agent-driven UI sensory test was performed, per user
  instruction.

## Scope Deviations

- None recorded.

## Follow-up Needed

- User manual test:
  1. Open `/Applications/ThesisForge.app`.
  2. Open `examples/complete-thesis/thesis.md`.
  3. Select the example university 2026 template.
  4. Wait for the right pane to show `LibreOffice PDF`.
  5. Check that body Chinese text resembles Songti, Heading 1/2/3 are black
     Heiti-style text, and the TOC is populated.
  6. Build/download the DOCX and compare it in WPS without expecting
     pixel-identical pagination.

## Adjudication

Production behavior and automated evidence are complete. Manual sensory remains
explicitly assigned to the user and does not block development completion.
