# ThesisForge Maintenance Guide

This guide defines the reproducible verification and distribution path for the
ThesisForge Python package, Web workbench, and Tauri desktop packages. Product
commands and packaged desktop workflows remain offline after build dependencies
are installed.

## Supported Environment

- Python 3.11 or newer.
- A local virtual environment.
- Node.js and pnpm 10.34.5 for frontend builds.
- Rust and Tauri CLI 2 for native desktop builds.
- OpenSpec CLI for lifecycle validation.
- LibreOffice is optional for TOC refresh, automatic final-layout PDF preview,
  and manual Office compatibility review.

Create the development environment:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
make install
```

The project does not require AI credentials for `inspect`, `validate`, `build`,
tests, linting, distribution verification or OpenSpec validation. Packaged
desktop applications must not require separately installed Python, Node.js,
Rust, an HTTP service, an account, telemetry, or external sockets.

## Daily Checks

Run the complete source, Web, and sidecar maintainer gate:

```bash
make verify
```

This executes:

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m pip check
.venv/bin/python -m build --no-isolation --outdir dist/python
.venv/bin/python scripts/verify_distribution.py --dist-dir dist/python
pnpm frontend:test
pnpm frontend:typecheck
pnpm frontend:lint
pnpm frontend:build
pnpm frontend:e2e
cargo fmt --manifest-path src-tauri/Cargo.toml -- --check
cargo test --manifest-path src-tauri/Cargo.toml
cargo check --manifest-path src-tauri/Cargo.toml
.venv/bin/python scripts/build_sidecar.py
.venv/bin/python scripts/verify_desktop_distribution.py --sidecar-only
OPENSPEC_TELEMETRY=0 openspec validate build-thesisforge-desktop-ui --strict --no-interactive
git diff --check
```

This command does not build or verify native `.app`, `.dmg`, `.msi`, or NSIS
installer artifacts. Run the platform-native commands under **Native Packages**
in addition to `make verify` before treating a desktop distribution as
accepted.

`verify_distribution.py` inspects wheel and sdist contents, rejects AppleDouble
files, checks the console entry point and bundled templates, installs the wheel
without dependency downloads into a temporary isolated prefix, then runs
`inspect`, `validate` and `build` from outside the repository with network
connections blocked. The verifier also proves the temporary install did not
replace or remove the maintainer environment's editable package.

For hermetic execution, the verifier copies only the installed recursive
closure of `[project].dependencies` into the prefix, evaluates PEP 508 markers
with no extras, and launches the generated console script through `python -S`.
It fails if checkout paths or parent `purelib`/`platlib` appear on `sys.path`,
or if ThesisForge, Typer, Rich, PyYAML, python-docx, lxml or Pydantic resolve
outside the temporary prefix.

## Example Build

```bash
make inspect
make validate
make build-example
```

The default output is `output/thesis.docx`. Build uses a same-directory
temporary file, validates the DOCX package and atomically replaces the target
only after all required stages succeed. After DOCX publication it may derive
`output/thesis.preview.pdf` through LibreOffice. The PDF is signature-checked
and atomically replaced; exporter absence, timeout or failure must not downgrade
the valid DOCX build.

## Distribution Boundary

`make package` creates:

```text
dist/python/thesis_forge-<version>-py3-none-any.whl
dist/python/thesis_forge-<version>.tar.gz
```

The wheel bundles the base and example-university templates under
`thesis_forge/template_data/`. The sdist includes source, templates, examples,
tests, specifications and maintenance scripts.

These artifacts are locally installable verification distributions. The
repository has not selected a project license, so do not publish them to a
public package index until ownership and license review are complete.

## Web Distribution

Build the static frontend independently:

```bash
make package-web
```

The result is `dist/web/`. It contains only static Vite assets and does not
embed Python or a compiler service. At runtime the Web product must use the
configured versioned ThesisForge HTTP adapter. Browser source persistence uses
workspace-save or download semantics and must not claim native filesystem
paths.

Automatic final-preview bytes are served only through
`GET /api/v1/workspaces/{workspace_id}/files/{plain_pdf_name}` with
`application/pdf`, `no-store` and `nosniff`. The runtime rejects malformed
workspace IDs, traversal, non-PDF names, workspace-escaping symlinks and invalid
PDF signatures. Live-preview artifacts use a separate server-issued capability
route and a runtime-owned `.thesisforge-live-previews/` directory; reads and
explicit discard consume the capability, while startup/allocation sweeps remove
expired files left by a process restart. User-selected Office PDFs stay
browser-local.

