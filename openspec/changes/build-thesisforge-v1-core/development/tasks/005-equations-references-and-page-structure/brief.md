# Task Brief: 005-equations-references-and-page-structure

## Goal

A thesis author can build an editable DOCX whose supported equations,
cross-references, captions, table of contents, footnotes, sections, headers,
footers and page numbers are real Word/OOXML objects driven by Compiler-resolved
semantics and Template Model policy.

## Parent Artifacts

- `openspec/changes/build-thesisforge-v1-core/requirements.md`
- `openspec/changes/build-thesisforge-v1-core/acceptance.md`
- `openspec/changes/build-thesisforge-v1-core/design.md`
- `openspec/changes/build-thesisforge-v1-core/prototype/handoff.md`

## Vertical Slice

Extend the existing offline `FLOW-BUILD` path from Compiler-resolved equation,
reference, footnote and section instructions into editable OMML, Word fields
and DOCX package parts. The generated package must expose each advanced
capability for direct XML and relationship verification, and unsupported math
must fail explicitly through the existing build error boundary.

## In Scope

- Define a renderer-neutral, replaceable `MathConverter` contract and document
  the exact V1 supported LaTeX subset.
- Convert supported identifiers, numbers, operators, parentheses, subscript,
  superscript, fractions, sums, Greek symbols and basic functions to editable
  OMML.
- Fail unsupported or malformed LaTeX explicitly without plain-text or image
  fallback.
- Render equation numbering and Compiler-supplied bookmarks around real OMML.
- Centralize tested complex Word field construction and reuse the existing
  bookmark helper.
- Replace static figure/table caption labels with `SEQ` fields while preserving
  Compiler-resolved chapter-aware display text.
- Replace static cross-reference text with `REF` fields targeting
  Compiler-supplied bookmarks.
- Add a TOC field for configured heading levels and set update-on-open in
  document settings.
- Create real `word/footnotes.xml`, content-type/relationship entries,
  `w:footnote` definitions and body `w:footnoteReference` runs.
- Materialize cover, front-matter and main section policies as real section
  breaks, header/footer parts and relationships.
- Render `PAGE` and `NUMPAGES` fields plus `w:pgNumType` format/restart policy.
- Add focused Compiler/RenderPlan tests and direct DOCX ZIP/XML tests for every
  advanced object.

## Out Of Scope

- New Markdown syntax, Parser changes or Domain Model Word implementation
  details.
- New Template Model fields or template YAML schema changes.
- Bibliography loading, citation formatting or bibliography output; task 006
  owns those capabilities.
- Temporary output, package smoke validation and atomic replacement; task 007
  owns those capabilities.
- Full production example completion and broad red-team/sensory matrix beyond
  this slice; later tasks own those completion surfaces.
- Production UI, network services, accounts or AI-assisted compilation.
- A complete TeX engine or unsupported LaTeX compatibility fallback.

## Files Allowed

- `src/thesis_forge/core/__init__.py`
- `src/thesis_forge/core/compiler.py`
- `src/thesis_forge/core/math.py`
- `src/thesis_forge/core/render_plan.py`
- `src/thesis_forge/renderers/docx/__init__.py`
- `src/thesis_forge/renderers/docx/bookmarks.py`
- `src/thesis_forge/renderers/docx/captions.py`
- `src/thesis_forge/renderers/docx/equations.py`
- `src/thesis_forge/renderers/docx/errors.py`
- `src/thesis_forge/renderers/docx/fields.py`
- `src/thesis_forge/renderers/docx/figures.py`
- `src/thesis_forge/renderers/docx/footnotes.py`
- `src/thesis_forge/renderers/docx/inlines.py`
- `src/thesis_forge/renderers/docx/renderer.py`
- `src/thesis_forge/renderers/docx/sections.py`
- `src/thesis_forge/renderers/docx/tables.py`
- `src/thesis_forge/cli.py`
- `docs/MATH_SPEC.md`
- `docs/TEMPLATE_SPEC.md`
- `tests/test_architecture.py`
- `tests/test_cli.py`
- `tests/test_compiler.py`
- `tests/test_docx_renderer.py`
- `tests/test_math.py`
- `tests/test_render_plan.py`

## Interfaces / Seams

- `MathConverter.convert(latex: str) -> MathExpression` is renderer-neutral;
  its output contains semantic math nodes rather than DOCX or XML objects.
- `EquationInstruction` continues to carry resolved chapter, number, label and
  bookmark values supplied by Compiler.
- `ReferenceRun` continues to carry the exact Compiler-supplied target bookmark
  and fallback display text.
- Figure/table caption helpers receive typed instructions and add `SEQ` fields;
  they do not recalculate numbering or generate bookmark names.
- Word field helpers create complete begin/instruction/separate/result/end
  structures and are reused by REF, SEQ, TOC, PAGE and NUMPAGES.
- Footnote rendering consumes Compiler-resolved numeric footnote IDs and typed
  definitions/references.
- Section rendering consumes only `RenderPlan.section_policy` and template page
  values; it does not load YAML or infer school policy.

