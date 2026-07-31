# Task Brief: 007-safe-and-repeatable-builds

## Goal

A thesis author can run inspect, validate and build through one shared offline
application boundary, and a failed rebuild never replaces a previously valid
DOCX.

## Parent Artifacts

- `openspec/changes/build-thesisforge-v1-core/requirements.md`
- `openspec/changes/build-thesisforge-v1-core/acceptance.md`
- `openspec/changes/build-thesisforge-v1-core/acceptance.json`
- `openspec/changes/build-thesisforge-v1-core/design.md`
- `openspec/changes/build-thesisforge-v1-core/prototype/handoff.md`
- `openspec/changes/build-thesisforge-v1-core/specs/offline-cli-pipeline/spec.md`
- `openspec/specs/system-architecture/design.md`
- `openspec/specs/component-architecture/design.md`
- `openspec/specs/frontend-backend-data-flow/design.md`

## Vertical Slice

Extract the existing CLI orchestration into reusable inspect, validation and
build application services. Build renders to a unique temporary DOCX in the
requested output directory, performs DOCX package smoke validation, and uses
one atomic replacement only after every earlier stage succeeds. The CLI remains
a presentation adapter that maps structured stage failures and validation
results to Chinese output and stable exit codes.

## In Scope

- Add renderer-neutral application result, progress-stage and failure contracts.
- Provide shared `inspect_service`, `validation_service` and `build_service`
  entrypoints for the CLI and future PySide6 adapters.
- Preserve the existing Parser -> Validation -> Compiler -> RenderPlan ->
  Renderer order and reuse the bibliography database loaded by validation.
- Report build stages as `parse`, `validate`, `compile`, `render` and
  `finalize`.
- Keep temporary output in the requested target directory so final
  `os.replace` has same-filesystem atomic semantics.
- Validate the temporary DOCX ZIP integrity, required package parts and
  parseable core XML before replacement.
- Remove temporary output after parser, validation, compiler, renderer,
  package-validation or replacement failure.
- Preserve an existing valid output byte-for-byte on every failure path before
  successful replacement.
- Keep Renderer responsible only for rendering to the path it receives; atomic
  replacement belongs to the application/output boundary.
- Verify repeated builds have semantically equivalent numbering, bookmark,
  reference and field structures even when ZIP metadata differs.
- Add direct service, CLI, architecture and DOCX package tests.

## Out Of Scope

- The complete V1 example expansion and broad Office sensory acceptance owned
  by task 008.
- Packaging, installation and final maintenance documentation owned by task
  009.
- Byte-for-byte identical DOCX archives; semantic OOXML equivalence is the V1
  contract.
- Watch mode, cancellation, background workers or asynchronous rendering.
- UI implementation, progress widgets, accounts, cloud storage or AI.
- Renderer content changes, new Markdown syntax or new Template Model fields.

## Files Allowed

- `src/thesis_forge/application/__init__.py`
- `src/thesis_forge/application/contracts.py`
- `src/thesis_forge/application/output.py`
- `src/thesis_forge/application/services.py`
- `src/thesis_forge/cli.py`
- `src/thesis_forge/renderers/docx/package.py`
- `tests/test_application_services.py`
- `tests/test_architecture.py`
- `tests/test_cli.py`

## Interfaces / Seams

- `inspect_service(source) -> InspectionResult` parses one local source
  snapshot without writing output.
- `validation_service(source, template_path) -> ValidationResult` parses once,
  resolves the validation context and returns deterministically ordered issues.
- `build_service(source, output, template_path, on_progress) -> BuildResult`
  owns the complete safe build lifecycle.
- Application dependencies are injectable for focused failure-stage tests;
  default dependencies remain the production Parser, Validator, Compiler,
  DOCX Renderer and package validator.
- `BuildStageError.stage` identifies the exact failed stage without Rich,
  Typer, DOCX or OOXML objects entering Core Domain.
- `validate_docx_package(path)` raises a typed package-validation error and
  never replaces the requested output.

## Components To Create

- Typed application contracts for inspection, validation, build results,
  progress stages and stage failures.
