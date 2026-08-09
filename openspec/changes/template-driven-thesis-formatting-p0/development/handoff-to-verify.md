# Development Handoff To Verify: template-driven-thesis-formatting-p0

## Implemented Slices

- 001: legacy-compatible typed paragraph policy.
- 002: shared DOCX paragraph-style translation.
- 003: renderer-neutral semantic paragraph roles.
- 004: configurable real Word TOC field and TOC 1-3 styles.
- 005: citation superscript and bibliography presentation.
- 006: page geometry plus first/default/even header/footer variants.
- 007: HUT school template, complete fixture and offline distribution build.
- 008: full regression, current-artifact WPS review and lifecycle closeout.
- User follow-up at commit `f59c81f`: title color, alignment and zero
  indentation are template parameters and render as real Word style
  properties.

## Files Changed

- Typed template and DOCX translation:
  `src/thesis_forge/templates/model.py`,
  `src/thesis_forge/renderers/docx/fonts.py`,
  `src/thesis_forge/renderers/docx/styles.py` and focused OOXML helpers.
- Compiler/RenderPlan semantic-role implementation under
  `src/thesis_forge/core` and the existing DOCX renderer boundary.
- HUT template:
  `templates/schools/hunan-university-of-technology/master-2026.yaml`.
- Complete local fixture under `examples/complete-thesis`.
- Template specification, tests, package-data declarations and native sidecar
  packaging files.
- OpenSpec task reports, reviews, validation/drift ledgers, acceptance matrix,
  CodeGraph evidence and this handoff.

## Requirements Covered

- A1: body and Heading 1-3 font/color/alignment/indentation/spacing/line and
  pagination policy is YAML-driven and serialized to Word styles.
- A2: omitted P0 fields preserve existing template defaults.
- A3: Chinese/English abstracts and keywords use independent semantic styles.
- A4: real TOC field and configurable TOC 1-3 styles/tabs/leaders.
- A5: inline/superscript citations and configurable bibliography hanging
  indentation.
- A6: physical page geometry, document grid, first/default/even
  header/footer relationships, borders and page fields.
- A7: semantic roles resolve before rendering and RenderPlan remains free of
  Word implementation objects.
- A8: school values remain outside renderer constants; core commands are
  offline and deterministic.
- A9: the complete example produces a valid editable DOCX with direct OOXML
  package assertions.
- A10: the current artifact was opened and inspected in WPS Office for macOS.

## Prototype Decisions Implemented

- Approved variant `policy-role-docx-seam-v1`.
- Formatting policy is strongly typed and template-owned.
- Semantic document context is compiler-owned.
- RenderPlan remains renderer-neutral.
- The DOCX renderer owns real Word styles, fields, relationships and OOXML
  translation.
- Parser, domain and core offline commands do not depend on DOCX or AI.

## Components Created / Reused / Extracted

- Reused the single `ParagraphStyleSpec` across body, headings, semantic
  roles, TOC, bibliography and header/footer paragraphs.
- Reused one shared DOCX paragraph-style translator for font slots, color,
  emphasis, alignment, indentation, spacing, pagination and grid controls.
- Added focused color serialization that removes stale Word theme-color
  attributes when an explicit template color is set.
- Reused stable semantic Word style IDs, TOC/SEQ/REF/PAGE fields, bookmarks,
  section relationships and package validators.
- Kept school-specific dimensions, fonts, colors and text in YAML rather than
  adding a second renderer policy path.

## API / Data Flow Changes

- YAML `ParagraphStyleSpec.color` accepts `auto` or six hexadecimal digits;
  `null` means the style does not override inherited color.
- Heading `alignment`, `left_indent`, `right_indent` and
  `first_line_indent` use the existing paragraph-policy contract and may be
  set independently per level.
- Data flow remains:
  `Markdown -> ThesisDocument -> Validation -> Template -> RenderPlan -> DOCX`.
- The Web, macOS and Windows clients continue to use the same versioned
  application-service/HTTP or Tauri adapter contracts.

## Tests Added

- Template model validation for all new fields, defaults, compatibility and
  invalid combinations, including `color`.
- Compiler/RenderPlan tests for semantic-role transitions and architecture
  boundaries.
- Direct `styles.xml`, `document.xml`, `settings.xml`, section relationship,
  header/footer, field, tab, leader, border, indentation and color assertions.
- Complete offline inspect/validate/build, input immutability, determinism and
  two-template semantic-equivalence acceptance tests.
- Wheel/native sidecar package-data and macOS/Windows distribution-contract
  tests.
- Shared frontend unit/E2E, real Python HTTP adapter and Rust protocol tests.

## Local Validation

- Python focused suite: `132 passed`.
- Python full suite: `367 passed`.
- Ruff, `pip check`, package sdist/wheel build, OpenSpec strict validation and
  `git diff --check`: passed.
- Frontend: `53 passed`; typecheck, lint and production build passed.
- Playwright shared suite: `15 passed, 18 skipped` on isolated port `4273`.
- Playwright real Python HTTP adapter: `1 passed`.
- Rust: `11 passed`; fmt and check passed.
- Current DOCX SHA-256:
  `14cc3a07788bae9f1f5d69e27713f8bcc9bd57cca459d366d136eb29571e3325`.
- WPS Office for macOS opened the current 13-page artifact and direct sensory
  evidence is recorded in task 008.
- CodeGraph guard/claims reports are green and task 008 has matched evidence.

## Known Risks

- Microsoft Word was launched but the automated local-file search timed out;
  no Word layout claim is made. WPS satisfies the primary-client criterion.
- LibreOffice lacks the configured Chinese fonts and does not update the TOC;
  it is compatibility evidence only.
- The external volume cannot hard-link Rust incremental-cache files. Cargo
  copies them and all tests/checks pass.
- Port `4173` is owned by an unrelated local process; the unchanged browser
  suite passed on isolated port `4273`.

## Items Requiring Six-Domain Verification

- Re-check A1-A10 evidence references against the current commit and task
  ledgers.
- Inspect Heading 1-3 `w:color`, `w:jc` and `w:ind` properties and confirm the
  HUT values originate only from YAML.
- Review current WPS screenshots for abstracts, heading hierarchy, body,
  figure/table/equation, bibliography, headers and page numbers.
- Treat the Microsoft Word probe with the caveat above; do not infer sensory
  success from LibreOffice.
- Confirm no school values, DOCX imports or raw Word objects crossed into
  Parser, domain, compiler or RenderPlan.
- Re-run focused/full/static/browser/Rust commands where independent replay is
  required.
