# Task Brief: 009-installation-and-maintenance-handoff

## Goal

A new contributor can install, test, package and maintain ThesisForge from the
repository, while a reviewer can audit every development slice and verify the
SpecNav development handoff before six-domain verification begins.

## Parent Artifacts

- `openspec/changes/build-thesisforge-v1-core/requirements.md`
- `openspec/changes/build-thesisforge-v1-core/acceptance.md`
- `openspec/changes/build-thesisforge-v1-core/acceptance.json`
- `openspec/changes/build-thesisforge-v1-core/design.md`
- `openspec/changes/build-thesisforge-v1-core/spec-map.json`
- `openspec/changes/build-thesisforge-v1-core/component-impact-map.json`
- `openspec/changes/build-thesisforge-v1-core/prototype/handoff.md`
- `openspec/changes/build-thesisforge-v1-core/tasks.md`

## Vertical Slice

Turn the completed V1 core into a reproducible local contributor workflow:
install development dependencies, run one documented verification gate, build
wheel and sdist, inspect their contents, install the wheel outside the checkout
without dependency downloads, and run offline inspect/validate/build using
bundled templates. Reconcile public documentation with implemented behavior,
then assemble auditable evidence for tasks 001 through 009 and satisfy the
SpecNav development handoff contract.

## In Scope

- Preserve task `9.1`: A contributor can reproduce the full `pytest`, `ruff`,
  package-build and OpenSpec validation suites.
- Preserve task `9.2`: A contributor can rely on README, architecture,
  Markdown/template specifications and third-party notes matching implemented
  behavior.
- Preserve task `9.3`: A reviewer can inspect final task reports, independent
  spec reviews, quality reviews, validation ledgers and drift checks.
- Preserve task `9.4`: A reviewer can verify the SpecNav development handoff
  contract before six-domain verification starts.
- Add standard local package build dependencies to the development extra.
- Define one Makefile maintainer gate for tests, lint, dependency checks,
  distribution build/installation verification, strict OpenSpec validation and
  whitespace checks.
- Build wheel and sdist without an isolated dependency download after the
  development environment is installed.
- Verify console entry-point metadata, bundled templates, source-distribution
  maintenance files and absence of AppleDouble files.
- Install the wheel with `--no-index --no-deps` into a temporary isolated prefix
  and run the complete example outside the repository with network connections
  blocked and AI/provider credentials removed.
- Copy only the active recursive closure of declared runtime dependencies into
  the prefix, run with `python -S`, and reject parent site-packages, checkout
  paths or key imports outside the prefix.
- Update README, architecture, Markdown/template specifications, third-party
  notes and a maintainer guide to match the accepted V1 implementation.
- Audit all task packets, ledgers, drift checks, validation logs, CodeGraph
  claims and final handoff content.

## Out Of Scope

- Public package publication, signing, notarization or package-index upload.
- Selecting a project license or making legal conclusions about dependency
  licenses.
- New Markdown syntax, Template Model fields or thesis rendering behavior.
- A production desktop UI, backend, cloud service, account system or AI
  provider.
- Rewriting accepted task 001-008 implementation or evidence without a
  reproduced defect.
- Starting six-domain verification, archive or release before the development
  handoff contract passes.

## Files Allowed

