## Context

The generated DOCX already declares `宋体` for body text and `黑体` for headings. On the current
macOS host, LibreOffice converts `宋体` to Arial Unicode MS even though Songti is installed. Direct
use of `Songti SC`, `STSong`, and PostScript names also falls back incorrectly. A conversion-only
DOCX copy using `Source Han Serif SC` resolves to the installed `STSongti-SC-Regular`, while
`PingFang SC` provides a stable macOS sans heading family. The original and adapted PDFs retain the
same six-page count in the complete thesis fixture.

## Goals / Non-Goals

**Goals:**

- Improve macOS live PDF body and heading font fidelity.
- Preserve the published DOCX and its school template font names.
- Keep the adaptation isolated, bounded, testable, and disposable.
- Make heading color deterministic in the example template.

**Non-Goals:**

- Bundle proprietary or large CJK font files.
- Change Word/WPS font semantics for Windows.
- Promise WPS/Word pagination equality.
- Add a user-facing font manager in this slice.

## Decisions

### Adapt a disposable DOCX package

Before conversion on macOS, copy the DOCX into the isolated LibreOffice profile and rewrite only
OOXML font-name attribute values. Do not perform unrestricted text replacement, because thesis
content may legitimately mention font names.

### Use macOS aliases proven by a complete fixture

Map `宋体` to `Source Han Serif SC`, which LibreOffice resolves to the installed
`STSongti-SC-Regular`, and map `黑体` to `PingFang SC`. Do not apply these aliases on Windows or
Linux. A later Linux slice may add distribution-specific aliases after equivalent real PDF evidence.

### Preserve the source package

LibreOffice receives only the disposable adapted copy. The exporter validates and atomically
publishes only the PDF; the input and published DOCX are never rewritten.

### Keep failure best-effort

If package adaptation or conversion fails, return preview unavailable and preserve the previous
valid PDF and DOCX behavior.

## Risks / Trade-offs

- [Risk] macOS font availability may change across OS releases.
  -> Keep the mapping small, isolate it to preview conversion, and retain the best-effort fallback.
- [Risk] Repacking a DOCX may lose ZIP metadata.
  -> Preserve each `ZipInfo` entry and modify only XML parts containing exact font-name attributes.
- [Risk] The preview uses macOS-compatible font aliases rather than the literal Windows family.
  -> Keep the engine label truthful and never modify the formal DOCX.

## Migration Plan

No source or template migration is required. Rollback removes the conversion-only package adapter
and leaves the explicit heading colors valid.

## Open Questions

None.
