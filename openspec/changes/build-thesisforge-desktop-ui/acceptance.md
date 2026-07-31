# Acceptance Criteria: build-thesisforge-desktop-ui

## User-Visible Criteria

- Launching `thesisforge-ui` with the `ui` extra installed opens one local
  `zh-CN`, light-theme workbench without network access.
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
- Core modules and product CLI remain importable and executable without PySide6.
- PySide6 imports remain inside the optional UI package and entrypoint.
- Build progress order is `parse`, `validate`, `compile`, `render`, `finalize`.
- The approved archived prototype tests remain runnable after OpenSpec changes
  are archived.
- All desktop flows work with sockets blocked and no API credentials.

## Data Criteria

- The UI introduces no database, server state, remote cache, account data, or
  telemetry.
- Source and template reads respect local filesystem permissions.
- Source writes occur only after explicit Save/Save As and use atomic
  replacement so a failed save preserves the prior source.
- Build writes retain the existing temporary-package validation and atomic
  output replacement behavior.

## Component Criteria

- Reusable components, hooks, utilities, or services named in
  `component-impact-map.json` are extracted instead of duplicated.
- Widgets consume typed view models and do not receive raw python-docx, lxml, or
  renderer-private objects.
- Controller and view-model tests run headlessly without requiring a visible
  desktop session.

## Verification Surfaces

- Facticity: trace every UI claim to current source, archived prototype evidence,
  application contracts, or executed desktop evidence.
- Static: enforce UI-to-application dependency direction and absence of PySide6
  imports from core/application/compiler/renderer modules.
- Unit: cover controller states, save/build guards, progress, cancellation,
  diagnostics mapping, preview mapping, and archive-safe prototype discovery.
- Redteam: exercise path permissions, stale callbacks, repeated clicks, invalid
  templates, missing resources, socket blocking, and failed atomic saves/builds.
- E2E: open, edit, save, validate, select template, build, cancel, recover, and
  reopen a complete example through the real PySide6 adapter.
- Sensory: review focus order, keyboard operation, labels, contrast, resize
  behavior, populated/loading/empty/error/disabled/permission states, and
  alignment with the approved academic three-pane prototype.

## Unresolved Gaps

- None.
