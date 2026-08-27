# Task Report: 004-runtime-protocol

## Status

DONE

## Files Changed

- Shared protocol schema, examples, and parity fixture under `protocol/`.
- Python runtime DTOs, HTTP/workspace adapter, sidecar envelope handling, and
  BuildReport contract under `src/docforge/`.
- TypeScript transport constants, DTO guards, build-event parsing, Web
  transport, workspace state fixtures, and browser protocol tests.
- Rust Tauri project loading, sidecar dispatch, request validation, build
  events, output authorization, final-preview authorization, and protocol
  tests.
- Frozen component fixtures whose typed BuildReport literals had to follow the
  shared schema identity for repository-wide TypeScript validation.

## What Changed

- Added `protocol/runtime-contract.v1.json` as the cross-language parity
  fixture for:
  - `docforge.yaml`;
  - `docforge.project.v1`;
  - `document.md`;
  - neutral build and Review paths;
  - `docforge.workbench.v1`;
  - `docforge.build-report.v2`;
  - the ordered seven-stage lifecycle;
  - diagnostics, output, and Microsoft Word final-preview authorization.
- Migrated the BuildReport JSON Schema and canonical examples to DocForge
  identity and neutral filenames.
- Centralized the runtime identity and default-path constants independently at
  the Python, TypeScript, and Rust boundaries.
- Python now rejects a project identity unless its manifest is the canonical
  `docforge.yaml` directly under the declared project root. Web workspaces use
  DocForge opaque roots, canonical manifest/source names, neutral default
  output names, and the DocForge live-preview namespace.
- TypeScript runtime guards now accept only the DocForge workbench and
  BuildReport identities. Web transport response validation, project snapshots,
  progress/completed events, cancellation, stale completion, and preview
  descriptor checks use the centralized constants.
- Rust now opens only a directory or `docforge.yaml`, requires
  `docforge.project.v1`, defaults an omitted source to `document.md`, and
  preserves traversal, URI, NUL, non-Markdown, and symlink-escape rejection.
- Rust development sidecar dispatch now starts
  `docforge.adapters.sidecar`. Request validation happens before spawning the
  sidecar or authorizing output.
- Rust final-preview authorization requires both `docforge.workbench.v1` and
  `docforge.build-report.v2`; obsolete event or report identities are rejected
  before an authorization is created.
- Rust and Python now share the `docforge-live-preview-*` capability namespace.
  Rust validates the complete live-preview output capability before revoking
  any prior final-preview authorization.
- Python and TypeScript accept both `.md` and `.markdown` at project source
  boundaries. Desktop and Web build output derivation always changes either
  extension to `.docx`, and Python rejects any normalized source/output path
  collision before invoking the builder.
- No compatibility alias, fallback parser, or old-protocol dispatch path was
  added. Old identifiers remain only as explicit negative-test vectors and
  obsolete constants used by those tests.

## TDD Evidence

- The initial Python Task 004 run produced `126 passed, 7 failed`; every failure
  was an active adapter test still constructing an obsolete manifest, source,
  output, live-preview prefix, or BuildReport identity.
- The initial frontend suite was green only because its fixtures followed old
  constants. After changing the production types, repository-wide TypeScript
  checking exposed three frozen component fixtures with the obsolete
  BuildReport literal; they now consume the centralized constant.
- The shared fixture initially used a nonconforming final-preview
  `authorizationId`. The fixture was corrected to a 32-character lowercase
  hexadecimal identifier and the full positive completed event is now accepted
  by TypeScript and Rust.
- Python, TypeScript, and Rust each read
  `protocol/runtime-contract.v1.json` in executable tests.
- Negative tests prove obsolete workbench requests are rejected before Python
  application-service dispatch and Rust sidecar spawn, and obsolete
  BuildReports cannot pass TypeScript event guards or Rust preview
  authorization.
- Regression tests prove `document.markdown` derives `document.docx` in desktop
  and Web flows, and a forged `livePreviewId` cannot revoke an already
  authorized preview or overwrite the Markdown source.
- The real HTTP browser test now supplies the DocForge project contract. The
  later Task 006 picker migration completed the component boundary, and the
  current real Python HTTP Playwright receipt passes.

## Verification Commands

- `PYTHONPATH=src .venv/bin/python -m pytest tests/adapters tests/application tests/test_adapters.py -q`
  -> `140 passed`.
- `.venv/bin/ruff check src/docforge/adapters src/docforge/application/contracts.py tests/adapters tests/application tests/test_adapters.py`
  -> `All checks passed`.
- `pnpm --dir frontend typecheck`
  -> passed.
- `pnpm --dir frontend lint`
  -> passed.
- `pnpm --dir frontend test`
  -> `20 files, 243 tests passed`.
- `pnpm --dir frontend build`
  -> production Vite build passed.
- `cargo fmt --check --manifest-path src-tauri/Cargo.toml`
  -> passed.
- `cargo check --manifest-path src-tauri/Cargo.toml`
  -> passed.
- `cargo test --manifest-path src-tauri/Cargo.toml`
  -> `12` project tests and `32` protocol-contract tests passed.
- `git diff --check`
  -> passed.
- `OPENSPEC_TELEMETRY=0 openspec validate docforge-project-format-v1 --strict --no-interactive --json`
  -> `1` change passed, `0` failed.

## Concerns

- Product-owned legacy environment variables, packaged
  `thesisforge-sidecar` names, application metadata, and user-visible picker
  copy were assigned to Task 006 and have now been migrated. They were never
  accepted as runtime protocol aliases.

## Scope Deviations

- Three committed component test fixtures were updated through explicit
  `frozen-tests` overrides because the shared BuildReport type change otherwise
  made repository-wide TypeScript validation fail.
- `frontend/e2e/real-http.acceptance.ts` was migrated to the DocForge project
  contract. Its remaining component-level picker dependency is not changed in
  this task.

## Follow-up Needed

- Task 008 must bind the passing real HTTP, runtime parity, and installed
  desktop evidence to the committed HEAD through trusted verification receipts.
