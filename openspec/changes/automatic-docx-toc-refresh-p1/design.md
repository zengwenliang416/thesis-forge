## Context

`TocInstruction` already produces `TOC \o "1-3" \h \z \u`, and the DOCX settings contain
`w:updateFields=true`. The Renderer currently places that field and cached result `"目录"` in one
paragraph styled as `TFTOCTitle`. Office applications that do not refresh fields on open show only
the cached title, while updating the field can consume the title because it is inside the field
result. Page-number calculation requires a layout engine and does not belong in the deterministic
Markdown/compiler pipeline.

## Goals / Non-Goals

**Goals:**

- Keep the TOC title independent from field updates.
- Preserve a real editable Word TOC field in every build.
- Automatically materialize entries/page numbers when a compatible local LibreOffice is available.
- Keep builds successful and outputs valid when Office refresh is unavailable or fails.
- Support browser deployments, macOS and Windows through the shared application service.
- Preserve package validation, cancellation and atomic replacement guarantees.

**Non-Goals:**

- Calculate page numbers in ThesisForge code.
- Emit static fake TOC text.
- Require LibreOffice installation.
- Automate Microsoft Word or WPS private APIs.
- Guarantee identical pagination across Office suites.

## Decisions

### Separate title and field paragraphs

Renderer emits one `toc.title` paragraph with literal `"目录"`, followed by an unstyled field
paragraph containing the TOC complex field. The field has no fake cached result. Existing TOC level
styles and `w:updateFields=true` remain unchanged.

### Refresh at the application finalization seam

The application service calls a `DocumentRefresher` after Renderer writes the temporary DOCX and
before package validation and atomic replacement. This keeps subprocess/UNO concerns out of the
Renderer and gives CLI, Web and Tauri one behavior.

### LibreOffice is optional and best-effort

The default refresher discovers LibreOffice on macOS, Linux and Windows. Missing executable,
startup/connection/update/save errors and timeout return a no-refresh result instead of failing the
core build. The untouched rendered package still contains a valid dirty TOC field.

### Use isolated LibreOffice process state

Every refresh uses a temporary user profile and private UNO endpoint, loads the DOCX hidden, updates
all document indexes and refreshable text fields, stores back to the same temporary DOCX, closes the
document, terminates the process and removes the profile. All waits are bounded.

### Validate only the post-refresh package

Package validation runs after the optional refresher. A refresher that corrupts the temporary DOCX
is therefore caught as a finalization failure, and the previous output remains untouched.

## Risks / Trade-offs

- [Risk] LibreOffice startup adds latency.
  -> Start at most once per build, use a bounded timeout and skip when no executable is found.
- [Risk] A failed refresh may leave a process/profile.
  -> Use isolated process ownership, `finally` cleanup and termination escalation.
- [Risk] LibreOffice pagination can differ from Word/WPS.
  -> Keep the field editable and dirty fallback valid; sensory verification documents suite variance.
- [Risk] Best-effort failure is invisible to the current `BuildResult`.
  -> Preserve the existing public contract in this slice; tests prove the fallback document remains
  valid. A future diagnostics feature can expose capability status without changing correctness.

## Migration Plan

No input or template migration is required. Rollback removes the application refresher and restores
the prior finalization sequence; the standalone title and real TOC field remain independently valid.

## Open Questions

None for this slice.
