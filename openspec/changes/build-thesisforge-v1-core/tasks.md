## 1. Offline Thesis Inspection

**User outcome:** A contributor can set up the project locally and a thesis author can
run `thesisforge inspect` offline to see every supported V1 semantic object without
creating output files.

- [x] 1.1 A contributor can initialize the repository as Git while preserving all existing scaffold files.
- [x] 1.2 A contributor can create a project-local Python 3.11+ virtual environment and install editable development dependencies.
- [x] 1.3 A contributor can run package and test discovery without AppleDouble `._*`, build output or local environments polluting results.
- [x] 1.4 A contributor can run architecture tests proving that Parser and Domain cannot depend on DOCX, Renderer, UI or AI modules.
- [x] 1.5 A thesis author can inspect lists, footnotes, inline content and bibliography configuration with preserved source locations.
- [x] 1.6 A thesis author receives stable ID-prefix diagnostics without Word implementation details entering the domain.
- [x] 1.7 A thesis author receives deterministic parser behavior from explicit block helpers and state transitions.
- [x] 1.8 A thesis author can inspect parsed lists and footnote definitions and references.
- [x] 1.9 A thesis author can inspect figure, table, equation, algorithm and listing containers, including fenced listing content.
- [x] 1.10 A thesis author can inspect inline cross-reference and citation locations in source order.
- [x] 1.11 A contributor can verify every V1 semantic object and malformed container/front-matter case with parser tests.
- [x] 1.12 A thesis author can consult `docs/MARKDOWN_SPEC.md` for every finalized syntax behavior.
- [x] 1.13 A contributor can reproduce recorded baseline `pytest` and `ruff` results from the project-local environment.

## 2. Actionable Validation

**User outcome:** A thesis author can run `thesisforge validate` and receive complete,
deterministically ordered diagnostics with stable exit behavior.

- [x] 2.1 A contributor can compose validation rules through `ValidationContext` while existing `validate_document(doc)` callers remain compatible.
- [x] 2.2 A thesis author receives structured issues for invalid ID prefixes, missing citations, missing bibliography data and required metadata.
- [x] 2.3 A thesis author receives deterministically ordered issues and documented warning/error exit behavior.
- [x] 2.4 A template maintainer can configure typed heading, caption, numbering, section, header/footer and citation models instead of untyped dictionaries.
- [x] 2.5 A template maintainer receives field-specific errors for unsupported or malformed length units.
- [x] 2.6 A thesis author can select templates by explicit path or metadata template ID.
- [x] 2.7 A contributor can verify invalid units, missing templates and required styles with validator and template tests.
- [x] 2.8 A template maintainer can consult `docs/TEMPLATE_SPEC.md` for every finalized template field.

## 3. Template-Driven Basic DOCX

**User outcome:** A thesis author can select a typed school YAML template and build an
editable DOCX whose basic layout comes entirely from that template.

- [x] 3.1 A contributor can inspect renderer-neutral typed render instructions for every V1 block type.
- [x] 3.2 A contributor can migrate to typed instructions while existing generic `RenderNode` consumers remain compatible.
- [x] 3.3 A thesis author receives deterministic chapter-aware figure, table and equation counters.
- [x] 3.4 A thesis author receives stable bookmark names and explicit collision diagnostics.
- [x] 3.5 A thesis author receives compiled cross-reference and citation instructions before rendering.
- [x] 3.6 A thesis author receives resolved template styles and section policy before rendering starts.
- [x] 3.7 A contributor can verify Compiler and RenderPlan contracts with focused tests.
- [x] 3.8 A contributor can maintain separate DOCX document, style, font, unit and package helper modules.
- [x] 3.9 A thesis author receives template-driven page size, margins, fonts, spacing, indentation and alignment.
- [x] 3.10 A thesis author receives template-driven heading levels, pagination and paragraph behavior.
- [x] 3.11 A contributor can verify page, font, paragraph and heading OOXML structures with direct XML tests.

## 4. Numbered Figures And Tables

**User outcome:** A thesis author can build local images and Markdown tables into
editable, chapter-numbered figures and three-line tables.