## Desktop Sidecar

Build and verify the frozen sidecar for the current native Rust target:

```bash
make verify-desktop-dist
```

The builder:

- rejects a target triple different from the native host;
- packages `thesis_forge.adapters.sidecar` with required templates and
  python-docx data;
- writes `src-tauri/binaries/thesisforge-sidecar-<target>`;
- keeps PyInstaller in development dependencies only.

The verifier removes API-key/token and proxy variables, sets
`THESISFORGE_BLOCK_NETWORK=1`, copies the complete example outside the checkout,
and proves inspect, validate, preview, cancellation, ordered build, valid DOCX
output, and reopen behavior. Cancellation must preserve the prior output.

`THESISFORGE_SIDECAR_EXECUTABLE` and `THESISFORGE_PYTHON` are explicit
development/test overrides. A release build without those overrides resolves
the Tauri-managed `thesisforge-sidecar` bundled beside the application.

## Native Packages

macOS packages must be built on macOS:

```bash
.venv/bin/python scripts/build_sidecar.py \
  --target-triple aarch64-apple-darwin
cargo tauri build \
  --config src-tauri/tauri.release.conf.json \
  --target aarch64-apple-darwin \
  --bundles app,dmg
dot_clean -m src-tauri/target/aarch64-apple-darwin/release/bundle
.venv/bin/python scripts/verify_desktop_distribution.py \
  --target-triple aarch64-apple-darwin \
  --platform macos \
  --web-dist dist/web \
  --bundle-root src-tauri/target/aarch64-apple-darwin/release/bundle
```

When `--target` is omitted, Tauri writes to
`src-tauri/target/release/bundle/`; pass that directory to the verifier instead.
Run `dot_clean -m` before checksums and upload because external macOS volumes
may create `._*` AppleDouble files.

Windows packages must be built and verified on a Windows runner:

```powershell
python scripts/build_sidecar.py --target-triple x86_64-pc-windows-msvc
cargo tauri build `
  --config src-tauri/tauri.release.conf.json `
  --target x86_64-pc-windows-msvc `
  --bundles msi,nsis
python scripts/verify_desktop_distribution.py `
  --target-triple x86_64-pc-windows-msvc `
  --platform windows `
  --web-dist dist/web `
  --bundle-root src-tauri/target/x86_64-pc-windows-msvc/release/bundle
