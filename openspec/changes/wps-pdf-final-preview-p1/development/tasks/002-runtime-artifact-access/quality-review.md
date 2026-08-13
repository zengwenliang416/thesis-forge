# Quality Review: 002-runtime-artifact-access

## Verdict

approved

## Separation Of Concerns

- Python adapters own Web workspace presentation and PDF responses, Tauri owns
  native authorization and binary reads, and frontend transports own
  runtime-specific fetch/invoke behavior.
- React components do not directly call HTTP, Tauri IPC, or filesystem APIs.
- Office conversion remains in the application layer and is not duplicated in
  Web or Tauri runtime code.

## Component Cohesion / Coupling

- `PreviewAuthorizationState` now has one coherent identity model: unique
  capability handles map to bound engine, file name, and stable path identity.
- `stable_path_identity()` canonicalizes only the parent and preserves the
  final file name. Both authorization and path revocation reuse it, eliminating
  the previous coupling to the final component's mutable filesystem target.
- Same-named PDFs in different canonical directories remain independent, while
  all handles for one derived pathname can be revoked before a rebuild.

## Test Quality

- Rust tests directly cover unique authorization IDs, same-name files in
  separate directories, engine/file-name drift, explicit revoke, successful
  derived authorization, failed/canceled build revocation, deleted previews,
  content mutation, read-time symlink replacement, and symlink mutation before
  rebuild followed by replacement with a new PDF.
- The new regression asserts the old handle remains rejected after the new
  regular PDF is written back to the original pathname, closing the exact
  stale-handle resurrection found in the previous review.
- Python tests cover workspace isolation, traversal, extension/content checks,
  symlinks, response headers, strict descriptors, and path privacy.
- Frontend tests cover strict descriptor location rules, PDF signatures, Web
  route construction, browser WPS selection, and Tauri command arguments.

## Error Handling

- Descriptor validation fails closed for unknown fields, path-bearing data,
  invalid names and IDs, engine/label mismatch, and Web/desktop locator mixing.
- Authorization resolution rejects unknown handles and descriptor drift.
- `read_pdf_preview_path()` revalidates extension, regular-file/symlink status,
  and `%PDF-` content on every read.
- Pre-build path revocation no longer follows a mutated final symlink, so a
  silently retained old authorization cannot reappear after atomic replacement.

## Reuse / Duplication

- TypeScript descriptor and byte validation is shared by Web and Tauri.
- Python final-preview descriptor construction is centralized.
- Rust uses one stable path identity helper for authorization and revocation.
- Rust-side validation duplication is justified because Tauri is an independent
  native trust boundary.

## Complexity Delta

- The UUID capability map and linear path revocation remain small,
  understandable, and bounded by in-memory preview authorizations.
- The stable identity helper reduces lifecycle complexity compared with
  conditionally canonicalizing existing and missing final files.
- No material performance regression, speculative abstraction, or blocking
  maintainability issue was found.

## Required Fixes

- No blocking task-002 quality fix remains; the authorization lifecycle,
  runtime boundaries, and focused regression coverage meet the review bar.

## Reviewer Checks

- Rust formatting: passed.
- Rust focused/full crate tests: `1 passed` for the fixed regression and
  `22 passed` for the complete crate.
- Frontend focused transport tests: `21 passed`.
- Python focused adapter/HTTP/sidecar tests: `31 passed`; focused Ruff: passed.
- `git diff --check`: passed.
