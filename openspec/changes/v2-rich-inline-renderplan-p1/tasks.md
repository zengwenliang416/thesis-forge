## 1. Canonical Inline Run Seam

**User outcome:** Compiler and renderer implementers can rely on one canonical,
renderer-neutral inline vocabulary for every v2 inline capability.

- [ ] 1.1 Add `SoftBreakRun`, `HardBreakRun`, `HyperlinkRun`, and `MathRun` to `src/thesis_forge/core/render_plan.py` with the exact capability-registered names and semantic fields.
- [ ] 1.2 Extend the single `InlineRun` union with the four new run types and preserve the existing canonical variants.
- [ ] 1.3 Add `tests/core/test_typed_inline_render_plan.py` covering exact names, fields, union membership, nominal break semantics, renderer-neutral imports, and explicit unknown-run failure.

## 2. Ordered Consumer Handoff

**User outcome:** Downstream Preview, Review, compiler, and DOCX work receives a
verified typed seam without caption duplication or compatibility behavior.

- [ ] 2.1 Record the verified A1M seam and leave Preview, Review, compiler, DOCX body, DOCX footnote, and figure-caption consumers unchanged.
- [ ] 2.2 Hand the canonical union to the dependent A1P, A1R, A1D1, and A1D2 slices in dependency order.
