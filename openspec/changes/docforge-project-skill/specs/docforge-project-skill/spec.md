## ADDED Requirements

### Requirement: Develop the Skill through a locked Yao Governed target
Maintainers SHALL use the installed Yao Meta Skill as the authoring,
evaluation, packaging, and review engine. They MUST keep the Yao engine root
read-only, lock the repository-owned `docforge-project` target explicitly, and
use Governed mode for public npm distribution.

#### Scenario: Initialize the Skill target
- **WHEN** maintainers begin implementation
- **THEN** Yao initializes `packages/docforge-project-skill/docforge-project` with the confirmed job, input, output, exclusions, constraints, `mode: governed`, and `archetype: governed`

#### Scenario: Protect the Yao engine
- **WHEN** any Yao authoring, reporting, packaging, or verification command runs
- **THEN** no command uses `--self`, no declared output enters the Yao engine subtree, and the engine files remain byte-identical

#### Scenario: Compile target packages
- **WHEN** OpenAI, Agent Skills compatible, or generic package output is prepared
- **THEN** Yao validates `reports/skill-ir.json` first and the compiled target preserves the recurring job, exclusions, resources, scripts, permissions, output contract, rollback boundary, and degradation notes

#### Scenario: Evaluate governed readiness
- **WHEN** maintainers request promotion or public release readiness
- **THEN** Yao evidence covers trigger and output evaluation, `input_files` as a `file-backed fixture`, trust report, `reports/output_quality_scorecard.md`, conformance, runtime permissions, package verification, install simulation, upgrade, Atlas, registry, Review Studio, regression history, and explicit `missing evidence`

### Requirement: Install the Skill only through explicit user action
The npm package SHALL provide the `docforge-project` Agent Skill and SHALL
install or update it only after an explicit installer command. npm lifecycle
scripts MUST NOT write to Codex, Agent Skills, home-directory, or project Skill
locations.

#### Scenario: Install into Codex
- **WHEN** a user runs `npx docforge-project-skill install --target codex`
- **THEN** the package validates and atomically installs the `docforge-project` Skill into the resolved Codex Skill directory and reports the installed path and version

#### Scenario: Download package without installation
- **WHEN** npm downloads, installs, packs, or inspects the package without the explicit Skill installer command
- **THEN** no user Skill directory is created, modified, or deleted

#### Scenario: Update a managed installation
- **WHEN** a user explicitly updates an existing managed `docforge-project` installation
- **THEN** the installer validates the new package, retains a recoverable backup, atomically replaces the Skill, verifies the installed version, and reports the rollback action

### Requirement: Create a neutral DocForge Project Format V1 directory
The importer SHALL convert one UTF-8 Markdown file into a new project using the
existing `docforge.project.v1` contract, `document.type: general`,
`project.language: und`, `document.md`, and `docforge-standard` unless the user
provides valid explicit overrides.

#### Scenario: Import minimal ordinary Markdown
- **WHEN** a user imports a readable Markdown file into a non-existing destination
- **THEN** the destination contains a valid `docforge.yaml`, `document.md`, `assets/`, `review/`, and `build/` project with no required academic metadata

#### Scenario: Use explicit neutral metadata
- **WHEN** a user supplies valid language, localized title, author, organization, date, version, or keyword values
- **THEN** those values are serialized into the corresponding strict manifest fields without inventing additional metadata

#### Scenario: Preserve DocForge defaults
- **WHEN** output and Review paths are not explicitly requested
- **THEN** the manifest relies on DocForge defaults for `build/document.docx`, `review/document.review.md`, and `review/document.review-map.json`

### Requirement: Preserve supported Markdown semantics
The importer SHALL preserve DocForge-supported headings, paragraphs, emphasis,
inline code, links, lists, block quotes, tables, fenced code, inline/display
math, footnotes, citations, and images. It SHALL perform only documented,
deterministic compatibility rewrites.

#### Scenario: Source requires no rewrite
- **WHEN** the source is already compatible and all resources resolve
- **THEN** generated `document.md` is byte-identical to the input

#### Scenario: Standalone image has no stable ID
- **WHEN** a standalone local Markdown image lacks a valid `fig:` ID
- **THEN** the importer adds a deterministic unique `fig:` ID without changing its caption or image bytes

#### Scenario: Compatibility rewrite changes source bytes
- **WHEN** Front Matter removal or a resource or figure rewrite changes `document.md`
- **THEN** the original bytes are retained at `source/original.md` and every rewrite is recorded in `import-report.json`

