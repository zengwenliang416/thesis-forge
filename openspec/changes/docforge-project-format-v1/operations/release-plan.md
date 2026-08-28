# Release Plan: docforge-project-format-v1

## Release Target

`local-only`

This Operations pass prepares the change for a trusted local archive. It does
not publish a package, deploy a project, update a marketplace, push a branch,
or create a GitHub release.

## Required Artifacts

- `operations/verification-v2-proof.json`
- `operations/readiness.md`
- `operations/readiness.json`
- `operations/release-checklist.json`
- `operations/branch-finish.md`
- `operations/update-spec.json`
- `verify/receipt.json`
- `verify/receipt.md`
- `verify/v2/migration-status.json`

User-facing changelog and release notes are not applicable to this local-only
archive-preparation target.

## Release Decision

Proceed with Operations gate and archive dry-run after all required artifacts
validate. Stop before the non-dry-run archive transaction and request separate
explicit approval.
