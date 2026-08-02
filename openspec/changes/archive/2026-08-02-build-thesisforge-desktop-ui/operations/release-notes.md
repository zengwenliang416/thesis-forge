# Release Notes: build-thesisforge-desktop-ui

## Summary

- ThesisForge Workbench `0.1.0` provides one React + TypeScript + Vite frontend
  for Web browsers and Tauri 2 applications on macOS and Windows.
- The local-first Python compiler remains independent. Desktop packages use a
  managed frozen sidecar, while Web uses an explicitly configured Python HTTP
  adapter.
- This release is `local-only`: it supports repository-local development,
  local Web serving, local package builds, local installation, and acceptance.

## Verification

- `make verify` passed on August 2, 2026 with Python `256`, Vitest `53`,
  Playwright `15` plus real HTTP `1`, and Rust protocol `11`.
- All six SpecNav verification domains are green for 12 A1-A12 user cases.
- macOS packaged application acceptance completed open, edit, save, validate,
  and DOCX build.
- Windows 11 ARM64 generated MSI/NSIS, installed the MSI, completed the same
  workflow with the VM network disconnected, retained a native screenshot and
  valid DOCX, and passed the disconnected distribution verifier.
- Python wheel/sdist isolation, Vite production build, frozen sidecar offline
  behavior, strict OpenSpec, CodeGraph advisory guard, and whitespace checks
  passed.

## Known Limitations

- Installers are unsigned and the macOS application is not notarized.
- No public release is authorized until project license, third-party ownership,
  signing, and explicit owner approval are resolved.
- Windows native sensory evidence is ARM64-specific; x86_64 remains a
  compatibility target backed by configuration and static tests.
- Production Web hosting, authentication, collaboration, accounts, telemetry,
  database, AI, and exact Word pagination are outside this V1 scope.
- GitHub Actions billing is unavailable; remote matrix reruns are supplementary
  reproducibility evidence rather than a local completion gate.
