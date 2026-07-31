# Task Brief: 006-local-citations-and-bibliography

## Goal

A thesis author can validate local BibTeX citation keys and build deterministic
inline citations plus a referenced-only GB/T 7714-2025 bibliography without
network access or DOCX dependencies in the bibliography subsystem.

## Parent Artifacts

- `openspec/changes/build-thesisforge-v1-core/requirements.md`
- `openspec/changes/build-thesisforge-v1-core/acceptance.md`
- `openspec/changes/build-thesisforge-v1-core/design.md`
- `openspec/changes/build-thesisforge-v1-core/prototype/handoff.md`
- `openspec/changes/build-thesisforge-v1-core/specs/bibliography-citations/spec.md`
- `openspec/changes/build-thesisforge-v1-core/specs/validation-template-resolution/spec.md`
- `openspec/changes/build-thesisforge-v1-core/specs/render-plan-docx/spec.md`

## Vertical Slice

Extend the existing offline `FLOW-VALIDATE` and `FLOW-BUILD` paths from parsed
citations and Front Matter bibliography configuration through a local BibTeX
loader, structured missing-key diagnostics, deterministic formatter output,
Compiler-resolved citation/bibliography instructions and editable DOCX text.
The explicit `::: bibliography` semantic container is a renderer-neutral
placement marker; if it is absent, Compiler appends the referenced-only
bibliography after document content.

## In Scope

- Define renderer-neutral bibliography records, database, loader and formatter
  contracts.
- Parse local BibTeX deterministically without network access or a required
  optional dependency.
- Support the reviewed V1 BibTeX types `article`, `book`, `inproceedings`,
  `mastersthesis` and `phdthesis`.
- Reject malformed entries, duplicate keys, unsupported entry types and missing
  required formatting fields through typed errors.
- Validate every citation key against the loaded local bibliography and return
  `missing-citation` at the citation source line.
- Return `invalid-bibliography` for malformed or unsupported BibTeX data.
- Add renderer-neutral `BibliographyBlock`, `BibliographyInstruction` and
  bibliography entry instructions.
- Compile grouped inline citation text in declared key order using stable
  first-use ordinals.
- Compile all and only cited bibliography records in first-use order.
- Render resolved citation text in body and footnote targets and resolved
  bibliography entries as normal editable DOCX paragraphs.
- Document the BibTeX subset, placement behavior and deterministic
  GB/T 7714-2025 formatting contract.
- Add golden formatter fixtures and focused Parser, Validator, Compiler,
  RenderPlan, DOCX and CLI tests.

## Out Of Scope

- Network DOI lookup, remote CSL downloads or online metadata enrichment.
- Claiming complete GB/T 7714-2025 coverage beyond the documented V1 types and
  golden fixtures.
- Requiring `citeproc-py`; it remains an optional replaceable backend.
- New Template Model fields or citation-layout schema.
- Atomic output, temporary files or preservation of an older valid DOCX; task
  007 owns those behaviors.
- Complete production example and broad Office sensory coverage; task 008 owns
  that completion surface.
- UI, accounts, template marketplace or AI-assisted citation generation.

## Files Allowed

- `src/thesis_forge/bibliography/__init__.py`
- `src/thesis_forge/bibliography/engine.py`
- `src/thesis_forge/bibliography/bibtex.py`
- `src/thesis_forge/bibliography/formatter.py`
- `src/thesis_forge/core/__init__.py`
- `src/thesis_forge/core/model.py`
- `src/thesis_forge/core/parser.py`
- `src/thesis_forge/core/validator.py`
- `src/thesis_forge/core/compiler.py`
- `src/thesis_forge/core/render_plan.py`
- `src/thesis_forge/renderers/docx/renderer.py`
- `src/thesis_forge/renderers/docx/footnotes.py`
- `src/thesis_forge/cli.py`
- `docs/BIBLIOGRAPHY_SPEC.md`
- `docs/MARKDOWN_SPEC.md`
- `tests/fixtures/bibliography/gbt7714-v1.bib`
- `tests/fixtures/bibliography/gbt7714-v1.json`
- `tests/test_architecture.py`
- `tests/test_bibliography.py`
- `tests/test_cli.py`
- `tests/test_compiler.py`
- `tests/test_docx_renderer.py`
- `tests/test_parser.py`
- `tests/test_render_plan.py`
- `tests/test_validator.py`

## Interfaces / Seams

- `BibliographyLoader.load(path) -> BibliographyDatabase` reads local records
  and never formats citations or imports DOCX.
