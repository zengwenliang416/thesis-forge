# Development Basis: libreoffice-preview-fidelity-p1

## Requirements Reference

- `openspec/specs/ui-design/design.md`
- `openspec/specs/system-architecture/design.md`
- `openspec/specs/frontend-backend-data-flow/design.md`
- `openspec/specs/component-architecture/design.md`
- `openspec/changes/libreoffice-preview-fidelity-p1/requirements.md`
- `openspec/changes/libreoffice-preview-fidelity-p1/acceptance.md`
- `openspec/changes/libreoffice-preview-fidelity-p1/spec-map.json`
- `openspec/changes/libreoffice-preview-fidelity-p1/component-impact-map.json`

## Prototype Reference

- `openspec/changes/libreoffice-preview-fidelity-p1/prototype/handoff.md`
- `openspec/changes/libreoffice-preview-fidelity-p1/prototype/decision.json`
- `openspec/changes/libreoffice-preview-fidelity-p1/prototype/logic/harness.js`

## Handoff Reference

Development is allowed only after the prototype handoff and decision are valid.

## Component Architecture Constraint

Implementation must preserve high cohesion and low coupling. Any duplicated UI,
state, validation, formatting, or domain behavior that meets the extraction rule
must become a shared component, hook, utility, or service.
