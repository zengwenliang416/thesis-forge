## 1. Package And Skill Contracts

**User outcome:** The product has a clearly named, installable Skill whose
promise is Markdown-to-DocForge-project conversion rather than direct DOCX or
thesis generation.

- [x] 1.1 Record the Yao target lock: read-only engine root, repository-owned
  target root, external state root, `mode: governed`, `archetype: governed`,
  owner, review cadence, output contract, and rollback boundary.
- [x] 1.2 Run Yao `init` for `docforge-project` with the confirmed job,
  `input_files`, primary output, exclusions, constraints, and Project Format V1
  references; verify no Yao engine file changed.
- [x] 1.3 Add failing package identity, Skill frontmatter, interface metadata,
  lifecycle-script absence, package-files allowlist, and governance tests.
- [x] 1.4 Create the npm wrapper at `packages/docforge-project-skill/` with the
  Yao-managed Skill target at
  `packages/docforge-project-skill/docforge-project/`.
- [x] 1.5 Replace generic Yao scaffold prose with lean `SKILL.md`,
  `agents/interface.yaml`, OpenAI metadata, focused references,
  manifest metadata, license, and package exports without placeholder content.
- [x] 1.6 Add trigger positives, negatives, and near-neighbor evals covering
  direct Markdown-to-Word, thesis creation, existing-project edits, translation,
  summary, and explanation collisions.
- [x] 1.7 Run Yao intent confidence, reference scan/synthesis, output risk,
  system model, resource boundary, context budget, governance, and initial
  validation gates.

## 2. Explicit Installation And Rollback

**User outcome:** Users can install or update the Skill in Codex deliberately,
see exactly what changed, and recover the prior managed version.

- [x] 2.1 Add failing fresh-install, existing-unmanaged-target, explicit-update,
  backup, atomic replace, verification, and rollback tests.
- [x] 2.2 Implement `install --target codex` and explicit destination
  resolution without npm lifecycle filesystem writes.
- [x] 2.3 Validate packaged and installed Skill contents before activation and
  report exact version, destination, backup, and rollback command.
- [x] 2.4 Add macOS, Linux, and Windows destination/path tests and reload
  requirements for Codex.

## 3. Import Planning And Input Safety

**User outcome:** Import failures are discovered before any destination is
created, and unsafe files never escape the selected source boundary.

- [x] 3.1 Add failing tests for UTF-8 Markdown discovery, invalid encoding,
  missing input, existing destination, absolute/device paths, traversal,
  symlink escape, remote resources, and collision planning.
- [x] 3.2 Implement immutable import-plan and structured-diagnostic models.
- [x] 3.3 Resolve a deterministic valid project ID, neutral manifest defaults,
  optional explicit metadata, DocForge executable, and destination plan.
- [x] 3.4 Reject all blocking diagnostics before staging writes and redact
  private absolute paths, secrets, and unbounded document content from reports.

## 4. Markdown And Resource Normalization

**User outcome:** Supported Markdown remains readable and semantically intact,
while required DocForge compatibility changes are minimal and auditable.

- [x] 4.1 Build a comprehensive fixture covering headings, paragraphs,
  emphasis, inline code, links, lists, block quotes, tables, code fences,
  inline/display math, footnotes, citations, and local images.
- [x] 4.2 Add failing golden tests for byte-identical passthrough, conservative
  Front Matter mapping, stable figure IDs, asset rewriting, original retention,
  import reports, and deterministic repeated plans.
- [x] 4.3 Implement only the approved normalization rules and retain
  `source/original.md` whenever `document.md` changes.
- [x] 4.4 Copy local assets and optional BibTeX data into deterministic confined
  destinations with hash-based collision handling and no remote fetches.
- [x] 4.5 Emit blocking diagnostics for unsupported or ambiguous syntax instead
  of dropping, executing, or inventing content.

## 5. Project Publication And DocForge Verification

**User outcome:** Every successful result is a real DocForge project that can be
opened, inspected, validated, and built through the existing product.

- [x] 5.1 Add failing staged-publication, cleanup, atomic rename, inspect,
  validate, optional build, and failed-verification retention tests.
- [x] 5.2 Serialize strict `docforge.project.v1` YAML without package-specific
  extensions or duplicated default-path logic.
- [x] 5.3 Write the complete project in a sibling staging directory, run
  `docforge inspect` and `docforge validate --json`, then atomically publish.
- [x] 5.4 Add explicit build verification and prove the npm package never
  generates DOCX except by invoking the installed `docforge build` command.
- [x] 5.5 Verify imported projects open through both project directory and
  `docforge.yaml` entrypoints.
- [x] 5.6 Add the existing citation profile to `docforge-standard` without
  academic required metadata, then prove the neutral comprehensive fixture
  validates and builds.

## 6. Package Quality And Cross-Platform Verification

**User outcome:** The downloadable npm artifact behaves the same in clean
macOS, Linux, and Windows environments and contains only intended files.

- [x] 6.1 Export and validate Yao `reports/skill-ir.json`, compile OpenAI,
  Agent Skills compatible, and generic targets, and verify semantic parity.
- [x] 6.2 Run package lint/type checks, unit/redteam suites, Yao validation,
  trigger optimization, visible/blind/adversarial/route-confusion evals,
  output evals, dependency/license audit, secret scan, and `trust report`.
- [x] 6.3 Create at least five output cases covering `input_files` as a
  `file-backed fixture`, baseline versus with-Skill output, near-neighbor and
  boundary cases, and generate `reports/output_quality_scorecard.md` plus blind
  review artifacts.
- [x] 6.4 Run `npm pack --dry-run`, inspect the tarball allowlist, install it in
  a clean temporary project, and verify CLI help and explicit Codex install.
- [ ] 6.5 Run comprehensive offline import plus real
  `docforge inspect/validate/build` on macOS, Linux, and Windows path fixtures.
- [x] 6.6 Run Yao conformance, runtime permission probes, package verification,
  install simulation, registry audit, and upgrade check against the packed
  target artifacts.
- [x] 6.7 Simulate version upgrade, backup, rollback, and uninstall of only the
  managed Skill files.
- [x] 6.8 Build Skill Atlas, Review Studio, regression history, and promotion
  evidence; label unavailable provider, telemetry, human review, approval,
  metric, and benchmark facts as `missing evidence`.
- [x] 6.9 Run root repository checks affected by workspace/CI changes, OpenSpec
  strict validation, CodeGraph impact review, and `git diff --check`.

## 7. Documentation And Release Readiness

**User outcome:** Users and maintainers understand exactly what the Skill does,
what it refuses, how to install it, and how to verify or roll it back.

- [x] 7.1 Document supported input envelope, output tree, diagnostics, explicit
  install/update/rollback, DocForge runtime prerequisite, and no-direct-DOCX
  boundary.
- [ ] 7.2 Add CI package gates and prepare npm release metadata without storing
  credentials or publishing.
- [ ] 7.3 Recheck npm package-name availability and publisher authority, then
  record checksum, clean-install, compatibility, and release receipts.
- [ ] 7.4 Complete Yao Review Studio, human review or explicit pending state,
  promotion, six-domain verification, independent review, and archive
  readiness; stop before real npm publication, user-level installation, commit,
  push, or release unless each is separately approved.
