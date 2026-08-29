## Context

DocForge Project Format V1 deliberately treats a project directory or
`docforge.yaml` as the application boundary. A bare Markdown file is rejected
because it lacks project identity, template choice, resource confinement, and
output policy. The repository now has a neutral general-document contract and
`docforge-standard`, so the missing layer is a reusable importer rather than
another converter or a change to the compiler.

The importer must handle ordinary Markdown without claiming that every possible
Markdown extension is representable. Current DocForge accepts common
CommonMark/GFM structures and selected semantic extensions, but requires stable
IDs for objects such as standalone figures and rejects legacy project metadata
inside `document.md`. Unsafe or ambiguous input must therefore produce explicit
diagnostics rather than lossy rewriting.

The deliverable is both an Agent Skill and an npm package. The Skill provides
routing and decision guidance; deterministic scripts own repeated parsing,
filesystem, installation, and validation behavior. npm is a distribution
vehicle, not permission to mutate the user's Codex installation during package
installation.

## Goals / Non-Goals

**Goals:**

- Convert one ordinary Markdown file and local resources into a complete,
  neutral DocForge project.
- Preserve supported content and retain original bytes whenever normalization
  changes the primary source.
- Generate only the existing strict Project Format V1 manifest.
- Make filesystem operations deterministic, confined, atomic, and non-
  overwriting.
- Make `docforge inspect` and `docforge validate` the completion oracle.
- Package and explicitly install a discoverable Codex Skill through npm.
- Provide Governed trigger, output, package, installation, compatibility,
  and rollback evidence.

**Non-Goals:**

- Generate DOCX directly or wrap a second Markdown-to-Word engine.
- Extend the DocForge project schema or parser.
- Interpret arbitrary HTML, MDX, executable plugins, or remote websites.
- Infer academic identity or translate document content.
- Merge into or repair an existing DocForge project.
- Publish the package or mutate a user installation during proposal work.

## Decisions

### 1. Use Yao Meta Skill as the governed engineering engine

The installed Yao Meta Skill version is checked before authoring. Its
`engine_root` is:

```text
/Users/wenliang_zeng/.codex/skills/yao-meta-skill
```

It remains read-only. The canonical `target_root` is:

```text
packages/docforge-project-skill/docforge-project
```

The wrapper npm package root is not the Yao Skill target. Yao initialization
creates the named Skill below that wrapper with explicit intent and
`mode: governed`, `archetype: governed`. Yao state stays in its user cache/state
directories rather than entering source control.

The target is initialized with the confirmed contract:

- recurring job: turn ordinary Markdown and local resources into a verified
  DocForge project;
- `input_files`: one Markdown source plus optional local assets and BibTeX,
  treated as a `file-backed fixture` in governed evaluation;
- primary output: one new DocForge Project Format V1 directory plus bounded
  diagnostics and provenance;
- exclusions: direct DOCX conversion, thesis generation, existing-project
  merge, remote download, translation, summary, and format explanation;
- standards: Project Format V1, real DocForge inspect/validate/build, offline
  operation, non-overwrite, and cross-platform path safety.

### 2. Separate Skill identity from npm distribution identity

The installed Skill folder and frontmatter name are `docforge-project`.
The npm distribution is `docforge-project-skill`. This keeps invocation concise
while making the registry artifact explicit and searchable.

The npm name is provisional until Operations rechecks registry availability and
publisher authority immediately before release. No `@docforge` scope is assumed
because repository evidence does not establish control of that npm scope.

### 3. Use an explicit installer and forbid lifecycle installation

`npm install` or `npm exec` may download the package, but no `preinstall`,
`install`, `postinstall`, or `prepare` hook may copy files into a user
directory. Installation occurs only through:

```text
npx docforge-project-skill install --target codex
```

The installer resolves the destination, validates the packaged Skill, stages
the new version, backs up an existing managed installation for an explicit
update, atomically replaces it, verifies the installed files, and reports a
rollback command. Fresh installation never overwrites an existing unmanaged
directory.

### 4. Keep one deterministic importer behind both interfaces

The npm CLI and the Agent Skill call one Node-based importer. `SKILL.md` does
not ask the agent to reproduce path rewriting or YAML generation manually.
The importer has small testable modules for analysis, normalization, resource
mapping, manifest serialization, staged publication, and DocForge command
verification.

The package uses the repository's existing Node/pnpm toolchain and minimizes
runtime dependencies. It does not import Python source files or renderer code.

### 5. Plan before writing and publish the directory atomically

The importer first resolves all inputs and produces an immutable import plan.
Any blocking diagnostic stops before destination creation. It then writes a
sibling staging directory, runs DocForge verification against that staged
project, and renames the complete directory to the requested destination.

The destination must not exist. This avoids partial merge semantics, accidental
data loss, and ambiguous idempotency. Running the same analysis again produces
the same plan; publishing twice to the same destination fails safely.

### 6. Generate a minimal neutral manifest

The default manifest contains only fields needed to satisfy the existing
contract:

```yaml
schema: docforge.project.v1
project:
  id: <validated deterministic id>
  language: und
document:
  source: document.md
  type: general
resources:
  root: .
  assets: assets
render:
  template_id: docforge-standard
```

Output and Review sections are omitted so DocForge supplies its authoritative
neutral defaults. Optional metadata is added only from explicit user arguments
or a conservative, type-safe Front Matter mapping. No academic profile is
created automatically.

### 7. Preserve content and make compatibility rewrites auditable

