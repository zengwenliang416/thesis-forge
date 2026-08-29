# Requirements: docforge-project-skill

## Summary

Provide a Governed Agent Skill, developed through Yao Meta Skill, that converts
one ordinary Markdown document and its local resources into a new DocForge
Project Format V1 directory. The generated project must open in DocForge and
pass `inspect` and `validate` without the Skill generating DOCX directly or
inventing academic metadata.

## Users & Actors

- Authors who already have a Markdown document but not a DocForge project.
- Codex users who want a reusable project-creation workflow.
- Maintainers who package, test, publish, install, update, and review the Skill.
- The installed `docforge` CLI, which remains the authority for project loading,
  inspection, validation, and optional build verification.

## In Scope

- Skill identity: `docforge-project`.
- npm distribution identity: `docforge-project-skill`.
- npm workspace location: `packages/docforge-project-skill/`.
- Locked Yao target:
  `packages/docforge-project-skill/docforge-project/`.
- Yao engine root:
  `/Users/wenliang_zeng/.codex/skills/yao-meta-skill`, treated as read-only.
- Yao runtime state remains in its user cache/state locations and must not be
  written into the repository or Skill target as source.
- Agent Skill source containing `SKILL.md`, `agents/interface.yaml`, deterministic
  scripts, focused references, trigger/output evals, fixtures, and lifecycle
  metadata justified by Governed public distribution.
- Initialization through Yao `init` with the real recurring job, input,
  primary output, exclusions, constraints, local references, `mode: governed`,
  and `archetype: governed`; generic scaffold text must be replaced before
  promotion.
- A platform-neutral Yao Skill IR generated before target-specific adapters or
  npm release packaging.
- Yao Governed gates covering intent confidence, reference scan and synthesis,
  output risk, system model, resource boundary, context budget, trigger
  optimization, visible/blind/adversarial/route-confusion evaluation, output
  evaluation, conformance, trust report, permission probes, package
  verification, install simulation, upgrade checks, Skill Atlas, registry
  audit, Review Studio, promotion, and regression history.
- Governed/file-backed evidence uses the literal labels `input_files`,
  `file-backed fixture`, `owner`, `review cadence`, `output contract`,
  `rollback boundary`, `trust report`,
  `reports/output_quality_scorecard.md`, and `missing evidence` where evidence
  is unavailable.
- Explicit Codex installation into
  `${CODEX_HOME:-$HOME/.codex}/skills/docforge-project` or an explicit
  destination.
- One UTF-8 `.md` or `.markdown` primary input per import.
- A destination that does not already exist; the importer must not merge into,
  delete, or overwrite an existing project.
- A pre-write import plan covering source identity, required rewrites, local
  resources, manifest values, diagnostics, and destination paths.
- A staged, atomic project-directory publication after all mandatory analysis
  and validation steps pass.
- The authoritative Project Format V1 layout:
  `docforge.yaml`, `document.md`, `assets/`, `review/`, and `build/`, with
  optional `references.bib`, `templates/`, provenance, and diagnostic files
  only when justified by the input or selected workflow.
- Minimal neutral manifest values:
  `schema: docforge.project.v1`, a deterministic valid project ID,
  `project.language: und`, `document.source: document.md`,
  `document.type: general`, `resources.assets: assets`, and
  `render.template_id: docforge-standard`.
- Existing defaults for `build/document.docx`,
  `review/document.review.md`, and
  `review/document.review-map.json`; the Skill must not define a competing
  project format.
- Optional explicit language, localized title, authors, organization, date,
  version, keywords, bibliography, and template selection when each value can
  be represented by the current strict manifest.
- Conservative YAML Front Matter extraction. Only known, type-safe neutral
  fields may move to `docforge.yaml`; unknown or ambiguous fields remain
  visible in the import report and are never translated into academic data.
- Preservation of headings, paragraphs, emphasis, inline code, links, lists,
  block quotes, GFM tables, fenced code, inline/display math, footnotes,
  citations, and local images when the current DocForge parser supports them.
- Deterministic compatibility rewrites required by DocForge, including stable
  IDs for standalone images that lack a valid `fig:` ID and safe rewritten
  paths for copied local image resources.
- Byte-identical retention of the original input under `source/original.md`
  whenever `document.md` differs from the input bytes.
- Deterministic local-resource copying under `assets/`, preserving a stable
  relative layout and using content-derived collision handling when necessary.
- No implicit network access. Remote images and other remote resources are not
  downloaded; unsupported remote dependencies block a verified import.
