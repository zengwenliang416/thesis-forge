# Release Plan: build-thesisforge-v1-core

## Release Target

`local-only`

ThesisForge V1 is closed as a local repository and installation artifact only.
The repository has no project license, so this plan does not authorize publishing
the wheel, sdist, source tree, or generated artifacts to a public registry.

## Required Artifacts

- `operations/readiness.md`
- `operations/readiness.json`
- `operations/release-checklist.json`
- `operations/changelog.md`
- `operations/release-notes.md`
- `operations/branch-finish.md`
- `operations/update-spec.json`

## Release Decision

Prepare version `0.1.0` for local installation and acceptance. Keep the current
repository history as the distribution source of truth, retain the verified
wheel/sdist workflow for local use, and do not create an external release,
package-index upload, deployment, or marketplace entry.

Final closure requires a fresh green verification aggregate, completed readiness
and branch-finish evidence, and `operations-gate.js --json` returning `ok: true`.
