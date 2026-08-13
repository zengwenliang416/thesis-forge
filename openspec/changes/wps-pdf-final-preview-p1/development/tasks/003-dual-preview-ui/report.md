# Task Report: 003-dual-preview-ui

## Status

DONE

## Files Changed

- `frontend/src/state/workspace.ts`
- `frontend/src/components/PreviewPanels.tsx`
- `frontend/src/components/WorkbenchApp.tsx`
- `frontend/src/components/WorkbenchShell.tsx`
- `frontend/src/components/usePdfObjectUrl.ts`
- `frontend/src/styles.css`
- related frontend reducer, component, transport and E2E tests
- `src-tauri/tauri.conf.json`

## What Changed

- Added accessible `结构 / 最终版式` switching and truthful engine labels.
- Added empty, building, ready, stale, unavailable and failed presentation.
- Added operation-generation and content-revision guards so old async results
  cannot replace current state.
- Added Blob URL creation/revocation and retained stale PDFs as inspectable with
  a warning.
- Added responsive desktop/mobile layouts without horizontal overflow.

## TDD Evidence

- Reducer tests cover source/template/editor mutations and stale async results.
- Component/integration tests cover automatic build events and WPS picker
  bytes reaching the viewer.
- E2E covers automatic PDF Blob rendering, stale state and mobile final-layout
  navigation.

## Verification Commands

- `pnpm --dir frontend exec vitest run --pool=forks --maxWorkers=1
  --testTimeout=15000` -> `75 passed`.
- `pnpm --dir frontend typecheck`, `lint` and `build` -> passed.
- `pnpm --dir frontend exec playwright test` -> `16 passed`, `20 skipped` by
  intentional project guards, `0 failed`.
- In-app browser desktop and 390px checks showed no console warnings and
  `scrollWidth == innerWidth`.

## Concerns

- Native PDF controls remain browser/WebView-owned and can differ by platform.

## Scope Deviations

- None recorded.

## Follow-up Needed

- Verification should inspect the exact packaged macOS and Windows viewers.

## Adjudication

Implementation is ready for independent review.
