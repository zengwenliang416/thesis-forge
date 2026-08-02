# Real Web HTTP Acceptance

Date: 2026-08-02

## Product Under Test

- Built React + TypeScript + Vite workbench from `frontend/dist/`.
- Existing Python `WorkbenchHttpApp`, `WebWorkspaceRuntime`, and
  `WorkbenchCommandDispatcher`.
- Same-origin threaded WSGI acceptance host in
  `frontend/e2e/real_http_server.py`.
- Chromium desktop viewport at `1440x900`.

## TDD Evidence

- RED:
  `pnpm --dir frontend exec playwright test --config
  e2e/real-http.playwright.config.ts` failed because
  `frontend/e2e/real_http_server.py` did not exist.
- First integration run reached the real workspace, dispatch, save, and preview
  endpoints, then correctly exposed three validator errors because the initial
  fixture omitted a template and required metadata.
- The fixture was replaced with a minimal valid bachelor thesis containing
  `thesis.title`, `author.name`, and `render.template_id`.
- GREEN:
  the focused real-adapter run returned `1 passed`.
- Standard gate:
  `pnpm frontend:e2e` returned `14 passed`, `16` intentional matrix skips, then
  `1 passed` for the separate real HTTP adapter project.

## Verified Workflow

1. Loaded the production Vite build without Playwright route interception.
2. Uploaded a valid Markdown thesis through `POST /api/v1/workspaces`.
3. Confirmed the response came from the Python WSGI adapter through
   `X-ThesisForge-Adapter: python-wsgi`.
4. Confirmed editor and renderer-neutral preview populated from the saved
   workspace snapshot.
5. Edited the source and confirmed Validate and Build were disabled while
   dirty.
6. Explicitly saved through the real `save` dispatch operation.
7. Confirmed the exact UTF-8 text persisted under the opaque workspace ID.
8. Validated through the real `preview` dispatch operation.
9. Built through the real NDJSON `build-stream` endpoint.
10. Confirmed ordered completion in the UI, `thesis.docx` output identity,
    output size greater than 1,000 bytes, and the DOCX ZIP signature.

## Evidence Boundary

- This test proves the browser workbench uses the real Python HTTP adapter and
  application services rather than only mocked Playwright responses.
- Browser cancellation, permission, loading, error, disabled, dirty, success,
  keyboard, contrast, responsive, and reduced-motion states remain covered by
  the deterministic mock/state matrix.
- The acceptance host is test-only. Production Web deployment still requires
  an explicitly configured ThesisForge HTTP service.
