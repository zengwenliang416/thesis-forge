# Task Report: 003-python-package-cli

## Status

DONE

## Files Changed

- Python distribution and import package under `src/docforge/`.
- Package metadata and the sole `docforge` console entry point in
  `pyproject.toml`.
- CLI behavior and Review output transaction handling in `src/docforge/cli.py`.
- Distribution inspection and isolated-install verification in
  `scripts/verify_distribution.py`.
- Package, CLI, Review, wheel, sdist, and desktop-distribution tests.
- Active package and CLI documentation in `README.md` and `Makefile`.

## What Changed

- Renamed the active Python distribution, import package, resources, and
  console command to `docforge` without a `thesis_forge` compatibility package
  or `thesisforge` command alias.
- Kept `inspect`, `validate`, `review`, and `build` on the shared typed project
  application services.
- Made `review --output-dir` optional. When omitted, Review uses the manifest
  paths under the project root.
- Made the Review Markdown and source-map pair failure-safe:
  - both payloads are serialized to same-directory temporary files;
  - both staged files are read back before replacement begins;
  - existing targets are backed up;
  - a failure during either final replacement restores the previous pair or
    removes newly created partial output;
  - temporary files are removed on success and failure.
- Kept the neutral default build path `build/document.docx`.
- Hardened artifact inspection:
  - all four bundled template YAML files are required;
  - console entry-point metadata must contain only
    `docforge = docforge.cli:app`;
  - active wheel `Requires-Dist` names must match the eight declared runtime
    distributions;
  - wheel and sdist contents reject obsolete `thesis_forge/` package paths.
- Replaced host `site-packages` copying with a clean installation flow:
  - requirements are read from the built wheel `METADATA`;
  - active direct and transitive requirements are resolved against installed
    distribution metadata and version constraints;
  - those validated distributions are materialized as a temporary local
    wheelhouse;
  - a new virtual environment installs DocForge and dependencies with
    `pip --isolated --no-index`, followed by an isolated `pip check`;
  - inherited `PIP_*` settings are removed and `PIP_CONFIG_FILE` is forced to
    the platform null device;
  - every verifier subprocess has a 180-second hard timeout;
  - import provenance must stay inside the new virtual environment;
  - the platform-native generated `docforge` launcher is executed directly,
    including the `docforge.exe` path on Windows.
- Narrowed the runtime network claim to its tested boundary. The verification
  guard blocks Python DNS, connect, send, and UDP socket APIs; it does not claim
  an OS-level network sandbox.

## TDD Evidence

- Review fault injection initially reproduced partial output: failure during
  the source-map replacement left or overwrote Review Markdown.
- The final tests cover both pre-existing output rollback and the no-existing-
  output case, including temporary-file cleanup.
- Wheel fixtures cover missing runtime metadata and obsolete package paths in
  both wheel and sdist artifacts.
- Network probes cover `connect_ex`, UDP `sendto`, and DNS `getaddrinfo`.
- Pip isolation tests cover inherited find-links, index, and config settings,
  the `--isolated` command path, and subprocess timeout reporting.
- The platform-path test proves Windows selects `Scripts/docforge.exe` and
  POSIX selects `bin/docforge`; the verifier no longer passes a Windows
  executable to `runpy`.

## Verification Commands

- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_distribution.py tests/cli/test_review_command.py -q`
  -> `21 passed in 17.92s`.
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_package_import.py tests/cli tests/test_cli.py tests/test_parser_markdown_it.py tests/test_distribution.py tests/test_desktop_distribution.py -q`
  -> `115 passed in 12.01s`.
- `.venv/bin/ruff check src tests qa spikes scripts`
  -> `All checks passed`.
- `.venv/bin/python -m build --no-isolation --outdir /tmp/docforge-task003-r2.qbHmz5`
  -> built `docforge-0.1.0-py3-none-any.whl` and
  `docforge-0.1.0.tar.gz`.
- `PIP_FIND_LINKS=http://127.0.0.1:1/ PIP_INDEX_URL=https://example.invalid/simple PIP_CONFIG_FILE=/tmp/untrusted-pip.conf .venv/bin/python scripts/verify_distribution.py --dist-dir /tmp/docforge-task003-r2.qbHmz5`
  -> `ok: true`; exact wheel metadata, obsolete-path rejection, 16 dependency
  wheels, sanitized pip configuration, isolated `pip --no-index`
  installation, `pip check`, import provenance, platform console launcher,
  Python socket guard, default Review outputs, and valid DOCX output passed.
- `git diff --check -- scripts/verify_distribution.py tests/test_distribution.py src/docforge/cli.py tests/cli/test_review_command.py`
  -> passed.
- `SPECNAV_CHANGE=docforge-project-format-v1 node development-contract.js --mode entry --json`
  -> `ok: true`; no blockers.

## Concerns

- The temporary dependency wheelhouse is reconstructed from distributions
  already installed in the verifier's host interpreter. This proves that the
  wheel metadata is complete enough for pip dependency resolution and a clean
  target installation without copying host packages into the target. It does
  not prove that every dependency wheel is available from an external package
  index.
- The runtime network guard is intentionally reported as
  `python-socket-apis`. It blocks the Python network paths covered by tests but
  is not an OS-level sandbox for arbitrary native child processes.
- The last recorded repository-wide run before this review round reported
  `1261 passed, 38 failed, 32 errors`, primarily from obsolete repository-owned
  projects and templates assigned to Task 007. It was not rerun in this fix
  round and is not represented as current green evidence.

## Scope Deviations

- `frontend/e2e/real_http_server.py`, `qa/tools/parser_diff.py`, and two phase-0
  spike imports required direct import migration because removing
  `thesis_forge` otherwise broke active Python consumers.
- Runtime protocol, desktop transport, templates, examples, release identity,
  and remaining repository delivery surfaces remain assigned to Tasks 004
  through 007.

## Follow-up Needed

- Task 004 must migrate runtime and BuildReport protocol identities.
- Task 005 must add the neutral standard template profile.
- Tasks 006 and 007 must migrate desktop and repository delivery surfaces
  before the complete change can pass end to end.
