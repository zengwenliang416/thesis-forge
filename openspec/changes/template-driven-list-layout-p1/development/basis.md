# Development Basis: template-driven-list-layout-p1

## Requirements Reference

- `openspec/changes/template-driven-list-layout-p1/requirements.md`
- `openspec/changes/template-driven-list-layout-p1/acceptance.md`
- `openspec/changes/template-driven-list-layout-p1/spec-map.json`
- `openspec/changes/template-driven-list-layout-p1/component-impact-map.json`

## Prototype Reference

- `openspec/changes/template-driven-list-layout-p1/prototype/handoff.md`
- `openspec/changes/template-driven-list-layout-p1/prototype/decision.json`
- `openspec/changes/template-driven-list-layout-p1/prototype/component/component-map.md`

## Foundation Spec Reference

- `openspec/specs/ui-design/design.md`
- `openspec/specs/system-architecture/design.md`
- `openspec/specs/frontend-backend-data-flow/design.md`
- `openspec/specs/component-architecture/design.md`

## Handoff Reference

- Prototype contract returned `ok:true` after user approval of
  `list-policy-docx-seam-v1`.
- Production implementation starts from Git baseline `a6b606b`, which tracks the approved
  prototype decision and the unchanged 12-task `tasks.md` baseline.
- Scope is locked by `openspec/changes/template-driven-list-layout-p1/scope.json`.

## Implementation Boundary

- Parser, Domain Model, Compiler and `ListInstruction` remain renderer neutral.
- Template Model owns ordered/unordered level policy and validation.
- DOCX Renderer owns semantic Word format mapping, numbering.xml construction and paragraph
  style application.
- HUT-specific values remain in YAML.
- Existing offline CLI and service signatures remain unchanged.

## Component Architecture Constraint

- Reuse `LengthSpec`, `ParagraphStyleSpec` and the shared DOCX paragraph-style translator.
- Keep one Renderer-local semantic number-format mapper.
- Keep one deterministic list-level policy resolver.
- Do not duplicate font, spacing or length conversion logic.
- Do not introduce UI, database, network, AI or school-specific Renderer branches.
