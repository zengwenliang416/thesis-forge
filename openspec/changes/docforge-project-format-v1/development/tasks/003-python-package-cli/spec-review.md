# Spec Review: 003-python-package-cli

## Verdict

approved

This independent rereview covers Task 003 items 3.1 through 3.5 only. The
current implementation satisfies the package, CLI, resource, distribution, and
offline-install requirements owned by this task.

## Missing Requirements

- None for Task 003 items 3.1 through 3.5.
- `docforge` is the active Python distribution, import package, and console
  command identity, with no active `thesis_forge` import package or
  `thesisforge` command alias.
- `inspect`, `validate`, `review`, and `build` use the shared typed project
  application services and expose DocForge diagnostics.
- `review --output-dir` is optional; when omitted, Review resolves the
  manifest-owned Markdown and source-map paths under the project root.
- The wheel contains all four required template YAML resources and exactly one
  console entry point: `docforge = docforge.cli:app`.
- A fresh wheel and sdist install into a new virtual environment from a local
  wheelhouse with `pip --no-index`, pass `pip check`, and run the four CLI
  commands without network access.

## Extra Behavior

- None that expands the Task 003 contract.
- Review writes its Markdown and source-map pair through temporary staging,
  readback verification, backup, rollback, and cleanup; this strengthens the
  required output behavior without adding a public compatibility path.
- Distribution verification rejects obsolete `thesis_forge/` package paths in
  wheel and sdist artifacts, validates active wheel runtime metadata, and
  executes the platform-native generated console launcher.
- The final verifier hardening removes inherited `PIP_*` settings, forces a
  null pip configuration, invokes pip with `--isolated`, and bounds every
  verifier subprocess to 180 seconds; these are deterministic verification
  safeguards, not additional runtime behavior.

## Misunderstood Requirements

- None.
- Removing obsolete package and command identities is intentional; no
  compatibility package, migration shim, fallback loader, or alias is required.
- The local dependency wheelhouse and Python socket guard are verification
  mechanisms. They prove isolated offline installation and the tested Python
  socket API boundary, not availability from an external package index or an
  OS-level network sandbox.
- Task 003 does not claim ownership of the later runtime protocol, template,
  desktop, repository-delivery, or release migrations.

## Cannot Verify From Diff

- `A4` is only partially owned here: the Python package/import/CLI clauses are
  verified, while the old workbench protocol and BuildReport clauses remain
  assigned to Task 004.
- `A5` is verified for the Python project paths and CLI behavior, but this
  review does not claim desktop or repository-owned fixture migration.
- The current repository-wide run is not green: `1261 passed, 38 failed, 32
  errors` from `PYTHONPATH=src .venv/bin/python -m pytest -q`. The failures are
  concentrated in legacy project, template, adapter, desktop, and repository
  acceptance fixtures owned by later tasks, not in the Task 003 focused suites.
- SpecNav entry validation returned `ok: true`. The aggregate handoff
  validation remains `ok: false` because later tasks are incomplete and the
  change-level handoff, receipt authority, task acceptance artifacts, and
  historical failed validation receipts are not yet closed; those blockers are
  outside this Task 003 spec review.
- The resolved handoff command returned `ok: false`. The exact blocker list
  from that run is preserved below; it spans change-level and other-task
  lifecycle state and does not overturn the Task 003 implementation verdict.

  ```text
  task-acceptance:receipt-authority-unavailable:validation-receipt-authority:runtime-status-invalid:ENOENT: no such file or directory, lstat '/Volumes/zwl/open_sources/thesis-forge/openspec/changes/docforge-project-format-v1/verify/v2/runtime-status.json'
  tasks-md:incomplete-checkboxes
  task-ledger-missing-status:004-runtime-protocol:spec_review_passed
  task-ledger-missing-status:004-runtime-protocol:quality_review_passed
  task-ledger-missing-status:004-runtime-protocol:complete
  task-ledger-missing-status:005-template-profiles:spec_review_passed
  task-ledger-missing-status:005-template-profiles:quality_review_passed
  task-ledger-missing-status:005-template-profiles:complete
  task-ledger-missing-status:006-workbench-desktop:spec_review_passed
  task-ledger-missing-status:006-workbench-desktop:quality_review_passed
  task-ledger-missing-status:006-workbench-desktop:complete
  task-ledger-missing-status:007-repository-delivery:spec_review_passed
  task-ledger-missing-status:007-repository-delivery:quality_review_passed
  task-ledger-missing-status:007-repository-delivery:complete
  task-ledger-missing-status:008-end-to-end-verification:spec_review_passed
  task-ledger-missing-status:008-end-to-end-verification:quality_review_passed
  task-ledger-missing-status:008-end-to-end-verification:complete
  validation-log:executed-evidence-failed:002-generic-document-domain
  validation-log:executed-evidence-failed:003-python-package-cli
  scaffold-placeholder:handoff-to-verify.md:decision-required
  missing-task-artifact:acceptance.json
  invalid-task-report:status
  invalid-quality-review:verdict
  scaffold-placeholder:report.md:decision-required
  scaffold-placeholder:report.md:replace-scaffold
  scaffold-placeholder:spec-review.md:replace-scaffold
  invalid-spec-review:verdict
  scaffold-placeholder:quality-review.md:replace-scaffold
  ```

## Acceptance Assertions Verified

- `A4`: current production Python imports use `docforge`, `pyproject.toml`
  exposes only `docforge = docforge.cli:app`, and fresh wheel contents contain
  no `thesis_forge/` package path or `thesisforge` console alias. The
  workbench-protocol portion remains pending Task 004.
- `A5`: project constants, manifest path tests, default Review behavior, the
  installed CLI smoke test, and DOCX output verification establish
  `document.md`, `build/document.docx`, `review/document.review.md`, and
  `review/document.review-map.json`.

## Independent Verification

- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_distribution.py tests/cli/test_review_command.py -q` -> `21 passed`, including hostile inherited pip configuration, `pip --isolated` command construction, and subprocess timeout regression coverage.
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_package_import.py tests/cli tests/test_cli.py tests/test_parser_markdown_it.py tests/test_distribution.py tests/test_desktop_distribution.py -q` -> `115 passed`.
- `.venv/bin/ruff check src tests qa spikes scripts` -> `All checks passed`.
- `.venv/bin/python -m build --no-isolation --outdir /tmp/docforge-task003-r2.qbHmz5` built the wheel and sdist successfully.
- `PIP_FIND_LINKS=http://127.0.0.1:1/ PIP_INDEX_URL=https://example.invalid/simple PIP_CONFIG_FILE=/tmp/untrusted-pip.conf .venv/bin/python scripts/verify_distribution.py --dist-dir /tmp/docforge-task003-r2.qbHmz5` returned `ok: true` with sanitized pip configuration, `pip --isolated --no-index`, `pip check`, import provenance, native launcher, Python socket guard, offline CLI smoke, and valid DOCX evidence.
- `git diff --check -- scripts/verify_distribution.py tests/test_distribution.py src/docforge/cli.py tests/cli/test_review_command.py` -> passed.
- `OPENSPEC_TELEMETRY=0 SPECNAV_CHANGE=docforge-project-format-v1 node /Users/wenliang_zeng/.codex/plugins/cache/specnav-marketplace/specnav-development/0.3.0/scripts/development-contract.js --mode entry --json` returned `ok: true`.

## Required Fixes

- None for Task 003.
