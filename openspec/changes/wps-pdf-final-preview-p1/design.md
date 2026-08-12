## Context

`PaperPreview` currently renders serialized RenderPlan blocks into simplified HTML and CSS. The real
DOCX renderer applies template page geometry and OOXML styles that the browser preview does not own.
The existing application layer already discovers and isolates LibreOffice for TOC refresh, but it
does not export a PDF or expose a preview artifact to Web/Tauri.

The installed macOS WPS application has PDF UI components but no AppleScript dictionary or documented
headless export command. P1 therefore cannot promise reliable unattended WPS automation on macOS.
It can accurately display a PDF explicitly exported by WPS, while using LibreOffice for optional
automatic conversion.

## Goals / Non-Goals

**Goals:**

- Preserve fast structural feedback and make a real PDF view the default preview.
- Refresh the PDF automatically from current unsaved editor text after a bounded debounce.
- Keep live-preview DOCX/PDF artifacts isolated from the saved source and published output.
- Keep engine identity truthful and visible.
- Support automatic LibreOffice PDF generation and explicit WPS PDF selection.
- Share behavior across Web, macOS and Windows without leaking private paths.
- Mark final previews stale whenever their build inputs change.
- Preserve DOCX success, cancellation and atomic output guarantees.

**Non-Goals:**

- Reimplement Word/WPS layout in HTML.
- Automate undocumented WPS UI or private APIs.
- Promise pagination equality between different Office engines.
- Add PDF editing, annotation, search or thumbnail navigation.

## Decisions

### Keep PDF export in the application layer

Add `PdfPreviewExporter` beside `DocumentRefresher`. `build_service` publishes the validated DOCX
first, then attempts a best-effort derived PDF. The result is typed metadata on `BuildResult`;
export failure never converts a valid DOCX build into failure.

The same service accepts an optional source-text snapshot for live preview. Parsing preserves the
original Markdown path so relative images, bibliography files and template discovery keep their
normal semantics. Live preview passes an isolated output path and never writes the snapshot back to
the source file.

### Reuse LibreOffice process boundaries

The exporter reuses executable discovery and process cleanup primitives from `office_refresh.py`,
but owns a separate conversion command and output validation. It writes to a temporary directory,
checks the PDF signature and size, then atomically replaces the derived preview path.

### Treat WPS PDF as an explicit user artifact

Web uses a PDF file input and object URL. Tauri uses an `.pdf`-only native picker and a binary read
command. The UI labels this source `WPS PDF`; it never infers WPS from a LibreOffice artifact.

### Keep preview locators runtime-specific

The shared build DTO carries only status, engine, label and plain file name. Web derives a
workspace-bound URL from the opaque workspace ID. Tauri derives the automatic PDF path from the
already authorized DOCX output request, then reads it through a restricted command.

### Own stale state in the workspace reducer

The reducer records preview mode and final-preview state. A successful build or explicit PDF
selection creates a fresh preview. Text edits, template changes and source replacement mark or clear
it deterministically. The controller debounces edits, aborts superseded work and tags every request
with its content revision. Stale results from older operations cannot replace current state, and the
previous PDF remains visible while a replacement is being generated.

### Consume live-preview artifacts once

Web live previews use server-issued capabilities inside a runtime-owned hidden workspace directory.
The runtime deletes their temporary DOCX/PDF after reading or explicit release, and sweeps expired
files by mtime on startup and later allocations so process restarts cannot make them permanent.
Tauri records a capability-to-canonical-path mapping, authorizes only its derived PDF, and removes
the directory after reading or explicit cancellation. Formal build outputs and user-selected WPS
PDFs are never deleted by either cleanup path.

## Risks / Trade-offs

- [Risk] Browser/WebView native PDF viewers differ in controls.
  -> P1 verifies page rendering and reserves PDF.js as a later enhancement if viewer parity fails.
- [Risk] LibreOffice conversion may be slow or unavailable.
  -> Use bounded best-effort export and an explicit WPS PDF recovery action.
- [Risk] Large Tauri PDFs cross IPC.
  -> Use binary IPC response rather than JSON byte arrays; revoke object URLs when replaced.
- [Risk] A previous PDF may remain on disk after a failed export.
  -> The returned descriptor is authoritative; failed export is never marked fresh.
- [Risk] Rapid edits may finish out of order or accumulate temporary files.
  -> Abort superseded requests, reject stale revisions, use unique paths and perform best-effort
     cleanup in both frontend and runtime boundaries.

## Migration Plan

No source/template migration is required. Rollback removes PDF metadata and UI controls while leaving
DOCX build behavior unchanged. Derived `.preview.pdf` files are disposable build artifacts.

## Open Questions

None for P1.
