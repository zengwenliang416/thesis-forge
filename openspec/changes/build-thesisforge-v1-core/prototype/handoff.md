# Prototype Handoff: build-thesisforge-v1-core

## Approved Branch Variant

- Approved branch: `ui-html`.
- Approved variant: `academic-three-pane`.
- Generation source: Open Design project `thesisforge-html-workbench-20260729`.
- User approval recorded on July 30, 2026.

## Screens Or Flows

- `thesisforge-workbench`: product bar, paper outline, Markdown editor, Word paper preview and Diagnostics.
- `FLOW-INSPECT`: outline and source metadata communicate the read-only document model.
- `FLOW-VALIDATE`: diagnostics map severity, stable code, source line and semantic target.
- `FLOW-BUILD`: template selection and simulated parse, validate, compile, render and finalize progress.

## Components To Create

- Desktop workbench shell and responsive panel controller.
- Paper outline view.
- Markdown editor adapter.
- Word preview adapter backed by a renderer-neutral preview contract.
- ValidationIssue diagnostics view.
- School template selector.
- Build action, progress surface and local output feedback.

## Components To Reuse

- Parser and `ThesisDocument` domain model.
- `ValidationIssue` and validation service.
- Template loading service.
- Compiler and `RenderPlan`.
- Build service and optional progress events.
- Atomic output writer behavior from the approved logic-state prototype.

## Extraction Targets

- UI controllers must call inspect, validation and build application services rather than duplicate compiler logic.
- Build progress events must be renderer-neutral and reusable by CLI or future desktop adapters.
- Diagnostics localization must map stable domain codes to zh-CN copy without changing domain models.
- Preview data must use typed render instructions rather than raw DOCX or OOXML objects.

## API Contracts

- `inspect_service(source) -> inspection result`.
- `validation_service(source, context) -> validation result`.
- `build_service(source, template, output, context, on_progress) -> build result`.
- Progress stages remain `parse`, `validate`, `compile`, `render`, `finalize`.
- UI state owns only selection, panel visibility, progress and presentation copy.

## Data Flows

- Source Markdown is read into `ThesisDocument`; the outline and diagnostics derive from the same snapshot.
- Template selection resolves through the Template Model before compilation.
- Fatal validation blocks compile and render.
- Successful build writes a temporary DOCX, validates the package and atomically replaces the requested output.
- The HTML prototype uses static fixtures and performs no real reads or writes.

## State Behavior

- Populated: document, template, preview and diagnostics are reviewable; build is enabled.
- Loading: local workspace metadata is being read; build is disabled and recovery opens the prior fixture.
- Empty: no Markdown is selected; build is disabled and the sample thesis can be loaded.
- Error: template validation failed; build is disabled and recovery returns to the default template.
- Disabled: local DOCX builder is unavailable; editing remains visible but build is disabled.
- Permission: output directory is read-only; build is disabled and recovery requests a writable destination.

## Theme And Locale Policy

- Theme support: `light-only`.
- Theme shown: `light`.
- Theme toggle: intentionally omitted.
- Internationalization runtime: disabled for V1.
- Product copy shown: fixed `zh-CN`.
- Locale switcher: intentionally omitted.

## Out Of Scope Items

- Production PySide6 implementation, persistence, actual file selection and real DOCX rendering.
- AI chat, account system, cloud synchronization, collaboration and template marketplace.
- Dark mode, theme switching, runtime localization and locale switching.
- Reusing prototype DOM or CSS as compiler implementation code.

## Required Tests

- Desktop and mobile layout tests for panel visibility and navigation.
- Keyboard, focus, ARIA state and reduced-motion checks.
- State transition tests for populated, loading, empty, error, disabled and permission.
- Build progress order and cancellation tests.
- Integration tests proving UI adapters call the same inspect, validate and build services as the CLI.
- Tests proving fatal validation and permission failures do not replace an existing output.

## Open Risks

- The paper preview is a visual review fixture and does not prove Word pagination or OOXML fidelity.
- A production editor will require cancellation and stale-result handling for rapid source changes.
- PySide6 component density and platform-native controls may require measured adaptation while preserving this information architecture.
- The production desktop UI remains deferred until the deterministic compiler core and end-to-end DOCX build are stable.
