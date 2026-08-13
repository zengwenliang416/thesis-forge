# Quality Review: 001-pdf-export-build-contract

## Verdict

approved

## Separation Of Concerns

- Office conversion is isolated in `application/pdf_preview.py`; application
  orchestration only consumes the `PdfPreviewExporter` protocol and typed
  artifact.
- The export runs after successful DOCX publication. Parser, Domain, Compiler,
  RenderPlan and DOCX Renderer remain unaware of PDF, subprocesses and viewers.
- Runtime opt-in is outside this task, while the core/CLI dependency default
  stays disabled, preserving the offline build boundary.

## Component Cohesion / Coupling

- `LibreOfficePdfPreviewExporter` owns one cohesive flow: discover, convert into
  a temporary directory, validate, atomically replace, and return metadata.
- Coupling to Office process management is narrow and reused through
  `start_office_process` and `terminate_office_process_tree`; no second process
  lifecycle implementation was introduced.
- `BuildResult.final_preview` and `ApplicationDependencies.pdf_preview_exporter`
  are small typed seams rather than path- or engine-specific conditionals
  spread through `build_service`.

## Test Quality

- `tests/test_pdf_preview.py` directly covers signature validation, successful
  atomic publication, missing executable, conversion exceptions, timeout
  cleanup, invalid output, replacement failure, and preservation of an older
  PDF.
- `tests/test_application_services.py` verifies exporter ordering after DOCX
  publication, the exact derived path, returned metadata, disabled behavior,
  and non-fatal `None`/exception results while revalidating the DOCX package.
- I independently reran the two task test paths and obtained `83 passed`.
  The tests use injected runners/processes/replacers and therefore exercise the
  failure contract deterministically.

## Error Handling

- Export integration is explicitly best-effort at both the exporter and
  application boundary. Exceptions cannot downgrade a published DOCX build.
- Temporary directories clean converted output and isolated profiles; the
  existing process helper is called in `finally`, including timeout paths.
- The broad catches are justified at this optional integration boundary and
  return the typed absence state rather than leaking third-party exceptions.

## Reuse / Duplication

- Executable discovery, Office process startup/termination, and atomic output
  replacement reuse existing application helpers.
- PDF validation and derived-path logic are centralized in
  `application/pdf_preview.py`; tests and services do not duplicate the rules.
- The `file_name` property is a compatibility convenience over the artifact's
  canonical `name`; it does not create a second metadata representation.

## Complexity Delta

- The production delta is bounded: one focused 143-line module, one optional
  dependency field, one result field, and a short post-publication integration
  block.
- Control flow remains linear and injection seams keep process, replacement,
  and application tests small. No immediate extraction beyond the reused
  Office helpers is warranted.
- The duplicated defensive catch at exporter and service boundaries is
  intentional defense in depth for an optional third-party integration, not a
  competing behavior path.

## Required Fixes

- No task 001 quality fix is required; the optional exporter boundary,
  failure isolation, and focused test coverage are acceptable as reviewed.

## Reviewer Checks

- Task tests: `83 passed`.
- Focused Ruff: passed.
- `git diff --check`: passed.
- Current task-owned diff and untracked files remain within the allowlist.
