# Spec Review: 007-repository-delivery

## Verdict

approved

This independent review covers items 7.1 through 7.5 against the current
checkout on August 27, 2026. The active examples, generated Review output,
facticity coverage, packaging, CI, and macOS release collection now satisfy the
Task 007 contract.

## Missing Requirements

- None for Task 007 items 7.1 through 7.5.
- Active example assets and Review output use `ForgeDocument`; the facticity
  checker now detects obsolete `ThesisDocument` occurrences and distinguishes
  active, historical, and explicit-negative surfaces.

## Extra Behavior

- No unrequested compatibility alias or external publication behavior was
  found.
- The release collector and desktop verifier enforce AppleDouble-free,
  symlink-safe, version-matched DocForge artifacts, executable managed
  sidecars, offline operations, cancellation, and atomic DOCX behavior. These
  checks remain within the delivery contract.
- The release workflow removes macOS metadata sidecars after DMG verification
  and before release collection. A temporary-copy replay of that sequence
  passed the desktop verifier and produced the expected five release files.

## Misunderstood Requirements

- The migration correctly preserves historical ThesisForge documents and
  explicit obsolete-input vectors. Those allowlisted references are not the
  active contract.
- Local build, DMG verification, and release collection do not prove that a
  GitHub Release was tagged, uploaded, or published; no such claim is made
  here.

## Cannot Verify From Diff

- External Woodpecker staging and GitHub Release publication were intentionally
  not executed and remain outside this task's authorization.
- Build outputs under `src-tauri/target/` are ignored and cannot bind a release
  artifact to a committed HEAD. The local macOS volume can also create an
  ignored `._DocForge_0.1.0_aarch64.dmg` sidecar when `hdiutil verify` runs;
  the release workflow's post-verification cleanup is required and was
  replayed successfully in a temporary copy.
- `acceptance.json` still records change-level assertions as `failing`; this
  task review does not mutate the change-level acceptance ledger or close
  Task 008's trusted receipt binding.

## Acceptance Assertions Verified

- `A4`: `tests/core/test_forge_document.py` confirms that `ForgeDocument` is
  exported and `ThesisDocument` is not. Active runtime/protocol checks reject
  obsolete contracts without compatibility dispatch or aliases.
- `A10`: active examples, fixtures, documentation, packaging, and CI use the
  DocForge project contract and neutral filenames. Facticity reports zero
  active findings after the `ThesisDocument` rule was added.
- Items 7.1 through 7.5 are covered by the converted project surfaces,
  classified facticity report, distribution tests, CI/release configuration,
  and the clean temporary macOS release replay.

## Required Fixes

- None for Task 007.
- Task 008 still owns binding fresh A4/A10 receipts to the final committed
  HEAD; that change-level follow-up does not block this task-local approval.

## Verification Evidence

- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_desktop_distribution.py tests/cli tests/project -q`
  -> `165 passed`.
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_facticity.py tests/test_desktop_distribution.py -q`
  -> `40 passed`.
- `PYTHONPATH=src .venv/bin/python -m pytest tests/core/test_forge_document.py -q`
  -> `3 passed`.
- `.venv/bin/ruff check scripts tests/test_desktop_distribution.py`
  -> passed.
- `PYTHONPATH=src .venv/bin/python scripts/check_facticity.py --json /tmp/docforge-facticity-review-r2-20260827.json --markdown /tmp/docforge-facticity-review-r2-20260827.md`
  -> `ok=true`, `activeFindingCount=0`, `allowedFindingCount=325`,
  `scannedFiles=332`, `skippedFiles=43`; allowed findings include the
  historical and explicit-negative `obsolete-domain` cases.
- `pnpm --dir frontend build` -> passed.
- `cargo check --manifest-path src-tauri/Cargo.toml` -> passed with only
  incremental-cache hard-link warnings.
- `PYTHONPATH=src .venv/bin/python scripts/prepare_release.py --tag v0.1.0 --validate-only`
  -> `{"ok": true, "tag": "v0.1.0", "version": "0.1.0"}`.
- Temporary clean-bundle replay of `hdiutil verify`, AppleDouble cleanup,
  `scripts/verify_desktop_distribution.py`, and `scripts/prepare_release.py`
  -> DMG checksum valid, desktop verifier `ok=true`, collector `ok=true`, and
  exactly five release files:
  `DocForge_0.1.0_aarch64.dmg`,
  `docforge-0.1.0-py3-none-any.whl`,
  `docforge-0.1.0.tar.gz`, `SHA256SUMS`, and `RELEASE_NOTES.md`.
- `shasum -a 256 -c SHA256SUMS` on the temporary release -> all three assets
  returned `OK`.
