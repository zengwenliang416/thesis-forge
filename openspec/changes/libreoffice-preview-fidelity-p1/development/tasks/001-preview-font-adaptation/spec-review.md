# Spec Review: 001-preview-font-adaptation

## Verdict

approved

## Missing Requirements

- None. The current implementation covers task items 1.1-1.3: macOS aliases are gated by installed compatible families, only a disposable DOCX is adapted, non-macOS and no-candidate cases convert the source DOCX directly, and the existing timeout, process cleanup, PDF validation and atomic publication flow is retained.
- The prior refresh findings are resolved. Renderer-owned `word/styles.xml` and `word/fontTable.xml` are restored when modified or deleted by LibreOffice, and an invalid refreshed ZIP rolls back to the original package.

## Extra Behavior

- The refresh finalization seam now preserves renderer-owned style and font-table parts. This is explicitly required by the task brief and does not change the public refresher/exporter contract.
- No changes were found in Parser, Domain, Compiler, RenderPlan, Renderer, frontend, template schema, persistence or network behavior for task 001.

## Misunderstood Requirements

- None. `preview_font_aliases()` now distinguishes platform support from installed-family availability. Probe failure or no compatible family produces an empty alias map and safely uses the authoritative source DOCX.
- `_replace_ooxml_font_attributes()` parses namespace declarations and limits changes to WordprocessingML `rFonts` and `font` attributes. A reviewer-executed foreign-namespace counterexample remained byte-identical.

## Cannot Verify From Diff

- Windows and Linux behavior is covered by focused branch tests but was not executed on target-native LibreOffice installations during this macOS review. This does not block A1 because those branches perform no adaptation and pass the source DOCX directly.
- The checked-in `sha256.txt` records PDF SHA-256 `bb87e112...`, while the current checked-in PDF is `724b5860...`; an independent reviewer conversion produced another valid PDF hash because LibreOffice embeds changing metadata. This derived-PDF hash drift should be refreshed or bound by a receipt before six-domain verification, but it does not undermine A1: the formal DOCX hash remained stable and the reviewer independently reproduced a valid conversion.

## Acceptance Assertions Verified

- A1 - verified and satisfied. The reviewer executed the focused suites (`29 passed` for PDF preview and `19 passed, 52 deselected` for refresh), inspected the current diff, and ran LibreOffice 26.2.3.2 against the complete thesis DOCX in a fresh `/tmp` directory. The source SHA-256 remained `b358ea9e...` before and after conversion; the exporter returned a validated seven-page PDF artifact; `qpdf --check` passed; `pdffonts` showed `STSongti-SC-Regular` and `PingFangSC-Semibold` with no Arial Unicode MS. The formal DOCX retained `宋体` and `黑体` and did not contain `Source Han Serif SC` or `PingFang SC`.

## Required Fixes

- None for task 001.
