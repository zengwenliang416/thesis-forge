# Task Brief: 008-complete-thesis-acceptance

## Goal

A thesis author can inspect, validate and build one complete bachelor-thesis
example offline, while a reviewer can verify the resulting editable DOCX and
the approved HTML workbench across all required review states.

## Parent Artifacts

- `openspec/changes/build-thesisforge-v1-core/requirements.md`
- `openspec/changes/build-thesisforge-v1-core/acceptance.md`
- `openspec/changes/build-thesisforge-v1-core/acceptance.json`
- `openspec/changes/build-thesisforge-v1-core/design.md`
- `openspec/changes/build-thesisforge-v1-core/spec-map.json`
- `openspec/changes/build-thesisforge-v1-core/component-impact-map.json`
- `openspec/changes/build-thesisforge-v1-core/prototype/handoff.md`
- `openspec/changes/build-thesisforge-v1-core/prototype/decision.json`
- `openspec/changes/build-thesisforge-v1-core/prototype/prototype-manifest.json`
- `openspec/changes/build-thesisforge-v1-core/specs/offline-cli-pipeline/spec.md`
- `openspec/changes/build-thesisforge-v1-core/specs/render-plan-docx/spec.md`
- `openspec/changes/build-thesisforge-v1-core/specs/thesis-markdown-model/spec.md`
- `openspec/specs/ui-design/design.md`
- `openspec/specs/system-architecture/design.md`
- `openspec/specs/component-architecture/design.md`
- `openspec/specs/frontend-backend-data-flow/design.md`

## Vertical Slice

Expand the repository bachelor-thesis example into the complete V1 acceptance
document, invoke the installed CLI offline for inspect, validate and build, and
inspect the generated package for real Word structures and visible thesis
content. Reuse the approved standalone HTML prototype and its browser harness
to record fresh desktop, mobile and required-state evidence. If the complete
example exposes a missing V1 rendering capability, add only the smallest
renderer-neutral instruction and focused DOCX adapter needed to satisfy the
existing acceptance contract.

## In Scope

- Provide one deterministic local bachelor-thesis source with complete cover
  metadata, Chinese and English abstracts, TOC transition, chapter headings,
  one real local figure, one three-line table, one editable equation,
  cross-references, local citations, bibliography, footnote, acknowledgements
  and appendix.
- Keep every source, template, bibliography and image input unchanged during
  inspect, validate and build.
- Add subprocess-level CLI acceptance tests that fail closed if any network
  connection is attempted and run without AI or provider credentials.
- Assert inspect emits the required semantic object inventory and creates no
  output.
- Assert validate exits successfully with no errors.
- Assert build produces a valid DOCX package at the requested output only.
- Verify cover text, abstracts, headings, figure media, three-line table,
  OMML, TOC/SEQ/REF/PAGE/NUMPAGES fields, bookmarks, footnotes, sections,
  headers, footers, citations, bibliography, acknowledgements and appendix
  through package and OOXML assertions.
- Verify repeated builds remain semantically equivalent for numbering,
  references, fields, bookmarks and section structures.
- Add a metadata-driven cover instruction and focused DOCX cover adapter only
  if the RED acceptance test proves visible cover content is absent.
- Run the existing prototype logic harness and fresh browser verification at
  desktop and mobile viewports for populated, loading, empty, error, disabled
  and permission states.
- Record DOCX package, Office-client conversion, PDF inspection and browser
  evidence in the task report and validation ledgers.

## Out Of Scope

- Packaging, installation, release, README consolidation and maintainer
  handoff owned by task 009.
- New Markdown syntax, Template Model fields or school-specific hard-coded
  formatting.
- Word, WPS or LibreOffice automation beyond opening/converting the acceptance
  DOCX and recording sensory evidence.
- A production PySide6 UI, backend service, account system, cloud storage,
  template market or AI feature.
- Byte-for-byte deterministic DOCX archives.
- Changes to the approved prototype design unless verification proves the
  artifact does not satisfy its existing contract.

## Files Allowed

- `examples/bachelor-thesis/thesis.md`
- `examples/bachelor-thesis/references.bib`
- `examples/bachelor-thesis/images/acceptance-architecture.svg`
- `examples/bachelor-thesis/images/acceptance-architecture.png`
- `templates/schools/example-university/2026.yaml`
- `src/thesis_forge/core/render_plan.py`
- `src/thesis_forge/core/compiler.py`
- `src/thesis_forge/renderers/docx/cover.py`
- `src/thesis_forge/renderers/docx/figures.py`
- `src/thesis_forge/renderers/docx/renderer.py`
- `tests/test_acceptance.py`
- `tests/test_compiler.py`
- `tests/test_docx_renderer.py`
- `tests/test_template.py`
- `tests/test_prototype_acceptance.py`
- `openspec/changes/build-thesisforge-v1-core/prototype/evidence/browser-verification.json`
- `openspec/changes/build-thesisforge-v1-core/prototype/evidence/desktop-populated.png`
- `openspec/changes/build-thesisforge-v1-core/prototype/evidence/mobile-preview.png`
- `openspec/changes/build-thesisforge-v1-core/prototype/evidence/mobile-permission.png`

## Interfaces / Seams

- The full example remains ordinary supported Markdown plus YAML front matter,
  local BibTeX and a local PNG asset.
