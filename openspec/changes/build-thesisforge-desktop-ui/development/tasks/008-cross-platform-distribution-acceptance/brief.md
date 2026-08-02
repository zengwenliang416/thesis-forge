# Task Brief: 008-cross-platform-distribution-acceptance

## Goal

Users can install or open the Web, macOS, and Windows products, complete the
same open, edit, explicit-save, validate, preview, build, cancel, retry, and
reopen workflow, and run the desktop products offline without Python, Node.js,
Rust, network access, API keys, accounts, or telemetry installed separately.

## Parent Artifacts

- `openspec/changes/build-thesisforge-desktop-ui/requirements.md`
- `openspec/changes/build-thesisforge-desktop-ui/acceptance.md`
- `openspec/changes/build-thesisforge-desktop-ui/prototype/handoff.md`

## Vertical Slice

Turn the already working shared React workbench and Python application services
into independently verifiable Web, macOS, Windows, and Python distributions.
Build one platform-native frozen Python sidecar per desktop target, bundle it
through a release-only Tauri configuration, verify the complete example and
required workbench states, and document reproducible maintainer and user flows.

## In Scope

- A deterministic PyInstaller sidecar build that runs the existing
  `thesis_forge.adapters.sidecar` entrypoint and embeds required package data.
- Target-triple-specific sidecar names and Tauri `externalBin` release
  configuration without changing the normal development fallback.
- Tauri Rust launch logic that prefers the packaged managed sidecar and retains
  explicit executable/Python overrides for development and tests.
- Desktop distribution verification that rejects target mismatches, missing or
  polluted sidecars, checkout/toolchain leakage, external socket use, malformed
  protocol output, invalid DOCX output, and missing native bundle artifacts.
- Separate Web, Python, macOS, and Windows artifact directories and checks.
- macOS `app`/`dmg` and Windows `msi`/`nsis` native release workflows.
- Browser acceptance for populated, loading, empty, error, disabled,
  permission, dirty, canceled, and success states.
- Keyboard-only, labels, focus visibility, contrast, responsive resize, and
  reduced-motion assertions.
- Complete-example protocol smoke tests for both development and frozen
  sidecars with external sockets blocked and credentials removed.
- README and maintenance guidance for installation, launch, runtime capability
  differences, limitations, troubleshooting, packaging, checksums, signing,
  notarization, and release evidence.
- Final Slice 008 development evidence and inputs required by six-domain
  verification and operations readiness.

## Out Of Scope

- No parser syntax, semantic ID, validation rule, template schema, compiler
  numbering, bibliography, renderer, DOCX, or OOXML behavior changes.
- No alternate frontend or desktop stack, mobile native package, Linux desktop
  release, auto-update service, account, database, AI, telemetry, or cloud
  deployment.
- No public package-index or app-store publication.
- No production signing, Apple notarization, Microsoft code signing, release
  upload, or paid certificate operation; document those external gates.
- No claim that a Windows package passed until a Windows runner produced and
  verified it.

## Files Allowed

- `.github/workflows/**`
- `.gitignore`
- `Makefile`
- `README.md`
- `docs/MAINTENANCE.md`
- `frontend/e2e/**`
- `frontend/src/**`
- `package.json`
- `pyproject.toml`
- `scripts/build_sidecar.py`
- `scripts/verify_desktop_distribution.py`
- `src-tauri/Cargo.lock`
- `src-tauri/Cargo.toml`
- `src-tauri/src/**`
- `src-tauri/tests/**`
- `src-tauri/tauri.conf.json`
- `src-tauri/tauri.release.conf.json`
- `tests/test_desktop_distribution.py`
- `tests/test_frontend_contract.py`
- `tests/test_architecture.py`

## Interfaces / Seams

- `thesis_forge.adapters.sidecar` remains the only frozen desktop application
  entrypoint and continues to invoke `WorkbenchCommandDispatcher`.
- `THESISFORGE_SIDECAR_EXECUTABLE` and `THESISFORGE_PYTHON` remain explicit
  development/test overrides. Packaged applications use the Tauri-managed
  `thesisforge-sidecar` external binary.
- The sidecar protocol remains `thesisforge.workbench.v1`; packaging may not
  add a second request/event schema.
- The base Tauri config remains suitable for local development. Release-only
  binary and bundle settings live in a mergeable release config.
- PyInstaller is a distribution tool only and may not become a runtime
  dependency of the Python wheel or core CLI.

## Components To Create

- Sidecar build script with target-triple and package-data validation.
- Desktop distribution verifier and focused Python tests.
- Release-only Tauri config.
- Native macOS/Windows distribution workflow.
- Dedicated Slice 008 browser acceptance tests.

