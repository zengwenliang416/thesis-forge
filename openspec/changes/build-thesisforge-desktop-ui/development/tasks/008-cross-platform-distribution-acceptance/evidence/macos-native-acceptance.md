# macOS Native Acceptance

Date: 2026-08-02

## Product Under Test

- App:
  `src-tauri/target/release/bundle/macos/ThesisForge.app`
- DMG:
  `src-tauri/target/release/bundle/dmg/ThesisForge_0.1.0_aarch64.dmg`
- Target: `aarch64-apple-darwin`
- Runtime label observed: `本地桌面`

## Visible Workflow

1. Launched the packaged `.app` directly, without a Vite development server.
2. Confirmed the `zh-CN` light-theme three-pane workbench, product title,
   outline, Markdown editor, renderer-neutral preview, diagnostics, template
   selector, progress, and output regions.
3. Found that the original macOS `rfd` extension filter grayed out `.md`
   sources and disabled the native Open button.
4. Added a Rust boundary regression test, removed the broken native filter,
   retained a clear `.md` / `.markdown` picker title, rebuilt the bundle, and
   confirmed the Open button became enabled for `thesis.md`.
5. Copied `examples/bachelor-thesis` to
   `/tmp/thesisforge-gui-ZL5KQd`, opened the copied `thesis.md`, and confirmed
   outline, editor, preview, diagnostics, Validate, and Build populated from
   the saved snapshot.
6. Appended `<!-- native acceptance -->` by keyboard. The UI changed to dirty,
   enabled Save, and disabled Validate and Build.
7. Used `Cmd+S`. The temporary source was written, the dirty state cleared, and
   Validate and Build became available again.
8. Ran validation and built DOCX. The visible progress reached `构建完成` and
   the output region displayed `thesis.docx`.

## Artifact Checks

- `/tmp/thesisforge-gui-ZL5KQd/thesis.docx`: 187082 bytes.
- SHA-256:
  `14434fc044a55d7556957356d0c3d79147c28012552697eea75e45f3ecdfcc96`.
- `validate_docx_package` passed.
- `unzip -t` reported no compressed-data errors.
- Final distribution verification passed after `dot_clean -m`; `.app` and
  `.dmg` contained no `._*` AppleDouble files.
- The packaged `.app` contained an executable managed sidecar and did not use
  system Python during the visible workflow.

## Evidence Boundary

- External-socket blocking, credential stripping, cancellation preservation,
  ordered build stages, and reopen were executed by
  `scripts/verify_desktop_distribution.py` against the frozen sidecar.
- The visible macOS run proves native launch, picker behavior, keyboard edit and
  save, validation, build completion, and output identity.
- Windows packaging and native interaction remain CI-only evidence and must not
  be claimed until the Windows matrix job succeeds.
