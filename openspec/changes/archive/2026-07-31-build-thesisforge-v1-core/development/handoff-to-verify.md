# Development Handoff To Verify: build-thesisforge-v1-core

## Implemented Slices

- `001-offline-thesis-inspection`: offline Front Matter, semantic Markdown and
  structured inspect inventory.
- `002-actionable-validation`: structured document, resource, reference,
  bibliography and typed-template diagnostics.
- `003-template-driven-basic-docx`: renderer-neutral RenderPlan and
  template-driven basic DOCX.
- `004-numbered-figures-and-tables`: real drawings, tables, captions,
  numbering and bookmarks.
- `005-equations-references-and-page-structure`: OMML, Word fields, footnotes,
  sections, headers, footers and page numbering.
- `006-local-citations-and-bibliography`: local BibTeX validation, deterministic
  citations and referenced-only bibliography.
- `007-safe-and-repeatable-builds`: reusable application services, package
  validation, temporary output and atomic replacement.
- `008-complete-thesis-acceptance`: complete bachelor-thesis, Office package
  review and approved desktop/mobile prototype states.
- `009-installation-and-maintenance-handoff`: reproducible contributor gate,
  wheel/sdist verification, installed offline CLI and current documentation.

## Files Changed

- Core/domain/compiler: `src/thesis_forge/core/`.
- Application orchestration: `src/thesis_forge/application/` and
  `src/thesis_forge/cli.py`.
- Local bibliography: `src/thesis_forge/bibliography/`.
- Typed templates: `src/thesis_forge/templates/`, `templates/` and package
  `template_data` configured in `pyproject.toml`.
- Focused DOCX adapters: `src/thesis_forge/renderers/docx/`.
- Complete local example: `examples/bachelor-thesis/`.
- Product and maintainer documentation: `README.md`, `docs/`, `Makefile` and
  `scripts/verify_distribution.py`.
- Unit, architecture, package, acceptance, prototype and distribution tests:
  `tests/`.
- SpecNav task packets, reviews, ledgers, CodeGraph evidence and prototype
  evidence under the active change.

## Requirements Covered

- Offline `inspect`, `validate` and `build` without AI credentials or network.
- Renderer-neutral Parser, Domain, Validator, Compiler and RenderPlan
  boundaries.
- Stable IDs, deterministic numbering, bookmarks, references, citations and
  section policies.
- Template-driven school formatting and structured validation.
- Real DOCX drawings, tables, TOC/SEQ/REF/PAGE/NUMPAGES fields, OMML,
  footnotes, sections, headers and footers.
- Safe build output preservation and normalized repeated-build semantics.
- Complete Office/package and approved HTML prototype acceptance.
- Reproducible installation, package build, distribution verification,
  documentation and development evidence handoff.

## Prototype Decisions Implemented

- The approved standalone HTML artifact remains the V1 workbench interaction
  reference across desktop, mobile, populated, loading, empty, error, disabled
  and permission states.
- Production core implementation remains CLI-first and local-first.
- A production PySide6 workbench remains deferred; no prototype-only sample
  state was represented as live backend data.

## Components Created / Reused / Extracted

- Created typed ThesisDocument, ValidationContext, RenderPlan instructions,
  local bibliography objects, application service contracts and package
  validation.
- Reused python-docx for high-level document objects and isolated low-level
  OOXML in focused helpers.
- Extracted ID validation, math conversion, fields, bookmarks, captions,
  figures, tables, footnotes, sections, output replacement and distribution
  verification into cohesive modules.
- Reused one complete local example and package-bundled templates for source,
  acceptance and installed-wheel verification.

## API / Data Flow Changes

- Public CLI remains `thesisforge inspect|validate|build`.
- CLI delegates to `inspect_service`, `validation_service` and `build_service`.
- Build data flow is parse -> validate -> compile -> render temporary DOCX ->
  package validation -> atomic replace.
- Template resolution prefers the source's nearest project `templates/` tree,
  then installed `thesis_forge/template_data`.
- Bibliography and image resources remain local and constrained to allowed
  resource roots.
- Distribution verification installs to a temporary prefix with
  `--no-index --no-deps --ignore-installed`, blocks sockets, runs outside the
  checkout, copies only the active declared runtime dependency closure, runs
  with `python -S`, rejects parent/check-out path leakage and proves the parent
  editable package remains unchanged.

## Tests Added

- Parser, validator, template, RenderPlan, compiler and architecture tests.
- Focused DOCX package/XML tests for real Word structures and failure behavior.
- Local BibTeX golden and citation-order tests.
- Application-stage, atomic replacement, corrupt ZIP and repeated-build tests.
- Complete offline CLI, DOCX package, LibreOffice and prototype acceptance.
- Real wheel/sdist build, package-content, isolated installation and offline
  installed-CLI regression.

## Local Validation

- Python 3.11.11, 3.12.9 and 3.14.4: `make verify` passed `124` tests,
  Ruff, pip check, wheel/sdist build, distribution verification, strict
  OpenSpec and whitespace checks in every environment.
- Wheel contains `51` files and both bundled templates; SHA-256
  `36c308bf7cf4038c26dab254455438c22519793668add8be753b631bce41984e`.
- Sdist contains `86` files including source, docs, examples, tests and
  maintainer scripts; SHA-256
  `faa635eb731f48ec35a384ecad42369911560236231e1438b4c5c951cbc17b6e`.
- Installed-wheel inspect, validate and build passed outside the repository
  with network blocked on all three Python versions, and verification left the
  parent editable installations unchanged. Fifteen active production
  dependency distributions and seven key module origins were proven inside
  the temporary prefix.
- CodeGraph task-009 evidence `ev-ms8ykosi` matched with no blockers; all
  development claims have evidence.

## Known Risks

- The project has no selected license; verified artifacts are not cleared for
  public publication.
- The V1 GB/T 7714-2025 formatter is an explicitly documented supported subset,
  not full coverage of every standard branch.
- The V1 math converter supports a documented LaTeX subset and fails closed on
  unsupported commands.
- LibreOffice headless field expansion differs from interactive Word/WPS
  behavior for TOC and NUMPAGES; real dirty fields and update-on-open settings
  are present.
- DOCX byte hashes may differ while normalized semantic output remains
  equivalent.

## Items Requiring Six-Domain Verification

- Product: verify the complete offline author and contributor outcomes.
- UI/UX: verify the approved standalone prototype at desktop/mobile and all
  required states without treating it as a production backend.
- Architecture: recheck layer boundaries, template ownership and optional AI.
- Data/API: recheck local resource boundaries, CLI/service contracts and error
  exits.
- Quality: rerun tests, Ruff, package/OOXML checks, distribution installation
  and Office evidence.
- Security/operations: recheck offline enforcement, output preservation,
  dependency/publication boundaries and the no-license release blocker.
