# Acceptance Criteria: build-thesisforge-desktop-ui

## User-Visible Criteria

- Opening the Web build or launching the macOS/Windows Tauri package displays
  the same `zh-CN`, light-theme workbench and feature set, subject only to
  explicit runtime capability differences.
- With no source selected, the workbench shows an empty state, disables Save,
  Validate, and Build as applicable, and offers an Open action.
- Opening a valid Markdown source populates the outline, editor, preview, and
  diagnostics from one saved source snapshot.
- Editing marks the source dirty and disables Validate and Build until an
  explicit Save or Save As succeeds; no autosave occurs.
- Selecting a valid school template revalidates the source and updates preview
  presentation without changing source Markdown.
- Diagnostics expose severity, stable code, message, source line, and target;
  activating a diagnostic focuses the relevant editor line when available.
- A successful build displays ordered progress and the final DOCX path.
- Validation, permission, render, finalize, cancellation, and stale-result
  failures show recovery actions and preserve any previously valid output.

## System Criteria

- UI controllers call existing application services and do not duplicate
  parsing, validation, numbering, bibliography, compilation, or rendering.
- The React bundle depends only on typed transport DTOs, not Python domain or
  renderer implementation objects.
- The Web HTTP adapter and Tauri sidecar adapter both call the same Python
  application services.
- Core modules and product CLI remain importable and executable without Node.js,
  Rust, Tauri, or an HTTP server.
- Build progress order is `parse`, `validate`, `compile`, `render`, `finalize`.
- The approved archived prototype tests remain runnable after OpenSpec changes
  are archived.
- All macOS and Windows desktop flows work with external sockets blocked and no
  API credentials. Web flows work through an explicitly configured
  ThesisForge HTTP endpoint.

## Data Criteria

- The UI introduces no database, server state, remote cache, account data, or
  telemetry.
- Source and template reads respect local filesystem or browser workspace
  permissions.
- Source writes occur only after explicit Save/Save As and use atomic
  replacement in desktop mode so a failed save preserves the prior source. Web
  mode uses explicit workspace-save or download semantics.
- Build writes retain the existing temporary-package validation and atomic
  output replacement behavior.

## Component Criteria

- Reusable components, hooks, utilities, or services named in
  `component-impact-map.json` are extracted instead of duplicated.
- React components consume typed selectors/view models and do not receive raw
  python-docx, lxml, pathlib, exception, or renderer-private objects.
- Frontend state and transport tests run without requiring a visible desktop
  session; Tauri integration tests remain isolated.

## Verification Surfaces

- Facticity: trace every UI claim to current source, archived prototype evidence,
  application contracts, or executed desktop evidence.
- Static: enforce frontend-to-transport-to-application dependency direction and
  absence of React, Tauri, and HTTP framework imports from
  core/compiler/renderer modules.
- Unit: cover TypeScript workspace states, Python reference parity,
  save/build guards, progress, cancellation, diagnostics mapping, preview
  mapping, transport serialization, and archive-safe prototype discovery.
- Redteam: exercise path permissions, stale callbacks, repeated clicks, invalid
  templates, missing resources, socket blocking, and failed atomic saves/builds.
- E2E: open, edit, save, validate, select template, build, cancel, recover, and
  reopen a complete example in the browser plus macOS and Windows Tauri
  adapters.
- Sensory: review focus order, keyboard operation, labels, contrast, resize
  behavior, populated/loading/empty/error/disabled/permission states, and
  alignment with the approved academic three-pane prototype.

## Unresolved Gaps

- None.
