# Quality Review: 003-semantic-roles

## Verdict

approved

The review is limited to the task packet's allowed implementation, test, and
task-artifact paths. The current `spec-review.md` was checked first and is
`approved`. Unrelated dirty worktree changes, including generated change-level
CodeGraph and ledger artifacts, were not used as implementation evidence and
were not modified.

## Separation Of Concerns

- `ParagraphRole` is a closed `Literal` containing semantic names only in
  `src/thesis_forge/core/render_plan.py:66-79`; it carries no Word style IDs,
  OOXML names, or renderer objects. `HeadingInstruction` and
  `ParagraphInstruction` only carry renderer-neutral roles at
  `src/thesis_forge/core/render_plan.py:82-112`.
- Compiler-owned semantic state and stable-ID recognition are isolated in the
  private `_SemanticContext` at `src/thesis_forge/core/compiler.py:554-578`.
  The parser and domain model were not changed. H1 transitions reset unknown
  sections to ordinary body context, while nested headings leave the active
  abstract context unchanged.
- DOCX policy lookup, Heading/Normal base-style selection, and OOXML style
  creation stay in the renderer layer at
  `src/thesis_forge/renderers/docx/renderer.py:74-109` and
  `src/thesis_forge/renderers/docx/styles.py:60-181`.
- The inherited-`em` fix preserves the boundary between conversion-only and
  emitted values. For a partial semantic policy with no `size`,
  `_semantic_word_style()` passes `fallback_size=None` and separately passes
  `em_size_pt`; `apply_paragraph_style()` therefore leaves `size=None` for
  `apply_font()` while using `size_pt=em_size_pt` for `em` indentation,
  spacing, and fixed line spacing (`styles.py:209-290`). This avoids an
  unintended child `w:sz`/`w:szCs`.
- `resolve_role_em_size_points()` resolves Heading-based roles from the
  effective configured Heading level, with body size fallback, and body,
  keyword, and bibliography-entry roles from the effective body/Normal size
  (`styles.py:140-170`). `configure_styles()` applies the same template body
  policy to Normal and Heading policies to the built-in Heading styles
  (`styles.py:347-359`).

## Component Cohesion / Coupling

- `_SemanticContext.role_for()` owns only document-semantic classification:
  stable heading IDs, abstract context lifetime, and constrained paragraph-start
  keyword labels (`compiler.py:554-578`). It does not resolve Word styles or
  write output.
- `resolve_paragraph_style()` is the single role-to-template-policy resolver
  (`styles.py:60-137`). `_semantic_word_style()` selects the correct Heading
  inheritance family for title-like roles, and `ensure_paragraph_style()` plus
  `apply_paragraph_style()` own stable style creation and common translation
  (`styles.py:209-344`). The responsibilities are cohesive and the seams match
  the approved component map.
- Heading-like semantic roles inherit from the corresponding `Heading N`;
  body-like semantic roles inherit from Normal. Partial title policies
  therefore do not silently inherit the wrong body policy.
- The core/compiler and RenderPlan import scans in
  `tests/test_architecture.py:58-73` enforce that core code has no `docx`,
  `lxml`, or renderer dependency and that RenderPlan contains no internal Word
  style identifiers.

## Test Quality

- The requested focused suite passed:
  `.venv/bin/python -m pytest tests/test_compiler.py tests/test_render_plan.py
  tests/test_docx_renderer.py tests/test_architecture.py
  tests/test_acceptance.py -q`
  -> `79 passed in 12.20s`.
- Compiler tests cover role transitions, nested abstract headings, H1 exit,
  Chinese/English keyword recognition, false positives, text and inline-run
  preservation, and repeated compilation
  (`tests/test_compiler.py:512-639`).
- The partial semantic title test saves a DOCX and inspects `word/styles.xml`.
  It proves `w:basedOn="Heading1"`, inherited Heading properties, absence of
  child font/bold/font-family/size/alignment/keep-next emission, the converted
  `1em` spacing, and an explicit false `w:pageBreakBefore`
  (`tests/test_docx_renderer.py:395-443`).
