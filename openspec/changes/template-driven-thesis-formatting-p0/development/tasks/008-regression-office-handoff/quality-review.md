# Quality Review: 008-regression-office-handoff

## Verdict

approved

## Separation Of Concerns

- `ParagraphStyleSpec.color` is a generic paragraph-style input alongside font,
  size, alignment and indentation. The template model remains free of
  `python-docx`, OOXML tags and school-specific behavior.
- `apply_paragraph_style()` passes the typed value through the existing shared
  paragraph translator. Only the DOCX font adapter creates or edits `w:color`,
  so Word implementation details remain inside the renderer boundary.
- HUT-specific black text, left alignment and zero indentation are declared in
  `master-2026.yaml`. A source search found no HUT name, template id or school
  formatting constant under the renderer, core or template-model packages.
- The post-verification production correction is explicitly recorded as a
  constrained drift from baseline `f59c81f`; it does not cross the
  `Template Model -> RenderPlan -> DOCX Renderer` architecture seam.

## Component Cohesion / Coupling

- `_apply_color()` has one responsibility: serialize an explicit color and
  remove stale `themeColor`, `themeTint` and `themeShade` attributes from the
  same Word property.
- Both paragraph styles and concrete paragraph runs reuse `apply_font()`;
  headings, body and semantic roles do not introduce parallel color paths.
- Heading alignment and indentation reuse the existing
  `ParagraphStyleSpec`/`apply_paragraph_style()` contract. There is no
  Heading1-3 special case in production Python.
- The only low-level coupling is the existing localized use of
  `Font._element` inside the DOCX adapter. It is contained, directly tested and
  does not leak into compiler or domain components.

## Test Quality

- Model tests cover `auto`, upper- and lower-case six-digit hexadecimal input,
  plus invalid prefixes, lengths, digits and names.
- Renderer tests cover body `auto`, lowercase heading input `abcdef`,
  normalization to OOXML `ABCDEF` and removal of all three Word theme-color
  attributes from the built-in Heading1 style.
- Complete acceptance tests inspect the generated HUT `styles.xml` and require
  Heading1-3 to contain `w:color="000000"`, no `themeColor`, `w:jc="left"` and
  `w:ind` values `left/right/firstLine="0"`. Separate assertions verify that
  these values originate from the HUT template model.
- The refreshed system-executed focused suite passed `132` tests in `14.81s`
  and the full suite passed `367` tests in `39.45s` after the lowercase
  serialization assertion was added. Independent review also reran the changed
  renderer test with cache and bytecode writes disabled: `1 passed in 0.45s`.
- The append-only validation log contains current-commit system-executed
  evidence for `132` focused tests, `367` full tests, Ruff, package build,
  `pip check`, strict OpenSpec validation, frontend checks, isolated-port
  Playwright, real HTTP Playwright, Rust checks and `git diff --check`.
- Historical browser environment failures are retained and linked to exact
  later passing evidence rather than being deleted or silently reclassified.

## Error Handling

- Pydantic rejects malformed color values at the template boundary before DOCX
  generation. No broad exception handler or silent fallback was introduced.
- `color=None` intentionally preserves inherited output semantics, while
  `auto` and explicit hexadecimal values produce deterministic Word
  properties.
- Existing validation continues to handle alignment enums and conflicting
  indentation inputs; explicit zero values are valid and serialize as zero
  rather than being mistaken for missing configuration.

## Reuse / Duplication

- The change extends the existing shared font and paragraph translators rather
  than adding school, heading or semantic-role formatting branches.
- Theme cleanup exists in one helper and is reused for style-level and
  run-level application.
- Repeated `color: "000000"` entries in the HUT YAML are intentional explicit
  policy for independently configurable semantic roles, not duplicated
  renderer logic.

## Complexity Delta

- Production complexity is small: one short color helper, one optional
  translator argument and one validated model field. No new module, loop
  nesting, state machine or cross-layer dependency was added.
- The current DOCX SHA-256
  `14cc3a07788bae9f1f5d69e27713f8bcc9bd57cca459d366d136eb29571e3325`
  was independently inspected. Heading1-3 each contain black explicit color,
  no theme attributes, left alignment and three zero-indent properties.
- WPS evidence for the same byte-identical artifact shows editable black,
  flush-left Heading1-3, distinct body indentation, native navigation,
  figures, tables, equations, bibliography, headers and page numbers.
- WPS `引用 -> 更新目录` updated the current artifact from `1199` to `1299`
  words. `wps-current-toc-updated.png` directly shows hierarchical entries,
  dot leaders and right-aligned page numbers; LibreOffice remains supplemental
  compatibility evidence only.

## Required Fixes

- No blocking production-code, architecture or test-quality fix is required
  for this quality verdict.
- Preserve the current evidence linkage in final handoff: the TOC claim should
  reference the current `1299`-word WPS screenshot, and lowercase color
  normalization should reference the `abcdef -> ABCDEF` renderer assertion and
  refreshed focused/full test logs.
- This approval covers quality only. The controller must still replace the
  remaining task ledger states and obtain development handoff contract
  `ok:true` before claiming lifecycle completion.
