# Development Handoff To Verify: template-driven-list-layout-p1

## Implemented Slices

- `001-list-policy`
- `002-docx-list-rendering`
- `003-hut-list-verification`

## Files Changed

- Template Model/public exports, DOCX list renderer, HUT YAML, template documentation, focused/acceptance tests and lifecycle evidence.

## Requirements Covered

- Typed ordered/unordered policies, strict list validation, deterministic legacy defaults, true numbering OOXML, paragraph styling, HUT configuration and offline two-template behavior.

## Prototype Decisions Implemented

- Approved `list-policy-docx-seam-v1`: Markdown/RenderPlan retain semantics; Template Model owns presentation; DOCX Renderer owns Word translation.

## Components Created / Reused / Extracted

- Created typed list level/policy models and a semantic number-format mapper; reused `LengthSpec`, `ParagraphStyleSpec`, `to_docx_length` and `apply_paragraph_style`.

## API / Data Flow Changes

- Added additive `ThesisTemplate.list`; public Markdown, Parser, Domain, Compiler, RenderPlan and CLI signatures are unchanged.

## Tests Added

- Model defaults/errors, HUT/default template comparison, non-1 start, deep fallback, ordered/unordered numbering references, exact OOXML format/marker/alignment/indentation and paragraph/run style assertions.

## Local Validation

- Focused: `147 passed`; full Python: `383 passed`; Ruff and strict OpenSpec passed; three CodeGraph claims verified; complete HUT DOCX built and package/numbering references validated.

## Known Risks

- Unicode marker appearance depends on installed fonts and the HUT list values remain editable template policy; pixel-identical pagination across Office clients is not claimed.

## Items Requiring Six-Domain Verification

- Facticity, static, unit, redteam and E2E evidence are ready. Sensory verification should open `output/verification/template-driven-list-layout-p1/hut-list-policy.docx` in Word or WPS and inspect list flow.
