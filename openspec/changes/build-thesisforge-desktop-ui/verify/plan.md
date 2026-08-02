# Verification Plan: build-thesisforge-desktop-ui

## Verification Scope

- Active change: `build-thesisforge-desktop-ui`
- Development handoff: `openspec/changes/build-thesisforge-desktop-ui/development/handoff-to-verify.md`
- Git baseline: `f1adc43` (the archived V1 change immediately before the desktop UI change)
- Verification target: current working tree on 2026-08-02
- Scope: shared React/Vite Web workbench, Tauri 2 macOS/Windows shells, Python HTTP/sidecar adapters, source lifecycle, templates, diagnostics, renderer-neutral preview, build/cancel/recovery behavior, and cross-platform distributions.
- Non-goals: AI, accounts, cloud sync, telemetry, database, exact Word pagination, signing/notarization, public package publication, and GitHub billing availability.

## Required Domains

1. Facticity
2. Static
3. Unit
4. Redteam
5. E2E
6. Sensory

## Evidence Plan

- Direct source, command logs, native screenshots, package manifests, generated DOCX, and verifier output are authoritative.
- Current full gate is `make verify`, recorded in `verify/e2e/make-verify.log`.
- Web evidence uses the production Vite build and real Python HTTP adapter.
- macOS evidence uses the packaged `.app/.dmg` and frozen managed sidecar.
- Windows evidence uses the MSI-installed ARM64 application in a disconnected Windows 11 VM plus MSI/NSIS manifests.
- GitHub Actions failures caused by billing are retained as historical provenance but are not product execution evidence.

## User-Aligned Test Case Gate

- Twelve approved cases map one-to-one to acceptance assertions `A1` through `A12`.
- User decision on 2026-08-02: ignore GitHub pipeline availability and require complete local development and testing.
- Every approved case maps to all six domains in `verify/domain-case-matrix.json`.

## Runtime Evidence Gate

- Runtime surface: current `make verify`, isolated Python distribution, frozen sidecar, macOS native workflow, and Windows installed workflow.
- Browser surface: Playwright matrix, real Python HTTP adapter, and Windows WebView2 screenshot/acceptance record.
- No database surface is required because `development/migrations/manifest.json` declares no migration.

## Planned Commands

- `make verify`
- `OPENSPEC_TELEMETRY=0 openspec validate build-thesisforge-desktop-ui --strict --no-interactive`
- SpecNav development handoff and six-domain aggregate contracts
- CodeGraph verification-stage sync/guard/claims
- `git diff --check`

## Manual Reviews

- Review the Windows installed-workbench screenshot and macOS native acceptance transcript.
- Review Web, macOS, and Windows capability boundaries and residual release risks.
- Review test quality, architecture boundaries, and full change traceability.
