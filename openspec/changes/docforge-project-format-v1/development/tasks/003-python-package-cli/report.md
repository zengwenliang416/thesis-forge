# Task Report: 003-python-package-cli

## Status

DONE

## Files Changed

- `src/thesis_forge/` moved to `src/docforge/`, with imports updated across
  Python source, tests, QA, the real HTTP acceptance server, and packaging
  helpers.
- `pyproject.toml`, `scripts/build_sidecar.py`, `scripts/prepare_release.py`,
  `scripts/verify_distribution.py`, `scripts/verify_thesisforge_v2_goal.py`,
  `README.md`, and `Makefile`.
- CLI and distribution coverage in `tests/cli/`, `tests/test_cli.py`,
  `tests/test_package_import.py`, `tests/test_distribution.py`,
  `tests/test_desktop_distribution.py`, and the direct Python consumers whose
  imports changed with the package move.

## What Changed

- Renamed the Python distribution, import package, packaged resource namespace,
  and sole console script to `docforge`.
- Removed the active `thesis_forge` package and `thesisforge` command without
  adding an alias, shim, fallback loader, or compatibility package.
- Kept `inspect`, `validate`, `review`, and `build` on the shared typed project
  application services, accepting only a project directory or `docforge.yaml`.
- Made `review` use the manifest-resolved project paths by default, while
  preserving `--output-dir` as an explicit export-root override.
- Updated CLI help and parser diagnostics to DocForge terminology, removed the
  ineffective per-command template override, and made the default build path
  `build/document.docx`.
- Restored validation against the strict DocForge manifest by discovering
  `docforge.yaml` and mapping generic and optional academic metadata into the
  existing template-facing metadata groups.
- Extended the distribution verifier to build and inspect DocForge artifacts,
  install the wheel into an isolated prefix, block network access, prove import
  provenance, and execute `inspect`, `validate`, default-path `review`, and
  `build`.
- Tightened wheel inspection to require all four bundled template YAMLs and
  exactly one console script, `docforge = docforge.cli:app`, rejecting an
  additional obsolete alias.
- Closed the offline-launcher socket bypass by blocking `connect_ex` alongside
  `create_connection` and `connect`, with a subprocess regression that proves
  the bypass raises before network I/O.

## TDD Evidence

- `tests/test_package_import.py` initially produced three failures for the old
  distribution name, missing `docforge` import package, and thesis-specific CLI
  help.
- The first integrated run then exposed the omitted QA import in
  `qa/tools/parser_diff.py`; the next run exposed the stale
  `LoadedProject.source_path` validator dependency. Both were corrected without
  introducing compatibility behavior.
- Final task-focused and extended CLI/distribution suites pass with the real
  renamed package and clean wheel installation.

## Verification Commands

- `PYTHONPATH=src .venv/bin/python -m pytest tests/cli tests/test_package_import.py tests/test_desktop_distribution.py -q`
  -> `47 passed`.
- `PYTHONPATH=src .venv/bin/python -m pytest tests/cli tests/test_cli.py tests/test_package_import.py tests/test_distribution.py tests/test_desktop_distribution.py -q`
  -> `69 passed`.
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_package_import.py tests/cli tests/test_cli.py tests/test_parser_markdown_it.py tests/test_distribution.py tests/test_desktop_distribution.py -q`
  -> `104 passed`.
- `PYTHONPATH=src .venv/bin/python -m pytest --collect-only -q`
  -> `1331 tests collected`.
- `.venv/bin/ruff check src tests`
  -> `All checks passed`.
- `.venv/bin/python -m build --no-isolation --outdir /tmp/docforge-task003-final.Y0JrcS`
  -> built `docforge-0.1.0-py3-none-any.whl` and
  `docforge-0.1.0.tar.gz`.
- `.venv/bin/python scripts/verify_distribution.py --dist-dir /tmp/docforge-task003-final.Y0JrcS`
  -> `ok: true`; hermetic imports and offline `inspect`, `validate`, `review`,
  and `build` passed, producing Review artifacts and a valid DOCX ZIP package.
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_distribution.py tests/cli/test_review_command.py -q`
  -> `11 passed`, including a subprocess proof that `connect_ex` is blocked.
- `.venv/bin/docforge review --help`
  -> `--output-dir` is optional.
- `PYTHONPATH=src .venv/bin/python -m docforge.cli review <copied-docforge-academic-project>`
  -> `status: ready`; wrote `review/document.review.md` and
  `review/document.review-map.json` without an output option.
- `OPENSPEC_TELEMETRY=0 openspec validate docforge-project-format-v1 --strict --no-interactive --json`
  -> `1 passed; 0 failed`.
- `SPECNAV_CHANGE=docforge-project-format-v1 node development-contract.js --mode entry --json`
  -> `ok: true`.

## Concerns

- The full repository run currently reports `1261 passed, 38 failed, 32
  errors`. The sampled failures are obsolete repository-owned
  `thesisforge.yaml` / `thesis.md` project and template fixtures rejected by the
  strict Task 001 contract. Their conversion is explicitly owned by Task 007;
  no failure is caused by a missing `docforge` import, console script, packaged
  resource, or Task 003 CLI path.

## Scope Deviations

- `frontend/e2e/real_http_server.py` and `qa/tools/parser_diff.py` required
  direct import updates because removal of `thesis_forge` otherwise breaks
  active Python acceptance and QA entrypoints.
- Desktop sidecar names, workbench and BuildReport protocol identifiers,
  template compatibility fields, application bundle identity, examples, CI,
  and release asset identity remain deferred to Tasks 004 through 007.

## Follow-up Needed

- Task 004 must migrate runtime and BuildReport protocol identities.
- Task 005 must add `docforge-standard` and typed template bindings.
- Tasks 006 and 007 must migrate desktop identity and repository-owned
  examples, fixtures, CI, and release surfaces before the full suite can pass.

## Adjudication

The full-suite failures are assigned to their declared downstream task and do
not overturn the executed Task 003 package, CLI, build, and hermetic
distribution evidence.
