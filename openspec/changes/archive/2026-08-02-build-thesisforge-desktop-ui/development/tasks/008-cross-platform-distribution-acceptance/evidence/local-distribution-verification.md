# Local Distribution Verification

Date: 2026-08-02
Host: `aarch64-apple-darwin`

## Python Distribution

- `python -m build --no-isolation --outdir dist/python` succeeded.
- `scripts/verify_distribution.py --dist-dir dist/python` succeeded.
- Wheel SHA-256:
  `d927543b74994276fce9daf4da82af7da1deaaa75d8bb077391c8d8db44b12e7`.
- Sdist SHA-256:
  `b5c1baf1ad22daeaab19e5c2ac313b795abb90ad9b7e5f797c564755e44e431f`.
- The isolated wheel run was hermetic, resolved runtime dependencies only from
  the temporary prefix, loaded packaged templates, blocked external sockets,
  and built a valid `187059` byte DOCX.

## Web Distribution

- `make package-web` succeeded.
- `dist/web/` contains one HTML entry and two hashed assets.
- `dist/web/index.html` SHA-256:
  `6f897d5960daea8ef5f0fd391a8a7611e21a900ce04d0916077c2b1226c8fa03`.
- The desktop verifier accepted the Web artifact root and found no AppleDouble
  pollution.

## Frozen Sidecar

- `scripts/build_sidecar.py --target-triple aarch64-apple-darwin` succeeded.
- Sidecar SHA-256:
  `0a7d56b9d6d7a0383a868ab1ce91e63b08a6d625a0c85bc45441526501c91aa0`.
- The verifier stripped credentials and proxy variables, blocked socket
  connections, copied the complete bachelor example outside the checkout, and
  passed inspect, validate, preview, cancellation, ordered build, DOCX package
  validation, and reopen.
- Cancellation preserved the prior valid output.
- Cross-host target selection and AppleDouble sidecar pollution have focused
  regression tests.

## macOS Native Bundles

- `cargo tauri build --config src-tauri/tauri.release.conf.json --bundles
  app,dmg` succeeded.
- `dot_clean -m src-tauri/target/release/bundle` completed before verification.
- `scripts/verify_desktop_distribution.py` accepted:
  - `src-tauri/target/release/bundle/macos/ThesisForge.app`
  - `src-tauri/target/release/bundle/dmg/ThesisForge_0.1.0_aarch64.dmg`
- The `.app` contains an executable managed sidecar at
  `Contents/MacOS/thesisforge-sidecar` with the same SHA-256 as the source
  sidecar.
- DMG SHA-256:
  `7181c5c41af7dcc7cb1672fba145ef50f3700327b7ae8029c8d48645d5e905f6`.
- Visible native workflow evidence is recorded in
  `evidence/macos-native-acceptance.md`.

## Windows Boundary

- Static tests prove the release workflow uses `windows-2025`,
  `x86_64-pc-windows-msvc`, native PyInstaller, Tauri `msi,nsis`, the release
  external binary config, and the strict distribution verifier.
- The builder rejects relabeling a macOS sidecar as a Windows target.
- The Windows verifier looks for the managed PE sidecar in the native release
  directory and requires both MSI and NSIS artifacts.
- No successful Windows runner result exists in this local session. Windows
  package execution, installer behavior, and sensory acceptance remain an
  external gate and are not claimed as passing.

## Regression Gates

- Frontend unit: `53 passed`.
- Browser E2E: `14 passed`, `16` intentional skips, plus real HTTP `1 passed`.
- Python focused distribution set: `26 passed`.
- Python full suite: `244 passed`.
- Rust protocol tests: `6 passed`.
- Ruff, frontend lint, frontend typecheck, Cargo fmt/check, pip check, strict
  OpenSpec validation, CodeGraph sync/status, and `git diff --check` passed.
