## Why

ThesisForge V1 core is complete, but authors still need CLI commands and manual
file inspection to understand document structure, resolve diagnostics, select a
school template, and build DOCX output. The approved workbench prototype can now
be promoted because the deterministic application services and package boundary
are stable.

The archived prototype acceptance test also exposes a lifecycle defect: it
points at the removed active-change directory and fails after a correct OpenSpec
archive. The workbench milestone must begin by restoring an archive-safe
baseline.

## What Changes

- Restore archived prototype contract tests without recreating or mutating the
  completed V1 change.
- Add one React + TypeScript + Vite academic three-pane workbench shared by Web,
  macOS, and Windows.
- Add a Tauri 2 desktop shell for macOS and Windows without forking frontend
  behavior or presentation.
- Add explicit Web HTTP and Tauri command/sidecar transports that reuse the same
  deterministic Python application services.
- Add local source open, explicit atomic save, template selection, validation,
  diagnostics, renderer-neutral preview, build progress, cancellation, and
  output feedback.
- Reuse the existing inspect, validation, and build application services.
- Add shared frontend state/transport tests and real browser plus desktop
  interaction, accessibility, offline, permission, and failure-path
  verification.
- Keep the core CLI usable without Node.js, Rust, Tauri, or a web server. The
  local compiler remains usable without network, accounts, AI, autosave, dark
  mode, or runtime localization.

## Capabilities

### New Capabilities

- `desktop-workbench`: Legacy capability identifier for the cross-platform
  authoring workbench, archive-safe prototype contract, explicit source
  lifecycle, diagnostics, preview, and DOCX build orchestration across Web,
  macOS, and Windows.

### Modified Capabilities

None. Existing compiler, validation, template, rendering, bibliography, and
offline CLI requirements remain unchanged and are reused through their public
application contracts.

## Impact

- New frontend workspace under `frontend/` using React, TypeScript, and Vite.
- New desktop workspace under `src-tauri/` using Tauri 2 for macOS and Windows.
- New Python Web and sidecar adapters that serialize stable application DTOs
  without exposing domain or renderer implementation objects.
- New frontend state, transport, component, accessibility, browser, and desktop
  end-to-end tests.
- Targeted repair to `tests/test_prototype_acceptance.py` so archived evidence
  remains discoverable.
- No database, migration, account, AI, or compiler-domain change. Web transport
  is an adapter around existing application services, not a second compiler.
