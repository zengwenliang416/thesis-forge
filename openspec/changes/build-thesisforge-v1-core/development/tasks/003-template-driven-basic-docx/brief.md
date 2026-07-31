# Task Brief: 003-template-driven-basic-docx

## Goal

A thesis author can run `thesisforge build` with a resolved school template and
receive an editable DOCX whose page, body and heading layout comes from that
template, while Compiler output remains renderer-neutral and inspectable.

## Parent Artifacts

- `openspec/changes/build-thesisforge-v1-core/requirements.md`
- `openspec/changes/build-thesisforge-v1-core/acceptance.md`
- `openspec/changes/build-thesisforge-v1-core/prototype/handoff.md`

## Vertical Slice

Implement the basic `FLOW-BUILD` path from validated `ThesisDocument` and
resolved `ThesisTemplate`, through deterministic semantic resolution and typed
`RenderPlan` instructions, into a template-driven editable DOCX. Preserve the
generic `RenderNode` compatibility surface for existing consumers.

## In Scope

- Add typed renderer-neutral instructions for heading, paragraph, list, figure,
  table, equation, listing, algorithm and footnote-definition blocks.
- Preserve `RenderNode(kind, payload)` and `RenderPlan.nodes` compatibility
  while preventing new compiler behavior from depending on magic payload keys.
- Resolve chapter context and deterministic chapter-aware figure, table and
  equation labels before rendering.
- Resolve stable bookmark names, reference targets and citation order before
  rendering, with explicit compiler errors for bookmark collisions.
- Bind the resolved template, template source path, page setup, body style,
  heading styles and section policy into `RenderPlan`.
- Split DOCX orchestration from unit conversion, font application, style
  application and package inspection helpers.
- Render template-driven page size, orientation, margins, body font/size,
  alignment, indentation, line spacing, heading font/size/emphasis/spacing and
  heading page-break behavior.
- Render editable basic representations for semantic types whose advanced Word
  objects are owned by later slices.
- Update `thesisforge build` to pass the already validated resolved template
  into Compiler and Renderer.
- Add focused Compiler/RenderPlan tests and direct DOCX package/XML tests.

## Out Of Scope

- Real image relationships, image sizing, caption fields and three-line table
  borders; task 004 owns those capabilities.
- OMML, SEQ, REF, TOC, footnote package parts, multiple Word sections,
  headers/footers and page-number fields; task 005 owns those capabilities.
- BibTeX loading, citation-key validation and formatted bibliography output;
  task 006 owns those capabilities.
- Atomic output replacement and failed-build preservation; task 007 owns those
  capabilities.
- Production UI, network services, accounts or AI-assisted compilation.

## Files Allowed

- `src/thesis_forge/core/__init__.py`
- `src/thesis_forge/core/compiler.py`
- `src/thesis_forge/core/render_plan.py`
- `src/thesis_forge/renderers/docx/__init__.py`
- `src/thesis_forge/renderers/docx/document.py`
- `src/thesis_forge/renderers/docx/fonts.py`
- `src/thesis_forge/renderers/docx/lists.py`
- `src/thesis_forge/renderers/docx/package.py`
- `src/thesis_forge/renderers/docx/renderer.py`
- `src/thesis_forge/renderers/docx/styles.py`
- `src/thesis_forge/renderers/docx/units.py`
- `src/thesis_forge/cli.py`
- `tests/test_architecture.py`
- `tests/test_cli.py`
- `tests/test_compiler.py`
- `tests/test_docx_renderer.py`
- `tests/test_render_plan.py`
- `docs/TEMPLATE_SPEC.md`

## Interfaces / Seams

- `compile_document(document, template=None, template_path=None) -> RenderPlan`
- Typed render instructions expose a stable `kind` and can be converted to a
  compatibility `RenderNode`.
- `RenderPlan.nodes` remains iterable by generic consumers.
- `DocxRenderer.render(plan, output) -> Path`
- DOCX helper modules accept typed template/instruction values and keep
  `python-docx` and OOXML objects inside `renderers/docx/`.

## Components To Create

- Typed render instruction dataclasses and render-plan template binding.
- Compiler semantic-resolution state for counters, bookmarks, references and
  citation order.
- DOCX unit, font, style, document and package inspection helpers.
- Compiler, RenderPlan and DOCX OOXML test suites.

## Components To Reuse

- Existing `ThesisDocument` block and inline dataclasses.
- Existing `ThesisTemplate` and `ValidationContext.template/template_path`.
- Existing Parser, Validator, Typer CLI and `python-docx` dependency.
- Stable semantic IDs from `core/ids.py`.

## Components To Extract

- Length conversion is centralized in `renderers/docx/units.py`.
- East Asian and Latin font application is centralized in
  `renderers/docx/fonts.py`.
- List numbering instances, start values and nesting levels are centralized in
  `renderers/docx/lists.py`.
- Body and heading style application is centralized in
  `renderers/docx/styles.py`.
- DOCX construction and package/XML inspection stay separate from instruction
  dispatch.
- Numbering, bookmark and reference resolution remain Compiler responsibilities
  and are never recalculated by Renderer.

## API / Data Flow Contracts

- Build must complete Parser and fatal validation before Compiler or Renderer.
- CLI passes the exact resolved template from `ValidationContext`; Compiler and
  Renderer do not search for templates.
- Compiler output contains no `docx`, `lxml`, Rich, UI or AI objects.
- Renderer consumes only `RenderPlan` and never imports Parser.
- Same document and template produce identical instruction order, counters,
  bookmark names, reference targets and citation order.
- Source Markdown and template YAML remain read-only; only the requested DOCX
  output is written.

## State / Error / Empty / Loading Behavior

- Loading: all work is synchronous and local with no hidden network access.
- Empty: fatal validation prevents compilation of an empty thesis.
- Error: compiler semantic conflicts use typed exceptions; renderer failures
  propagate without traceback through the CLI command boundary.
- Disabled: advanced Word capabilities remain explicit later-slice behavior,
  not silent fake fields.
- Permission: unreadable source/template failures remain validation/source
  errors; unwritable output paths produce a concise build failure.

## TDD Requirement

- Write or update focused behavior tests before or alongside implementation.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_render_plan.py tests/test_compiler.py tests/test_docx_renderer.py tests/test_cli.py`
- `.venv/bin/python -m pytest`
- `.venv/bin/ruff check .`
- `.venv/bin/python -m pip check`
- `.venv/bin/thesisforge build examples/bachelor-thesis/thesis.md -o /tmp/thesisforge-003.docx`
- Direct ZIP/XML inspection of `/tmp/thesisforge-003.docx`.
- `git diff --check`
- SpecNav development entry, handoff review checks and CodeGraph claim checks.

## Stop Conditions

- Scope lock mismatch.
- Missing product, architecture, data-flow, or component decision.
- Component duplication that should be extracted.
- Parser or Domain would need to import Template, Renderer, DOCX, UI or AI.
- Renderer would need to compute numbering, bookmarks, references or citation
  order.
- Completing the slice would require advanced capabilities owned by tasks
  004-007.

## Unsafe Assumptions

- Do not assume python-docx default styles match the selected school template.
- Do not infer final numbering in Parser or Renderer.
- Do not expose OOXML or python-docx objects through Core public APIs.
- Do not silently accept duplicate bookmark names.
- Do not treat a generic `RenderNode` payload as the source of truth for new
  compiler behavior.
- Do not claim advanced figure/table/equation/reference/section behavior from
  editable fallback text.
