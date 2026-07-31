# Acceptance Criteria: build-thesisforge-v1-core

## User-Visible Criteria

- `thesisforge inspect <source>` reports metadata, semantic blocks, IDs, references and citations without writing output files.
- `thesisforge validate <source>` reports all detected issues with stable severity, code, line and target fields.
- `thesisforge validate` exits 0 when there are no errors and non-zero when any error exists; warnings alone do not fail validation.
- `thesisforge build <source> --template <template> -o <output>` creates a DOCX only after fatal validation passes.
- Core commands work with network disabled and without API keys.
- A complete example thesis builds with cover, abstracts, TOC, headings, figure, three-line table, equation, cross-references, citations, bibliography, acknowledgements and appendix.
- Build failures identify the failing stage and do not replace a previously valid output file.
- The generated DOCX opens successfully in at least one of Word, WPS or LibreOffice and remains editable.
- A standalone HTML prototype opens locally and presents the ThesisForge workbench with outline, editor, preview, diagnostics, template selection and build controls.
- The HTML prototype supports desktop and mobile review and exposes populated, loading, empty, error, disabled and permission states.

## System Criteria

- Parser produces `ThesisDocument` and never imports `docx`, `lxml`, Renderer or AI modules.
- Domain Model contains no Word/OOXML implementation objects.
- Compiler resolves numbering, bookmarks, references, citations and section policy before rendering.
- RenderPlan is renderer-neutral and behavior-testable.
- School fonts, sizes, margins, spacing, captions, numbering and page policy come from Template Model.
- Figure/table/equation numbering is deterministic and chapter-aware where the template requests it.
- TOC, SEQ, REF, Bookmark, PAGE/NUMPAGES and OMML are real OOXML/Word objects.
- Footnotes, sections, headers and footers use DOCX package structures rather than visual text simulation.
- Bibliography loading and citation formatting are local and deterministic.
- AI packages are optional and are not imported by inspect, validate or build.

## Data Criteria

- Every referencable object has a unique stable ID using an approved prefix.
- Duplicate IDs, missing reference targets, missing images and missing citation keys produce errors.
- Source locations remain attached to parsed objects and diagnostics.
- Template YAML rejects invalid values and explicit-length fields without supported units.
- Input Markdown, YAML, BibTeX and image assets are never mutated by core commands.
- The output path is the only production write target; temporary output is cleaned on failure.
- Same input, template and dependency versions produce semantically equivalent numbering, references and OOXML fields.

## Component Criteria

- Reusable components, hooks, utilities, or services named in
  `component-impact-map.json` are extracted instead of duplicated.
- Parser, Validator, Compiler, Template, Bibliography and Renderer dependencies comply with the foundation component architecture.
- OOXML helpers have focused tests that inspect XML structure, not only file existence.
- Public `__init__.py` exports expose stable APIs and do not leak private XML helpers.

## Verification Surfaces

- Facticity: compare implementation against README, AGENTS, Markdown/Template specs and this requirements packet.
- Static: run `ruff check .`, architecture import checks and package/build validation.
- Unit: parser, model, validator, template, numbering, bibliography and OOXML helper tests.
- Redteam: malformed YAML/Markdown, duplicate IDs, path escapes, invalid units, missing assets, oversized inputs and malicious XML/resource cases.
- E2E: build the full example and inspect the DOCX zip/package parts and field XML.
- Sensory: review the HTML prototype at desktop/mobile sizes, then open the generated DOCX in Word/WPS/LibreOffice and review pagination, typography, captions, tables, equations, references and TOC.

## Unresolved Gaps

None.
