# Prototype Question: docforge-project-format-v1

## Question

Can one breaking DocForge cutover preserve a single deterministic compiler
pipeline by assigning project/schema/profile validation to the project
boundary, Markdown semantics to `ForgeDocument`, orchestration to shared
application services, and runtime identity to one cross-language protocol,
without adding compatibility loaders or renderer profile branching?

## Branch

`component-seam`

## Review Target

- Entry: `component/component-map.md`
- Required reviewer decision: approve or reject the proposed component
  ownership, public APIs, extraction targets, and forbidden dependencies as the
  production migration boundary.

## Out of Scope

- Production implementation.
- Database writes.
- Deployment behavior.
- UI layout or visual redesign.
- Arbitrary Markdown importing and the npm Agent Skill.
