## Why

LibreOffice on macOS does not reliably resolve DOCX `宋体` to the installed Songti family and
currently emits Arial Unicode MS in the live PDF preview. The example template also leaves heading
color implicit, allowing built-in Word theme blue to leak into DOCX and PDF output.

## What Changes

- Adapt a temporary DOCX copy before LibreOffice conversion so macOS resolves Chinese template
  fonts to stable local serif and sans families.
- Keep the rendered and published DOCX byte-for-byte unchanged by preview adaptation.
- Keep Windows font names unchanged and avoid macOS aliases outside macOS conversion.
- Set explicit black Heading 1, Heading 2, and Heading 3 colors in the example template.
- Add package-level and real PDF font audits for the conversion boundary.

## Capabilities

### New Capabilities

- `libreoffice-preview-fidelity`: Isolated platform-aware font adaptation for optional
  LibreOffice PDF preview conversion.

### Modified Capabilities

- `render-plan-docx`: The example school template explicitly defines black colors for all supported
  heading levels.

## Impact

- Affected code: `src/thesis_forge/application/pdf_preview.py`, focused tests, and the example
  school template.
- Public API: unchanged.
- Dependencies: no new Python package, service, network, or bundled font dependency.
- Runtime: LibreOffice remains optional and best-effort.
