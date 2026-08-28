# Development Basis: docforge-project-format-v1

## Foundation Spec Reference

- `openspec/specs/ui-design/design.md`
- `openspec/specs/system-architecture/design.md`
- `openspec/specs/frontend-backend-data-flow/design.md`
- `openspec/specs/component-architecture/design.md`

## Requirements Reference

- `openspec/changes/docforge-project-format-v1/requirements.md`
- `openspec/changes/docforge-project-format-v1/acceptance.md`
- `openspec/changes/docforge-project-format-v1/acceptance.json`
- `openspec/changes/docforge-project-format-v1/spec-map.json`
- `openspec/changes/docforge-project-format-v1/component-impact-map.json`
- `openspec/changes/docforge-project-format-v1/design.md`
- `openspec/changes/docforge-project-format-v1/specs/`
- `openspec/changes/docforge-project-format-v1/tasks.md`

## Prototype Reference

- `openspec/changes/docforge-project-format-v1/prototype/component/component-map.md`
- `openspec/changes/docforge-project-format-v1/prototype/component-tree.md`
- `openspec/changes/docforge-project-format-v1/prototype/verifier-report.json`
- `openspec/changes/docforge-project-format-v1/prototype/handoff.md`
- `openspec/changes/docforge-project-format-v1/prototype/decision.json`

## Handoff Reference

The approved prototype freezes the `component-seam` variant
`single-docforge-pipeline`: one strict DocForge project boundary, one
`ForgeDocument` core aggregate, one application pipeline, and one versioned
runtime protocol. Production development is allowed only after the prototype
handoff, decision, scope lock, task ownership, and committed `tasks.md` baseline
are valid.

## Scope Reference

- `openspec/changes/docforge-project-format-v1/scope.json`
- Production edits are limited to the allowed roots in that file.
- Other active OpenSpec changes, archives, Git internals, CodeGraph storage,
  dependency caches, and build outputs remain outside this change.

## Component Architecture Constraint

Implementation must preserve high cohesion and low coupling. Any duplicated UI,
state, validation, formatting, or domain behavior that meets the extraction rule
must become a shared component, hook, utility, or service.

The project loader owns manifest and path validation; parser and core own
renderer-neutral Markdown semantics; templates own generic and academic
bindings; application services own orchestration; adapters own DTO validation
and serialization; the DOCX renderer consumes only RenderPlan.
