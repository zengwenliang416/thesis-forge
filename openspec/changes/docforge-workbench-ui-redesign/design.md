## Context

The shared React workbench already supports Web and Tauri runtimes through
`WorkbenchTransport`, a workspace reducer, resizable panels, preview modes,
structured diagnostics, build progress, cancellation, and Microsoft Word PDF
preview. The current shell places template and progress controls in a secondary
status strip, stacks diagnostics under the right preview rail, reserves a large
dark footer, and uses thesis-specific copy across the product.

The approved `ui-html` prototype and
`assets/docforge-workbench-reference.png` define the target hierarchy: one
compact command bar, outline/editor/Word preview in the main canvas, diagnostics
as a bottom contextual drawer, and a narrow readiness bar.

## Goals / Non-Goals

**Goals:**

- Reframe the product as the general `DocForge` Markdown-to-Word document
  workshop.
- Match the approved dual-canvas hierarchy at 1440x1024 while retaining useful
  responsive behavior at the existing mobile breakpoint.
- Preserve all existing workspace actions, reducer semantics, transport
  requests, preview modes, build stages, cancellation, and output behavior.
- Make Microsoft Word compatibility and final layout preview explicit.
- Keep React component responsibilities and runtime boundaries intact.

**Non-Goals:**

- Rename the repository, Python package, CLI, Tauri bundle identifier,
  `ThesisDocument`, `RenderPlan`, protocol, or backend service.
- Add a new editor dependency, AI, accounts, cloud sync, collaboration,
  analytics, template marketplace, database, theme toggle, dark mode, i18n, or
  WPS-specific behavior.
- Change Markdown syntax, template IDs, compiler behavior, OOXML, pagination, or
  final preview generation.

## Decisions

### 1. Preserve the component tree and move responsibilities through props

`WorkbenchApp` remains the only command/state orchestrator.
`WorkbenchShell` continues to compose the workbench and resizers.
`ProductBar` receives the existing template callback so template selection can
move into the command bar without adding state or transport logic.
`StatusStrip` becomes a compact contextual state surface and keeps recovery and
build progress. Existing panels continue to consume their current state and
callbacks.

Alternative considered: create a second DocForge shell alongside the existing
workbench. Rejected because it would duplicate runtime behavior, tests, and
responsive state.

### 2. Use CSS grid areas for desktop and existing mobile panel state for narrow screens

The desktop shell uses grid rows for command bar, contextual status, main
outline/editor/preview canvas, diagnostics drawer, and output status. The main
canvas keeps the existing outline and preview resizers. On narrow screens, the
existing `mobilePanel` state selects outline, editor, preview, or diagnostics;
the desktop grid is not merely scaled down.

Alternative considered: remove resizers and hard-code the generated image
proportions. Rejected because user panel widths are existing behavior and are
covered by tests.

### 3. Treat DocForge as a presentation rename only

Visible branding, labels, accessibility copy, empty states, and documentation
use `DocForge`. Internal package names, protocol values, template IDs, build
services, and domain types remain unchanged.

Alternative considered: full repository and API rename. Rejected because it is
unrelated to the UI goal and would create a breaking migration.

### 4. Keep template IDs while generalizing template labels

The selector label becomes “Word 模板” and the existing IDs remain unchanged.
Current sample option labels may be generalized where they are only frontend
presentation; no new ID is sent to the transport.

Alternative considered: introduce new report/manual template IDs. Rejected
because the backend does not currently define those templates.

### 5. Use the existing icon dependency and tokenized CSS

The implementation continues to use `lucide-react`; no handwritten SVG, CSS art,
or additional icon package is introduced. Styles use a light paper-gray canvas,
ink text, teal primary action, amber warning, fine dividers, limited shadow, and
Chinese-friendly font stacks.

Alternative considered: import a second icon or design-system dependency.
Rejected because the existing library covers every required command and the
dependency would add no functional value.

## Risks / Trade-offs

- [Tests depend on old copy and DOM placement] -> update focused component and
  E2E expectations while preserving ARIA semantics and callbacks.
- [Moving diagnostics changes available vertical space] -> use bounded desktop
  drawer height and keep mobile diagnostics as its own selected panel.
- [Visible DocForge name differs from internal ThesisForge identifiers] ->
  document the presentation-only boundary in requirements and UI copy.
- [Template labels can imply unsupported templates] -> preserve existing option
  IDs and avoid inventing backend capabilities.
- [Exact Word preview depends on generated PDF availability] -> preserve
  existing empty, stale, loading, selected PDF, and live preview states.

## Migration Plan

1. Freeze the approved prototype and requirements as the development baseline.
2. Update visible copy and command-bar props with focused component tests.
3. Recompose the workbench DOM and CSS while preserving state and callbacks.
4. Update responsive and Playwright expectations.
5. Run frontend static, unit, build, E2E, accessibility, and sensory checks.
6. Build and install the macOS application using the existing release workflow.

Rollback is commit-based and affects only frontend presentation and related
tests. User Markdown, templates, DOCX outputs, and protocol contracts are
unchanged.

## Open Questions

None.
