# Task Report: 008-complete-thesis-acceptance

## Status

DONE_WITH_CONCERNS

## Files Changed

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

## What Changed

- Expanded the bachelor-thesis example into a deterministic local acceptance
  document containing cover metadata, Chinese and English abstracts, TOC,
  headings, lists, a real figure, a three-line table, OMML equation,
  cross-references, algorithm, listing, footnote, local citations,
  bibliography, acknowledgements and appendix.
- Added renderer-neutral `CoverInstruction` compilation from front matter and
  a focused DOCX cover adapter. School section, header, footer and page-number
  behavior remains template-driven.
- Enabled the example-school section policy so the complete output contains
  real cover, front-matter and main sections with editable Word fields.
- Prevented figure paragraphs from inheriting fixed body line spacing, which
  previously clipped the acceptance image in LibreOffice.
- Rendered algorithm and listing bodies with left alignment and automatic
  single line spacing so preformatted content is not stretched by justified
  body formatting.
- Added subprocess-level offline CLI acceptance, complete package/OOXML
  assertions, repeated-build semantic checks and static prototype acceptance.
- Refreshed Chrome evidence for desktop, mobile, populated, loading, empty,
  error, disabled and permission states.

## TDD Evidence

- Initial acceptance tests failed because the example lacked the required local
  image, footnote and complete semantic inventory.
- The complete build then exposed missing header/footer parts because the
  example template did not configure the already-supported section policy.
- A focused cover test proved the cover section contained no visible metadata
  before `CoverInstruction` and the DOCX cover adapter were added.
- LibreOffice page rendering exposed a clipped figure caused by inherited
  fixed line spacing. The XML regression test failed before the drawing
  paragraph override and passed after it.
- Visual review exposed unsupported emphasis/code markers in the example and
  stretched algorithm/listing bodies. The fixture and focused paragraph-format
  assertions were corrected before final verification.
- Independent quality review found that the university and thesis title used
  `Heading 1`, which could add cover text to an updated TOC. A focused XML test
  reproduced the issue, the cover adapter was changed to ordinary centered
  paragraphs, and the complete acceptance test now proves cover text is absent
  from the Heading set while real chapter headings remain present.
- Final focused acceptance/compiler/renderer/template group: `45 passed`.
- Final full suite: `123 passed`.

## Verification Commands

- `SPECNAV_CHANGE=build-thesisforge-v1-core OPENSPEC_TELEMETRY=0 node .../development-contract.js --mode entry --json`
  returned `ok:true`.
- `.venv/bin/python -m pytest` returned `123 passed in 5.65s`.
- `.venv/bin/ruff check .` returned `All checks passed!`.
- `.venv/bin/python -m pip check` returned `No broken requirements found`.
- `git diff --check` returned no whitespace errors.
- Offline `thesisforge inspect`, `validate` and `build` completed with provider
  credentials removed and proxy variables disabled.
- The final review-fix DOCX is `187059` bytes with SHA-256
  `244f52abac221d56dd73bd0ef717ca93614d1c7f9044e4e2a877a06cf9b3eeb9`.
- DOCX validation found `23` package parts, one media part, two header parts,
  two footer parts, real TOC/SEQ/REF/PAGE/NUMPAGES fields, `23` bookmarks,
  three sections, one drawing, one table, one OMML object and one footnote
  reference. `python-docx` reloaded `67` paragraphs and one table.
- LibreOffice `26.2.3.2` converted the final DOCX to a `5`-page A4 PDF.
  `qpdf --check` reported no syntax or stream errors. The final review-fix PDF
  SHA-256 is
  `7614f36b5f00bada4b92ffa50901e880ab3a010598a9810e49943fd2da036acf`.
- Fresh page-image review confirmed visible cover, abstracts, full figure,
  three-line table, equation, citations, bibliography, acknowledgements and
  appendix without clipping or overflow.
- `node .../prototype/logic/harness.js` returned `ok:true` for all six safe
  build cases.
- Fresh Chrome verification returned `ok:true` for desktop width `1440`,
  mobile width `390`, all four mobile panels and all six review states.
- Final CodeGraph evidence `ev-ms8vslgo` matched the cover Heading review fix
  with no blockers; all eight development claims are verified.
- Direct Heading XML inspection returned the real thesis headings and excluded
  the cover university/title strings.

## Concerns

- LibreOffice headless conversion updates PAGE and NUMPAGES fields across the
  restarted sections, but reports `7` logical pages in NUMPAGES while the
  exported PDF contains `5` physical pages. The source DOCX contains real
  dirty fields and `w:updateFields=true`; no static page total is substituted.
- LibreOffice headless conversion leaves the TOC field unexpanded. The DOCX
  contains a real dirty TOC field and requests field updates when opened.
- These Office-client field-update differences require independent review
  adjudication before task completion.

## Scope Deviations

- The example-school template was added to the allowlist after the RED
  acceptance build proved its existing section fields had to be enabled.
- `figures.py` was added to the allowlist after sensory verification exposed
  LibreOffice clipping caused by inherited fixed line spacing.
- No new Markdown syntax or Template Model field was introduced.

## Follow-up Needed

- Independent spec and quality reviews must decide whether the LibreOffice
  NUMPAGES/TOC update behavior blocks acceptance or is a documented
  client-specific limitation of otherwise real Word fields.
- Task `009-installation-and-maintenance-handoff` remains out of scope.

## Adjudication

Both independent reviewers approved the final checkout after the cover Heading
regression was fixed. The LibreOffice field-update observations are documented
as non-blocking client differences. Tasks `8.1` through `8.5` may be closed;
task 009 remains the only downstream development slice.