- [x] 4.1 A thesis author can render images from validated local paths with template-driven widths.
- [x] 4.2 A thesis author can render figure captions, chapter-aware numbering and bookmarks.
- [x] 4.3 A thesis author can compile Markdown table rows into structured render instructions.
- [x] 4.4 A thesis author can render table objects with template-driven caption placement and three-line borders.
- [x] 4.5 A contributor can verify figure/table numbering, relationships, bookmarks and borders with direct XML tests.

## 5. Equations, References And Page Structure

**User outcome:** A thesis author can build equations, references, footnotes, a table
of contents and page structures as real editable Word objects.

- [x] 5.1 A thesis author can consult the `MathConverter` contract and documented supported LaTeX subset.
- [x] 5.2 A thesis author can render supported equations as editable OMML with numbering and bookmarks.
- [x] 5.3 A contributor can reuse one tested implementation for Word fields and bookmarks.
- [x] 5.4 A thesis author can render SEQ and REF fields for captions and cross-references.
- [x] 5.5 A thesis author can render TOC fields with update-on-open behavior.
- [x] 5.6 A thesis author can render real footnote package parts and references.
- [x] 5.7 A thesis author can render section breaks, headers, footers, PAGE/NUMPAGES fields and page-number format/restart policy.
- [x] 5.8 A contributor can verify OMML, fields, bookmarks, footnotes and sections with focused XML tests.

## 6. Local Citations And Bibliography

**User outcome:** A thesis author can validate local BibTeX citation keys and build
deterministic citations and a GB/T 7714-2025 bibliography offline.

- [x] 6.1 A thesis author can load local BibTeX into normalized bibliography records.
- [x] 6.2 A thesis author receives missing citation-key diagnostics through `ValidationContext`.
- [x] 6.3 A contributor can use deterministic inline-citation and bibliography formatter interfaces.
- [x] 6.4 A thesis author receives GB/T 7714-2025 output locked by golden fixtures and formatter tests.
- [x] 6.5 A contributor can compile citation and bibliography instructions without DOCX dependencies.
- [x] 6.6 A thesis author can render inline citations and bibliography paragraphs from compiled instructions.

## 7. Safe And Repeatable Builds

**User outcome:** A thesis author can repeatedly run all core commands and retain the
previous valid DOCX when a rebuild fails.

- [x] 7.1 A thesis author receives consistent behavior because build, inspect and validation commands use shared application services.
- [x] 7.2 A thesis author can build through temporary output, package validation and atomic replacement of the requested target.
- [x] 7.3 A contributor can prove with failure tests that an existing valid output survives parser, validation, compiler and renderer failures.
- [x] 7.4 A thesis author receives the exact failing build stage while temporary output is cleaned.
- [x] 7.5 A thesis author receives semantically equivalent numbering, references and field structures across repeated builds.

## 8. Complete Thesis Acceptance

**User outcome:** A thesis author can build a complete example thesis that passes
automated package checks and opens successfully in a supported Office client.

- [ ] 8.1 A thesis author can use a bachelor-thesis example covering every required V1 semantic and Word capability.
- [ ] 8.2 A contributor can verify offline `inspect`, `validate` and `build` through end-to-end CLI tests without network or API keys.
- [ ] 8.3 A reviewer can inspect the generated DOCX package through recorded OOXML verification evidence.
- [ ] 8.4 A reviewer can open the generated DOCX in Word, WPS or LibreOffice and consult recorded sensory verification results.
- [ ] 8.5 A reviewer can confirm the approved HTML prototype covers desktop, mobile and all required review states.

## 9. Installation And Maintenance Handoff

**User outcome:** A new contributor can install, test, package and maintain ThesisForge
using repository documentation that matches verified behavior.

- [ ] 9.1 A contributor can reproduce the full `pytest`, `ruff`, package-build and OpenSpec validation suites.
- [ ] 9.2 A contributor can rely on README, architecture, Markdown/template specifications and third-party notes matching implemented behavior.
- [ ] 9.3 A reviewer can inspect final task reports, independent spec reviews, quality reviews, validation ledgers and drift checks.
- [ ] 9.4 A reviewer can verify the SpecNav development handoff contract before six-domain verification starts.