```

The repository workflow `.github/workflows/distribution.yml` runs native macOS
and Windows matrix jobs and uploads Web, Python, sidecar, and desktop artifacts
separately. A workflow definition is not Windows execution evidence; only a
successful Windows job may establish `.msi` / NSIS acceptance.

The primary release orchestrator is Woodpecker:

- `.woodpecker/quality.yml` runs the Linux quality gate for `v*` tags;
- the Linux clone and quality images are pinned by digest, and Cargo validation
  uses the committed lockfile;
- `.woodpecker/release-macos.yml` waits for that gate, then selects a
  `darwin/arm64` local agent with `purpose=thesisforge-release` and the
  repository-specific `repo=zengwenliang416/thesis-forge` label;
- the macOS workflow disables Woodpecker's automatic Local-backend clone and
  fetches only `origin/main` plus the requested release tag from the fixed
  GitHub repository before checking commit provenance;
- the macOS workflow verifies version consistency, builds Web/Python/sidecar
  outputs, creates the native `.app` and `.dmg`, validates the offline desktop
  contract, then uploads the allowlisted assets with write-only staging
  credentials; verifier and platform-security evidence is retained under a
  separate staging prefix and is not published as a user download;
- `.woodpecker/release-publish.yml` runs on the isolated Linux Docker agent,
  downloads the staged assets with read-only credentials, verifies
  the exact asset allowlist and `SHA256SUMS`, refuses to modify any existing
  release for the tag, and creates a new GitHub Prerelease;
- the repository secret `github_release_token` must be a dedicated
  least-privilege token with GitHub repository contents write access, restricted
  to the tag event and available only to `release-publish.yml`;
- no Release tag may be pushed until the native agent and secret are confirmed.

The local backend executes tag-controlled release code directly on the native
host. It must run as a non-root user, must not be enabled for pull requests, and
must use a repository-scoped agent label. Release tags must resolve to the
checked-out commit and that commit must already be reachable from `origin/main`.
The host must provide AWS CLI `2.36.30`; the workflow verifies this exact version
and does not install release upload tooling from the network at runtime.
The native builder must not receive the GitHub Release token. Its staging
credentials must be limited to writing only the tag-specific release prefix;
the Linux publisher uses a separate read-only identity. The staging bucket must
be dedicated to ThesisForge rather than reusing another project's bucket. Use
separate `release_staging_write_endpoint` and
`release_staging_read_endpoint` secrets because the native macOS agent reaches
staging through a loopback SSH tunnel while the Linux publisher reaches the
server-local endpoint.
A future Windows workflow must use a native `windows/amd64` agent and attach
`.msi` / NSIS assets to the same tag.

## Installation And Launch

For local macOS acceptance, open the DMG and copy `ThesisForge.app` to
`Applications`, or launch the generated `.app` directly. For Windows, install
the generated MSI or NSIS executable from the native Windows job.

The workbench uses native file dialogs and accepts `.md` and `.markdown`.
Desktop source writes occur only after explicit Save / `Cmd/Ctrl+S`. Build /
`Cmd/Ctrl+B` writes `thesis.docx` next to the source unless the transport
provides another output path. Web builds require the configured HTTP service
and return browser-appropriate output identity/download behavior.

The Tauri bridge authorizes only the derived `.preview.pdf` sibling from a
successful build or a PDF returned by the native picker. `read_pdf_preview`
returns raw IPC bytes and rejects arbitrary paths, symlinks, non-PDF files and
invalid signatures.

## Signing, Checksums, And Publication

Current local and CI test artifacts are development distributions. The macOS
Prerelease workflow uses Tauri ad-hoc signing (`signingIdentity: "-"`) so the
bundle has a structurally valid code signature, but it is not Developer ID
signed or notarized.
Production release requires all of the following external gates:

- select a project license and complete third-party ownership review;
- sign macOS bundles with Apple Developer ID and notarize/staple them;
- sign Windows installers with an approved Authenticode certificate;
- generate SHA-256 checksums only after signing, notarization, and AppleDouble
  cleanup;
- verify checksums after artifact download on each native platform;
- retain the successful native CI run and distribution verifier JSON as release
  evidence.

Do not bypass operating-system security warnings or publish ad-hoc/unsigned
artifacts as production releases.

## Troubleshooting

- `failed to resolve packaged ThesisForge sidecar`: rebuild the native sidecar,
  then rebuild the Tauri bundle with the release config.
- Markdown is visible but cannot be opened: use `.md` or `.markdown`; other
  extensions are rejected at the Rust boundary.
- A source cannot be saved: verify filesystem permissions. The editor remains
  dirty and the prior file must remain unchanged.
- Build cancellation or failure: retry from the workbench; the previous valid
  DOCX must remain intact.
- Desktop final preview is unavailable: confirm Microsoft Word is installed,
  allow ThesisForge under the operating system's automation permissions, then
  refresh or select a PDF explicitly exported by Microsoft Word.
- Final preview is marked stale: the Markdown, template or workspace changed
  after the PDF was bound. Stop editing briefly for automatic refresh, click
  refresh, or select a new Office PDF.
- `Bundle contains AppleDouble files`: run `dot_clean -m` on the bundle root,
  then rerun the verifier and checksums.
- Web actions cannot reach the compiler: configure and start the ThesisForge
  HTTP adapter; static Vite files alone are not a compiler service.
- Windows artifacts are missing locally on macOS: use the native Windows CI
  matrix job. Do not relabel or copy the macOS sidecar.

## Change Checklist

- Markdown syntax changes require `docs/MARKDOWN_SPEC.md`, parser tests and an
  example update.
- Template fields require `docs/TEMPLATE_SPEC.md`, Template Model tests and
  renderer/compiler coverage.
- DOCX XML changes require direct package/XML assertions and at least one
  Word/WPS/LibreOffice review.
- Third-party implementation reuse requires an entry in
  `docs/THIRD_PARTY_NOTES.md` before merge.
- Core commands must continue to pass with network blocked and AI credentials
  absent.
- Release candidates require `make verify`, the applicable native package build
  and verifier, and review of the active SpecNav task reports, ledgers, drift
  checks and handoff contract.
