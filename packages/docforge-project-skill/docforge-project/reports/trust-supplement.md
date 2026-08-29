# Trust Supplement

## Effective Capabilities

- Network: forbidden; remote resources fail with `DFP-RESOURCE-REMOTE`.
- File write: required and approved only for owned staging, a new project
  destination, and explicit managed Skill installation/rollback paths.
- Subprocess: required and approved only for local Node and DocForge commands.
- Interactive input: not required.

## Scanner Limitation

Yao Meta Skill 2.1.0 statically inventories only top-level Python files in its
trust scanner. The canonical importer is Node ESM (`.mjs`), so static trust
output alone cannot prove its transitive file-write behavior. A Yao-visible
Python bridge exposes the subprocess boundary; `security/permission_policy.json`
declares both effective capabilities; Node unit/redteam/E2E tests verify actual
behavior.

This is bounded local evidence, not native host sandbox enforcement.
