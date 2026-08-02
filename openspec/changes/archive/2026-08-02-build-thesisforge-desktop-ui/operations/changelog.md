# Changelog: build-thesisforge-desktop-ui

## Added

- Shared React + TypeScript + Vite academic three-pane workbench for Web,
  macOS, and Windows.
- Tauri 2 shells with a versioned managed Python sidecar protocol and native
  macOS/Windows packaging.
- Explicit source open/save lifecycle, atomic desktop replacement, Web workspace
  save/download semantics, dirty guards, template selection, diagnostics,
  renderer-neutral preview, build progress, cancellation, retry, and recovery.
- Real Python HTTP adapter acceptance, native macOS package acceptance, and
  MSI-installed disconnected Windows ARM64 acceptance.
- Six-domain verification for 12 user-approved A1-A12 cases.

## Changed

- Promoted the approved static academic-three-pane prototype into a production
  shared frontend without changing Parser, ThesisDocument, Validator, Compiler,
  RenderPlan, or DOCX Renderer ownership.
- Preserved the standalone Python CLI/wheel/sdist while adding Web and desktop
  transport adapters.
- Expanded `make verify` to cover Python, frontend, Playwright, Rust, Web,
  sidecar, distribution, strict OpenSpec, and whitespace gates.

## Fixed

- Native macOS Markdown picker filtering.
- Windows WebView2 CDP source selection, compact-toolbar save fallback,
  controlled textarea input, and hidden control lookup.
- Target-native sidecar packaging, UTF-8 protocol output, bundle icons, and
  distribution artifact isolation.
