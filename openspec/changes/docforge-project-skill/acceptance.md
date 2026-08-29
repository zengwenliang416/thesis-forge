# Acceptance Criteria: docforge-project-skill

## User-Visible Criteria

- `npx docforge-project-skill install --target codex` performs an explicit,
  reviewable installation of the `docforge-project` Skill and reports the exact
  installed path and version.
- Invoking the Skill with an ordinary Markdown file creates a new DocForge
  project containing `docforge.yaml`, `document.md`, and the neutral project
  directories required by the Project Format V1 contract.
- The result uses general-document defaults and contains no fabricated thesis,
  student, university, degree, or advisor information.
- Common Markdown formatting remains semantically intact, and local image
  references continue to resolve after resources are copied into the project.
- Users receive precise blocking diagnostics for missing resources,
  unsupported constructs, unsafe paths, citations without bibliography, absent
  DocForge runtime, or an existing destination.
- A successful import can be opened by the DocForge CLI and workbench; the npm
  package never presents itself as a Markdown-to-Word converter.

## System Criteria

- The Skill name is `docforge-project`; the npm package name is
  `docforge-project-skill`.
- The package contains no npm lifecycle script that installs, updates, or
  modifies user files.
- The Skill target was initialized and evaluated through Yao Meta Skill in
  Governed mode while the Yao engine directory remained byte-identical.
- Import uses an explicit pre-write plan and publishes a fully validated staged
  directory atomically.
- `docforge.yaml` validates as `docforge.project.v1` and uses the existing
  neutral defaults rather than a package-owned schema variant.
- `docforge inspect <project>` and `docforge validate <project>` both exit zero
  before the importer reports success.
- The importer never invokes DocForge renderer internals or writes a DOCX
  directly.
- Repeated analysis of identical inputs produces the same manifest, rewritten
  Markdown, resource destinations, and diagnostics.

## Data Criteria

- The original Markdown bytes are retained when compatibility normalization
  changes `document.md`.
- Local resources are confined to the selected source boundary and destination
  project. Absolute paths, traversal, symlink escapes, device paths, NUL values,
  and remote fetches are rejected.
- Existing destinations and installed Skill directories are not overwritten
  without an explicit update operation with a validated backup and rollback
  path.
- Unknown metadata is reported and never mapped to unrelated manifest fields.
- Generated reports do not contain credentials, environment secrets, private
  home-directory paths, or document body content beyond bounded source
  locations and user-visible filenames.

## Component Criteria

- Reusable components, hooks, utilities, or services named in
  `component-impact-map.json` are implemented once and tested at their owned
  boundary.
- Skill instructions remain lean; schema details and compatibility tables live
  in focused references, while filesystem and transformation logic lives in
  deterministic scripts.
- The npm CLI and Agent Skill route through one shared importer and one shared
  installer implementation.
- Skill IR is the platform-neutral semantic source, and compiled target
  contracts preserve the recurring job, exclusions, permissions, scripts,
  references, output contract, and degradation notes.
- Tests do not mock away path confinement, atomic publication, package content,
  or real `docforge inspect/validate/build` acceptance.

## Verification Surfaces

- Facticity: package identity, Skill identity, Project Format V1 constants,
  absence of thesis/direct-DOCX claims, and no npm lifecycle installer.
- Static: package schema, TypeScript/JavaScript lint and type checks, Skill
  validation, Yao resource/context/governance checks, trigger evals,
  dependency/license audit, and `npm pack --dry-run`.
- Unit: import planning, IDs, metadata mapping, Markdown rewrites, resource
  mapping, diagnostics, installer destinations, and rollback.
- Redteam: traversal, symlink escape, remote resources, malformed front matter,
  binary/invalid encoding, collision, existing destination, missing CLI, and
  malicious package paths.
- E2E: clean npm install, explicit Codex install, Markdown import, DocForge
  inspect/validate/build, reinstall/update, and uninstall/rollback simulation.
- Compatibility: macOS, Linux, and Windows path semantics and Node runtime.
- Governance: Yao Skill IR, compiler, trigger/output eval, blind review state,
  trust report, runtime permission probes, package verification, install
  simulation, upgrade check, Atlas, registry audit, Review Studio, promotion,
  regression history, and explicit `missing evidence`.

## Unresolved Gaps

None for proposal.
