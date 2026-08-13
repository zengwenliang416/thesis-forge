# Spec Review: 001-pdf-export-build-contract

## Verdict

approved

## Missing Requirements

- None within the task-owned application slice.
- `PdfPreviewExporter.export(docx_path, pdf_path) -> PdfPreviewArtifact | None`
  exists in `application/pdf_preview.py`; `BuildResult.final_preview` and the
  injectable `ApplicationDependencies.pdf_preview_exporter` carry the typed
  result without changing Parser, Domain, Compiler, RenderPlan or Renderer.
- The LibreOffice exporter uses the existing executable discovery and process
  lifecycle helpers, an isolated user profile, bounded `wait(timeout=...)`,
  temporary conversion output, `%PDF-` plus non-empty validation, and atomic
  replacement of the derived `.preview.pdf`.
- `build_service` invokes the exporter only after the validated DOCX has been
  published. Missing runtime, timeout, invalid output, replacement failure,
  exporter exception, or a disabled exporter returns `final_preview=None`
  without changing DOCX build success.

## Extra Behavior

- No blocking extra behavior was found.
- The core dependency default is deliberately `pdf_preview_exporter=None`;
  runtime adapters opt in separately. This preserves the parent requirement
  that CLI/core builds do not require Office while retaining the injectable
  automatic-preview seam.
- `start_office_process` and `terminate_office_process_tree` are public aliases
  of the existing refresh helpers. This is a small extraction within the
  allowed application surface and avoids duplicating process cleanup.

## Misunderstood Requirements

- None found.
- The implementation truthfully labels only exporter-produced artifacts as
  `engine="libreoffice"` and `label="LibreOffice PDF"`; it does not infer or
  claim WPS provenance.
- A failed preview attempt preserves any prior PDF on disk but returns no ready
  artifact, so the old file is not represented as the current build result.

## Cannot Verify From Diff

- I did not independently repeat the recorded real HUT LibreOffice conversion.
  `development/validation-log.jsonl` records it as
  `attestation: "system-executed"` with a valid 12-page PDF, clean qpdf result,
  and no residual exporter process.
- Cross-platform LibreOffice discovery/process behavior is inherited from the
  existing `office_refresh.py` implementation and covered by unit seams here;
  this review did not execute native Linux or Windows Office processes.
- Git shows `pdf_preview.py` and `test_pdf_preview.py` as untracked, so their
  current complete contents were reviewed in addition to the tracked diff.

## Acceptance Assertions Verified

- `A2` verified for the complete task-owned slice.
  - Current source inspection confirms isolated LibreOffice invocation,
    timeout/process cleanup, PDF signature/size validation, temporary output,
    atomic replacement, and optional typed `BuildResult.final_preview`.
  - I reran
    `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider tests/test_pdf_preview.py tests/test_application_services.py`
    and obtained `83 passed`.
  - The tests directly cover valid publication, missing Office, timeout,
    invalid/missing/empty PDF, replacement failure, previous-PDF preservation,
    exporter exceptions, disabled export, and successful DOCX preservation.

## Required Fixes

- No task 001 fix is required after the current source inspection and focused
  `83 passed` application test run.

## Reviewer Checks

- Focused task tests: `83 passed in 208.41s`.
- Focused Ruff across application and task tests: `All checks passed!`.
- `git diff --check`: passed.
- Reported changed production/test files are all inside `context.json.allowed_files`;
  no task-001 implementation edit was found in adapters, frontend, Tauri,
  Parser, Domain, Compiler, RenderPlan, or Renderer.
