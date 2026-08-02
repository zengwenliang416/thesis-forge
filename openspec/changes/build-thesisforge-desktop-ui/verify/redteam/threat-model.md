# Redteam Threat Model

## Assets

- Source Markdown, school templates, prior valid DOCX, generated packages, and local user paths.

## Trust Boundaries

- Browser workspace handles, native file dialogs, Web HTTP DTOs, Tauri commands, sidecar stdin/stdout, filesystem replacement, and package manifests.

## Hostile Conditions

- Missing/read-only paths, failed atomic replacement, malformed templates, stale callbacks, repeated clicks, canceled builds, protocol drift, corrupt packages, leaked credentials, external socket attempts, and target/architecture mismatch.

## Required Invariants

- No autosave, no stale build, no prior-output replacement on failure, no core frontend dependency, no hidden network requirement, and no cross-target artifact reuse.
