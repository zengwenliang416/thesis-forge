# Development Basis: docforge-workbench-ui-redesign

## Requirements Reference

- `openspec/specs/ui-design/design.md`
- `openspec/specs/system-architecture/design.md`
- `openspec/specs/frontend-backend-data-flow/design.md`
- `openspec/specs/component-architecture/design.md`
- `openspec/changes/docforge-workbench-ui-redesign/requirements.md`
- `openspec/changes/docforge-workbench-ui-redesign/acceptance.md`
- `openspec/changes/docforge-workbench-ui-redesign/spec-map.json`
- `openspec/changes/docforge-workbench-ui-redesign/component-impact-map.json`

## Prototype Reference

- `openspec/changes/docforge-workbench-ui-redesign/prototype/handoff.md`
- `openspec/changes/docforge-workbench-ui-redesign/prototype/decision.json`
- `openspec/changes/docforge-workbench-ui-redesign/prototype/artifact/index.html`

## Handoff Reference

Development is allowed only after the prototype handoff and decision are valid.

## Component Architecture Constraint

Implementation must preserve high cohesion and low coupling. Any duplicated UI,
state, validation, formatting, or domain behavior that meets the extraction rule
must become a shared component, hook, utility, or service.