- `inspect`, `validate` and `build` are invoked through the installed
  `thesisforge` console command, not by bypassing the application services.
- Offline enforcement is injected through subprocess `sitecustomize` so any
  socket connection fails the command.
- Acceptance OOXML helpers read closed package parts and normalize semantic
  structures without coupling production code to test-only XML logic.
- If needed, `CoverInstruction` carries only renderer-neutral metadata strings;
  Word paragraph/page-break implementation remains in the DOCX adapter.
- Prototype verification reuses `prototype/logic/harness.js` and
  `prototype/evidence/verify-ui.cjs`.

## Components To Create

- Complete deterministic bachelor-thesis acceptance fixture and real local
  figure asset.
- End-to-end offline CLI and DOCX package acceptance test module.
- Static prototype contract acceptance test module.
- Metadata-driven cover instruction and DOCX cover renderer only if required by
  observed RED evidence.

## Components To Reuse

- Existing application services, CLI, Parser, Validator, Compiler, RenderPlan
  and safe-build lifecycle.
- Existing template selection and example-university template.
- Existing figure, table, equation, field, bookmark, footnote, section,
  header/footer, citation and bibliography implementations.
- Existing DOCX package helpers and XML test conventions.
- Existing approved prototype artifact, logic harness and Playwright verifier.

## Components To Extract

- Keep complete-package XML queries in the new acceptance test rather than
  duplicating focused production helpers.
- If visible cover rendering is missing, extract it into one focused
  `renderers/docx/cover.py` adapter instead of embedding metadata formatting in
  `renderer.py`.
- Do not extract generalized UI or installation infrastructure in this slice.

## API / Data Flow Contracts

- `thesisforge inspect` reads one immutable source snapshot, emits JSON semantic
  inventory and writes no files.
- `thesisforge validate` reads the same local source/template/bibliography/image
  graph, emits no error diagnostics and writes no files.
- `thesisforge build` executes parse -> validate -> compile -> render ->
  package validation -> atomic replacement without network or AI credentials.
- Complete cover metadata remains in `ThesisDocument.metadata`; any cover
  instruction copies plain values into RenderPlan without Word objects.
- The generated DOCX exposes real editable OOXML structures instead of visual
  placeholder text.
- The prototype remains standalone and uses only local HTML/CSS/JavaScript
  assets.

## State / Error / Empty / Loading Behavior

- Loading: prototype shows the approved loading state and build progress stage.
- Empty: prototype shows the approved empty workspace without fabricated thesis
  content.
- Error: prototype shows the approved diagnostic/error state; CLI failures
  retain stable non-zero exits and no traceback.
- Disabled: prototype disables build where the selected state requires it.
- Permission: prototype shows the approved local-file permission guidance.
- Populated: desktop and mobile surfaces expose outline, editor, preview,
  diagnostics, template selection and build controls.

## TDD Requirement

- Strict TDD route.
- Add full-example inventory and offline CLI tests before changing the example.
- Add complete DOCX package assertions before any cover/product repair.
- Preserve focused compiler/renderer tests for each production capability
  introduced by acceptance.
- Run focused tests after each behavior group, then the full suite.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_acceptance.py`
- `.venv/bin/python -m pytest tests/test_prototype_acceptance.py`
- `.venv/bin/python -m pytest tests/test_compiler.py tests/test_docx_renderer.py`
- `.venv/bin/python -m pytest`
- `.venv/bin/ruff check .`
- `.venv/bin/python -m pip check`
- `.venv/bin/thesisforge inspect examples/bachelor-thesis/thesis.md`
- `.venv/bin/thesisforge validate examples/bachelor-thesis/thesis.md`
- `.venv/bin/thesisforge build examples/bachelor-thesis/thesis.md -o /tmp/thesisforge-008.docx`
- Direct ZIP/CRC, package-part and OOXML XPath verification of the review DOCX.
- python-docx reload and LibreOffice headless DOCX-to-PDF conversion.
- PDF metadata/page inspection with `qpdf` or an equivalent installed tool.
- `node openspec/changes/build-thesisforge-v1-core/prototype/logic/harness.js`
- Serve the prototype locally and run
  `prototype/evidence/verify-ui.cjs` with the installed Chrome.
- `git diff --check`
- SpecNav development entry, task review and CodeGraph claim checks.

## Stop Conditions

- Scope lock mismatch.
- Missing product, architecture, data-flow or component decision.
- Complete acceptance would require new Markdown syntax or Template Model
  fields rather than supported V1 behavior.
- Parser or Domain would need DOCX, UI, AI or network dependencies.
- School formatting would need to be hard-coded outside Template Model.
- A generated figure would not be a valid local image asset.
- A package check would accept placeholder text in place of real Word objects.
- Office or browser evidence cannot be reproduced from repository artifacts.
- Completion would require task-009 installation or maintenance scope.

## Unsafe Assumptions

- A section whose role is `cover` necessarily contains visible cover content.
- Successful validation proves every required semantic object is present.
- Successful ZIP/package validation proves required OOXML structures exist.
- A DOCX-to-PDF conversion proves pagination and content are sensible without
  inspecting the rendered PDF.
- Static HTML anchors prove responsive behavior and interactive states without
  a browser run.
- Existing screenshots are fresh evidence for the current artifact.