- Bibliography copying and manifest configuration only when the user provides a
  valid local BibTeX file. Citation syntax without a resolvable bibliography is
  a blocking diagnostic.
- Structured diagnostics with code, severity, source location when available,
  target, message, and recommended action.
- Runtime discovery through an explicit `--docforge-bin` or the `docforge`
  executable on `PATH`; no hidden repository-specific fallback.
- Mandatory `docforge inspect` and `docforge validate` execution before success.
- Optional user-requested build verification and mandatory fixture build
  verification in package CI.
- macOS, Linux, and Windows path and installation coverage.
- npm package-content, clean-install, upgrade, rollback, checksum, and
  no-lifecycle-side-effect verification.

## Out of Scope

- Direct Markdown-to-DOCX conversion in the Skill or npm package.
- Reimplementation of DocForge parsing, validation, template resolution,
  compilation, RenderPlan, DOCX rendering, or Office finalization.
- Thesis-only defaults, fabricated author/student/institution/degree/advisor
  data, or automatic selection of an academic template.
- DOCX-to-Markdown, DOCX-to-project, multi-document include, website crawling,
  remote asset downloading, OCR, MDX execution, arbitrary HTML execution, or
  arbitrary TeX macro execution.
- Automatic repair of content whose meaning cannot be represented safely.
- Merging into an existing DocForge project or overwriting an existing source,
  manifest, asset, Review output, or build output.
- npm account creation, namespace transfer, registry credentials, publication,
  user-level installation, release creation, deployment, commit, or push in the
  proposal stage.
- Modification, self-update, or packaging of Yao Meta Skill itself.
- Changes to the DocForge desktop UI, parser, project schema, template schema,
  renderer, or runtime protocol.

## UI Design Impact

- Foundation spec: `openspec/specs/ui-design/design.md`
- No DocForge production UI change.
- `agents/openai.yaml` supplies only Skill discovery metadata and a concise
  default prompt; it does not introduce a workbench screen or visual system.

## Theme & Locale Capability Impact

- DocForge theme support remains `light-only`.
- Theme toggle policy remains `none`.
- DocForge internationalization remains disabled with `zh-CN` as the product
  locale.
- The Skill accepts Unicode Markdown and uses language-neutral diagnostic codes.
  Its initial explanatory copy may be Simplified Chinese, but generated document
  content is never translated.
- No UI prototype is required.

## Architecture & Database Impact

- Foundation spec: `openspec/specs/system-architecture/design.md`
- The npm package is an external preparation layer:
  `Markdown + local resources -> DocForge project -> existing DocForge CLI`.
- The importer may analyze and rewrite Markdown syntax but must not import or
  emulate Python domain, compiler, RenderPlan, renderer, or OOXML code.
- The installed `docforge` CLI remains the acceptance oracle.
- Runtime conversion is local, offline, deterministic, and database-free.

## Frontend-Backend Data Flow Impact

- Foundation spec: `openspec/specs/frontend-backend-data-flow/design.md`
- No HTTP, Tauri, frontend state, or runtime protocol change.
- New package flow:
  `input discovery -> import plan -> staged project -> inspect -> validate ->
  atomic destination publication`.
- Build verification, when explicitly requested, runs after project publication
  through `docforge build` and writes only to the manifest-resolved build path.

## Component Architecture Impact

- Foundation spec: `openspec/specs/component-architecture/design.md`
- Keep Skill routing/instructions in `SKILL.md`, exact Project Format V1
  guidance in `references/`, and repeated deterministic mechanics in scripts.
- Treat Yao Skill IR as the durable semantic source before compiling OpenAI,
  Agent Skills compatible, generic, or other explicitly requested adapters.
- Separate input analysis, Markdown normalization, resource planning,
  manifest serialization, filesystem publication, CLI verification, and
  installer behavior into testable modules without creating a framework.
- The npm CLI and installed Skill must call the same importer implementation.
- No package module may write DOCX, call Office applications, access AI
  providers, or depend on DocForge implementation internals.
- The neutral `docforge-standard` template must expose the existing
  `GB-T-7714-2025` citation capability without introducing academic required
  metadata. Real importer E2E proved this narrow product prerequisite is needed
  for a neutral project containing valid citations to pass `docforge validate`.

## Unresolved Gaps

None for proposal. Yao-generated telemetry, external model review, human blind
review, npm package-name availability, and publisher authorization are
`missing evidence` until their governed collection or Operations stage.