If the source already satisfies DocForge syntax, `document.md` is byte-identical
to the input. When a required rewrite occurs, the package keeps the original at
`source/original.md` and writes `import-report.json` containing bounded
diagnostics, rewrite categories, source-relative paths, and hashes.

The importer may perform only defined rewrites:

- remove and map recognized YAML Front Matter;
- add stable `fig:` IDs to standalone local images that lack them;
- copy referenced local images and rewrite their destinations;
- normalize line endings only when required by a documented parser constraint.

It does not rewrite prose, translate content, invent headings, convert HTML
semantics, manufacture citation data, or silently discard unsupported nodes.

### 8. Keep resources local and confined

The source file's parent is the default read boundary. Referenced local image
paths must resolve inside it without traversal, symlink escape, NUL, device, or
remote semantics. Files are copied under `assets/` using a deterministic
relative mapping. Collision resolution uses a short content hash and is
recorded in the import report.

Remote images are never fetched. Citations require a user-supplied local BibTeX
file, which is copied to `references.bib` and declared in the manifest.

### 9. Treat DocForge as the compatibility oracle

The importer discovers `docforge` from an explicit `--docforge-bin` or `PATH`.
There is no checkout-specific fallback. Before success it runs:

```text
docforge inspect <staged-project>
docforge validate <staged-project> --json
```

A user may request build verification. Package E2E tests always build the
comprehensive fixture with network and AI credentials unavailable. The npm
package does not consider its own parser or schema checks sufficient.

The first real comprehensive E2E found that `docforge-standard` lacked a
`citation` semantic style while citation-capable school templates required
academic identity. The importer must not fabricate those fields or shadow the
installed template with a private copy. This change therefore adds only the
existing `GB-T-7714-2025` citation profile to the neutral product template and
locks it with a template regression test.

### 10. Keep Skill guidance progressively disclosed

`SKILL.md` contains trigger boundaries, input/output contract, the safe default
workflow, and links to focused references. Project Format V1 details,
compatibility rules, diagnostics, and installation/update behavior live in
separate references. Deterministic scripts can run without loading their source
into the agent context.

Trigger evals distinguish this Skill from direct Markdown-to-Word conversion,
editing an existing DocForge project, creating a thesis, translating Markdown,
or merely explaining the project format.

### 11. Use Yao Skill IR before target packaging

Yao exports `reports/skill-ir.json` before compiling any target-specific
contract. The IR owns the recurring job, trigger description, positive and
negative routing cases, workflow, failure modes, resources, scripts, eval plan,
permission boundary, `owner`, `review cadence`, `output contract`, and
`rollback boundary`.

OpenAI/Codex and Agent Skills compatible outputs are compiled from that IR.
Target-specific metadata may degrade only with an explicit warning and must not
silently change import behavior, filesystem permissions, or exclusions.

### 12. Release as a Governed package

The package declares `owner`, version, `review cadence`, license, supported Node
versions, target hosts, package files, `output contract`, and
`rollback boundary`. Governed release evidence includes a `trust report`,
`reports/output_quality_scorecard.md`, at least five output cases with
`input_files` labeled as `file-backed fixture`, blind A/B review state,
permission probes, package content, clean installation, explicit Codex
installation, trigger and output evals, dependency/license review, checksum
generation, cross-platform tests, upgrade simulation, Skill Atlas, registry
audit, Review Studio, promotion, regression history, and real DocForge E2E
verification.

Unavailable telemetry, provider-backed runs, human review, approvals, metrics,
or benchmarks remain labeled `missing evidence`; recorded fixtures are not
misrepresented as model-executed evidence.

## Risks / Trade-offs

- [Risk] "Any Markdown" can be interpreted as support for every extension.
  -> Define ordinary Markdown as the tested CommonMark/GFM envelope and fail
  explicitly on unrepresentable HTML, MDX, executable, or remote constructs.
- [Risk] Rewriting asset paths can alter source meaning.
  -> Limit rewrites to parsed standalone local images, retain the original
  bytes, record hashes and rewrites, and verify the final project with DocForge.
- [Risk] npm installation may be mistaken for permission to alter Codex state.
  -> Forbid lifecycle installers and require an explicit install/update command.
- [Risk] Yao can accidentally target its own installed engine or write evidence
  outside the selected Skill.
  -> Lock canonical engine, target, and state roots; never pass `--self`; verify
  the Yao engine tree remains unchanged after authoring and packaging.
- [Risk] A package can drift from the current Project Format V1.
  -> Treat `docforge inspect/validate` as the oracle and run repository fixtures
  in CI instead of duplicating the full schema.
- [Risk] The unscoped npm name can be claimed before publication.
  -> Recheck availability and publisher authority at Operations; rename the
  distribution artifact if necessary without changing Skill identity.
- [Trade-off] Requiring a non-existent destination is less convenient than
  merging, but makes atomicity, rollback, and non-destruction auditable.
- [Trade-off] Keeping `source/original.md` and an import report adds files only
  when rewriting is necessary, but provides lossless provenance.

## Migration Plan

No existing DocForge project or runtime migration is required. Implementation
first initializes the locked target through Yao, replaces generic scaffolding,
builds deterministic behavior, exports Skill IR, compiles target contracts, and
runs governed gates. It then adds the npm wrapper, CI, and release packaging.
npm publication and user installation occur only after separate Operations
approval.

Rollback before publication removes the new workspace package and root workspace
entries. Rollback after installation uses the installer-produced backup for an
explicit update or removes only the exact managed Skill version after verifying
its manifest.

## Open Questions

None for proposal.
