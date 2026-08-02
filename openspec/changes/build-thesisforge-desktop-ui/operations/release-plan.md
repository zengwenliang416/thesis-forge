# Release Plan: build-thesisforge-desktop-ui

## Release Target

`local-only`

## Required Artifacts

- `operations/readiness.md`
- `operations/readiness.json`
- `operations/release-checklist.json`
- `operations/changelog.md`
- `operations/release-notes.md`
- `operations/branch-finish.md`
- `operations/update-spec.json`
- `operations/signoff.yaml`

## Release Decision

Close ThesisForge Workbench `0.1.0` as a local-only release. Retain Git history,
the verified Python/Web/sidecar build paths, the macOS application evidence, and
the Windows ARM64 MSI/NSIS evidence as the local distribution source of truth.

Do not create a public GitHub release, package-index upload, hosted deployment,
marketplace listing, Apple notarization claim, or Microsoft signing claim.
GitHub Actions may be rerun later as supplementary reproducibility evidence,
but billing availability is not part of this local product gate.

Final closure requires:

- a fresh green six-domain aggregate;
- a green operations and archive gate;
- the local-only project-owner risk signoff;
- reviewed branch/worktree provenance;
- the requested logical batch commits before the archive action.
