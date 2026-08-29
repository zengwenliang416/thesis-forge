## Why

DocForge intentionally rejects a bare Markdown file because a build needs a
project manifest, template selection, safe resource roots, and output policy.
Users therefore need a repeatable, non-academic bridge from an ordinary
Markdown document to a complete DocForge project before they can use the
workbench or CLI.

## What Changes

- Add a reusable Agent Skill named `docforge-project`.
- Use the installed Yao Meta Skill as the mandatory engineering and release
  pipeline. Keep its engine directory read-only and direct all generated Skill
  source and evidence to the repository-owned target.
- Publish the Skill through the provisional unscoped npm package name
  `docforge-project-skill`; package-name availability and publisher authority
  are rechecked at release time.
- Add an explicit npm installer for Codex. Installation never occurs from an
  npm lifecycle hook and never silently modifies a user Skill directory.
- Add a deterministic local importer that analyzes one UTF-8 Markdown source,
  copies referenced local resources, normalizes only required DocForge syntax,
  and creates a new DocForge Project Format V1 directory.
- Generate a minimal `docforge.yaml` using `document.type: general`,
  `project.language: und`, `render.template_id: docforge-standard`, and the
  existing neutral source, Review, and build defaults unless the user supplies
  valid explicit metadata.
- Preserve ordinary Markdown structure and formatting. When compatibility
  rewrites are required, retain a byte-identical original source and emit a
  machine-readable import report.
- Reject unsupported, unsafe, missing, remote, or ambiguous inputs with
  actionable diagnostics instead of fabricating content, downloading remote
  resources, or silently dropping syntax.
- Verify every completed import with the installed `docforge inspect` and
  `docforge validate` commands. Build verification is available as an explicit
  option and is mandatory in package acceptance tests.
- Add trigger, output, packaging, installation, offline, path-security, and
  macOS/Linux/Windows tests for the Skill package.

## Capabilities

### New Capabilities

- `docforge-project-skill`: Install and run a reusable Agent Skill that turns
  ordinary Markdown plus local resources into a verified DocForge project.

### Modified Capabilities

None. The Skill consumes the existing `docforge.project.v1` and DocForge CLI
contracts without changing the compiler or project format.

## Impact

- New npm workspace package under `packages/docforge-project-skill/`, with the
  Yao-managed Skill target at
  `packages/docforge-project-skill/docforge-project/`.
- New Skill source, installer, deterministic importer, references, evals,
  fixtures, package tests, and distribution metadata.
- New Yao Governed evidence for intent, references, output risk, Skill IR,
  compiled target contracts, trigger/output evaluation, trust, conformance,
  package/install/upgrade, Atlas, registry, Review Studio, and promotion.
- Root npm workspace scripts and lockfile may be updated during implementation.
- CI and release workflows may gain package validation and npm release jobs.
- No change to `src/docforge`, the Markdown parser, renderer, frontend, Tauri
  application, template schema, or archived OpenSpec evidence is required.
- The neutral `templates/base/docforge-standard.yaml` gains the existing
  `GB-T-7714-2025` citation profile, with one focused compiler regression test,
  so a general project containing citations can validate without fabricated
  academic metadata.
- npm publication, user-level installation, commit, push, and release remain
  separate Operations actions and are not authorized by this proposal.