#### Scenario: Input cannot be represented safely
- **WHEN** the source contains unsupported executable, HTML, MDX, remote-resource, or ambiguous syntax that has no approved lossless mapping
- **THEN** import stops with a blocking diagnostic and does not silently drop, execute, or reinterpret the content

### Requirement: Copy only confined local resources
The importer MUST confine reads to the selected source boundary and MUST copy
referenced local images and an explicitly supplied bibliography into
deterministic project-relative destinations. It MUST reject absolute, device,
remote, traversal, NUL, and symlink-escape paths.

#### Scenario: Copy local image
- **WHEN** a Markdown image resolves to a regular file inside the source boundary
- **THEN** the file is copied under `assets/`, the Markdown destination is rewritten to the copied path, and the content hash is recorded

#### Scenario: Resolve resource collision
- **WHEN** two referenced files would map to the same destination name with different bytes
- **THEN** the importer assigns deterministic content-hash suffixes and rewrites each reference to its own copied file

#### Scenario: Reject remote image
- **WHEN** a Markdown image uses an HTTP, HTTPS, data, or other remote scheme
- **THEN** the importer emits a blocking remote-resource diagnostic and performs no download

#### Scenario: Citation has no bibliography
- **WHEN** the Markdown contains DocForge citation syntax and no valid local bibliography is supplied
- **THEN** the importer stops with a diagnostic explaining how to provide the BibTeX file

### Requirement: Plan and validate before publishing
The importer SHALL resolve an immutable import plan before writing, SHALL build
the project in a sibling staging directory, and SHALL publish the destination
only after real DocForge inspection and validation succeed.

#### Scenario: Analyze invalid input
- **WHEN** input analysis produces any blocking diagnostic
- **THEN** no destination or staging residue remains

#### Scenario: Verify completed staged project
- **WHEN** staged files have been written
- **THEN** the importer runs the explicitly resolved `docforge inspect` and `docforge validate --json` commands against the staged project

#### Scenario: DocForge validation fails
- **WHEN** inspect or validate exits non-zero
- **THEN** the importer reports the command diagnostics, removes owned staging files, and leaves the requested destination absent

#### Scenario: Destination already exists
- **WHEN** the requested project destination exists as a file or directory
- **THEN** import fails before writing and does not merge, delete, or overwrite existing content

### Requirement: Keep project creation offline and independent of DOCX rendering
Project import MUST require no network, AI provider, database, Office
application, or DOCX library. The npm package MUST NOT generate DOCX except by
explicitly invoking the installed `docforge build` command for requested
verification.

#### Scenario: Import with network and AI credentials unavailable
- **WHEN** all input resources and the DocForge CLI are local
- **THEN** project creation, inspect, and validate complete successfully offline

#### Scenario: Request build verification
- **WHEN** a user explicitly enables build verification
- **THEN** the importer invokes `docforge build` on the completed project and reports its result without calling renderer internals

### Requirement: Provide actionable and privacy-bounded diagnostics
Every import and installation failure SHALL expose a stable code, severity,
target, concise message, and recommended action. Diagnostics and reports MUST
not expose credentials, environment secrets, unbounded document content, or
unnecessary private absolute paths.

#### Scenario: Missing local image
- **WHEN** a referenced local image does not exist
- **THEN** the diagnostic identifies the bounded source-relative target and recommends restoring or correcting the resource

#### Scenario: DocForge executable is unavailable
- **WHEN** neither `--docforge-bin` nor `docforge` on `PATH` resolves to an executable
- **THEN** import stops before writing and explains the runtime prerequisite

### Requirement: Distribute a verified cross-platform npm artifact
The package SHALL declare its supported Node runtime, owner, version, license,
review cadence, package file allowlist, executable entrypoint, and rollback
boundary. The packed artifact SHALL pass clean-install and macOS, Linux, and
Windows path-behavior tests.

#### Scenario: Inspect packed tarball
- **WHEN** maintainers run `npm pack --dry-run` and inspect the produced package
- **THEN** it contains only declared runtime, Skill, reference, license, and metadata files and contains no repository secrets, fixtures with private data, caches, or build residue

#### Scenario: Run comprehensive fixture
- **WHEN** the packed package imports the comprehensive Markdown fixture in an offline clean environment
- **THEN** the result passes real `docforge inspect`, `docforge validate`, and `docforge build`
