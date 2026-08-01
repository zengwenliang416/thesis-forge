# Quality Review: 006-outline-renderer-neutral-preview

## Verdict

approved

## Separation Of Concerns

- `preview_service` owns parse/validate/compile orchestration without rendering.
- The Python presentation mapper owns JSON-safe renderer-neutral projection.
- The adapter owns protocol routing, and React consumes only the versioned DTO.
- Lazy presentation export preserves the headless `thesis_forge.ui` import
  boundary.

## Component Cohesion / Coupling

- Preview state, panel rendering, workspace orchestration, and transport
  validation are separate owners.
- Outline and paper preview intentionally share one `selectionId`/source-line
  contract without sharing HTTP, Tauri, Python, filesystem, or renderer code.
- `PanelHeader` removes repeated shell heading markup from the old panels and
  the new preview panels.

## Test Quality

- Golden parity covers nested DTO shape, diagnostics markers, inline runs,
  absolute-path rejection, and explicit unsupported nodes.
- Real complete-example coverage verifies service-to-mapper compiler order and
  template numbering rather than relying only on hand-built instructions.
- Reducer, component, workbench-flow, adapter, architecture, browser, and full
  regression suites cover stale suppression, blocked/empty/dirty behavior,
  keyboard/pointer activation, editor focus, and shared Web/Tauri protocol.

## Error Handling

- Fatal validation and unavailable templates return a blocked preview without
  weakening validation or compiling invalid input.
- Compile failures retain `ApplicationStageError(BuildStage.COMPILE)`.
- Frontend consumers reject incomplete or malformed preview responses before
  they enter workspace state.
- Unknown top-level render nodes remain visible as unsupported content.

## Reuse / Duplication

- Parse, validation, template resolution, compiler numbering, and diagnostics
  presentation are reused from existing owners.
- Python and TypeScript runtime projections are constrained by one versioned
  golden fixture.
- Two small preview-response application paths remain in `WorkbenchApp`; they
  are acceptable now but should be extracted if Slice 007 adds response
  variants.

## Complexity Delta

- No maintained source file exceeds 800 lines. `WorkbenchApp.test.tsx` remains
  at 789 lines and received only compatibility updates, not new Slice 006
  scenarios.
- `transport/dto.ts` grows to 644 lines because it owns the complete versioned
  preview union and strict validator. This remains cohesive but is a monitored
  extraction candidate.
- `PreviewPanels.tsx` is 360 lines. Its large discriminated-union `Content`
  renderer is cohesive and exhaustive for the current schema.
- One new command operation and one compatibility detector branch were added;
  the old frontend `inspect` plus `validate` refresh path was retired.
- Net entropy is increased with justification: new versioned presentation
  capability is isolated in dedicated state/component/presentation owners.

## Required Fixes

- None.

## Residual Risk

- A future unknown inline-run variant would currently be omitted by
  `_inline_runs`; extending the compiler inline union requires a matching DTO,
  mapper, and contract test.
- Extract `transport/previewDto.ts` and one Workbench preview-response helper if
  Slice 007 materially grows either owner.
- Installed Windows runtime and package behavior remain unverified until Slice
  008.

## Independent Validation

- Independent quality review found no blocking defect in data leakage,
  unsupported-node behavior, stale suppression, selection sync, error states,
  accessibility, compatibility responses, or regression coverage.
- The reviewer independently executed focused Python, Vitest, Playwright,
  typecheck, and Ruff commands successfully.
