# Development Basis: template-driven-thesis-layout-p1

## Requirements Reference

- `openspec/changes/template-driven-thesis-layout-p1/requirements.md`
- `openspec/changes/template-driven-thesis-layout-p1/acceptance.md`
- `openspec/changes/template-driven-thesis-layout-p1/spec-map.json`
- `openspec/changes/template-driven-thesis-layout-p1/component-impact-map.json`
- `openspec/changes/template-driven-thesis-layout-p1/tasks.md`

## Foundation Reference

- `openspec/specs/ui-design/design.md`
- `openspec/specs/system-architecture/design.md`
- `openspec/specs/frontend-backend-data-flow/design.md`
- `openspec/specs/component-architecture/design.md`

## Prototype Reference

- `openspec/changes/template-driven-thesis-layout-p1/prototype/handoff.md`
- `openspec/changes/template-driven-thesis-layout-p1/prototype/decision.json`
- `openspec/changes/template-driven-thesis-layout-p1/prototype/component/component-map.md`
- Approved variant: `cover-policy-docx-seam-v1`.

## Handoff Reference

Requirements and prototype owning contracts returned `ok:true`; the user approved continuing the
parameterization work on August 9, 2026. Production implementation is bound to `scope.json`, the
committed task baseline `3c5da9b`, and the development entry contract.

## Component Architecture Constraint

Implementation must preserve:

- Front Matter owns cover content and remains free of school formatting.
- Template Model owns ordered cover policy.
- Compiler and RenderPlan remain renderer neutral.
- DOCX Renderer owns Word paragraph creation.
- Every cover paragraph reuses `ParagraphStyleSpec` and the shared DOCX translator.
- School-specific cover values remain in YAML, never Renderer constants.
