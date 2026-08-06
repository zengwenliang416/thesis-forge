# Quality Review: 004-toc-styles

## Verdict

approved

The task packet, allowed implementation diff and tests were reviewed after
confirming `spec-review.md` was `approved`. The quality review is limited to
the task 004 implementation and test paths; unrelated dirty change-level
SpecNav artifacts were not used as implementation evidence or modified.

## Separation Of Concerns

- `TocLevelSpec` remains a renderer-neutral `ParagraphStyleSpec` extension
  containing only policy values, defaults and validation
  (`src/thesis_forge/templates/model.py:192-209`). It contains no Word style
  IDs, `w:*` names, `docx` objects or OOXML conversion.
- Stable package style names and the six Word leader tokens are owned by the
  DOCX renderer (`src/thesis_forge/renderers/docx/styles.py:58-71`).
  `configure_toc_styles()` creates/updates `TOC1`-`TOC3` only when
  `template.toc` exists (`styles.py:405-410`), so the template model does not
  leak renderer details.
- The existing TOC field emission remains in the renderer and the field helper
  was not changed by the allowed diff (`renderer.py:179-190`,
  `fields.py:33-77`). The implementation therefore preserves the
  `begin/instr/separate/end` complex field instead of replacing it with static
  entries.

## Component Cohesion / Coupling

- `configure_toc_styles()` owns TOC style resolution, effective size
  selection, printable-width fallback and right-tab application
  (`styles.py:405-452`). `_set_right_tab()` is a focused OOXML seam rather
  than a second paragraph-style translator.
- Common fonts, indentation, spacing and line-spacing conversion reuse
  `apply_paragraph_style()` (`styles.py:226-323, 436-441`). `em` tab positions
  use the effective TOC-level size with the body size as fallback
  (`styles.py:430-447`), avoiding a global 12pt assumption.
- The default tab derives from the active document section's page width minus
  left and right margins and has no school-specific constant
  (`styles.py:393-402`). Style IDs are confined to the renderer, while
  `TocSpec` remains a level 1-3 policy contract.

## Test Quality

- The requested focused suite passed:
  `.venv/bin/python -m pytest tests/test_template.py
  tests/test_docx_renderer.py -k 'toc or style' -q`
  -> `34 passed, 61 deselected in 6.20s`.
- Tests directly inspect generated `word/styles.xml` for stable `TOC1`-`TOC3`
  IDs, `w:basedOn`, indentation, spacing, right tabs, positions and leaders
  (`tests/test_docx_renderer.py:396-532`).
- All six leader policies are parameterized and checked against their Word
  tokens (`tests/test_docx_renderer.py:535-569`), and the effective-size
  `10em` tab conversion is asserted in package XML
  (`tests/test_docx_renderer.py:572-592`).
- The same focused test reads `word/document.xml` and
  `word/settings.xml`, asserting the real TOC instruction, `begin/separate/end`,
  dirty state and `w:updateFields=true` (`tests/test_docx_renderer.py:430-443`).
  The legacy `toc=None` case asserts no TOC style override while preserving the
  real field (`tests/test_docx_renderer.py:595-616`).
- Template tests cover the zero first-line default, invalid/non-positive tab
  paths and rejection of a fourth TOC level
  (`tests/test_template.py:805-879`). The generated-package assertions prove
  the normal path has one right tab; `_set_right_tab()` also explicitly removes
  existing right tabs before appending the replacement
  (`styles.py:370-390`). A dedicated reapplication/idempotence fixture would
  strengthen this seam, but no blocking test gap or behavioral defect was
  found.

## Error Handling

- Invalid `page_number_tab` values are rejected at template validation with a
  field-specific path and a positive-value requirement
  (`model.py:201-209`; `tests/test_template.py:813-845`).
- Unsupported fourth-level input is rejected by the closed `TocSpec` model
  with the exact `toc.level4` path (`tests/test_template.py:848-879`).
- The printable-width fallback fails explicitly if section content width is
  non-positive rather than emitting an invalid tab position
  (`styles.py:393-402`).
- The leader lookup is closed by `TocLevelSpec` validation and the renderer
  mapping, so invalid leader values cannot silently produce malformed OOXML.

## Reuse / Duplication

- TOC styles delegate shared paragraph formatting to the existing
  `apply_paragraph_style()` helper; no TOC-specific duplicate font,
  indentation, spacing or line-spacing translator was added
  (`styles.py:226-323, 436-441`).
- Existing unit conversion helpers are reused for explicit and `em` tab
  positions (`styles.py:443-447`), while `_set_right_tab()` contains only the
  TOC-specific tab/leader XML operation.
- `renderer.py` and `fields.py` remain unchanged in the task diff, so the
  real field helper is reused rather than rewritten. The allowed production
  diff is limited to `templates/model.py` and `renderers/docx/styles.py`;
  tests are limited to the declared task test paths.

## Complexity Delta

- The production change adds one small policy validator, two closed renderer
  maps, one printable-width helper, one right-tab helper and one TOC
  configurator. The complexity is proportional to TOC 1-3 style configuration
  and does not introduce new parser, compiler, persistence, UI, network or AI
  dependencies.
- The control flow is deterministic: omitted level policies use
  `TocLevelSpec()` defaults, explicit tabs override the printable-width
  fallback, and `toc=None` returns before any style mutation
  (`styles.py:405-452`).
- No school-specific geometry or display-name lookup was added. The stable
  `TOC1`-`TOC3` IDs are renderer-owned and package-level XML assertions cover
  the resulting contract.

## Required Fixes

None.

## Independent Validation

- `.venv/bin/python -m pytest tests/test_template.py tests/test_docx_renderer.py -k 'toc or style' -q`
  -> `34 passed, 61 deselected in 6.20s`.
- `.venv/bin/ruff check .`
  -> `All checks passed!`.
- `git diff --check`
  -> exit `0`, no output.
- The SpecNav handoff contract was not rerun: its runtime-resolver command was
  interrupted when the user requested immediate convergence. No handoff result
  is claimed; this is a process-command limitation, not an implementation
  finding.
