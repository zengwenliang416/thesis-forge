# Task Brief: 001-docforge-workbench-redesign

## Goal

Deliver the approved `DocForge` Markdown-to-Word workbench while preserving all
existing document commands, transport contracts, preview behavior, responsive
navigation, packaging, and Microsoft Word final-preview behavior.

## Parent Artifacts

- `openspec/specs/ui-design/design.md`
- `openspec/specs/system-architecture/design.md`
- `openspec/specs/frontend-backend-data-flow/design.md`
- `openspec/specs/component-architecture/design.md`
- `openspec/changes/docforge-workbench-ui-redesign/requirements.md`
- `openspec/changes/docforge-workbench-ui-redesign/acceptance.md`
- `openspec/changes/docforge-workbench-ui-redesign/spec-map.json`
- `openspec/changes/docforge-workbench-ui-redesign/component-impact-map.json`
- `openspec/changes/docforge-workbench-ui-redesign/prototype/handoff.md`
- `openspec/changes/docforge-workbench-ui-redesign/prototype/decision.json`
- `openspec/changes/docforge-workbench-ui-redesign/prototype/artifact/index.html`

## Vertical Slice

Reframe and recompose the existing shared React workbench from the product
command bar through outline, Markdown editor, Microsoft Word preview,
diagnostics, output status, responsive behavior, macOS packaging, and installed
application verification without changing its state or transport contracts.

## In Scope

- Replace visible academic-only branding and copy with `DocForge` and general
  Markdown-to-Word document language.
- Move the existing Word template selector into `ProductBar` through its
  existing template ID and callback contract.
- Recompose `WorkbenchShell` into a compact command/status area, desktop
  outline/editor/preview canvas, bottom diagnostics drawer, and narrow output
  status.
- Rebuild the light UI styling to match the approved teal editorial-workshop
  reference while preserving focus, resizers, loading, empty, error, disabled,
  permission, progress, and populated states.
- Update focused React and Playwright coverage, perform visual QA, build and
  install the macOS application, and verify the Microsoft Word preview path.

## Out Of Scope

- Repository, Python package, CLI, Tauri bundle identifier, protocol, domain
  type, and template ID renames.
- Parser, domain, compiler, RenderPlan, DOCX renderer, OOXML, pagination, build
  semantics, transport DTO, or final preview generation changes.
- AI, accounts, cloud sync, collaboration, analytics, database, template
  marketplace, new editor or icon dependencies, WPS, dark mode, and i18n.

## Files Allowed

- `frontend/src/components`
- `frontend/src/styles.css`
- `frontend/e2e`
- `frontend/scripts`
- `frontend/index.html`
- `src-tauri`
- `docs`
- `README.md`
- `design-qa.md`
- `openspec/changes/docforge-workbench-ui-redesign`

## Interfaces / Seams

- `WorkbenchApp` remains the sole reducer, command, transport, build, and final
  preview orchestrator.
- `WorkbenchShell` remains layout-only and receives all state and callbacks by
  props.
- `ProductBar` receives the existing template selector state and callback.
- `StatusStrip` retains contextual status, recovery, and build progress.
- Existing `workbench.v1`, preview, save, build, cancel, build event, final
  preview descriptor, and Office PDF selection contracts remain unchanged.

## Components To Create

- No new data, state, transport, or service component.
- Visual grouping elements may be added inside existing components where they
  have a single semantic layout responsibility.

## Components To Reuse

- `WorkbenchApp`, `WorkbenchShell`, `ProductBar`, `StatusStrip`,
  `OutlinePanel`, `MarkdownEditor`, `DualPreviewPanel`, `DiagnosticsPanel`,
  `OutputFeedback`, and `PanelHeader`.
- Existing workspace reducer selectors, diagnostic presentation utilities,
  final preview resolution, PDF object URL lifecycle, and Lucide icons.

## Components To Extract

- No extraction is planned for this single production screen.
- Extract a command or status group only if implementation creates a second
  production use site; do not create a parallel shell or state layer.

## API / Data Flow Contracts

- Preserve open source/project, save, validate/preview, build/cancel, live
  preview, final preview resolution, Office PDF selection, and output download
  flows exactly.
- Preserve template IDs, generation tokens, stale-preview protection, command
  gating, reducer actions, and Web/Tauri transport boundaries.

## State / Error / Empty / Loading Behavior

- Loading: retain the workbench structure and state that document or Word
  layout content is loading.
- Empty: prompt the user to open a Markdown document or DocForge project.
- Error: retain document content and show failure plus recovery in the
  contextual status or diagnostics area.
- Disabled: block DOCX generation only when current diagnostics or operation
  state requires it; editing and diagnostics remain available.
- Permission: state that the selected destination is not writable and do not
  use fallback-output copy or silently select another destination.
- Populated: show synchronized outline, Markdown editor, Word preview,
  diagnostics, and output readiness.

## TDD Requirement

- Update focused component and E2E expectations before or alongside production
  markup and CSS changes.
- Preserve existing accessibility labels where they are behavioral contracts;
  update thesis-specific labels only where the accepted product copy requires.

## Verification Commands

- `pnpm frontend:test`
- `pnpm frontend:typecheck`
- `pnpm frontend:lint`
- `pnpm frontend:build`
- `pnpm frontend:e2e`
- `cargo fmt --manifest-path src-tauri/Cargo.toml -- --check`
- `cargo test --manifest-path src-tauri/Cargo.toml`
- `OPENSPEC_TELEMETRY=0 openspec validate docforge-workbench-ui-redesign --strict --no-interactive --json`
- `git diff --check`
- Existing macOS release build and installation workflow documented in
  `README.md` and `docs/MAINTENANCE.md`.

## Stop Conditions

- Scope lock mismatch or unrelated dirty-worktree conflict.
- Missing product, architecture, data-flow, component, packaging, or Microsoft
  Word preview decision.
- Any required backend, parser, compiler, renderer, OOXML, protocol, or
  template-ID change.
- Any regression in existing transport, build cancellation, preview freshness,
  mobile panel routing, resizers, or keyboard/focus behavior.

## Unsafe Assumptions

- `DocForge` is a presentation name only; internal ThesisForge identifiers are
  deliberately unchanged.
- Prototype fixtures, inline scripts, and hard-coded document content cannot be
  promoted into production.
- Frontend green checks do not prove production visual fidelity, installed app
  freshness, or Microsoft Word final preview behavior.
- Office preview verification targets Microsoft Word, not WPS.
