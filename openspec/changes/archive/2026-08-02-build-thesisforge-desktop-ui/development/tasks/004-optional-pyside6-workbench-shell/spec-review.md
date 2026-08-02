# Spec Review: 004-optional-pyside6-workbench-shell

## Verdict

approved

## Missing Requirements

- None after review fixes.
- Task `4.1`: deterministic pnpm scripts, frozen lockfile, Vite build, Vitest,
  TypeScript, lint, and Playwright configuration exist.
- Task `4.2`: the light academic workbench is responsive, resizable, and tested
  at `1440x900`, `1024x680`, and mobile viewport sizes.
- Task `4.3`: all named shell components exist as extracted React components.
- Task `4.4`: intent crosses `WorkbenchTransport`; no component imports Web,
  Tauri, Python, or compiler implementations.
- Task `4.5`: unit and E2E tests cover labels, shortcuts, focus, state guards,
  panel navigation, viewport containment, and keyboard resize.
- Task `4.6`: Python CLI import isolation is exercised with an empty `PATH` and
  blocked sockets.
- Task `4.7`: RED/GREEN, validation, CodeGraph, report, drift, and review
  evidence are recorded.
- Task `4.8`: Web workspace creation and versioned dispatch call the existing
  application services without exposing service paths.
- Task `4.9`: Tauri request validation, native source selection, sidecar
  dispatch, and protocol parity are implemented and tested.

## Extra Behavior

- Successful Save immediately advances the saved snapshot, then runs
  inspect/validation refresh. If refresh fails, recovery reruns analysis before
  Build is re-enabled.
- Unexpected adapter exceptions are normalized as `transport` failures instead
  of escaping the protocol boundary.
- Mobile E2E checks complete viewport containment, not only DOM visibility.

## Misunderstood Requirements

- The initial shell treated `Ctrl/Cmd+S` and the Save button as visual-only.
  Both now dispatch explicit save and refresh through `WorkbenchTransport`.
- The initial Web build output omitted the opaque workspace ID and could not be
  resolved safely by the Python Web runtime. Output now remains inside the
  current opaque workspace.
- The initial mobile CSS hid the brand and later still clipped controls because
  Grid items retained intrinsic minimum width. The final layout keeps product
  identity and all compact actions inside the viewport.

## Cannot Verify From Diff

- Windows shell execution and installer behavior cannot be verified on this
  macOS host and remain Slice 008.
- Signed/notarized macOS packages and signed Windows MSI/NSIS packages remain
  Slice 008.
- Final template diagnostics, semantic outline/preview content, streamed build
  progress, cancellation, and output download presentation remain later
  slices and are not claimed here.

## Acceptance Assertions Verified

- `A1`: one `zh-CN`, light-theme React tree serves Web and Tauri runtimes.
- `A2`: source open creates one saved snapshot and refreshes inspect/validation;
  final semantic outline/preview rendering remains Slice 006.
- `A3`: dirty state disables Validate/Build until explicit save succeeds.
- `A7`: components depend on typed state/transport only; Python core remains
  free of React, Tauri, and HTTP framework imports.
- `A8`: CLI import succeeds without frontend tools or network access.
- `A10`: TypeScript parity and Python reference state tests run headlessly.
- `A11`: browser labels, focus, shortcuts, resize, responsive panels, reduced
  viewport behavior, and visual containment are covered; cross-host sensory
  acceptance remains Slice 008.
- `A12`: Tauri uses local path/sidecar boundaries and Web uses only configured
  HTTP transport with opaque handles.

## Required Fixes

- None. Save binding, Web output identity, transport validation, post-save
  recovery, component extraction, and mobile containment findings were fixed.