## Components To Reuse

- Existing sidecar main, versioned command/event DTOs, application services,
  complete bachelor example, Web/Tauri transports, workspace reducer, shared
  React components, offline wheel verifier, Tauri command bridge, and atomic
  source/output replacement.

## Components To Extract

- Keep target naming, artifact discovery, checksum, socket blocking, credential
  stripping, and protocol smoke logic in distribution scripts rather than CI
  YAML or Rust UI commands.
- Keep accessibility/runtime-state fixtures in dedicated Slice 008 tests
  instead of expanding the existing large `WorkbenchApp.test.tsx`.

## API / Data Flow Contracts

- Web production output is static Vite content and requires an explicitly
  configured ThesisForge HTTP endpoint at runtime.
- Desktop production output is the shared Vite content plus one Tauri shell and
  one target-native frozen Python sidecar.
- The frozen sidecar reads one request line from stdin and emits one response
  or an ordered build event stream on stdout exactly like the development
  module entrypoint.
- CI builds the frozen sidecar and Tauri bundle on the same native runner; no
  cross-OS PyInstaller artifact is accepted.
- Web, wheel/sdist, macOS, and Windows artifacts are uploaded independently and
  never copied into one another's package roots.

## State / Error / Empty / Loading Behavior

- Loading: show the active operation/build stage, keep controls responsive, and
  retain the last valid output.
- Empty: expose Open and disable actions that require a saved source.
- Error: expose validation, render, finalize, transport, and package-start
  recovery without clearing saved source or prior output.
- Disabled: dirty, fatal diagnostics, missing output, or active operations
  visibly explain why Validate/Build cannot run.
- Permission: surface source/output access recovery and preserve the previous
  file.
- Canceled: preserve prior output and enable a new Build/Retry.
- Success: show the final runtime-appropriate output identity and permit reopen.

## TDD Requirement

- TDD route is `strict`.
- Add focused failing tests for release config, target naming, frozen sidecar
  protocol/offline execution, artifact isolation, native bundle discovery,
  accessibility states, reduced motion, and release workflow matrices before
  implementation.

## Verification Commands

- `pnpm frontend:test`
- `pnpm frontend:typecheck`
- `pnpm frontend:lint`
- `pnpm frontend:build`
- `pnpm frontend:e2e`
- `.venv/bin/python -m pytest tests/test_desktop_distribution.py
  tests/test_distribution.py tests/test_frontend_contract.py
  tests/test_architecture.py -q`
- `.venv/bin/python -m pytest -q`
- `.venv/bin/ruff check .`
- `.venv/bin/python -m pip check`
- `.venv/bin/python -m build --no-isolation --outdir dist/python`
- `.venv/bin/python scripts/verify_distribution.py --dist-dir dist/python`
- `.venv/bin/python scripts/build_sidecar.py`
- `.venv/bin/python scripts/verify_desktop_distribution.py --sidecar-only`
- `cargo fmt --manifest-path src-tauri/Cargo.toml -- --check`
- `cargo test --manifest-path src-tauri/Cargo.toml`
- `cargo check --manifest-path src-tauri/Cargo.toml`
- `cargo tauri build --config src-tauri/tauri.release.conf.json --bundles
  app,dmg` on macOS.
- Native Windows CI: `cargo tauri build --config
  src-tauri/tauri.release.conf.json --bundles msi,nsis`.
- `OPENSPEC_TELEMETRY=0 openspec validate
  build-thesisforge-desktop-ui --strict --json`
- `SPECNAV_CHANGE=build-thesisforge-desktop-ui OPENSPEC_TELEMETRY=0 node
  /Users/wenliang_zeng/.codex/plugins/cache/specnav-marketplace/specnav-development/0.3.0/scripts/development-contract.js
  --mode entry --json`
- `git diff --check`

## Stop Conditions

- Scope lock mismatch.
- A platform would require a second frontend, application service, protocol, or
  compiler/rendering implementation.
- Desktop offline operation would still require a separately installed Python
  runtime or network service.
- A sidecar built on one OS would be relabeled as another OS target.
- Release work requires public publishing, signing, notarization, paid
  credentials, or destructive external writes.
- The task would modify parser, validator, template, compiler, bibliography,
  renderer, DOCX, OOXML, account, database, AI, or telemetry behavior.

## Unsafe Assumptions

- A successful `cargo check` proves a native installer can be built.
- A macOS sidecar can be renamed and shipped for Windows.
- A Tauri shell that falls back to system Python is an offline desktop package.
- A generated bundle is valid merely because the output path exists.
- Browser accessibility evidence automatically proves native package launch.
- CI configuration is equivalent to an executed Windows package run.