- `CitationFormatter.format_citation(...)` and
  `CitationFormatter.format_bibliography(...)` consume resolved records and
  ordinals without reading files.
- `BibliographyDatabase.records` is keyed by stable citation key.
- `CitationRun.text` contains the resolved inline display result.
- `BibliographyInstruction.entries` contains ordered, resolved, renderer-neutral
  entry text.
- Parser records `BibliographyBlock` placement but never loads BibTeX.
- Validator loads through the bibliography loader only after local path checks.
- Compiler receives an already loaded database and never reads bibliography
  files.
- DOCX Renderer does not parse BibTeX or select citation styles.

## Components To Create

- Typed bibliography records/database and loader errors.
- Deterministic V1 local BibTeX loader.
- Replaceable citation formatter protocol.
- Deterministic GB/T 7714-2025 V1 formatter.
- Bibliography placement block and typed RenderPlan instructions.
- Golden bibliography fixture tests.

## Components To Reuse

- Existing Front Matter `BibliographyConfig`, parsed `Citation` objects and
  source locations.
- Existing `ValidationContext`, local resource path policy and deterministic
  issue sorting.
- Existing Compiler first-use citation ordinal map.
- Existing shared body/footnote inline dispatcher.
- Existing template citation style selection.
- Existing DOCX paragraph and style infrastructure.

## Components To Extract

- Replace the placeholder `BibliographyEngine` with explicit loader and
  formatter contracts.
- Keep BibTeX tokenization/parsing in `bibliography/bibtex.py`.
- Keep GB/T text rules in `bibliography/formatter.py`.
- Keep DOCX paragraph creation in Renderer; no formatting rule may move there.

## API / Data Flow Contracts

- CLI resolves and validates source/template/resource paths before build.
- Validator loads local BibTeX and reports missing keys before Compiler runs.
- CLI passes the validated local database to Compiler.
- Compiler preserves first-use numbering and grouped citation key order.
- The referenced-only bibliography contains each cited key exactly once in
  first-use order.
- A bibliography marker renders the resolved entries at that location; without
  a marker, Compiler appends one instruction after all blocks.
- Same source, BibTeX, template and dependency versions produce identical
  citation text, bibliography order and paragraph text.
- Markdown, template and BibTeX source files remain read-only.

## State / Error / Empty / Loading Behavior

- Loading: synchronous, local and offline.
- Empty: no citations produce no bibliography entries; an empty marker produces
  no fake records.
- Error: missing file, escaped path, malformed BibTeX, duplicate key,
  unsupported type and missing citation key are explicit structured failures.
- Disabled: absent bibliography configuration with no citations creates no
  bibliography behavior.
- Permission: only the requested DOCX output is written.

## TDD Requirement

- Strict TDD route.
- Add failing loader/formatter golden tests before implementation.
- Add failing missing-key validation, Compiler instruction, DOCX output and CLI
  tests before production wiring.
- Run focused tests after each behavior group, then the full suite.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_bibliography.py tests/test_validator.py`
- `.venv/bin/python -m pytest tests/test_parser.py tests/test_compiler.py tests/test_render_plan.py`
- `.venv/bin/python -m pytest tests/test_docx_renderer.py tests/test_cli.py tests/test_architecture.py`
- `.venv/bin/python -m pytest`
- `.venv/bin/ruff check .`
- `.venv/bin/python -m pip check`
- `.venv/bin/thesisforge validate <focused-source>`
- `.venv/bin/thesisforge build <focused-source> -o /tmp/thesisforge-006.docx`
- Direct DOCX ZIP/XML inspection and python-docx reload.
- LibreOffice headless conversion of the focused review DOCX.
- `git diff --check`
- SpecNav development entry, task review checks and CodeGraph claim checks.

## Stop Conditions

- Scope lock mismatch or edits outside the allowed files.
- Parser, Domain or bibliography code would need DOCX, XML, UI, AI or network
  dependencies.
- Renderer would need to read BibTeX, resolve citation keys, assign ordinals or
  select a citation style.
- Validation would permit an unresolved citation to reach build.
- Formatter would claim unsupported GB/T document types as compliant.
- Completing the slice would require atomic-output behavior owned by task 007.
- Golden, direct DOCX or either independent review fails.

## Unsafe Assumptions

- Do not assume `citeproc-py` is installed or available offline.
- Do not assume BibTeX is valid because the file exists.
- Do not assume citation order equals BibTeX file order.
- Do not include uncited records in the referenced-only bibliography.
- Do not silently ignore unknown entry types or missing cited keys.
- Do not treat visible raw `[@key]` text as formatted citation evidence.