## Components To Create

- Renderer-neutral math expression nodes and `MathConverter` protocol.
- Deterministic V1 LaTeX subset converter.
- DOCX OMML equation renderer.
- Shared complex Word field helper.
- DOCX footnote package-part manager.
- Shared typed inline dispatcher for body and footnote targets.
- DOCX section/header/footer/page-number policy helper.
- Typed DOCX capability error boundary.
- Direct package/XML regression tests for math, fields, footnotes and sections.

## Components To Reuse

- Existing `Equation`, `CrossReference`, `FootnoteDefinition`,
  `FootnoteReference` and stable semantic IDs.
- Existing Compiler chapter numbering, bookmark naming, collision detection and
  resolved reference targets.
- Existing `EquationSpec`, `SectionsSpec`, `SectionSpec`,
  `HeaderFooterSpec` and `PageNumberSpec`.
- Existing `bookmarks.py`, caption formatting, document creation, font/style
  and package inspection helpers.
- Existing CLI build error boundary.

## Components To Extract

- All complex field XML is centralized in `renderers/docx/fields.py`.
- All OMML construction is centralized in `renderers/docx/equations.py`.
- All footnote package mutations are centralized in
  `renderers/docx/footnotes.py`.
- Typed inline dispatch is centralized in `renderers/docx/inlines.py`.
- All section/header/footer/page-number XML is centralized in
  `renderers/docx/sections.py`.
- Math parsing remains renderer-neutral in `core/math.py`.
- `renderer.py` remains orchestration-only and never parses LaTeX or Markdown.

## API / Data Flow Contracts

- Build completes Parser and fatal validation before Compiler or Renderer.
- Compiler resolves object numbers, labels, bookmarks, reference targets,
  footnote IDs and section-role transitions before rendering.
- Renderer consumes only typed RenderPlan instructions and selected template
  values.
- Supported math becomes OMML; unsupported math raises a typed error and does
  not silently emit text, PNG or partial OMML.
- `SEQ` and `REF` field result text matches Compiler-resolved deterministic
  labels while the instruction remains editable/updatable in Word.
- TOC, PAGE and NUMPAGES use complex Word fields and document settings request
  field updates on open.
- Footnote IDs are stable positive integers; reserved separator footnotes use
  Word's required negative IDs.
- Section breaks preserve template page size/margins and map start, header,
  footer, page-number format and restart values exactly.
- Same source, template and dependency versions produce semantically equivalent
  OMML, field instructions, bookmark targets, footnote IDs and section policy.
- Source Markdown, template YAML and assets remain read-only.

## State / Error / Empty / Loading Behavior

- Loading: compilation and rendering remain synchronous, local and offline.
- Empty: absent equations, references, footnotes or section policies create no
  fake advanced objects.
- Error: unsupported/malformed math or invalid field/bookmark input fails
  explicitly through a typed render/build error.
- Disabled: an omitted initial section role creates no object; a later disabled
  header/footer creates an empty non-inheriting part when needed to prevent
  prior visible content or fields from leaking forward; `format: none` creates
  no PAGE/NUMPAGES field.
- Permission: this slice writes only the requested DOCX output and does not add
  external or network writes.

## TDD Requirement

- TDD route is strict.
- Add focused failing math, Compiler and DOCX XML tests and observe the expected
  RED state before production-code changes.
- Run focused tests after each behavior group, then the full regression suite.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_math.py tests/test_compiler.py tests/test_render_plan.py tests/test_docx_renderer.py`
- `.venv/bin/python -m pytest`
- `.venv/bin/ruff check .`
- `.venv/bin/python -m pip check`
- `.venv/bin/thesisforge build examples/bachelor-thesis/thesis.md -o /tmp/thesisforge-005.docx`
- Direct ZIP/XML inspection of `/tmp/thesisforge-005.docx`.
- python-docx reload and LibreOffice headless conversion of a focused review
  document.
- `git diff --check`
- SpecNav development entry, task review checks and CodeGraph claim checks.

## Stop Conditions

- Scope lock mismatch or edits outside the allowed files.
- Parser or Domain would need to import Template, Renderer, DOCX, XML, UI or AI.
- Renderer would need to parse Markdown, calculate numbers, resolve references
  or generate bookmark names.
- Unsupported math would be silently emitted as text, image or partial OOXML.
- A Word capability would be simulated visually instead of represented by real
  package/XML structures.
- Completing the slice would require bibliography or atomic-output behavior
  owned by tasks 006-007.
- Direct XML tests or either independent review fails.

## Unsafe Assumptions

- Do not assume python-docx supports OMML, footnotes or all section policy
  through public high-level APIs.
- Do not assume a visible number proves that a SEQ, REF, PAGE or NUMPAGES field
  exists.
- Do not assume a footer paragraph proves that a header/footer relationship and
  package part exist.
- Do not assume Word, WPS and LibreOffice update fields identically.
- Do not assume arbitrary LaTeX is safe to accept in the V1 converter.
- Do not create a second bookmark implementation instead of extending the
  existing tested helper.