- The partial semantic body test also inspects the saved package, proving
  `w:basedOn="Normal"`, no child `w:rFonts` or `w:sz`, and correct `2em`,
  `0.5em`, and fixed `1.5em` OOXML values (`tests/test_docx_renderer.py:446-482`).
  These assertions directly cover the final inherited-`em` regression rather
  than only testing in-memory Python objects.
- The complete Markdown fragment test binds Chinese/English abstract title,
  body, and keyword roles plus TOC, bibliography, acknowledgements, and
  achievements to stable `w:pStyle` values in saved `document.xml` and
  `styles.xml` (`tests/test_docx_renderer.py:485-579`). Acceptance coverage
  was updated to assert semantic abstract title styles
  (`tests/test_acceptance.py:210-231`).
- Architecture, package, and deterministic repeated-build coverage remain in
  the requested test paths. No full test suite was run because the user
  explicitly prohibited expanding beyond the focused commands.

## Error Handling

- Unsupported paragraph roles fail explicitly in both policy lookup and stable
  style creation (`styles.py:126-137`, `styles.py:319-344`), while a semantic
  role with no effective font size fails rather than guessing a global size
  (`styles.py:154-155`).
- Unknown or unmarked heading IDs remain ordinary headings and body paragraphs
  (`compiler.py:559-578`), matching the task contract and avoiding guessed
  school mappings.
- DOCX boundary failures are converted to `DocxRenderError` with document,
  node-capability, or package context while existing typed errors are
  preserved (`renderer.py:221-258`). No broad exception swallowing or silent
  fallback was introduced.

## Reuse / Duplication

- The task reuses the existing `TextRun`/inline compilation path and the
  existing font and unit helpers. Semantic rendering calls the same
  `ensure_paragraph_style()` and `apply_paragraph_style()` path used by Normal
  and Heading configuration; there is one translator definition in
  `styles.py:209-344`.
- `HEADING_BASE_ROLES` centralizes the Heading inheritance category
  (`styles.py:45-53`), while the compiler's separate heading/body ID maps
  represent distinct source-semantic transitions rather than duplicated DOCX
  formatting logic.
- Stable internal style names are generated from the closed role map in
  `styles.py:31-43`; no template-facing Word style ID or school-specific style
  table was added.

## Complexity Delta

- The implementation adds one closed role type, two small source-semantic
  lookup maps, one compile-scoped context object, and one renderer-side base
  style set. The changed production surface is limited to the four allowed
  modules, and the added state is local to one `compile_document()` invocation
  (`compiler.py:581-590`, `compiler.py:842-864`).
- The final fixes make implicit behavior explicit: nested-heading context is
  level-driven, Word inheritance is represented by real `basedOn` styles, and
  conversion-only `em_size_pt` is not conflated with an emitted fallback size.
- No parser syntax, school profile, UI, persistence, network, AI dependency, or
  downstream TOC/citation/header-footer implementation was introduced in this
  task. The added complexity is proportionate to tasks 3.1-3.7 and does not
  create a speculative abstraction.

## Required Fixes

The approved task has no remaining blocking quality correction after the
inherited-em review fix.

## Independent Evidence

- `.venv/bin/python -m pytest tests/test_compiler.py tests/test_render_plan.py tests/test_docx_renderer.py tests/test_architecture.py tests/test_acceptance.py -q`
  -> `79 passed in 12.20s`.
- `.venv/bin/ruff check .`
  -> `All checks passed!`.
- `git diff --check`
  -> exit `0`, no output.
- SpecNav runtime resolver
  -> `ok:true` for `specnav-development`, `specnav-core`,
  `specnav-prototype`, and `specnav-codegraph`.
- The required post-review handoff contract was not rerun after this file
  write because the user interrupted the prior turn. No handoff result is
  claimed; this is a command-verification limitation, not an implementation
  finding.