- `pyproject.toml`
- `Makefile`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/MARKDOWN_SPEC.md`
- `docs/TEMPLATE_SPEC.md`
- `docs/THIRD_PARTY_NOTES.md`
- `docs/MAINTENANCE.md`
- `scripts/verify_distribution.py`
- `tests/test_distribution.py`
- `openspec/changes/build-thesisforge-v1-core/tasks.md`
- `openspec/changes/build-thesisforge-v1-core/development/task-context.jsonl`
- `openspec/changes/build-thesisforge-v1-core/development/task-ledger.jsonl`
- `openspec/changes/build-thesisforge-v1-core/development/drift-check.jsonl`
- `openspec/changes/build-thesisforge-v1-core/development/validation-log.jsonl`
- `openspec/changes/build-thesisforge-v1-core/development/handoff-to-verify.md`
- `openspec/changes/build-thesisforge-v1-core/development/tasks/009-installation-and-maintenance-handoff/brief.md`
- `openspec/changes/build-thesisforge-v1-core/development/tasks/009-installation-and-maintenance-handoff/context.json`
- `openspec/changes/build-thesisforge-v1-core/development/tasks/009-installation-and-maintenance-handoff/report.md`
- `openspec/changes/build-thesisforge-v1-core/development/tasks/009-installation-and-maintenance-handoff/spec-review.md`
- `openspec/changes/build-thesisforge-v1-core/development/tasks/009-installation-and-maintenance-handoff/quality-review.md`
- `openspec/changes/build-thesisforge-v1-core/codegraph/claims-map.json`
- `openspec/changes/build-thesisforge-v1-core/codegraph/evidence-query-plan.json`
- `openspec/changes/build-thesisforge-v1-core/codegraph/evidence-index.json`
- `openspec/changes/build-thesisforge-v1-core/codegraph/claims-report.json`
- `openspec/changes/build-thesisforge-v1-core/codegraph/guard-report.json`
- `openspec/changes/build-thesisforge-v1-core/codegraph/status.json`
- `openspec/changes/build-thesisforge-v1-core/codegraph/drift-report.json`
- `openspec/.specnav/change-registry.json`

## Interfaces / Seams

- `pyproject.toml` remains the source of package metadata, build backend,
  development dependencies, console entry point and bundled templates.
- Make targets call the selected `PYTHON` interpreter and compose existing
  pytest, Ruff, pip, OpenSpec and Git commands without duplicating product
  behavior.
- `verify_distribution.py` uses the Python standard library plus the explicit
  development `packaging` dependency for PEP 508 marker evaluation, and treats
  wheel/sdist artifacts as black-box inputs.
- Installation verification runs the generated console script outside the
  checkout so package resources, not repository fallback paths, resolve the
  template.
- SpecNav ledgers and handoff files record executed evidence; they do not
  replace tests or command results.

## Components To Create

- Lightweight distribution verifier with PEP 508-aware dependency provenance.
- Distribution build and installed-CLI regression test.
- Maintainer guide.

## Components To Reuse

- Existing Hatchling wheel configuration and console entry point.
- Existing package-resource Template Resolver fallback.
- Complete bachelor-thesis example and offline CLI acceptance behavior.
- Existing task reports, independent reviews, ledgers, drift checks,
  validation logs and CodeGraph contracts.

## Components To Extract

- Centralize distribution artifact inspection and isolated installation in
  `scripts/verify_distribution.py`; Makefile and pytest invoke that component
  rather than carrying duplicate shell logic.
- Do not extract or refactor the accepted product pipeline in this slice.

## API / Data Flow Contracts

- Development install -> full checks -> wheel/sdist -> artifact inspection ->
  temporary wheel install -> offline CLI -> valid DOCX.
- The temporary prefix install uses no package index or dependency resolution
  and must not uninstall or replace the parent editable package.
- Bundled template resolution must succeed without a checkout-level
  `templates/` directory.
- Distribution verification must fail non-zero for missing artifacts,
  missing package data, missing console entry point, AppleDouble contamination,
  checkout/parent dependency leakage, network access or CLI/DOCX failure.
- `make verify` must leave source/example inputs unchanged.

## State / Error / Empty / Loading Behavior

- Loading: build and command output is streamed by the invoked tools.
- Empty: a missing wheel, sdist or required package member fails explicitly.
- Error: subprocess failures include the command, exit code and captured output.
- Disabled: no public publication target exists while the project license is
  undecided.
- Permission: temporary environments and outputs are created only in writable
  build/test directories and cleaned automatically.

## TDD Requirement

- Record the initial missing `build` module failure before adding development
  build dependencies.
- Add the distribution build/install test with the verifier implementation.
- Run the focused distribution test before the full suite.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_distribution.py`
- `.venv/bin/python -m pytest`
- `.venv/bin/python -m ruff check .`
- `.venv/bin/python -m pip check`
- `.venv/bin/python -m build --no-isolation --outdir dist`
- `.venv/bin/python scripts/verify_distribution.py --dist-dir dist`
- `OPENSPEC_TELEMETRY=0 openspec validate build-thesisforge-v1-core --strict --no-interactive`
- `git diff --check`
- `make verify`
- SpecNav CodeGraph sync/context/claims checks.
- SpecNav development entry and final handoff contracts.

## Stop Conditions

- Scope lock mismatch.
- Missing product, architecture, data-flow, or component decision.
- Package verification requires network access after the documented development
  environment is installed.
- Installed CLI imports the repository checkout or cannot resolve bundled
  templates.
- Documentation would claim unsupported Markdown, templates, Word structures
  or publication readiness.
- Any task packet, ledger, drift check, validation log, CodeGraph claim or
  handoff artifact remains missing or contains scaffold markers.
- An independent review returns `needs-fix`.

## Unsafe Assumptions

- Editable-install success proves wheel installation works.
- A wheel build proves package data and console metadata are correct.
- Running the installed CLI from the repository proves package independence.
- `pip install` without `--no-index --no-deps` proves an offline artifact.
- Existing task reports alone prove current commands still pass.
- Public release is allowed before project and dependency license review.
