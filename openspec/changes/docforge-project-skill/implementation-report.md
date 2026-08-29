# Implementation Report: docforge-project-skill

Date: 2026-08-29

## Delivered Contract

- Agent Skill identity: `docforge-project`.
- npm distribution identity: `docforge-project-skill`.
- Canonical Skill target:
  `packages/docforge-project-skill/docforge-project/`.
- Governed owner: `DocForge maintainers`.
- Output contract: one new, non-overwriting `docforge.project.v1` directory
  with bounded provenance and successful real `docforge inspect` and
  `docforge validate` evidence.
- Rollback boundary: only owned staging paths, a managed Skill installation,
  and the exact installer-reported backup.

## Implementation

The package exposes `plan`, `import`, `install --target codex`, and `rollback`.
The Agent Skill and npm CLI delegate to one Node importer through a small
Python bridge that is visible to Yao.

The importer validates UTF-8 input, computes an immutable plan, maps only
approved neutral Front Matter, preserves compatible Markdown bytes, adds
stable figure IDs, copies confined local images and optional BibTeX, retains
`source/original.md` after rewrites, writes through a sibling staging
directory, and publishes only after real DocForge inspection and validation.
An explicit `--build` invokes the installed `docforge build`; the package does
not import renderer internals or write DOCX directly.

The installer performs no npm lifecycle mutation. Fresh installs reject an
existing directory, managed updates create a sibling backup, activation is
atomic, and rollback accepts only the reported managed backup.

The neutral `docforge-standard` template now declares the existing
`GB-T-7714-2025` citation profile. This is the only product-owned change and
allows the comprehensive general-document fixture to validate and build
without academic metadata.

## Governed Assets

The target contains lean instructions, focused references, structured
permissions, Skill IR, five compiled target contracts, 16 trigger cases, six
file-backed output cases, failure history, trust evidence, conformance,
package/install/upgrade evidence, Skill Atlas, Review Studio, promotion
decisions, and explicit external-evidence placeholders.

No Yao engine file was modified. No authoring, generation, packaging, or
validation command used `--self`; the only `--self` invocation was Yao's
read-only `check-update --notice --self` activation check, which reported
version `2.1.0` current.

The final local evidence records `21` npm tests, `1380` repository tests,
`153` Yao archive entries, `43` npm tarball entries, and one package-external
receipt for the source-contract, archive, and npm SHA-256 values.

## Deferred Operations

The following remain literal `missing evidence` and are not inferred:

- provider-backed evaluation;
- real independent human blind review;
- target-native permission enforcement;
- real external-client telemetry;
- npm package-name availability;
- npm publisher authority;
- clean committed release lock.

No npm publication, user-level installation, commit, push, or release was
performed.