- Shared synchronous application service composition.
- Same-directory temporary output and atomic replacement helper.
- DOCX package smoke validator.

## Components To Reuse

- Existing `parse_markdown`, `ValidationContext` and `validate_document`.
- Existing `compile_document` and renderer-neutral `RenderPlan`.
- Existing `DocxRenderer.render` path-based contract.
- Existing stable `ValidationIssue` ordering and bibliography database reuse.
- Existing CLI diagnostic localization and Typer exit-code behavior.

## Components To Extract

- Move parse/validation/build orchestration out of CLI command bodies into
  application services.
- Move package validation into the focused DOCX package helper.
- Keep temporary lifecycle and atomic replacement in a generic application
  output helper rather than Renderer.

## API / Data Flow Contracts

- Inspect and validation are read-only and never create temporary or production
  output.
- Build uses one parsed document snapshot and one resolved validation context.
- Fatal validation returns all collected issues and never calls Compiler,
  Renderer, package validation or replacement.
- Compiler receives the template and bibliography database from the successful
  validation result.
- Renderer receives only the unique temporary path, never the requested final
  path.
- Package validation runs against the closed temporary DOCX before replacement.
- Finalize performs one atomic replacement and returns the requested output
  path.
- Same source, template and dependency versions produce semantically equivalent
  numbering, references, bookmarks, bibliography order and field instructions.
- No application service reads network state or AI credentials.

## State / Error / Empty / Loading Behavior

- Loading: synchronous progress callbacks observe the five approved stages.
- Empty: inspect returns the parsed empty document; validation reports the
  existing structured empty-document issue; build stops in validation.
- Error: stage failures are typed, include the exact stage, do not expose a
  traceback through CLI, and preserve any old output.
- Disabled: no optional AI, UI or network dependency is required.
- Permission: local filesystem errors are attributed to render or finalize as
  appropriate; no privilege escalation is attempted.

## TDD Requirement

- Strict TDD route.
- Add failing shared-service and progress-order tests before implementation.
- Add parameterized failure tests for parse, validate, compile, render,
  package validation and replacement before production wiring.
- Assert old output bytes survive and same-directory temporary files are
  removed for every failing stage.
- Add repeated-build normalized OOXML semantic comparison before final closure.
- Run focused tests after each behavior group, then the full suite.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_application_services.py`
- `.venv/bin/python -m pytest tests/test_cli.py tests/test_architecture.py`
- `.venv/bin/python -m pytest`
- `.venv/bin/ruff check .`
- `.venv/bin/python -m pip check`
- `.venv/bin/thesisforge inspect examples/bachelor-thesis/thesis.md`
- `.venv/bin/thesisforge validate examples/bachelor-thesis/thesis.md`
- `.venv/bin/thesisforge build examples/bachelor-thesis/thesis.md -o /tmp/thesisforge-007.docx`
- Direct DOCX ZIP integrity, required-part and normalized XML semantic checks.
- python-docx reload and LibreOffice headless conversion of the review DOCX.
- `git diff --check`
- SpecNav development entry, task review checks and CodeGraph claim checks.

## Stop Conditions

- Scope lock mismatch.
- Missing product, architecture, data-flow, or component decision.
- Component duplication that should be extracted.
- Parser, Domain, Validator or Compiler would need DOCX, CLI, UI, AI or network
  dependencies.
- Renderer would need to own the requested final path or atomic replacement.
- A failure path could replace, truncate or delete an existing valid output.
- Temporary output would be created outside the requested target directory.
- Package validation would accept a corrupt ZIP, missing core part or malformed
  core XML.
- Completion would require task-008 example expansion or broad Office
  acceptance.

## Unsafe Assumptions

- A successful `document.save()` does not prove a valid DOCX package.
- A different temporary filesystem still provides atomic replacement semantics.
- Removing a failed temporary file may be skipped because the final output was
  preserved.
- Byte-for-byte DOCX equality is required for deterministic semantic output.
- CLI-only tests prove future adapters can reuse the same behavior.
- A generic `构建失败` message is sufficient without the failing stage.
