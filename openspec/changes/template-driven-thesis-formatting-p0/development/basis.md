# Development Basis: template-driven-thesis-formatting-p0

## Requirements Reference

- `openspec/changes/template-driven-thesis-formatting-p0/requirements.md`
- `openspec/changes/template-driven-thesis-formatting-p0/acceptance.md`
- `openspec/changes/template-driven-thesis-formatting-p0/acceptance.json`
- `openspec/changes/template-driven-thesis-formatting-p0/spec-map.json`
- `openspec/changes/template-driven-thesis-formatting-p0/component-impact-map.json`
- `openspec/changes/template-driven-thesis-formatting-p0/tasks.md`

## Foundation Reference

- `openspec/specs/ui-design/design.md`
- `openspec/specs/system-architecture/design.md`
- `openspec/specs/frontend-backend-data-flow/design.md`
- `openspec/specs/component-architecture/design.md`

## Prototype Reference

- `openspec/changes/template-driven-thesis-formatting-p0/prototype/handoff.md`
- `openspec/changes/template-driven-thesis-formatting-p0/prototype/decision.json`
- `openspec/changes/template-driven-thesis-formatting-p0/prototype/component/component-map.md`
- Approved variant: `policy-role-docx-seam-v1`.

## Handoff Reference

The requirements and prototype owning contracts returned `ok:true`; the user
explicitly approved the component-seam variant on August 3, 2026. Production
implementation remains bound to `scope.json`, the committed 56-task baseline
at `dda08b4`, and the development entry contract.

## Component Architecture Constraint

Implementation must preserve:

- Template Model owns renderer-neutral policy.
- Compiler owns semantic role resolution.
- RenderPlan contains no DOCX/OOXML objects.
- DOCX Renderer owns Word style and section translation.
- Body, heading, semantic, TOC, bibliography and header/footer formatting reuse
  one common paragraph policy and one DOCX translator.
- Existing YAML templates retain documented defaults.
- School-specific values remain in templates, never renderer constants.
