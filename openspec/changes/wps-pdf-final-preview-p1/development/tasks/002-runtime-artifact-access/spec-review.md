# Spec Review: 002-runtime-artifact-access

## Verdict

approved

## Missing Requirements

- None found in task 002's runtime artifact-access scope.
- The previous same-name collision is resolved with a unique 32-character UUID
  `authorizationId` for every authorization.
- Each handle is bound to `engine`, `fileName`, and a stable path identity made
  from the canonical parent plus the unchanged final file name.
- `authorize()` and `revoke_path()` now use the same non-dereferencing identity,
  so replacing the final PDF with a symlink cannot preserve an old handle
  through a subsequent rebuild.

## Extra Behavior

- No out-of-scope production behavior was found in the task-owned Python
  adapters, Tauri boundary, or frontend transport changes.
- The `blob:` CSP support is consistent with the downstream object-URL PDF
  viewer and does not expand native filesystem access.

## Misunderstood Requirements

- None found.
- Desktop descriptors remain path-free capabilities rather than authentication
  by file name. Distinct same-named PDFs receive distinct handles, and resolve
  rejects changes to the bound engine or file name.
- Automatic previews remain restricted to the derived DOCX sibling. Explicit
  WPS previews must pass the native picker and regular PDF validation.
- Web reads remain workspace-bound and reject traversal, cross-workspace
  access, symlinks, non-PDF names, and invalid PDF content.

## Cannot Verify From Diff

- Native packaged macOS and Windows picker/read execution was not performed in
  this task review. It remains a release verification surface, not a blocker
  for the shared runtime authorization contract covered by this task.
- Actual PDF rendering, stale UI transitions, and WPS page-by-page sensory
  comparison belong to tasks 003/004 rather than task 002.
- The change-level SpecNav handoff can remain blocked by incomplete task 4.3,
  task-ledger transitions, or other task artifacts independently of this
  approved task review.

## Acceptance Assertions Verified

- `A2` verified for task 002's runtime portion: automatic preview descriptors
  expose no private absolute path; Web reads are workspace-bound; desktop
  automatic previews receive an opaque handle bound to the requested derived
  sibling; previous derived authorizations are revoked before rebuild.
- `A3` verified for task 002's selection/read portion: Web and Tauri expose
  explicit WPS PDF selection seams, desktop reads require a valid
  `authorizationId`, same-named PDFs remain independently bound, and
  descriptor/content/symlink mutations fail closed. Display, stale state, and
  sensory comparison remain owned by later tasks.

## Required Fixes

- No blocking task-002 spec fix remains after stable path identity and the
  symlink-before-rebuild authorization regression were added.

## Reviewer Checks

- `CARGO_TARGET_DIR=/tmp/thesisforge-cargo-target-review-002-rerun cargo fmt --manifest-path src-tauri/Cargo.toml --check`
  -> passed.
- `CARGO_TARGET_DIR=/tmp/thesisforge-cargo-target-review-002-rerun cargo test --manifest-path src-tauri/Cargo.toml`
  -> `22 passed`.
- Focused Rust regression
  `a_new_build_revokes_old_authorization_after_preview_becomes_a_symlink`
  -> `1 passed`.
- `pnpm --dir frontend exec vitest run src/transport/finalPreview.test.ts src/transport/buildEvents.test.ts src/transport/transports.test.ts`
  -> `3 files passed`, `21 tests passed`.
- `.venv/bin/python -m pytest tests/test_adapters.py tests/test_http_adapter.py tests/test_sidecar.py -q`
  -> `31 passed`.
- Focused Ruff and `git diff --check` -> passed.
