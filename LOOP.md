# Loop: thesisforge-manifest-v2-review-and-build-report

**Status:** active

**Goal:** ThesisForge has exactly one manifest-based v2 project workflow in which readable Markdown compiles through one typed, lossless pipeline; every manual or live-preview build produces a visible, source-navigable BuildReport while retaining and clearly marking the last successful preview after failure; Review hides technical markers; DOCX passes structural postflight; and every legacy or unsupported construct is rejected by an explicit structured diagnostic in both CLI and desktop workflows.

**Stop condition:** `./stop-check.sh` exits `0`, `## Open` is empty, and `## Blocked` is empty.

**Verification surface:** `LOOP.md`, `lint-loop.sh`, `stop-check.sh`, `scripts/verify_thesisforge_v2_goal.py`, `docs/THESISFORGE_V2_PRODUCT_SPEC.md`, `docs/THESISFORGE_V2_IMPLEMENTATION_PLAN.md`, `spec/format-capabilities.yaml`, `protocol/**`, `tests/**`, `frontend/src/**/*.test.*`, `frontend/e2e/**`, `Makefile`, `pyproject.toml`, root and frontend `package.json`/lockfiles, `src-tauri/Cargo.toml`, `.github/workflows/**`, and every command named by an Open item. A Maker may change a verification-surface file only when the selected item explicitly names it and states why the contract itself changes.

**Cadence:** one fresh Codex cycle per Open item.

**Human gate:** pushing, opening or updating a remote PR, merging, releasing, deploying, deleting user data, changing external services, using credentials, or spending money requires explicit human approval. Local edits, targeted tests, isolated worktrees, and local commits on a non-default loop branch are allowed.

**Commits:** after independent verification, the Checker creates one descriptive local commit per Done item and includes the item ID. Never push automatically.

**Bounds:** hard stop after 120 cycles; halt after 3 consecutive no-progress cycles; move an item to Blocked after 3 failed verification attempts; halt immediately on an unresolved security, data-loss, credential, or product-decision boundary.

**Monitor cadence:** every 3 cycles.

**Code review:** every 5 cycles and once before final stop-check.

**Security review:** after project loader/path-boundary work and before final stop-check.

The loop reads this file first in every cycle and writes it last.

## Rules

- If `**Status:**` is not `active`, do not modify product code.
- One cycle handles exactly one Open item. Finish, split, reject, or block it; never start a second item.
- Before editing, list every repository file expected to change.
- **One implementation item may modify at most 3 repository files.** Source, test, fixture, documentation, schema, configuration, workflow, lockfile, generated output, creation, deletion, move, and rename all count.
- If a fourth file is required, do not edit product code. Split the item into ordered child items, each naming at most 3 exact files and one executable Verify command; update Open, append the Cycle log, and end the cycle.
- `docs/THESISFORGE_V2_PRODUCT_SPEC.md` is normative. `docs/THESISFORGE_V2_IMPLEMENTATION_PLAN.md` is a discovery catalogue, not a script. Re-slice any catalogue task that cannot finish green in one cycle.
- Every completed cycle must leave the selected item’s baseline green. Do not commit intentionally failing normal tests, disabled checks, partial public-entry migrations, or placeholder success paths.
- The Maker never marks its own item Done. An independent Checker audits the diff, rejects unnamed files and scope creep, runs the exact Verify command, and only then moves the item to Done.
- No executable evidence, no Done. Inspection, screenshots, prose, and the Maker’s claim are insufficient.
- Each Open item’s original Behavior and Acceptance text is immutable. Append attempt evidence; do not weaken the requirement after failure.
- On failed verification, record expected versus observed behavior. On the third failure, restore the item’s files and move it to Blocked with the full attempt history.
- Rejected or failed work must not remain in the working tree. Restore only the selected item’s files or discard its isolated worktree; never use a blanket reset that might destroy human work.
- A successful item ends with one local Checker-created commit. An unsuccessful item ends with its touched files restored.
- Do not add legacy compatibility, automatic migration, fallback parsers, parser feature flags, dual protocol payloads, old/new dual fields, or hidden compatibility branches.
- The only accepted document entry is a project directory or `thesisforge.yaml`. A bare thesis Markdown file is invalid.
- `thesisforge.yaml` is the only source for project metadata, resources, template selection, structural options, output policy, and object-level layout overrides.
- `thesis.md` contains readable prose and the minimum stable thesis semantics. YAML Front Matter and legacy `:::` thesis-object containers are invalid.
- Stable IDs, citations, cross-references, and footnotes are semantic data. They may exist in source syntax but must resolve to reader-facing content in Review and DOCX.
- There is exactly one production Markdown parser and one authoritative typed value for each semantic concept. Do not preserve `text + inlines`, `markdown + rows`, raw + resolved, or manually synchronized citation/reference caches.
- Every capability declared in `spec/format-capabilities.yaml` must have an end-to-end path through Source, Typed IR, validation/resolution, Typed RenderPlan, Review, DOCX, and automated evidence.
- Unknown Inline, Block, RenderInstruction, manifest field, object override, or unsupported syntax must fail with a stable diagnostic. Never silently ignore, flatten to prose, return `None`, emit `[kind] {payload}`, or leave raw semantic markers in normal output.
- Review hides Front Matter, legacy containers, stable IDs, citation keys, cross-reference targets, and absolute/local source paths while preserving readable text, numbering, formatted citations, footnotes, tables, figures, listings, algorithms, and rendered math. Literal code is exempt from marker scanning.
- Every manual or live-preview build ends with a typed BuildReport. A terminal build failure may never be represented only by a transient string.
- BuildReport preserves intent, outcome, failed stage, stage lifecycle, all structured diagnostics, primary diagnostic, bounded sanitized logs, and any usable output artifact.
- Manual build failure opens the build-output experience and offers source navigation. Live-preview failure updates the badge/report but must not repeatedly steal editor focus.
- The last successful preview remains visible after a failed attempt and is explicitly marked stale. Failure must not masquerade as current success.
- Stage UI distinguishes pending, running, succeeded, failed, and skipped. Entering a stage does not mark it complete.
- DOCX acceptance is structural: validate OPC parts, relationships, styles, numbering, fields, bookmarks, OMML, footnotes, sections, headers/footers, media, and absence of unresolved markers in normal body text.
- Parser and domain code do not import DOCX/OOXML implementation details. School formatting continues to come from template contracts.
- Core inspect, validate, review, and build work offline without AI services or API keys.
- Stay on Goal. LaTeX import, old-format migration, cloud collaboration, AI writing, unrelated UI redesign, and unrelated refactors are drift.
- Every completed Checker cycle appends exactly one line to `## Cycle log`.

## Discovery

Select work in this order:

1. Restore any regression reported by the previous Checker.
2. Implement the first unmet behavior reported by `scripts/verify_thesisforge_v2_goal.py` when it can be sliced into a green item.
3. Follow `docs/THESISFORGE_V2_IMPLEMENTATION_PLAN.md` dependency order.
4. Address CI, security, or independent review findings that directly block the Goal.

When Open has fewer than three executable items, refill it. Before adding an item:

- inspect current code and tests;
- deduplicate against Open, Done, and Blocked;
- name at most three exact repository files;
- state one observable behavior;
- provide one exact command with a meaningful nonzero failure;
- state whether verification-surface changes are authorized;
- preserve dependency order;
- ensure it can finish green in one cycle.

Use this shape:

```markdown
- [V2-XXX] Observable outcome
  - Files: `path/a`, `path/b`, `path/c`
  - Behavior: one externally observable or contract-level change
  - Verify: `exact command`
  - Acceptance: concrete pass conditions
  - Verification-surface change: `no` or explicit authorization
  - Attempts: 0
```

A regressed Done behavior returns as a new `REG-###` item with fresh evidence. Never rewrite historical Done entries.

## Open

- [V2-305B] Populate typed object fields during parsing
  - Parent: ordered child 2/5 of `V2-305`; depends on `V2-305A`.
  - Files: `src/thesis_forge/core/model.py`, `src/thesis_forge/core/parser.py`, `tests/core/test_thesis_object_model.py`
  - Behavior: figure/listing/algorithm captions and equation display state are populated from parser-normalized source data while current consumers remain green.
  - Verify: `.venv/bin/python -m pytest tests/core/test_thesis_object_model.py tests/test_parser.py tests/test_parser_contract.py`
  - Acceptance: parser-produced typed captions preserve citations/cross-references and object source locations; existing code/body semantics remain unchanged.
  - Verification-surface change: authorized; extends parser/object contract tests.
  - Attempts: 0

- [V2-305C] Compile typed object captions and content
  - Parent: ordered child 3/5 of `V2-305`; depends on `V2-305B`.
  - Files: `src/thesis_forge/core/compiler.py`, `tests/test_compiler.py`
  - Behavior: compiler consumes typed captions/content and derives renderer-neutral instruction text/runs without reading raw caption duplicates.
  - Verify: `.venv/bin/python -m pytest tests/test_compiler.py`
  - Acceptance: caption citations/cross-references/strong text and equation display semantics remain represented in the RenderPlan.
  - Verification-surface change: authorized; migrates compiler object fixtures.
  - Attempts: 0

- [V2-305D] Migrate DOCX/preview object fixtures
  - Parent: ordered child 4/5 of `V2-305`; depends on `V2-305C`.
  - Files: `tests/test_docx_renderer.py`, `tests/test_preview_presentation.py`, `tests/core/test_manifest_resource_validation.py`
  - Behavior: object fixtures construct typed captions/content and preserve DOCX/preview/validation assertions.
  - Verify: `.venv/bin/python -m pytest tests/test_docx_renderer.py tests/test_preview_presentation.py tests/core/test_manifest_resource_validation.py`
  - Acceptance: object XML/preview/resource checks remain green without raw caption fixture fields.
  - Verification-surface change: authorized; migrates object fixtures.
  - Attempts: 0

- [V2-305E] Remove raw thesis-object caption/text fields
  - Parent: ordered child 5/5 of `V2-305`; depends on `V2-305D`.
  - Files: `src/thesis_forge/core/model.py`, `src/thesis_forge/core/parser.py`, `tests/core/test_thesis_object_model.py`
  - Behavior: Figure/Listing/Algorithm no longer store raw caption strings and FootnoteDefinition no longer stores duplicate text; typed inlines/content are authoritative.
  - Verify: `.venv/bin/python -m pytest tests/core/test_thesis_object_model.py tests/test_parser.py tests/test_parser_contract.py tests/test_compiler.py tests/test_docx_renderer.py tests/test_preview_presentation.py`
  - Acceptance: no raw caption/text plus typed-inline duplication remains for the targeted objects; all structured object paths stay green.
  - Verification-surface change: authorized; finalizes the rich thesis-object model contract.
  - Attempts: 0

## Done

- [V2-305A] Add typed thesis-object caption/content primitives
  - Parent: ordered child 1/5 of `V2-305`; parent behavior remains unchanged.
  - Files: `src/thesis_forge/core/model.py`, `tests/core/test_thesis_object_model.py`
  - Behavior: Figure/Listing/Algorithm expose typed caption inline storage; Equation exposes display state; source identity defaults remain stable.
  - Verify: `.venv/bin/python -m pytest tests/core/test_thesis_object_model.py`
  - Acceptance: typed object primitives construct with source identity and caption inline tuples without changing parser/compiler consumers yet.
  - Verification-surface change: authorized; creates focused thesis-object model tests.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; Figure/Listing/Algorithm caption inline tuples, Equation display state, source identity/defaults and citation-bearing captions are covered, exact Verify 4/4, Ruff and `git diff --check` clean; no push.

- [V2-304E2B] Remove raw Table caption/markdown fields
  - Parent: ordered child 7/7 of `V2-304`; depends on `V2-304E2A`.
  - Files: `src/thesis_forge/core/model.py`, `src/thesis_forge/core/parser.py`, `tests/core/test_table_model.py`
  - Behavior: Table owns only typed caption inlines and rows/cells; parser no longer stores pipe-delimited markdown on the model.
  - Verify: `.venv/bin/python -m pytest tests/core/test_table_model.py tests/test_parser.py tests/test_parser_contract.py tests/test_compiler.py tests/test_docx_renderer.py`
  - Acceptance: no Table `markdown` or raw caption source field remains; structured table behavior stays green end to end.
  - Verification-surface change: authorized; finalizes the structured Table contract.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; Table retains only caption_inlines/rows, parser no longer stores caption/markdown, raw Table constructor/read scan is clean, exact Verify 157/157, Ruff and `git diff --check` clean; no push.

- [V2-304E2A] Migrate structured Table fixture captions
  - Parent: ordered child 6/7 of `V2-304`; depends on `V2-304E1`.
  - Files: `tests/test_compiler.py`, `tests/test_docx_renderer.py`
  - Behavior: structured Table fixtures carry caption inlines and no longer pass the raw Table caption field.
  - Verify: `.venv/bin/python -m pytest tests/test_compiler.py tests/test_docx_renderer.py`
  - Acceptance: compiler and DOCX table behavior remains green with caption inlines as the only fixture content source.
  - Verification-surface change: authorized; migrates structured Table fixture captions.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; AST found zero raw `caption`/`markdown` kwargs in Table constructors across compiler and DOCX fixtures, exact Verify 109/109, Ruff and `git diff --check` clean; no push.

- [V2-304E1] Migrate parser table contract to structured fields
  - Parent: ordered child 5/6 of `V2-304`; depends on `V2-304D`.
  - Files: `tests/test_parser_contract.py`
  - Behavior: table contract assertions read caption inlines and typed rows/cells instead of raw Table caption/markdown fields.
  - Verify: `.venv/bin/python -m pytest tests/test_parser_contract.py`
  - Acceptance: parser contract remains green and no assertion depends on Table `markdown` or raw caption storage.
  - Verification-surface change: authorized; migrates parser table contract assertions.
  - Attempts: 2
  - Attempt 1 (2026-08-22): exact Verify exposed a test expectation error for an unmarked `---` separator (alignment is `None`, not `left`); no production change, assertion corrected.
  - Attempt 2 (2026-08-22): Checker PASS; raw Table caption/markdown assertions are replaced by structured caption/row/cell assertions, exact Verify 32/32, Ruff and `git diff --check` clean; no push.

- [V2-304D] Migrate DOCX table fixtures to structured Tables
  - Parent: ordered child 4/5 of `V2-304`; depends on `V2-304C`.
  - Files: `tests/test_docx_renderer.py`
  - Behavior: DOCX table tests construct typed rows/cells and no longer pass pipe-delimited Table markdown.
  - Verify: `.venv/bin/python -m pytest tests/test_docx_renderer.py`
  - Acceptance: all table XML, borders, alignment, empty-table and numbering assertions remain green.
  - Verification-surface change: authorized; migrates DOCX table fixtures.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; migration landed in the V2-304C three-file slice to keep compiler/DOCX regression green, independent D Verify 86/86 and AST found zero Table markdown fixtures; no additional product diff; no push.

- [V2-304C] Compile structured table rows and migrate compiler/DOCX fixtures
  - Parent: ordered child 3/5 of `V2-304`; depends on `V2-304B`.
  - Files: `src/thesis_forge/core/compiler.py`, `tests/test_compiler.py`, `tests/test_docx_renderer.py`
  - Behavior: compiler consumes structured caption/cell rows rather than splitting a Table markdown string; compiler fixtures construct the structured Table shape.
  - Verify: `.venv/bin/python -m pytest tests/test_compiler.py tests/test_docx_renderer.py`
  - Acceptance: table row alignment, header flags and malformed-shape diagnostics remain green without compiler-side pipe parsing.
  - Verification-surface change: authorized; migrates compiler table fixtures.
  - Attempts: 2
  - Attempt 1 (2026-08-22): exact compiler Verify exposed one fixture alignment mismatch (`:---:` expected center but the candidate supplied right); no production behavior issue, corrected before final audit.
  - Attempt 2 (2026-08-22): Checker PASS; compiler pipe-splitting helpers are removed, structured rows/cell inline text drive TableInstruction, DOCX/compiler fixtures contain no Table markdown constructors, exact Verify 109/109, parse-to-compile probe and Ruff/diff-check clean; no push.

- [V2-304B] Populate structured table fields during parsing
  - Parent: ordered child 2/5 of `V2-304`; depends on `V2-304A`.
  - Files: `src/thesis_forge/core/model.py`, `src/thesis_forge/core/parser.py`, `tests/core/test_table_model.py`
  - Behavior: table-container parsing populates typed caption inlines and structured rows/cells with alignment while the current compiler consumer remains green during the ordered migration.
  - Verify: `.venv/bin/python -m pytest tests/core/test_table_model.py tests/test_parser.py tests/test_parser_contract.py`
  - Acceptance: parser-produced table structure preserves header/body shape, alignment and inline cell content; malformed table input remains diagnosable.
  - Verification-surface change: authorized; extends focused table/parser contract coverage.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; valid table containers populate caption inlines, header/body rows, cell alignment and inline citations; malformed shapes leave the structured side empty for the existing compiler diagnostic path, exact Verify 87/87 including markdown-it parser regressions, Ruff and `git diff --check` clean; no push.

- [V2-304A] Add typed table cell and row primitives
  - Parent: ordered child 1/5 of `V2-304`; parent behavior remains unchanged.
  - Files: `src/thesis_forge/core/model.py`, `tests/core/test_table_model.py`
  - Behavior: TableCell owns typed inline content/alignment and TableRow owns header state/cells with stable defaults; the existing Table parser/compiler path is not wired yet.
  - Verify: `.venv/bin/python -m pytest tests/core/test_table_model.py`
  - Acceptance: typed primitives construct, preserve tuple structure and source identity, and do not introduce a second rendered table path.
  - Verification-surface change: authorized; creates focused table-model tests.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; TableCell/TableRow typed defaults, tuple content, alignment/header state, SourceLocation/GeneratedOrigin and compare=False node identity are covered, exact Verify 4/4, Ruff and `git diff --check` clean; no push.

- [V2-303J] Remove the block text fields
  - Parent: ordered child 11/11 of `V2-303`; depends on `V2-303I`.
  - Files: `src/thesis_forge/core/model.py`, `tests/core/test_block_model.py`, `tests/test_preview_presentation.py`
  - Behavior: Heading, Paragraph and ListItem lose the `text` field; block-model tests pin that inlines are the single content source.
  - Verify: `.venv/bin/python -m pytest tests/core/test_block_model.py tests/test_preview_presentation.py tests/core/ tests/test_parser_contract.py tests/test_compiler.py`
  - Acceptance: no authoritative `text + inlines` duplication remains; baselines stay green.
  - Verification-surface change: authorized; finalizes the block-model shape tests.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; Heading/Paragraph/ListItem fields removed, all repo AST model constructors use inlines, block-model/preview/core/parser/compiler Verify 141/141, affected DOCX/adapter/CLI regression 123/123, Ruff/diff-check clean, full suite 1000 passed with 46 known failures plus one non-reproducible LibreOffice QA failure (the same test passed on both baseline `0e473aa` and current isolated reruns); no push.

- [V2-303I] Drop text kwargs from CLI fixtures
  - Parent: ordered child 10/11 of `V2-303`; depends on `V2-303H`.
  - Files: `tests/cli/test_project_commands.py`
  - Behavior: the remaining block `text=` construction drops the kwarg.
  - Verify: `.venv/bin/python -m pytest tests/cli/test_project_commands.py`
  - Acceptance: no block `text=` construction remains in the file; suite stays green.
  - Verification-surface change: authorized; removes redundant fixture kwargs.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; CLI service Heading now uses parser-shaped Text inline with zero model `text=` kwargs, exact Verify 4/4, AST/Ruff/diff-check clean; no push.

- [V2-303H] Drop text kwargs from remaining core/adapter fixtures
  - Parent: ordered child 9/11 of `V2-303`; depends on `V2-303G`.
  - Files: `tests/core/test_source_identity.py`, `tests/test_adapters.py`, `tests/core/test_manifest_resource_validation.py`
  - Behavior: block constructions drop the redundant `text=` kwarg.
  - Verify: `.venv/bin/python -m pytest tests/core/ tests/test_adapters.py`
  - Acceptance: no block `text=` construction remains in the three files; suites stay green.
  - Verification-surface change: authorized; removes redundant fixture kwargs.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; AST found zero `text=` kwargs in model block constructors across all three files, adapter protocol payloads remained unchanged, exact Verify 92/92, Ruff and `git diff --check` clean; no push.

- [V2-303G] Drop text kwargs from compiler fixtures
  - Parent: ordered child 8/11 of `V2-303`; depends on `V2-303F`.
  - Files: `tests/test_compiler.py`
  - Behavior: block constructions drop the redundant `text=` kwarg.
  - Verify: `.venv/bin/python -m pytest tests/test_compiler.py`
  - Acceptance: no block `text=` construction remains in the file; suite stays green.
  - Verification-surface change: authorized; removes redundant fixture kwargs.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; AST found zero `text=` kwargs in Heading/Paragraph/ListItem/FootnoteDefinition model constructors, RenderPlan text assertions remained intact, exact Verify 23/23, Ruff and `git diff --check` clean; no push.

- [V2-303F] Drop text kwargs from docx-renderer fixtures
  - Parent: ordered child 7/11 of `V2-303`; depends on `V2-303E`.
  - Files: `tests/test_docx_renderer.py`
  - Behavior: block constructions drop the redundant `text=` kwarg; inlines stay the single content source.
  - Verify: `.venv/bin/python -m pytest tests/test_docx_renderer.py`
  - Acceptance: no block `text=` construction remains in the file; suite stays green.
  - Verification-surface change: authorized; removes redundant fixture kwargs.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; AST found zero `text=` kwargs in Heading/Paragraph/ListItem/FootnoteDefinition model constructors while RenderPlan instruction text remained intact, exact Verify 86/86, Ruff and `git diff --check` clean; no push.

- [V2-303E] Parsers stop populating block text
  - Parent: ordered child 6/11 of `V2-303`; depends on `V2-303D2`.
  - Files: `src/thesis_forge/core/parser.py`, `src/thesis_forge/core/parser_markdown_it.py`, `src/thesis_forge/core/compiler.py`
  - Behavior: Heading/Paragraph/ListItem construction stops passing `text=`; the now-dead `_fallback_text_runs` path is removed from the compiler.
  - Verify: `.venv/bin/python -m pytest tests/test_parser.py tests/test_parser_markdown_it.py tests/test_parser_backend.py tests/test_parser_contract.py tests/test_compiler.py tests/core/`
  - Acceptance: no parser sets the block `text` field; baselines stay green.
  - Verification-surface change: none.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; parser block constructors no longer pass `text=` for Heading/Paragraph/ListItem/FootnoteDefinition, compiler `_fallback_text_runs` was deleted and all four callers use typed inline runs, exact Verify 172/172, Ruff and `git diff --check` clean, dual-backend probe confirmed text fields remain default-empty while inline_plain_text preserves heading/paragraph/list/footnote content; no push.

- [V2-303D2] Runtime outline derives heading text from inlines
  - Parent: ordered child 5/11 of `V2-303`; depends on `V2-303D1`.
  - Files: `src/thesis_forge/adapters/runtime.py`, `tests/test_adapters.py`
  - Behavior: desktop/project inspect outline projections read heading text via `inline_plain_text` instead of the block `text` field.
  - Verify: `.venv/bin/python -m pytest tests/test_adapters.py`
  - Acceptance: runtime outline text remains unchanged for parser-shaped documents; no runtime outline read of the block `text` field remains.
  - Verification-surface change: authorized; migrates adapter fixtures to parser-shaped inlines.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; both project and desktop inspect outline branches have zero model `block.text` reads, adapter fixtures use parser-shaped inlines with stale-text coverage, exact Verify 33/33, Ruff and `git diff --check` clean; no push.

- [V2-303D1] Preview outline derives heading text from inlines
  - Parent: ordered child 4/11 of `V2-303`; depends on `V2-303C`.
  - Files: `src/thesis_forge/presentation/preview.py`, `tests/test_preview_presentation.py`
  - Behavior: the preview outline projection reads heading text via `inline_plain_text` instead of the block `text` field.
  - Verify: `.venv/bin/python -m pytest tests/test_preview_presentation.py`
  - Acceptance: preview outline text remains unchanged for parser-shaped documents; no preview outline read of the block `text` field remains.
  - Verification-surface change: authorized; migrates preview fixtures to parser-shaped inlines.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; `_outline` has zero model `block.text` reads, parser-shaped preview fixtures and stale-text regression are covered, exact Verify 5/5, Ruff and `git diff --check` clean; no push.

- [V2-303C] Compiler derives block text from inlines
  - Parent: ordered child 3/10 of `V2-303`; depends on `V2-303B`.
  - Files: `src/thesis_forge/core/compiler.py`, `tests/test_compiler.py`, `tests/test_docx_renderer.py`
  - Behavior: bookmark labels, abstract/keywords detection and text fallbacks read `inline_plain_text(block.inlines)` instead of `block.text`; test fixtures that construct text-only blocks gain parser-shaped inlines.
  - Verify: `.venv/bin/python -m pytest tests/test_compiler.py tests/test_docx_renderer.py tests/core/`
  - Acceptance: compiler output is unchanged on the suite; no compiler read of the block `text` field remains.
  - Verification-surface change: authorized; migrates compiler and DOCX renderer fixtures to parser-shaped inlines.
  - Attempts: 2
  - Attempt 1 (2026-08-22): exact Verify exposed 4 DOCX regressions (TOC cached entries, cover content, bibliography title) because text-only fixtures in `tests/test_docx_renderer.py` lacked parser-shaped inlines; compiler and `tests/test_compiler.py` changes were retained, the third file was added within the three-file bound, and no unrelated production path was changed.
  - Attempt 2 (2026-08-22): Checker PASS; compiler uses `inline_plain_text` for heading labels/front-matter detection/keyword roles/list items/heading-paragraph-footnote render text, model block `.text` reads are absent, the new stale-text regression covers labels/roles/list/footnote/reference display, exact Verify 168/168, Ruff and `git diff --check` clean, full suite 46 failed / 999 passed with failures confined to the known acceptance/architecture/distribution/template-v2 clusters; no push.

- [V2-303B] Migrate parser-test block-text pins to derived text
  - Parent: ordered child 2/10 of `V2-303`; depends on `V2-303A`.
  - Files: `tests/test_parser.py`, `tests/test_parser_markdown_it.py`, `tests/test_parser_contract.py`
  - Behavior: assertions on parsed-block `.text` (heading text, list-item text, degraded raw content) re-express against `inline_plain_text(block.inlines)`; green both before and after parsers stop populating the field.
  - Verify: `.venv/bin/python -m pytest tests/test_parser.py tests/test_parser_markdown_it.py tests/test_parser_contract.py`
  - Acceptance: no parser test asserts on the block `text` field; baselines stay green.
  - Verification-surface change: authorized; migrates parser test assertions ahead of the parser change.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; scope exactly the 3 named test files (+21/−17, all 16 HEAD `.text` block-field reads migrated, zero residual `.text` in the files), both disclosed re-pins verbatim with comments (heading `"结果 [@k1] 见 fig:x"` via CrossReference fallback None→target; footnote `"第一行。第二行续行。"` with no SoftBreak), no fixture string/test name/docstring touched, substring and list-equality pins otherwise preserved non-vacuously, exact Verify 82/82, ruff and `git diff --check` clean, baselines 81/81 (tests/core + test_compiler), independent probes green on both backends (heading/footnote/degraded-substring derivations plus no-`text`-kwarg forward simulation on Heading/Paragraph/ListBlock/FootnoteDefinition), full-suite HEAD-vs-candidate failure sets identical at 46 failed / 998 passed confined to the 7 known files; no push.

- [V2-303A] Add typed block structures and the canonical plain-text derivation
  - Parent: ordered child 1/10 of `V2-303`; the parent behavior remains unchanged.
  - Files: `src/thesis_forge/core/model.py`, `tests/core/test_block_model.py`
  - Behavior: add typed BlockQuote(children), CodeBlock(language, code), OrderedList/BulletList(items) with recursive ListItem children, plus the canonical `inline_plain_text` derivation over inlines; pure addition, nothing emits or consumes the new types yet.
  - Verify: `.venv/bin/python -m pytest tests/core/test_block_model.py`
  - Acceptance: recursive lists and typed BlockQuote/CodeBlock are representable; baselines stay green.
  - Verification-surface change: authorized; creates focused block-model tests.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; scope exactly the 2 named files (model.py pure addition +53/−0: ListItem final `children` field, four `@dataclass(slots=True)` Block subclasses with contracted defaults, exhaustive `inline_plain_text` with TypeError naming unknown Inline subclasses and no input mutation; new test file pins every clause non-vacuously), no existing class/field touched, no `__init__.py` export change, src-wide grep shows only pre-existing unrelated `OrderedListSpec` template names and CodeSpan absent outside LOOP.md, exact Verify 20/20, ruff and `git diff --check` clean, baselines 163/163 (tests/core + parser + parser_markdown_it + parser_contract + compiler), independent probes green (subclass/slots/defaults, BulletList→ListItem.children→OrderedList read-back, every inline_plain_text clause incl. CrossReference fallback=None→target and unknown-subclass TypeError, non-mutation), full suite candidate-vs-HEAD failure sets byte-identical at 46 failed / 998 passed confined to the 7 known pre-existing files; no push.

- [V2-302E2] Retire the CodeSpan type
  - Parent: ordered child 7/7 of `V2-302`; depends on `V2-302E1`.
  - Files: `src/thesis_forge/core/model.py`, `tests/core/test_source_identity.py`
  - Behavior: remove the unemitted and undispatched CodeSpan class and drop it from the source-identity class enumeration.
  - Verify: `.venv/bin/python -m pytest tests/core/ tests/test_parser_contract.py tests/test_parser.py tests/test_compiler.py`
  - Acceptance: no CodeSpan reference remains in src or tests; baselines stay green.
  - Verification-surface change: none.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; diff is deletion-only across exactly the 2 named files (CodeSpan dataclass removed from model.py, CodeSpan dropped from the import block and INLINE_CLASSES in test_source_identity.py, the single "insertion" being the INLINE_CLASSES rewrite with zero new semantics), exact Verify 103/103 green, ruff and `git diff --check` clean, independent probes confirm `from thesis_forge.core.model import CodeSpan` raises ImportError while `import thesis_forge.core` and InlineCode/Strong/Emphasis imports work, repo-wide grep finds CodeSpan only in LOOP.md bookkeeping, both parser backends emit InlineCode('code_x') compiling to TextRun(code=True), parser_diff legacy-vs-markdown-it parity OK exit 0 (45 blocks / 81 inlines), and the full suite holds at 46 failed / 978 passed confined to the 7 known pre-existing files; no push.

- [V2-302E1] Re-pin the Strong contract on recursive children
  - Parent: ordered child 6/7 of `V2-302`; depends on `V2-302D2`.
  - Files: `tests/test_parser_contract.py`, `tests/core/test_inline_model.py`
  - Behavior: the Strong contract assertion pins recursive children content (restoring the content pin dropped in `V2-302C`); the inline-model tests cover Strong(children) recursion and its lack of a plain-text value field.
  - Verify: `.venv/bin/python -m pytest tests/test_parser_contract.py tests/core/test_inline_model.py`
  - Acceptance: the Strong contract pins children content; baselines stay green.
  - Verification-surface change: authorized; finalizes the inline contract assertions.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; diff confined to the 2 named files (isinstance-only Strong assertion replaced by a stricter children-content pin `Strong(children==[Text], children[0].value=="粗体")`, contract docstring untouched, 5 new Strong inline-model tests plus the disclosed one-line module-docstring update, all 12 prior tests intact), exact Verify 49/49 (32 contract + 17 inline-model), baselines 205/205 green, ruff and `git diff --check` clean, independent probes confirmed the re-pin is load-bearing (/tmp wrong-value `"错体"` and wrong-child-type `[Emphasis]` variants both fail against the real parser while the committed form passes and the weakened isinstance-only form is strictly weaker), all 5 new tests non-vacuous under dataclass mutations (tuple storage, empty default, field set exactly {location, node_id, origin, children}, nested Strong(Emphasis(Text)) access path, compare=False node_id equality), and both parser backends yield identical `Strong(children=[Text("粗体")])`, full suite 46 failed / 978 passed confined to the 7 known pre-existing files; no push.

- [V2-302D2] Make Strong a recursive container
  - Parent: ordered child 5/7 of `V2-302`; depends on `V2-302D1`.
  - Files: `src/thesis_forge/core/model.py`, `src/thesis_forge/core/parser.py`, `src/thesis_forge/core/compiler.py`
  - Behavior: Strong owns `tuple[Inline, ...]` children parsed recursively; inline registration and citation/footnote collection walk nested inlines; the compiler lowers Strong children with bold applied.
  - Verify: `.venv/bin/python -m pytest tests/test_parser_contract.py tests/test_parser.py tests/test_parser_markdown_it.py tests/test_parser_backend.py tests/test_compiler.py tests/core/`
  - Acceptance: Strong is not a plain string; nested citations/references inside strong register and resolve; baselines stay green.
  - Verification-surface change: none.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; diff was produced by the prior Maker run, parked during the D-split (/tmp/v2-302d.diff), and re-applied verbatim by the orchestrator — audited +27/−4 confined to the 3 named files matching the contract hunks exactly (`Strong.value`→`children`, pre-order `register_inlines` recursion into Strong/Emphasis, recursive compile with `replace(run, bold=True)` on TextRuns only, `citations_from_inlines` container branch, no dual shape/dispatch/fallback), exact Verify 146/146, tests/test_docx_renderer.py 86/86, ruff and `git diff --check` clean, independent probes confirmed both backends yield nested (Text, Citation, Text, CrossReference) children with correct original-text locations, identity-based registration in citations/cross_references/inline_content with container-before-children pre-order, no `value` field on Strong, parser_diff exit 0, nested citation compiles to CitationRun ordinals (1,) with bold nested TextRuns and ReferenceRun passthrough, `**a `code` b**` → TextRun(code=True, bold=True), nested footnote registers and compiles to FootnoteReferenceRun, HEAD-vs-candidate parser_diff normalized dumps byte-identical on both shipped examples, full suite 46 failed / 973 passed confined to the 7 known pre-existing files; no push.

- [V2-302D1] Unpin the legacy Strong shape in the inline-model tests
  - Parent: ordered child 4/7 of `V2-302`; depends on `V2-302C`.
  - Files: `tests/core/test_inline_model.py`
  - Behavior: the Emphasis children test stops using `Strong(value=...)` as its child example (uses a non-Strong inline), so no test pins Strong's legacy plain-string shape before the container flip.
  - Verify: `.venv/bin/python -m pytest tests/core/test_inline_model.py`
  - Acceptance: inline-model tests green both before and after the Strong flip; the Emphasis children assertions keep their intent.
  - Verification-surface change: authorized; adjusts the focused inline-model tests ahead of the flip.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; diff exactly 1 insertion / 2 deletions confined to tests/core/test_inline_model.py (`Strong(value="y")` child swapped for `InlineCode(value="y")`, now-unused Strong import removed, zero Strong matches remain), exact Verify 12 passed, tests/core/ 34 passed, ruff and `git diff --check` clean, independent probes ran the edited file 12 passed against BOTH the current model and a /tmp copy with /tmp/v2-302d.diff applied (import of the flipped Strong(children) model verified via `__file__` + dataclass fields), children-tuple assertions (tuple type, equality, all-Inline) unchanged in substance, full suite 46 failed / 973 passed confined to the 7 known pre-existing files; no push.

- [V2-302C] Flip code-span emission to InlineCode
  - Parent: ordered child 3/6 of `V2-302`; depends on `V2-302B`.
  - Files: `src/thesis_forge/core/parser.py`, `src/thesis_forge/core/compiler.py`, `tests/test_parser_contract.py`
  - Behavior: the parser emits InlineCode(value) instead of CodeSpan and the compiler lowers InlineCode to code runs; contract assertions migrate to InlineCode, and the Strong contract assertion becomes shape-neutral (isinstance-only) as ordered preparation for `V2-302D`.
  - Verify: `.venv/bin/python -m pytest tests/test_parser_contract.py tests/test_parser.py tests/test_parser_markdown_it.py tests/test_parser_backend.py tests/test_compiler.py`
  - Acceptance: nothing constructs or dispatches CodeSpan anymore; baselines stay green.
  - Verification-surface change: authorized; migrates the parser contract inline assertions.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; diff scoped to exactly the 3 named files (parser.py single-site `InlineCode(value=match.group("code_text"), location=location)` construction with CodeSpan→InlineCode import swap, compiler.py `elif isinstance(inline, InlineCode):` dispatch with identical `TextRun(inline.value, code=True)` body and no dual dispatch or reorder, contract test CodeSpan assertion migrated to InlineCode with value pin intact and Strong assertion isinstance-only as disclosed ordered prep), exact Verify 112 passed, baselines tests/core/ + test_docx_renderer 120 passed / 0 failed, ruff and `git diff --check` clean, independent probes confirm in-process parse emits InlineCode(value='code_x', line=1) registered in doc.inline_content, hand-built and parser+compiler-pipeline InlineCode('k = 1') both lower to TextRun('k = 1', code=True), parser_diff legacy-vs-markdown-it parity OK exit 0 (45 blocks / 81 inlines), grep sweep leaves CodeSpan only in model.py definition and test_source_identity.py enumeration, full suite 46 failed / 973 passed confined to the 7 known pre-existing files; no push.

- [V2-302B] Unify markdown-it inline construction onto the shared scanner
  - Parent: ordered child 2/5 of `V2-302`; depends on `V2-302A`.
  - Files: `src/thesis_forge/core/parser_markdown_it.py`
  - Behavior: the markdown-it backend builds all inline content through the shared `_parse_inline_content` scanner; the duplicate `_extract_inlines` token walk and its dead inline-rule machinery are removed.
  - Verify: `.venv/bin/python -m pytest tests/test_parser_markdown_it.py tests/test_parser_backend.py`
  - Acceptance: parse output stays byte-identical under the parity gate; exactly one inline construction site remains.
  - Verification-surface change: none.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; diff scoped to the 1 named file (622→418 lines, 15 insertions / 219 deletions: six `self._extract_inlines` call sites swapped to `_parse_inline_content` with byte-identical args, `_extract_inlines` + 5 inline rules + 5 `ruler` registrations + `_SUPPORTED_INLINE_TOKENS` + `_DISABLED_INLINE_RULES` + 5 regexes deleted, now-unused imports cleaned, docstring re-truthed, block machinery and preflight untouched), repo-wide grep confirms zero remaining references to every deleted symbol and `Token`/`Inline` still used, exact Verify 48/48 passed, baselines 98 passed / 0 failed, ruff and `git diff --check` clean, HEAD-vs-candidate parity probe empty diff on both example theses (complete-thesis 45 blocks/81 inlines, bachelor-thesis 43/78, mdit==legacy on both), adversarial inline probe (mixed strong/citation/crossref/footnote_ref, boundary code spans, soft/hard breaks, escapes, pathological `**a**b**c**`, empty `****`, full-width adjacency) parser_diff OK exit 0 with 12 blocks/66 inlines, in-process smoke asserts 22-in-line sequences identical legacy vs markdown-it and all deleted symbols absent, full suite 46 failed / 973 passed confined to the 7 known pre-existing files; no push.

- [V2-302A] Introduce the recursive inline type set
  - Parent: ordered child 1/5 of `V2-302`; the parent behavior remains unchanged.
  - Files: `src/thesis_forge/core/model.py`, `tests/core/test_inline_model.py`
  - Behavior: add SoftBreak, HardBreak, Emphasis(children), Link(label, destination), InlineMath, InlineCode leaf and CrossReference fallback/display_mode optional fields; containers own `tuple[Inline, ...]` children with no duplicate plain-text field.
  - Verify: `.venv/bin/python -m pytest tests/core/test_inline_model.py`
  - Acceptance: every new type constructs with defaults and inherits node_id/origin; pure addition keeps existing parser/compiler baselines green.
  - Verification-surface change: authorized; creates focused inline-model tests.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; scope exactly the 2 named files with a purely additive 33-insertion diff (six new slotted dataclasses between CodeSpan and CrossReference, Emphasis `tuple[Inline, ...]` children with no plain-text field, fallback/display_mode appended after target, no exports or wiring), exact Verify 12/12 passed, baselines 146 passed / 0 failed, ruff and `git diff --check` clean, independent probes confirmed defaults/unique node_id/origin None/equality-excludes-node_id for all six types, nested Emphasis tuple structure with asdict recursion and `_jsonable` node_id exclusion, and HEAD-vs-candidate CrossReference positional binding identical ("fig:a" binds to inherited location on both) with keyword fallback/display_mode round-trip, full suite 46 failed / 973 passed with failures confined to the 7 known pre-existing files; no push.

- [V2-301B] Add NodeId and complete SourceSpan to the typed model
  - Parent: ordered child 2/2 of `V2-301`; depends on `V2-301A`.
  - Files: `src/thesis_forge/core/model.py`, `tests/core/test_source_identity.py`
  - Behavior: every semantic node has stable internal identity and start/end file/line/column span.
  - Verify: `.venv/bin/python -m pytest tests/core/test_source_identity.py`
  - Acceptance: multi-line nodes and generated origins are representable; existing parser/compiler baselines stay green.
  - Verification-surface change: authorized; creates focused source-identity model tests.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; diff limited to the 2 named files (SourceLocation extended in place with end_line/end_column/source_file appended after line/column, NodeId = str alias plus itertools `_next_node_id()` "n1..", `node_id` with `compare=False` and `origin` appended to Inline/Block/ListItem only, frozen-slots GeneratedOrigin, all additive and defaulted; test file constructs model objects only), exact Verify 11/11 passed, baselines 102 passed / 0 failed, ruff and `git diff --check` clean, 22 independent probes confirmed identity uniqueness with equality ignoring node_id, asdict includes node_id while V2-301A `_jsonable` excludes it, positional span plus end-before-start representability with span fields compare=True, frozen GeneratedOrigin defaults and origin equality, 117 parsed nodes from complete-thesis all carrying unique node_id with origin None and legacy/legacy parser_diff OK exit 0, full-suite failure sets identical HEAD vs candidate (46 pre-existing / 950 passed → 46 / 961 passed, +11 exactly the new tests); no push.

- [V2-301A] Exclude node identity from parse-parity normalization
  - Parent: ordered child 1/2 of `V2-301`; the parent behavior remains unchanged.
  - Files: `qa/tools/parser_diff.py`
  - Behavior: normalized parity JSON generically excludes `compare=False` dataclass fields so per-instance node identity never affects byte parity.
  - Verify: `.venv/bin/python -m pytest tests/test_parser_markdown_it.py tests/test_parser_backend.py`
  - Acceptance: exclusion is a no-op for today's node set; the only failure is the pre-existing `test_parser_backend.py::test_parser_diff_cli_self_check`.
  - Verification-surface change: none; updates QA parity tooling only.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; diff limited to qa/tools/parser_diff.py (import swap asdict→fields, `_jsonable` builds the field dict via `fields()` skipping `field.compare == False` generically with no hardcoded names, `tagged` drops the asdict wrapper, only truthfulness docstring clauses otherwise; zero diff/allow/CLI/exit-code changes), exact Verify 48/48 passed, ruff and `git diff --check` clean, probe a byte-parity no-op confirmed (HEAD vs worktree `--dump-dir` diff -r empty on the 43456-byte normalized JSON, legacy/legacy self-check OK exit 0 on both), probe b exclusion proof (`compare=False` node_id/inner_id with distinct values yield byte-identical JSON with identity keys absent, semantic payload diff still detected, two-parse determinism), probe c import surface (asdict gone, fields used, module compiles, `--help` exits 0), full suite 46 failed / 950 passed identical to the fresh baseline with failures confined to the known template-v2/acceptance/architecture/distribution clusters; no push.

- [V2-215] Validate layout override targets and types
  - Files: `src/thesis_forge/core/validator.py`, `tests/core/test_object_overrides.py`
  - Behavior: layout override target must exist and match the expected semantic object type.
  - Verify: `.venv/bin/python -m pytest tests/core/test_object_overrides.py`
  - Acceptance: missing figure ID and applying figure width to an equation are errors with stable structured diagnostics.
  - Verification-surface change: authorized; creates focused object-override validation tests.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; diff limited to the 2 named files (manifest_layout_objects populated solely from the discovered project manifest, new _validate_layout_overrides rule with stable orphan-layout-override/layout-override-type-mismatch error codes, structured target/details, sorted deterministic ordering, registered in DEFAULT_VALIDATION_RULES), exact Verify 7/7 green, core+application+adapters baselines 67 passed, ruff clean, full-suite failure sets identical between HEAD and candidate (46 pre-existing, zero new), 5 independent probes confirmed orphan/type-mismatch structure, figure-width pass, projectless silence, and sorted validate_document output; no push.

- [V2-214B] Wire the desktop workbench project load flow
  - Parent: ordered child 2/2 of `V2-214`; depends on `V2-214A`.
  - Files: `frontend/src/components/WorkbenchApp.tsx`, `frontend/src/components/WorkbenchApp.project.test.tsx`, `frontend/src/components/WorkbenchApp.test.tsx`
  - Behavior: desktop open flows through `openProject` into `projectOpened`; refresh, validate, build, save and live-preview requests carry the typed project identity and current editor snapshot.
  - Verify: `pnpm --dir frontend test -- WorkbenchApp.project.test.tsx WorkbenchApp.test.tsx`
  - Acceptance: switching projects clears unrelated diagnostics/report and no stale final-preview path authorization survives; project-less web upload sessions keep working unchanged.
  - Verification-surface change: authorized; creates focused workbench project-flow tests and migrates existing workbench regressions.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; diff limited to the 3 named files (WorkbenchApp.tsx routes tauri open through openProject with explicit throw/null-cancel/projectOpened, payloads carry projectRef-stripped {id,root,manifestPath} via conditional spread, refreshSource takes the fresh identity explicitly; new WorkbenchApp.project.test.tsx plus migrated WorkbenchApp.test.tsx), exact Verify green with full suite 17 files/214 tests, typecheck/lint/diff-check clean, 4 independent probes confirmed exact identity keys (no name) on preview/validate/build/save/live-preview, A→B switch clears diagnostics/output/finalPreview with no post-switch resolveFinalPreview of A's descriptor and late resolution dropped, picker null/throw paths, and project-key-free web upload payloads; no push.

- [V2-214A] Carry typed project identity in the command envelope
  - Parent: ordered child 1/2 of `V2-214`; the parent behavior remains unchanged.
  - Files: `frontend/src/transport/dto.ts`, `frontend/src/transport/transports.test.ts`
  - Behavior: dispatch, build, save and preview payloads carry the loaded project identity (id/root/manifestPath) through one typed envelope field.
  - Verify: `pnpm --dir frontend test -- transports.test.ts`
  - Acceptance: project identity survives JSON envelope round-trip for every operation kind; envelopes without project identity remain valid only for the not-yet-migrated web upload path.
  - Verification-surface change: authorized; extends shared transport envelope regression tests.
  - Attempts: 1
  - Attempt 1 (2026-08-21): Checker PASS; diff limited to the 2 named files (dto.ts +3: type-only ProjectIdentityRef import and optional `project?` payload field; transports.test.ts +163 pure additions), exact Verify green with full suite 16 files/204 tests, typecheck/lint/diff-check clean, 8 independent probes confirmed byte-identical Web bodies for inspect/validate/save/build, Tauri pass-through, exact JSON round-trip, project-less positive control, and tsc rejection of envelopes missing required fields; no push.

- [V2-213B] Migrate e2e specs to project selection
  - Parent: ordered child 2/2 of `V2-213`; depends on `V2-213A`.
  - Files: `frontend/e2e/workbench.spec.ts`, `frontend/e2e/acceptance.spec.ts`, `frontend/e2e/tauri-windows.acceptance.ts`
  - Behavior: e2e specs drive the project-opening action instead of the retired standalone Markdown label.
  - Verify: `pnpm --dir frontend exec playwright test --list >/dev/null && ! grep -rn "打开 Markdown 文稿" frontend/e2e/`
  - Acceptance: all e2e specs parse and no e2e reference to the standalone Markdown open label remains.
  - Verification-surface change: authorized; migrates existing e2e project-opening references.
  - Attempts: 1
  - Attempt 1 (2026-08-21): diff contained exactly the 3 named files with 6 pure line-level replacements of `打开 Markdown 文稿` → `打开 ThesisForge 项目`; exact Verify exited 0 (playwright test --list parsed all specs, no e2e reference to the old label remains); ProductBar.tsx:74 aria-label="打开 ThesisForge 项目" matches the replacement; remaining e2e "Markdown" references are only out-of-scope editor/empty-state strings; git diff --check clean.

- [V2-213A] Make the product bar present project selection
  - Parent: ordered child 1/2 of `V2-213`; the parent behavior remains unchanged.
  - Files: `frontend/src/components/ProductBar.tsx`, `frontend/src/components/ProductBar.project.test.tsx`, `frontend/src/components/WorkbenchApp.test.tsx`
  - Behavior: product bar open action, manifest accept text and identity display describe project/manifest selection instead of standalone Markdown selection.
  - Verify: `pnpm --dir frontend test -- ProductBar.project.test.tsx WorkbenchApp.test.tsx`
  - Acceptance: open-button accessible name and file chooser accept text target `thesisforge.yaml`/project selection; a loaded project's display identity and active source are shown; existing workbench assertions migrate to the project-opening labels.
  - Verification-surface change: authorized; creates focused project-opening UI tests and migrates existing workbench assertions.
  - Attempts: 1
  - Attempt 1 (2026-08-21): exact Verify passed with full suite green (16 files, 197 tests incl. 8 new ProductBar project tests and 17 WorkbenchApp tests); typecheck, lint and git diff --check passed. Independent Checker probes (4 tests, then deleted) confirmed all-false-actions render exposes the open control only as "打开 ThesisForge 项目" (old "打开 Markdown 文稿" absent) with accept=".yaml,.yml,text/yaml" and no markdown/.md; a loaded project (本科论文 + thesis.md) shows project name and 活动源 plus dirty 有未保存修改; source-only state shows source name with no project fallback leakage; manifest upload routes to onFileSelected and open click to onChooseSource. Grep of ProductBar.tsx found no remaining markdown advertising.

- [V2-212] Track ProjectIdentity in workspace state
  - Files: `frontend/src/state/workspace.ts`, `frontend/src/state/workspace.project.test.ts`
  - Behavior: workspace state tracks project root, manifest, active source and display identity.
  - Verify: `pnpm --dir frontend test -- workspace.project.test.ts`
  - Acceptance: dirty/save/build permissions derive from loaded project state.
  - Verification-surface change: authorized; creates focused workspace project identity tests.
  - Attempts: 1
  - Attempt 1 (2026-08-21): exact Verify passed with full suite green (15 files, 189 tests incl. 10 new project tests); typecheck, lint and git diff --check passed. Independent Checker probes (6 tests) confirmed projectOpened populates id/root/manifestPath/name plus source/text with full session reset and contentRevision bump, dirty/save/build permissions derive from loaded project state (writable canSave, read-only blocked, fatal-vs-warning build gating, save flow retains identity), sourceOpened clears project with field-by-field parity otherwise, and source-only warning baseline keeps canBuild true.

- [V2-211B] Add the Tauri project transport implementation
  - Parent: ordered child 2/2 of `V2-211`; depends on `V2-211A`.
  - Files: `frontend/src/transport/tauri.ts`, `frontend/src/transport/WorkbenchTransport.project.test.ts`, `frontend/src/transport/transports.test.ts`
  - Behavior: Tauri transport invokes `pick_project` and validates the same typed project identity/source snapshot response.
  - Verify: `pnpm --dir frontend test -- WorkbenchTransport.project.test.ts transports.test.ts`
  - Acceptance: Tauri and Web share the project contract and reject malformed project picker responses.
  - Verification-surface change: authorized; extends shared frontend project transport regression tests.
  - Attempts: 1
  - Attempt 1 (2026-08-21): exact Verify passed 61 focused tests (46 project + 15 transports) with the full suite green (14 files, 179 tests); typecheck, lint and git diff --check passed. Independent Checker probes (5 groups, 18 malformed cases) confirmed exactly one arg-less pick_project invoke, lossless identity/source/text preservation, null-on-cancel, strict rejection of non-object/missing/empty/extra-keyed/unknown-kind/coercible responses, Web/Tauri cross-transport contract equality, and unchanged pick_source openSource behavior.

- [V2-211A] Add the typed project transport contract and Web implementation
  - Parent: ordered child 1/2 of `V2-211`; depends on `V2-210`.
  - Files: `frontend/src/transport/WorkbenchTransport.ts`, `frontend/src/transport/web.ts`, `frontend/src/transport/WorkbenchTransport.project.test.ts`
  - Behavior: Web transport opens project identity and source snapshot through one typed request/response contract.
  - Verify: `pnpm --dir frontend test -- WorkbenchTransport.project.test.ts`
  - Acceptance: project root/manifest/source identity is preserved and Web does not expose an uploaded-file-only project variant.
  - Verification-surface change: authorized; creates focused Web project transport tests.
  - Attempts: 1
  - Attempt 1 (2026-08-21): exact Verify passed 33 focused project transport tests with the full suite green (14 files, 165 tests); typecheck, lint and git diff --check passed. Independent Checker probes (12) confirmed exact identity/source/text preservation, rejection of missing or uploaded-file-only input, strict malformed-response rejection and no coercion or any-casts.

- [V2-210] Authorize Tauri project selection
  - Files: `src-tauri/src/lib.rs`, `src-tauri/src/project_tests.rs`
  - Behavior: desktop project selection accepts a project directory/manifest and returns authorized project source/manifest paths.
  - Verify: `cargo test --manifest-path src-tauri/Cargo.toml project`
  - Acceptance: standalone Markdown selection is rejected and path boundaries remain enforced.
  - Verification-surface change: authorized; creates focused Tauri project selection tests.
  - Attempts: 1
  - Attempt 1 (2026-08-21): initial Cargo Verify passed 4 tests but independent Checker found explicit manifest symlink-root confusion and incomplete Windows/URI path rejection. Final Checker PASS confirmed 6 tests, fmt check, protocol contract regression (28 tests), command registration and corrected boundaries.

- [V2-209] Define the backend workbench project DTO
  - Files: `src/thesis_forge/adapters/dto.py`, `src/thesis_forge/adapters/http.py`, `tests/adapters/test_project_dto.py`
  - Behavior: desktop requests identify project root/manifest and the current source snapshot through one typed transport DTO.
  - Verify: `.venv/bin/python -m pytest tests/adapters/test_project_dto.py tests/test_http_adapter.py`
  - Acceptance: no old bare-source DTO variant remains in the project DTO contract.
  - Verification-surface change: authorized; creates focused backend project DTO tests.
  - Attempts: 1
  - Attempt 1 (2026-08-21): exact Verify passed 17 tests; strict reader, HTTP pre-dispatch validation, old HTTP smoke and Ruff passed. Independent Checker PASS confirmed identity/snapshot/output preservation and no bare-source variant in the project DTO.

- [V2-208] Emit deterministic machine-readable CLI reports
  - Files: `src/thesis_forge/cli.py`, `tests/cli/test_json_reports.py`
  - Behavior: validate and build emit deterministic JSON diagnostics and typed BuildReport data for automation.
  - Verify: `.venv/bin/python -m pytest tests/cli/test_json_reports.py`
  - Acceptance: JSON stdout/stderr and exit codes remain deterministic and failure reports retain complete diagnostics.
  - Verification-surface change: authorized; creates focused CLI JSON report tests.
  - Attempts: 1
  - Attempt 1 (2026-08-21): initial exact Verify exposed CLI report helper syntax and a sanitizer-aware path assertion; corrected within the two named files. Independent Checker PASS confirmed 3 tests, repeated success/failure JSON equality, typed report completeness, deterministic IDs, sanitized paths and Ruff.

- [V2-207] Expose project-only CLI command contracts
  - Files: `src/thesis_forge/cli.py`, `tests/test_cli.py`, `tests/cli/test_project_commands.py`
  - Behavior: inspect, validate and build accept a project directory or manifest path and reject bare Markdown.
  - Verify: `.venv/bin/python -m pytest tests/test_cli.py tests/cli/test_project_commands.py`
  - Acceptance: project commands expose structured JSON/report output without a legacy source-path compatibility branch.
  - Verification-surface change: authorized; creates focused project CLI contract tests.
  - Attempts: 1
  - Attempt 1 (2026-08-21): exact Verify initially exposed legacy fixture expectations after project-only cutover; migrated tests through temporary project fixtures. Independent Checker found project build validation was message-only; CLI now emits typed BuildReport, with final Checker PASS confirming 20 tests, bare-entry rejection, directory/manifest success, failure reports, symlink errors and Ruff.

- [V2-206] Validate manifest resource paths through the project boundary
  - Files: `src/thesis_forge/core/validator.py`, `tests/core/test_manifest_resource_validation.py`
  - Behavior: validation resolves bibliography, template and asset paths from the loaded project rather than Markdown Front Matter.
  - Verify: `.venv/bin/python -m pytest tests/core/test_manifest_resource_validation.py`
  - Acceptance: manifest-derived resources are deterministic and path-boundary failures become structured diagnostics.
  - Verification-surface change: authorized; creates focused manifest resource validation tests.
  - Attempts: 1
  - Attempt 1 (2026-08-21): exact Verify initially exposed invalid fixture citation style and then a non-empty assets fixture directory; corrected within the two named files. Independent Checker found bare ProjectPathError and absolute bibliography detail leakage; fixes added. Final Checker PASS confirmed 4 tests, validator/application smoke (91 tests), structured boundary issues, sanitized details, Ruff and scope.

- [V2-205D] Migrate the headless UI project flow
  - Parent: ordered child 4/4 of `V2-205`; depends on `V2-205A`.
  - Files: `src/thesis_forge/ui/controller.py`, `src/thesis_forge/application/__init__.py`, `tests/test_ui_controller.py`
  - Behavior: headless desktop workspace operations carry project identity and typed editor snapshots into application services.
  - Verify: `.venv/bin/python -m pytest tests/test_ui_controller.py`
  - Acceptance: open, validate and build use the project contract without a legacy source-path compatibility branch.
  - Verification-surface change: authorized; migrates headless UI project-flow regressions.
  - Attempts: 1
  - Attempt 1 (2026-08-21): initial exact Verify exposed test task-runner reuse and project persistence refresh fallback; corrected within the three named files. Final Checker PASS confirmed 43 tests, frontend contract smoke (3 tests), typed project refresh, safe save-as rejection, Ruff and scope.

- [V2-205C] Migrate CLI to project requests
  - Parent: ordered child 3/4 of `V2-205`; depends on `V2-205A`.
  - Files: `src/thesis_forge/cli.py`, `tests/test_cli.py`, `tests/cli/test_project_commands.py`
  - Behavior: CLI inspect, validate, review and build construct the typed project request from a project directory or manifest path.
  - Verify: `.venv/bin/python -m pytest tests/test_cli.py tests/cli/test_project_commands.py`
  - Acceptance: CLI project commands no longer route a bare Markdown path into application services and preserve structured project errors.
  - Verification-surface change: authorized; adds project-only CLI contract tests and migrates existing CLI regressions.
  - Attempts: 1
  - Attempt 1 (2026-08-21): exact Verify initially exposed an over-specific JSON diagnostic assertion and a project test import/format issue; corrected within the three named files. Independent Checker then found uncaught ProjectPathError on symlink escape; CLI capture and root-external symlink regression were added. Final Checker PASS confirmed 19 tests, structured exit 2/no traceback, Ruff and scope.

- [V2-205B3] Migrate HTTP project request transport
  - Parent: ordered child 3/3 of `V2-205B`; depends on `V2-205B1`.
  - Files: `src/thesis_forge/adapters/dto.py`, `src/thesis_forge/adapters/http.py`, `tests/test_http_adapter.py`
  - Behavior: HTTP request/response transport preserves typed project identity, output and editor snapshot fields.
  - Verify: `.venv/bin/python -m pytest tests/test_http_adapter.py`
  - Acceptance: HTTP project requests share the application contract without a second source-path protocol or message-only build error.
  - Verification-surface change: authorized; migrates HTTP project-request and error-contract regressions.
  - Attempts: 1
  - Attempt 1 (2026-08-21): exact Verify initially hit a missing `pytest` import and DTO import ordering; fixed within the three named files. Final Checker PASS confirmed 12 tests, adapter smoke (33 tests), semantic identity validation before dispatcher, field preservation, Ruff and scope.

- [V2-205B2] Migrate sidecar stream project requests
  - Parent: ordered child 2/3 of `V2-205B`; depends on `V2-205B1`.
  - Files: `src/thesis_forge/adapters/sidecar.py`, `tests/test_sidecar.py`, `tests/adapters/test_build_report_events.py`
  - Behavior: sidecar dispatch and build streams carry the typed project request while retaining canonical terminal reports.
  - Verify: `.venv/bin/python -m pytest tests/test_sidecar.py tests/adapters/test_build_report_events.py`
  - Acceptance: sidecar project identity/editor snapshot and BuildReport lifecycle provenance remain typed and incremental.
  - Verification-surface change: authorized; migrates sidecar and terminal-report project-request regressions.
  - Attempts: 1
  - Attempt 1 (2026-08-21): exact Verify passed 17 tests; target Ruff/diff check and HTTP smoke (6 tests) passed. Independent Checker confirmed explicit project service composition, cancellation preservation and progress + canonical completed report with no message-only build failure.

- [V2-205B1] Migrate runtime dispatcher project requests
  - Parent: ordered child 1/3 of `V2-205B`; depends on `V2-205A`.
  - Files: `src/thesis_forge/adapters/runtime.py`, `tests/test_adapters.py`
  - Behavior: desktop and web runtime dispatch constructs and passes the typed project request into application services.
  - Verify: `.venv/bin/python -m pytest tests/test_adapters.py`
  - Acceptance: runtime project identity, output policy and editor snapshot are preserved without a second source-path protocol.
  - Verification-surface change: authorized; migrates runtime adapter project-request regressions.
  - Attempts: 1
  - Attempt 1 (2026-08-21): exact Verify passed 33 tests; target Ruff and diff check passed; independent Checker confirmed typed four-intent dispatch, source/output separation, HTTP/sidecar smoke (11 tests) and no new message-only build path.

- [V2-205A] Migrate application services to the typed project request
  - Parent: ordered child 1/4 of `V2-205`; the parent behavior remains unchanged.
  - Files: `src/thesis_forge/application/services.py`, `tests/application/test_project_services.py`, `tests/test_application_services.py`
  - Behavior: application inspect, validate, preview and build entrypoints load one typed project request before parsing and share one loaded project context.
  - Verify: `.venv/bin/python -m pytest tests/application/test_project_services.py tests/test_application_services.py`
  - Acceptance: manifest-derived project identity, source and resources reach every application service without a bare source-path compatibility union.
  - Verification-surface change: authorized; creates project-service integration tests and migrates application service regressions.
  - Attempts: 1
  - Attempt 1 (2026-08-21): exact Verify initially hit a test import error for `ApplicationDependencies`; corrected within the three named files. Final Checker PASS confirmed 82 tests, existing BuildReport contract regression (6 tests), Ruff and shared typed context/identity coverage.

- [V2-204] Represent application project requests as one typed contract
  - Files: `src/thesis_forge/application/contracts.py`, `tests/application/test_project_request_contract.py`
  - Behavior: represent project identity, intent, output policy and optional editor snapshot in one typed request without compatibility unions.
  - Verify: `.venv/bin/python -m pytest tests/application/test_project_request_contract.py`
  - Acceptance: inspect, validate, review and build request data share the project contract and preserve optional live editor text.
  - Verification-surface change: authorized; creates focused application project-request contract tests.
  - Attempts: 1
  - Attempt 1 (2026-08-21): exact Verify passed 11 tests; target Ruff initially required the existing `Mapping` import to move to `collections.abc`, then exact Verify, Ruff, diff check and existing BuildReport contract regression passed. Independent Checker PASS confirmed typed four-intent coverage and no compatibility union.

- [V2-203] Enforce project-relative path boundaries
  - Files: `src/thesis_forge/project/paths.py`, `tests/project/test_project_paths.py`
  - Behavior: resolve source, assets, bibliography and output paths without traversal, absolute-path, symlink-escape or remote-URL access.
  - Verify: `.venv/bin/python -m pytest tests/project/test_project_paths.py`
  - Acceptance: `..`, absolute paths, symlink escape and remote URLs fail with explicit stable diagnostics.
  - Verification-surface change: authorized; creates focused project path-boundary contract tests.
  - Attempts: 1
  - Attempt 1 (2026-08-21): initial exact Verify exposed a fixture symlink target that was still inside the project root; the fixture was corrected without product changes. Final Checker PASS confirmed 9 tests, root-external symlink probes for source/assets/bibliography/output/review, Ruff and scope.

- [V2-202] Load a project directory or manifest path safely
  - Files: `src/thesis_forge/project/loader.py`, `tests/project/test_manifest_loader.py`
  - Behavior: load `thesisforge.yaml` from a project directory or explicit manifest path and reject bare Markdown, duplicate YAML keys and a missing document source.
  - Verify: `.venv/bin/python -m pytest tests/project/test_manifest_loader.py`
  - Acceptance: the loader returns normalized project root and manifest path; all loader failures carry stable project diagnostic codes.
  - Verification-surface change: authorized; creates focused manifest loader contract tests.
  - Attempts: 1
  - Attempt 1 (2026-08-21): exact Verify initially passed 7 tests, but independent Checker found raw Pydantic input/path leakage, a bare TypeError for unhashable YAML keys, and missing non-manifest/nested-duplicate coverage. Candidate retained; fixes added. Final Checker PASS confirmed 11 tests, strict-warning collection, sanitized stable errors, nested duplicate-key handling, Ruff and scope.

- [V2-201] Define the strict ProjectManifestV2 model
  - Files: `src/thesis_forge/project/model.py`, `tests/project/test_manifest_model.py`, `src/thesis_forge/project/__init__.py`
  - Behavior: define typed `schema`, `project`, `document`, `metadata`, `resources`, `render`, `layout`, `output` and `review` manifest sections with project-relative path values.
  - Verify: `.venv/bin/python -m pytest tests/project/test_manifest_model.py`
  - Acceptance: the v2 schema version is exact; unknown fields and malformed section values fail; path-bearing fields are represented by the typed project-relative path value.
  - Verification-surface change: authorized; creates focused manifest model contract tests.
  - Attempts: 1
  - Attempt 1 (2026-08-21): initial exact Verify exposed a test assertion comparing the typed path object to a raw string; after correction, the independent Checker found and the candidate fixed mutable path invariants, strict bytes handling, schema warning under `PYTHONWARNINGS=error`, and incomplete section/path coverage. Final Checker PASS confirmed 77 tests, strict-warning collection, Ruff and scope.

- [V2-108A] Preserve typed reports in live-preview workspace state
  - Parent: final child of the fresh frontend transport sequence; depends on `V2-111D`.
  - Files: `frontend/src/components/WorkbenchApp.tsx`, `frontend/src/state/workspace.ts`, `frontend/src/components/WorkbenchBuildFlow.test.tsx`
  - Behavior: live-preview `completed.report` diagnostics retain source line, target and details; canceled reports end the active preview without stealing focus or leaving it in `building`.
  - Verify: `pnpm --dir frontend test -- WorkbenchBuildFlow.test.tsx && pnpm --dir frontend typecheck`
  - Acceptance: failed, canceled, and diagnostic-bearing live-preview reports do not overwrite the last successful stale preview or leave an active operation stuck.
  - Verification-surface change: authorized; adds focused live-preview completed-report regression cases.
  - Attempts: 1
  - Attempt 1 (2026-08-21): exact Verify passed 13 files/132 tests and typecheck; initial component assertions were corrected to target the actual final-preview empty-state UI. Independent Checker PASS confirmed diagnostics/details retention, stale/cancel state closure, request/revision guards, no focus stealing, and no legacy terminal production paths.

- [REG-001] Close unstarted upstream stages before runtime terminalization
  - Parent: regression discovered while completing `V2-107B`; restores the terminal snapshot guarantee of Done item `V2-107A` without rewriting its history.
  - Files: `src/thesis_forge/application/services.py`, `tests/application/test_build_stage_lifecycle.py`
  - Behavior: `BuildStageLifecycle.terminalize` marks unstarted upstream pending stages skipped before closing the requested boundary, while still rejecting upstream running stages.
  - Verify: `.venv/bin/python -m pytest tests/application/test_build_stage_lifecycle.py`
  - Acceptance: no terminal snapshot returned by cancellation or failure contains pending/running stages; the existing running-upstream rejection and all prior lifecycle transitions remain green.
  - Verification-surface change: authorized; adds one focused regression case for the completed V2-107A behavior.
  - Attempts: 1
  - Attempt 1 (2026-08-21): exact Verify initially passed 8 tests, but independent Checker found rejected terminalization partially mutated target/history. Validation order was made atomic and a regression test added; second independent Checker PASS confirmed 9 tests, atomicity matrix, Ruff, diff check, and prior transition history.

- [V2-107B] Preserve actual lifecycle provenance in runtime reports
  - Parent: ordered child 2/2 of the fresh backend lifecycle sequence; depends on `V2-107A`.
  - Files: `src/thesis_forge/adapters/runtime.py`, `tests/test_sidecar.py`
  - Behavior: runtime terminal reports serialize the actual application lifecycle snapshot for success, validation failure, stage failure, permission, cancellation, and transport errors instead of rebuilding default stages.
  - Verify: `.venv/bin/python -m pytest tests/test_sidecar.py tests/test_adapters.py::test_build_event_stream_emits_ordered_progress_and_one_success`
  - Acceptance: sidecar cancellation after partial progress retains prior succeeded/current terminal/downstream skipped states in `completed.report`; no cancellation or renderer-failure path calls `BuildReport.default_stages`.
  - Verification-surface change: authorized; migrates sidecar lifecycle provenance assertions.
  - Attempts: 1
  - Attempt 1 (2026-08-21): exact Verify initially exposed parse fixture not emitting progress; fixture corrected to model validate-checkpoint cancellation. Second independent Checker PASS confirmed 6 tests, 20+1 lifecycle matrix cases, no `default_stages` fallback, and terminal reports without pending/running stages.

- [V2-107A] Close application stage lifecycle at terminal boundaries
  - Parent: fresh replacement sequence for the blocked backend lifecycle prerequisites; independent of the frontend sequence.
  - Files: `src/thesis_forge/application/services.py`, `tests/application/test_build_stage_lifecycle.py`
  - Behavior: lifecycle terminalization marks the active stage failed or canceled and all downstream pending/running stages skipped, leaving no pending/running stage in a terminal snapshot.
  - Verify: `.venv/bin/python -m pytest tests/application/test_build_stage_lifecycle.py`
  - Acceptance: render-stage exceptions, cancellation checkpoints, and validation failures produce deterministic terminal stage states without marking an uncompleted stage succeeded.
  - Verification-surface change: authorized; adds focused terminalization lifecycle cases.
  - Attempts: 1
  - Attempt 1 (2026-08-21): exact Verify passed 6 tests, but independent Checker found terminalize could return a snapshot with an unfinished upstream stage; upstream-terminal validation and regression coverage were added. Second independent Checker PASS confirmed 7 tests, state matrix, Ruff, diff check, and scope.

- [V2-111D] Migrate public build-stream fixtures to completed reports
  - Parent: final public fixture child; depends on `V2-114B` and supersedes the unattempted `V2-110B`.
  - Files: `frontend/src/components/WorkbenchBuildFlow.test.tsx`, `frontend/src/transport/transports-build.test.ts`
  - Behavior: public publish and live-preview stream fixtures emit only progress plus `completed.report` and assert typed success, failure, cancellation, diagnostics and output behavior.
  - Verify: `pnpm --dir frontend exec vitest run src/components/WorkbenchBuildFlow.test.tsx src/transport/transports-build.test.ts && pnpm --dir frontend typecheck`
  - Acceptance: focused UI and transport flow tests are green with no legacy `success`/`error` event fixtures or `event.error` assertions; full frontend typecheck is green after the ordered cutover.
  - Verification-surface change: authorized; migrates existing public build-flow and stream regression fixtures.
  - Attempts: 1
  - Attempt 1 (2026-08-21): exact Verify passed 2 files/8 tests and frontend typecheck; independent Checker confirmed all fixtures use canonical `completed.report`, required fields and `report.output.finalPreview`, with no scoped legacy terminal references.

- [V2-114B] Consume canonical reports without losing diagnostics or preview state
  - Parent: fresh replacement child 2/2; depends on `V2-115A`.
  - Files: `frontend/src/components/WorkbenchApp.tsx`, `frontend/src/state/diagnostics.ts`, `frontend/src/transport/dto.ts`
  - Behavior: publish and live-preview consumers branch on report outcome, preserve boolean/null diagnostic details, and resolve authorized final-preview descriptors without clearing the last successful preview on failure.
  - Verify: `pnpm --dir frontend exec vite build`
  - Acceptance: no `event.error` or legacy terminal branch remains in production consumers; report diagnostics retain all scalar values; successful live-preview reports resolve PDF bytes through the authorized descriptor and failed/canceled reports keep prior output stale.
  - Verification-surface change: authorized; changes the frontend diagnostic presentation contract and direct BuildReport consumer.
  - Attempts: 1
  - Attempt 1 (2026-08-21): Vite build and static TypeScript passed, but independent Checker found publish success did not resolve `report.output.finalPreview`; candidate retained. Publish resolver was added; second independent Checker PASS confirmed canonical outcome mapping, diagnostic detail preservation, stale-preview behavior, and clean production legacy scan.

- [V2-115A] Rebuild final-preview output decoding with strict authorization IDs
  - Parent: fresh replacement for blocked `V2-114A`; this task used a new ID and did not mutate blocked preview-decoder history.
  - Files: `frontend/src/transport/buildEvents.ts`, `frontend/src/transport/buildEvents.test.ts`
  - Behavior: canonical report output accepts optional unlocated or authorized `finalPreview` descriptors, preserves null output, and rejects malformed descriptor fields, raw paths, mixed authorization domains, and explicit undefined IDs.
  - Verify: `pnpm --dir frontend exec vitest run src/transport/buildEvents.test.ts`
  - Acceptance: Word/LibreOffice unlocated, Tauri authorization, Web download, and Web live-preview descriptors each have isolated positive tests; null/omitted preview and every invalid ID/engine/label/path/extra-key boundary have isolated negative tests.
  - Verification-surface change: authorized; replaces the blocked decoder candidate with strict authorization-domain fixtures.
  - Attempts: 1
  - Attempt 1 (2026-08-21): exact Verify passed 37 tests, static TypeScript and diff check passed; first independent Checker found missing explicit undefined ID and Microsoft Word authorization coverage. Candidate retained; coverage and static preview type narrowing were added. Final independent Checker PASS confirmed 46 tests, 6 positive/14 negative/4 preservation matrix, and WPS excluded from the static type.

- [V2-111B] Carry authorized final-preview descriptors in canonical reports
  - Parent: fresh replacement child 2/4; independent of the frontend decoder and required before Workbench success consumers change.
  - Files: `protocol/build-report.v2.schema.json`, `src-tauri/src/lib.rs`, `src-tauri/tests/protocol_contract.rs`
  - Behavior: canonical completed reports expose a sanitized final-preview descriptor that Tauri authorizes against the requested derived PDF path, with revocation and live-preview cleanup preserved.
  - Verify: `cargo test --manifest-path src-tauri/Cargo.toml --test protocol_contract`
  - Acceptance: desktop canonical report preview descriptors receive an authorization ID only after path/engine/file-name checks; failed/canceled/new-build paths revoke prior authorization; no raw filesystem path is used as frontend authorization.
  - Verification-surface change: authorized; updates the protocol schema and focused Tauri authorization contract.
  - Attempts: 1
  - Attempt 1 (2026-08-21): exact integration tests passed 26 tests, but the first independent Checker found missing outcome gating, null preview passthrough, schema-invalid empty stages, and absent failed/canceled/live-preview authorization cases. Candidate retained; fixes and tests added. Second independent Checker PASS confirmed 28 tests, schema parse, fmt check, diff check, canonical-only authorization and cleanup boundaries.

- [V2-113A] Finalize schema-faithful decoder evidence with attributable boundary tests
  - Parent: fresh replacement for blocked `V2-112A`; this task used a new ID and did not mutate either blocked decoder history.
  - Files: `frontend/src/transport/buildEvents.ts`, `frontend/src/transport/buildEvents.test.ts`
  - Behavior: the canonical decoder accepts schema-valid stage subsets and pending/running stage statuses while preserving finite string/number/boolean/null diagnostic details and rejecting malformed values.
  - Verify: `pnpm --dir frontend exec vitest run src/transport/buildEvents.test.ts`
  - Acceptance: every listed boundary has an isolated positive or negative regression: arbitrary RFC3339 precision/case, valid and invalid leap seconds, year-zero Gregorian dates, undefined optional dates, reversed line/column ranges, non-finite numbers, unknown primary diagnostics, each extra-key layer, and legacy terminal events.
  - Verification-surface change: authorized; replaces the blocked decoder candidate with independently attributable typed boundary fixtures.
  - Attempts: 1
  - Attempt 1 (2026-08-21): exact Verify passed 5 tests, static TypeScript and diff check passed; first independent Checker found combined test blocks did not independently attribute source extra/range and leap-second negative evidence. Candidate retained; tests were split into 30 isolated boundary cases. Final independent Checker PASS confirmed all 28 boundary probes and 30 tests.

- [V2-106A] Enforce strict frontend DTO primitive validation
  - Parent: fresh replacement sequence for the blocked frontend transport prerequisite; this item did not retry `V2-103A1` and owned only shared DTO primitive guards.
  - Files: `frontend/src/transport/dto.ts`, `frontend/src/transport/transports.test.ts`
  - Behavior: serialized DTO readers accept only exact string enum values and finite numeric diagnostic details, rejecting coercible arrays/objects and non-finite numbers.
  - Verify: `pnpm --dir frontend test -- transports.test.ts && pnpm --dir frontend typecheck`
  - Acceptance: diagnostics, preview discriminators, and command failure kinds reject non-string enum values; `NaN` and infinities in diagnostic details are rejected; no `String(value)` coercion remains in the guarded DTO paths.
  - Verification-surface change: authorized; adds focused transport guard regression cases.
  - Attempts: 1
  - Attempt 1 (2026-08-20): the first independent Checker encountered an unrelated existing `WorkbenchBuildFlow.test.tsx` final-preview assertion failure while the candidate diff was limited to the two named DTO files; the candidate was not restored. The exact Verify was rerun and passed 13 files/84 tests with typecheck, diff-check, and LOOP-LINT; a second independent Checker returned PASS and confirmed the first failure was baseline fluctuation.

- [V2-105A] Model application stage lifecycle transitions
  - Parent: ordered child 1/2 of `V2-105`; the parent requirement remains unchanged: stage started is distinct from succeeded, failures are explicit, and downstream stages are skipped.
  - Files: `src/thesis_forge/application/services.py`, `tests/application/test_build_stage_lifecycle.py`
  - Behavior: application stage lifecycle collector records pending/running/succeeded/failed/skipped states without treating stage entry as completion.
  - Verify: `.venv/bin/python -m pytest tests/application/test_build_stage_lifecycle.py`
  - Acceptance: entering validate remains running until work completes; failed validate marks compile/render/finalize/postflight skipped; transition order is deterministic.
  - Verification-surface change: authorized; creates one focused lifecycle test.
  - Attempts: 0

- [V2-104] Serialize application BuildReport to protocol JSON
  - Files: `src/thesis_forge/adapters/dto.py`, `src/thesis_forge/adapters/runtime.py`, `tests/adapters/test_build_report_dto.py`
  - Behavior: serialize application BuildReport to the JSON Schema shape without dropping nullable fields or diagnostic parameters.
  - Verify: `.venv/bin/python -m pytest tests/adapters/test_build_report_dto.py`
  - Acceptance: success, validation failure, render failure and cancellation round-trip against protocol examples.
  - Verification-surface change: authorized; creates one focused DTO contract test and centralizes runtime serialization on the DTO helper.
  - Attempts: 3
  - Attempt 1 (2026-08-20): exact Verify `.venv/bin/python -m pytest tests/adapters/test_build_report_dto.py` passed 5 tests; related adapter/HTTP/BuildReport regression passed 54 tests; target Ruff, diff-check, and LOOP-LINT passed. Independent probes confirmed the DTO helper is the runtime canonical helper and all three golden examples match, but absolute paths in source/related locations, target, suggestion, diagnostic details, and output paths were serialized unchanged, and nested `NaN`/`Infinity` values inside diagnostic details were accepted. Checker FAIL: the three named files were restored; no Done move, commit, or push.
  - Attempt 2 (2026-08-20): exact Verify `.venv/bin/python -m pytest tests/adapters/test_build_report_dto.py` passed 8 tests; related adapter/HTTP/BuildReport regression passed 54 tests; target Ruff, diff-check, and LOOP-LINT passed. Independent probes confirmed the DTO helper identity/alias, success/validation/render/cancellation golden round-trips, all named path fields, finite scalar details, nested/list/non-finite/non-string-key rejection, and strict JSON encoding. Checker FAIL: a real validation stream with a line-numbered issue and no optional `source.fileName` raised `ValueError: BuildReport source ranges require file and start_line` from `src/thesis_forge/adapters/dto.py:59`, emitted no terminal `completed.report`, and violated nullable source handling; the three named files were restored, no Done move, commit, or push.
  - PASS (2026-08-20): independent Checker exact Verify passed 9 tests; related adapter/HTTP/BuildReport regression passed 54 tests; target Ruff, `git diff --check`, LOOP-LINT, helper identity, four golden round-trips, path/detail strictness, strict JSON, and real validation-stream missing-`source.fileName` probes passed; no push.

- [V2-102B] Add focused backend failure-matrix evidence for typed BuildReports
  - Parent: ordered child 2/2 of `V2-102`; its evidence completes the unchanged parent acceptance that every terminal failure includes outcome, failedStage, complete diagnostics, primaryDiagnosticId, stage states, and sanitized logs, with validation issue code, severity, source line, target, details, and order retained.
  - Files: `src/thesis_forge/adapters/runtime.py`, `tests/adapters/test_build_report_events.py`
  - Behavior: the backend failure matrix covers validation, compile, render, finalize, permission, cancellation, and transport errors through the same typed terminal report path.
  - Verify: `.venv/bin/python -m pytest tests/adapters/test_build_report_events.py`
  - Acceptance: the focused event-stream test proves one terminal `completed.report`, all required report fields, stage lifecycle values, diagnostic ordering/details, and sanitized bounded logs without any message-only error event.
  - Verification-surface change: authorized; creates one focused event-stream test.
  - Attempts: 2
  - Attempt 1 (2026-08-20): exact Verify `.venv/bin/python -m pytest tests/adapters/test_build_report_events.py` passed 8 tests; related adapter/HTTP/BuildReport regression passed 44 tests; target Ruff and diff-check passed. Checker FAIL: the candidate did not prove `pending`/`running` stage statuses, did not verify details for every validation diagnostic, did not inject a path into the asserted log message for sanitization, and the executable test file was restored; no commit or push was created.
  - PASS (2026-08-20): independent Checker exact Verify passed 10 tests; related adapter/HTTP/BuildReport regression passed 44 tests; target Ruff, diff-check, runtime old-protocol scan, and LOOP-LINT passed; the test file is committed as mode `100644`; no push.

- [V2-102A] Migrate backend build stream and existing public stream tests to typed terminal reports
  - Parent: ordered child 1/2 of `V2-102`; the parent requirement remains unchanged: validation, compile, render, finalize, permission, cancellation, and transport failures emit a terminal typed report instead of one error string.
  - Files: `src/thesis_forge/adapters/runtime.py`, `tests/test_adapters.py`, `tests/test_http_adapter.py`
  - Behavior: direct and HTTP build streams terminate cancellation with one `type: completed` event carrying a typed BuildReport instead of a message-only `type: error` event.
  - Verify: `.venv/bin/python -m pytest tests/test_adapters.py::test_build_event_stream_emits_one_typed_cancellation_error tests/test_http_adapter.py::test_http_build_stream_is_incremental_and_cancelable`
  - Acceptance: both existing public stream paths assert the BuildReport terminal shape, preserve incremental progress and cancellation cleanup, and pass without a compatibility or dual-protocol branch.
  - Verification-surface change: authorized; migrates two existing public stream assertions required by the parent contract.
  - Attempts: 1
  - Inherited attempt evidence (2026-08-20): the parent candidate's focused Verify passed 8 tests, but the two existing public stream tests failed on the obsolete `type: error` contract; the Checker restored the candidate files and rejected dual-protocol compatibility.

- [V2-101] Introduce the typed application BuildReport contract
  - Files: `src/thesis_forge/application/contracts.py`, `tests/application/test_build_report_contract.py`
  - Behavior: application-layer success, validation failure, stage failure, cancellation, and permission failure can all be represented by one typed BuildReport with stage lifecycle, complete diagnostics, a primary diagnostic, bounded logs, intent, outcome, and output policy
  - Verify: `.venv/bin/python -m pytest tests/application/test_build_report_contract.py`
  - Acceptance: BuildValidationError preserves every original issue; message-only terminal failures are not part of the application contract; stage states distinguish pending/running/succeeded/failed/skipped
  - Verification-surface change: authorized; creates one focused contract test
  - Attempts: 0

## Blocked

- [V2-114A] Extend frontend BuildReport output decoding for authorized previews
  - Parent: fresh replacement child 1/2 after V2-111C's five-file boundary; depended on completed V2-113A/V2-111B.
  - Files: `frontend/src/transport/buildEvents.ts`, `frontend/src/transport/buildEvents.test.ts`
  - Behavior: canonical report output accepts optional unlocated or authorized `finalPreview` descriptors, preserves null output, and rejects malformed descriptor fields or raw-path-shaped values.
  - Verify: `pnpm --dir frontend exec vitest run src/transport/buildEvents.test.ts`
  - Acceptance: authorized LibreOffice/Microsoft Word descriptors round-trip through `completed.report`; null/omitted preview passes through; extra keys, invalid IDs, unsupported engines and path-bearing fields fail.
  - Verification-surface change: authorized; extends decoder tests for the schema added by V2-111B.
  - Attempts: 3
  - Attempt 1 (2026-08-21): exact Verify passed 36 tests, static TypeScript and diff check passed; independent Checker found LibreOffice `downloadId + authorizationId` mixed-domain descriptors accepted. Candidate retained for correction.
  - Attempt 2 (2026-08-21): exact Verify passed 37 tests, static TypeScript and diff check passed; independent Checker found missing isolated positive coverage for Word/Web descriptor variants, missing invalid live/download ID and label cases, and missing null/omitted value assertions. Candidate retained for correction.
  - Attempt 3 (2026-08-21): exact Verify passed 45 tests and static TypeScript/diff check passed; independent Checker found explicit undefined preview IDs were treated as omitted. Candidate files restored and replaced by fresh `V2-115A`; no commit or push.

- [V2-112A] Rebuild the schema-faithful decoder with statically valid boundary tests
  - Parent: fresh replacement for blocked `V2-111A`; this task used a new ID and did not mutate the earlier blocked history.
  - Files: `frontend/src/transport/buildEvents.ts`, `frontend/src/transport/buildEvents.test.ts`
  - Behavior: the canonical decoder accepts schema-valid stage subsets and pending/running stage statuses while preserving finite string/number/boolean/null diagnostic details and rejecting malformed values.
  - Verify: `pnpm --dir frontend exec vitest run src/transport/buildEvents.test.ts`
  - Acceptance: protocol examples and partial lifecycle reports are accepted; RFC3339 precision/case/leap-second, undefined optional dates, reversed ranges, non-finite numbers, unknown primary diagnostics, extra keys, and legacy terminal events have statically valid regression coverage.
  - Verification-surface change: authorized; replaces the blocked decoder candidate with typed boundary fixtures.
  - Attempts: 3
  - Attempt 1 (2026-08-21): exact Verify passed 4 tests and static TypeScript passed; independent Checker rejected year `0000` Gregorian leap day because `Date.UTC(0, ...)` maps to 1900. Candidate retained for correction.
  - Attempt 2 (2026-08-21): exact Verify passed 4 tests and static TypeScript passed; independent Checker found non-leap `:60` accepted and missing coverage for pending/string/Infinity/same-line reverse ranges and each extra-key layer. Candidate retained for correction.
  - Attempt 3 (2026-08-21): exact Verify passed 5 tests, static TypeScript and diff check passed; independent Checker found source extra-key/range assertions were not independently attributable and valid leap-second coverage lacked invalid-position negatives. Candidate files restored and replaced by fresh `V2-113A`; no commit or push.

- [V2-111A] Make the frontend BuildReport decoder schema-faithful
  - Parent: fresh replacement child 1/4 after `V2-110A` exposed preview authorization and schema-fidelity gaps.
  - Files: `frontend/src/transport/buildEvents.ts`, `frontend/src/transport/buildEvents.test.ts`
  - Behavior: the canonical decoder accepts schema-valid stage subsets and pending/running stage statuses while preserving finite string/number/boolean/null diagnostic details and rejecting malformed values.
  - Verify: `pnpm --dir frontend exec vitest run src/transport/buildEvents.test.ts`
  - Acceptance: protocol examples and schema-valid partial lifecycle reports are accepted; invalid dates, non-finite numbers, unknown primary diagnostics, extra keys, and legacy terminal events are rejected.
  - Verification-surface change: authorized; extends focused decoder cases for schema boundaries.
  - Attempts: 3
  - Attempt 1 (2026-08-21): exact Verify passed 3 tests; independent Checker rejected RFC3339 fractional precision capped at 9 digits, accepted present-but-undefined optional dates, and found insufficient regression coverage. Candidate retained for correction.
  - Attempt 2 (2026-08-21): exact Verify passed 4 tests; independent Checker found lowercase RFC3339 `t/z`, leap-second `:60`, and reversed source ranges were rejected or accepted incorrectly. Candidate retained for correction.
  - Attempt 3 (2026-08-21): exact Verify passed 4 tests and 27/27 boundary probes passed, but the candidate test file itself had TypeScript errors accessing the union report and expressing an extra-key probe; full frontend typecheck also remained red on later migration consumers. Candidate files restored and replaced by fresh `V2-112A`; no commit or push.

- [V2-103A1] Enforce strict BuildReport transport guards and remove legacy event typing
  - Parent: ordered child 1/2 of `V2-103A`; the parent requirement remains unchanged: frontend transport and consumers use typed BuildReport terminal events, not message-only errors.
  - Files: `frontend/src/transport/buildEvents.ts`, `frontend/src/transport/buildEvents.test.ts`, `frontend/src/components/WorkbenchApp.tsx`
  - Behavior: transport guards reject invalid date-time/code fields and message-only errors; publish and live-preview code compile against `completed.report` types.
  - Verify: `pnpm --dir frontend test -- buildEvents.test.ts && pnpm --dir frontend typecheck`
  - Acceptance: BuildReport fields, source spans, related locations, stage statuses, logs, output/stale-preview and diagnostic code/date-time constraints are guarded without `any`; no consumer reads `event.error`.
  - Verification-surface change: authorized; extends the focused transport test and updates the direct event consumer.
  - Attempts: 3
  - Inherited Attempt 1 evidence (2026-08-20): the unsplit candidate passed its exact Verify but accepted invalid diagnostic code/date-time values; it was restored without commit.
  - Attempt 1 (2026-08-20): exact Verify `pnpm --dir frontend test -- buildEvents.test.ts && pnpm --dir frontend typecheck` passed; frontend lint, target diff-check, Workbench/transport regression, and LOOP-LINT passed. Independent strict probes accepted all three protocol examples and rejected invalid source ranges, related locations, stage/output extra keys, 501 logs, 4001-character logs, and unknown primary diagnostic IDs, but incorrectly accepted `startedAt: "2026-02-30T10:05:00Z"`; expected strict RFC3339 date-time rejection, observed acceptance. Checker FAIL: the candidate was restored from the three named files; no Done move, commit, or push.
  - Attempt 2 (2026-08-20): exact Verify `pnpm --dir frontend test -- buildEvents.test.ts && pnpm --dir frontend typecheck` passed 13 test files / 84 tests and typecheck; frontend lint, target diff-check, Workbench/transport regression, and LOOP-LINT passed. Independent strict probes rejected invalid calendar dates/timezones, diagnostic codes, source/related/stage/log/output bounds, and legacy `type: "error"`, but accepted `diagnostics[0].details.count = NaN`; expected strict JSON-number rejection, observed acceptance. Checker FAIL: the three named files were restored; no Done move, commit, or push.
  - Attempt 3 (2026-08-20): exact Verify `pnpm --dir frontend test -- buildEvents.test.ts && pnpm --dir frontend typecheck` passed 13 test files / 84 tests and typecheck; frontend lint, target diff-check, Workbench regression, and LOOP-LINT passed. Strict probes rejected invalid dates, timezone bounds, NaN/Infinity, unknown fields, log bounds, unknown primary diagnostics, and legacy `type: "error"`, but accepted non-string array/object coercions for `intent`, `outcome`, stage/status, severity/category, diagnostic code/stage, log stage/level, progress stage, and success output kind; expected strict type rejection, observed acceptance. Checker FAIL: third failure; the three named files were restored and V2-103A1 moved to Blocked, with no commit or push.

- [V2-105B1] Wire typed stage lifecycle through application service
  - Parent: ordered child 1/2 of `V2-105B`; the parent requirement remains unchanged: backend build events expose the typed lifecycle without breaking cancellation, atomic output, or error handling.
  - Files: `src/thesis_forge/application/services.py`, `tests/test_application_services.py`
  - Behavior: build service emits the typed lifecycle collector states while preserving existing progress, cancellation, atomic output and service error behavior.
  - Verify: `.venv/bin/python -m pytest tests/test_application_services.py`
  - Acceptance: no stage is marked succeeded before work completes; validation/failure transitions and existing output guarantees remain green.
  - Verification-surface change: authorized; updates existing service regression assertions for the lifecycle contract.
  - Attempts: 3
  - Inherited Attempt 1 evidence (2026-08-20): the unsplit B candidate passed its focused service/adapter Verify but the remaining sidecar stream test required a fourth file; candidate files were restored without commit.
  - Attempt 1 (2026-08-20): exact Verify `.venv/bin/python -m pytest tests/test_application_services.py` passed 76 tests; related application/adapter regressions passed 66 tests and LibreOffice finalizer regressions passed 13 tests; independent lifecycle probing found the actual PDF preview export emitted no `preview` running/succeeded transition, and cancellation before finalize start left `finalize`/`postflight`/`preview` pending; target Ruff, diff-check, and LOOP-LINT passed. The two candidate files were restored; no Done move, commit, or push.
  - Attempt 2 (2026-08-20): exact Verify `.venv/bin/python -m pytest tests/test_application_services.py` passed 76 tests; lifecycle collector, adapter/BuildReport, and LibreOffice finalizer regressions passed 73 tests; failure and cancellation probes confirmed validation downstream skips, terminal cancellation states at checks 1-6, and compile/render/finalize/postflight failure transitions. Preview success, exception, and disabled branches passed, but a configured optional exporter returning `None` emitted `preview running` then `preview succeeded` instead of `preview skipped` or `preview failed`; target Ruff, diff-check, and LOOP-LINT passed, while full-repository Ruff reported 12 unrelated existing errors. The two candidate files were restored; no Done move, commit, or push.
  - Attempt 3 (2026-08-20): exact Verify `.venv/bin/python -m pytest tests/test_application_services.py` passed 76 tests; lifecycle collector, adapter/BuildReport, and LibreOffice finalizer regressions passed 79 tests; preview artifact/None/exception, cancellation checks 1-6, validation downstream-skip, atomic-output, and temporary-cleanup probes passed. Expected: a renderer `ApplicationStageError` must emit `render failed` and terminal downstream `skipped` states. Observed: `ApplicationStageError(BuildStage.RENDER, ...)` propagated without lifecycle cleanup, leaving `render` running and `finalize`/`postflight`/`preview` pending. Target Ruff, diff-check, and LOOP-LINT passed. Checker FAIL: third failure; selected files were restored and V2-105B1 moved to Blocked, with no commit or push.

- [V2-105B2] Wire typed lifecycle through runtime and sidecar stream
  - Parent: ordered child 2/2 of `V2-105`; the parent requirement remains unchanged: backend build events expose the typed lifecycle without breaking cancellation, atomic output, or error handling.
  - Files: `src/thesis_forge/adapters/runtime.py`, `tests/test_sidecar.py`
  - Behavior: backend runtime carries typed lifecycle states into terminal reports and sidecar stream tests consume the single completed BuildReport contract.
  - Verify: `.venv/bin/python -m pytest tests/test_sidecar.py tests/test_adapters.py::test_build_event_stream_emits_ordered_progress_and_one_success`
  - Acceptance: sidecar cancellation and success streams remain incremental, terminal reports retain lifecycle states, and no message-only error compatibility branch returns.
  - Verification-surface change: authorized; migrates the remaining public sidecar stream assertion.
  - Attempts: 3
  - Attempt 1 (2026-08-20): exact Verify `.venv/bin/python -m pytest tests/test_sidecar.py tests/test_adapters.py::test_build_event_stream_emits_ordered_progress_and_one_success` passed 5 tests; related adapter/HTTP/BuildReport regression passed 63 tests; target Ruff, diff-check, and LOOP-LINT passed. Independent renderer failure snapshot passed with prior stages succeeded, current render failed, and downstream stages skipped, but cancellation after parse progress before validate reported `parse=running` and `validate=pending` instead of terminal current/previous states with no pending or running stages. Checker FAIL: the two selected files were restored; no Done move, commit, or push.
  - Attempt 2 (2026-08-20): exact Verify `.venv/bin/python -m pytest tests/test_sidecar.py tests/test_adapters.py::test_build_event_stream_emits_ordered_progress_and_one_success` passed 5 tests; related adapter/HTTP/BuildReport regression passed 63 tests; target Ruff, `git diff --check`, and LOOP-LINT passed. Independent renderer failure snapshot passed with prior stages succeeded, current render failed, and downstream stages skipped. Cancellation after parse progress before validate serialized terminal statuses with no pending or running stages, but `_failed_build_report` received no `_build_stage_states` snapshot because the cancellation branch skipped lifecycle finalization and fell back to `BuildReport.default_stages`; the reported `BuildStageLifecycle` snapshot therefore did not enter the terminal `completed.report`. Checker FAIL: the two selected files were restored; no Done move, commit, or push.
  - Attempt 3 (2026-08-20): exact Verify `.venv/bin/python -m pytest tests/test_sidecar.py tests/test_adapters.py::test_build_event_stream_emits_ordered_progress_and_one_success` passed 5 tests; related HTTP/adapter/BuildReport/lifecycle regression passed 66 tests; target Ruff, `git diff --check`, and LOOP-LINT passed. Renderer failure provenance passed with prior stages succeeded, current render failed, and downstream stages skipped. Expected: after parse progress, cancellation at the validate checkpoint must use the actual `BuildStageLifecycle` terminal snapshot so parse is succeeded, validate is skipped/failed, all downstream stages are skipped, and that snapshot enters `completed.report`. Observed: the cancellation branch at `src/thesis_forge/adapters/runtime.py:869` called `BuildReport.default_stages(...)`; the independent provenance probe failed with `default_stages used for cancellation: validate/canceled`, so the report did not prove actual lifecycle provenance. Checker FAIL: third failure; selected files were restored and V2-105B2 moved to Blocked, with no commit or push.

## Cycle log

- 2026-08-20 - V2-101 Checker PASS; exact Verify `.venv/bin/python -m pytest tests/application/test_build_report_contract.py` passed 6 tests; scope limited to the two named implementation/test files, no push.
- 2026-08-20 - V2-102 Checker FAIL; exact Verify passed 8 tests, but two existing build-stream tests failed on the obsolete `type: error` contract; selected files restored, no commit or push.
- 2026-08-20 - V2-102 split into ordered children V2-102A and V2-102B after Checker evidence showed four repository files were required; no product code edited in the split cycle.
- 2026-08-20 - V2-102A Checker PASS; exact Verify passed 2 tests, related adapter tests passed 38 tests and BuildReport contract tests passed 6 tests; ruff check and git diff --check passed, no push.
- 2026-08-20 - V2-102B Checker FAIL; exact Verify passed 8 tests and related adapter/HTTP/BuildReport regression passed 44 tests, but the focused evidence did not prove all required lifecycle, diagnostic-details, and path-sanitization assertions; candidate files restored, no commit or push.
- 2026-08-20 - V2-102B Checker PASS; exact Verify passed 10 tests, related adapter/HTTP/BuildReport regression passed 44 tests, target Ruff/diff-check and LOOP-LINT passed, no push.
- 2026-08-20 - V2-103 split into V2-103A because `WorkbenchApp.tsx` directly consumed the obsolete `event.error` branch; V2-104 and V2-105 refilled Open, with no product code edited in the split cycle.
- 2026-08-20 - V2-103A Checker FAIL Attempt 1; exact Verify passed, but strict schema guard and live-preview completed-report cancellation/diagnostic handling failed acceptance; three candidate files restored, no commit or push.
- 2026-08-20 - V2-103A split into ordered children V2-103A1 and V2-103A2 after Checker evidence required separate transport strictness and live-preview workspace/test files; no product code edited in the split cycle.
- 2026-08-20 - V2-103A1 Checker FAIL Attempt 2; exact Verify passed, but strict JSON-number guard accepted `diagnostics[0].details.count = NaN`; three candidate files restored, no Done move, commit, or push.
- 2026-08-20 - V2-103A1 Checker FAIL Attempt 3; exact Verify passed 13 test files / 84 tests and typecheck, frontend lint/diff-check, Workbench regression, and LOOP-LINT passed; strict probes accepted non-string array/object coercions for enum/code fields, so expected type-strict rejection was not met; three candidate files restored and V2-103A1 moved to Blocked, no commit or push.
- 2026-08-20 - V2-104 Checker FAIL Attempt 1; exact Verify passed 5 tests and related adapter/HTTP/BuildReport regression passed 54 tests, but independent probes found absolute-path leakage across report fields and accepted nested non-finite diagnostic details; three named files restored, no commit or push.
- 2026-08-20 - V2-104 Checker FAIL Attempt 2; exact Verify passed 8 tests and related adapter/HTTP/BuildReport regression passed 54 tests; target Ruff, diff-check, and LOOP-LINT passed, but a real validation stream with a line-numbered issue and no optional `source.fileName` raised during DTO serialization and emitted no terminal `completed.report`; three named files restored, no commit or push.
- 2026-08-20 - V2-104 Checker PASS Attempt 3; exact Verify passed 9 tests, related adapter/HTTP/BuildReport regression passed 54 tests, target Ruff/diff-check, LOOP-LINT, strict DTO probes, and real validation-stream missing-fileName probe passed; no push.
- 2026-08-20 - V2-105 split into ordered children V2-105A and V2-105B after existing progress callback consumers and service regressions showed the original two-file slice could not stay green; no product code edited in the split cycle.
- 2026-08-20 - V2-105A Checker PASS; exact Verify passed 3 tests, service/adapter regression passed 77 tests, application BuildReport regression passed 25 tests, lifecycle probe covered all report stages and required transitions, target Ruff/diff-check and LOOP-LINT passed; no push.
- 2026-08-20 - V2-105B Checker FAIL Attempt 1; exact Verify passed 77 tests, but the sidecar cancellation regression failed on the obsolete `type: error` assertion and target Ruff reported B010 for runtime `setattr`; three named files restored to `HEAD`, no dual protocol, no Done move, commit, or push.

- 2026-08-20 - V2-105B split into ordered children V2-105B1 and V2-105B2 because the remaining sidecar public stream assertion required a fourth file; no product code edited in the split cycle.
- 2026-08-20 - V2-105B1 Checker FAIL Attempt 1; exact Verify passed 76 tests, related application/adapter and LibreOffice finalizer regressions passed 66 and 13 tests, but independent lifecycle probing found missing preview success events and pending downstream states on pre-finalize cancellation; selected files restored, no Done move, commit, or push.
- 2026-08-20 - V2-105B1 Checker FAIL Attempt 2; exact Verify passed 76 tests and lifecycle/adapter/BuildReport/finalizer regressions passed 73 tests, but a configured optional preview exporter returning `None` was emitted as `preview succeeded`; target Ruff/diff-check and LOOP-LINT passed, selected files restored, no Done move, commit, or push.
- 2026-08-20 - V2-105B1 Checker FAIL Attempt 3; exact Verify passed 76 tests and lifecycle/adapter/BuildReport/finalizer regressions passed 79 tests; preview, cancellation, validation, atomic-output, and cleanup probes passed, but a wrapped renderer `ApplicationStageError` left `render` running and `finalize`/`postflight`/`preview` pending instead of emitting terminal failure/skip states; target Ruff/diff-check and LOOP-LINT passed, selected files restored and V2-105B1 moved to Blocked, no commit or push.

- 2026-08-20 - V2-105B2 Checker FAIL Attempt 1; exact Verify passed 5 tests, related adapter/HTTP/BuildReport regression passed 63 tests, target Ruff/diff-check and LOOP-LINT passed, and the renderer failure snapshot passed, but cancellation after parse progress before validate left `parse=running` and `validate=pending`; selected files restored, no Done move, commit, or push.
- 2026-08-20 - V2-105B2 Checker FAIL Attempt 2; exact Verify passed 5 tests, related adapter/HTTP/BuildReport regression passed 63 tests, target Ruff/diff-check and LOOP-LINT passed, renderer failure snapshot passed, but cancellation did not pass the reported BuildStageLifecycle snapshot into terminal completed.report and fell back to default stages; selected files restored, no Done move, commit, or push.
- 2026-08-20 - V2-105B2 Checker FAIL Attempt 3; exact Verify passed 5 tests, related HTTP/adapter/BuildReport/lifecycle regression passed 66 tests, target Ruff/diff-check and LOOP-LINT passed, renderer failure provenance passed, but cancellation provenance still called `BuildReport.default_stages(...)` instead of using the actual terminal `BuildStageLifecycle` snapshot; selected files restored and V2-105B2 moved to Blocked, no commit or push.

- 2026-08-20 - V2-106A Checker PASS; fresh topology replaced the dependent V2-103A2 Open item without retrying blocked IDs; exact Verify passed 13 frontend files/84 tests and typecheck, the second independent Checker confirmed strict DTO guards, and no push.
- 2026-08-20 - V2-106B was re-sliced into fresh V2-109A/V2-109B after CodeGraph found five affected frontend source/test files; no product code was edited in the split cycle, and the next queue item is V2-109A.
- 2026-08-20 - V2-109A Checker FAIL Attempt 1; candidate decoder/consumer tests passed, but exact typecheck exposed required changes in `WorkbenchBuildFlow.test.tsx` and `transports-build.test.ts` plus BuildReport diagnostic presentation mapping; selected three files were restored, and the work was re-sliced into V2-110A/V2-110B without a commit.
- 2026-08-21 - V2-110A Checker FAIL Attempt 1; exact decoder Verify passed, but independent review found live-preview success would discard the derived output without an authorized descriptor, the decoder rejected schema-valid pending/running stage subsets, and Workbench dropped boolean/null diagnostic details; selected files restored and work re-sliced into V2-111A through V2-111D without a commit.
- 2026-08-21 - V2-111A moved to Blocked after three independent Checker failures; selected decoder files were restored, and fresh V2-112A replaced it without mutating the blocked history.
- 2026-08-21 - V2-112A moved to Blocked after three independent Checker failures; selected decoder files were restored, and fresh V2-113A replaced it to isolate evidence attribution without mutating blocked history.
- 2026-08-21 - V2-113A Checker PASS; exact Verify passed 30 tests, static TypeScript and diff check passed, independent boundary audit passed 28/28, and only the two named decoder files are ready for local commit; no push.
- 2026-08-21 - V2-111B Checker PASS; exact Tauri integration Verify passed 28 tests, schema parse/fmt/diff checks passed, and canonical preview authorization plus cleanup boundaries were independently confirmed; no push.
- 2026-08-21 - V2-111C was re-sliced before product edits after CodeGraph found five affected frontend files, including the decoder/test pair required for `output.finalPreview`; no product code was edited in the split cycle, and the next queue is V2-114A.
- 2026-08-21 - V2-114A moved to Blocked after three independent Checker failures; selected decoder files were restored, and fresh V2-115A replaced it to close explicit undefined-ID coverage without mutating blocked history.
- 2026-08-21 - V2-115A Checker PASS; exact Verify passed 46 tests, static TypeScript and diff check passed, and the independent preview descriptor matrix passed; no push.
- 2026-08-21 - V2-114B Checker PASS; Vite build, static TypeScript, diff check, and scoped production legacy scan passed; publish/live-preview report consumers preserve authorized preview and diagnostic details; no push.
- 2026-08-21 - V2-111D Checker PASS; exact Verify passed 2 files/8 tests and frontend typecheck, scoped legacy scan was clean, and no push.
- 2026-08-21 - V2-107A Checker PASS; exact Verify passed 7 tests, independent lifecycle matrix/Ruff/diff checks passed, and no push.
- 2026-08-21 - V2-107B Checker PASS; exact Verify passed 6 tests, lifecycle matrix/Ruff/diff checks passed, no runtime `default_stages` fallback remained, and no push.
- 2026-08-21 - REG-001 opened after V2-107B independent probing found a V2-107A terminalization regression for unstarted upstream stages; the two correction files remain uncommitted for the next cycle.
- 2026-08-21 - REG-001 Checker PASS; exact Verify passed 9 tests, atomicity matrix/Ruff/diff checks passed, and the V2-107A regression was committed locally without push.
- 2026-08-21 - V2-108A Checker PASS; exact Verify passed 13 files/132 tests and typecheck, live-preview stale/cancel/revision guards passed, and no legacy production terminal paths remained.
- 2026-08-21 - V2-201 Checker PASS; exact Verify and `PYTHONWARNINGS=error` passed 77 manifest model tests, strict path/schema/section coverage and Ruff passed, and no push.
- 2026-08-21 - V2-202 Checker PASS; exact Verify and strict-warning Verify passed 11 loader tests, stable sanitized project errors and nested duplicate-key coverage passed, and no push.
- 2026-08-21 - V2-203 Checker PASS; exact Verify passed 9 path-boundary tests, root-external symlink probes and Ruff passed, and no push.
- 2026-08-21 - V2-204 Checker PASS; exact Verify passed 11 project request tests, existing BuildReport contract regression passed 6 tests, Ruff passed, and no push.
- 2026-08-21 - V2-205 split into ordered children V2-205A through V2-205D after CodeGraph found application service callers across services, adapters, CLI, UI and existing regressions beyond the three-file bound; no product code edited.
- 2026-08-21 - V2-205A Checker PASS; exact Verify passed 82 application service tests, existing BuildReport contract regression passed 6 tests, Ruff passed, and no push.
- 2026-08-21 - V2-205B split into ordered children V2-205B1 through V2-205B3 after CodeGraph found runtime, sidecar, HTTP/DTO and regression-test boundaries beyond the three-file slice; no product code edited.
- 2026-08-21 - V2-205B1 Checker PASS; exact Verify passed 33 adapter tests, HTTP/sidecar smoke passed 11 tests, Ruff passed, and no push.
- 2026-08-21 - V2-205B2 Checker PASS; exact Verify passed 17 sidecar/BuildReport tests, HTTP smoke passed 6 tests, Ruff passed, and no push.
- 2026-08-21 - V2-205B3 Checker PASS; exact Verify passed 12 HTTP tests, adapter smoke passed 33 tests, semantic identity validation and Ruff passed, and no push.
- 2026-08-21 - V2-205C Checker PASS; exact Verify passed 19 CLI tests, root-external symlink CLI probes and Ruff passed, and no push.
- 2026-08-21 - V2-205D Checker PASS; exact Verify passed 43 UI controller tests, frontend contract smoke passed 3 tests, typed project refresh/save-as boundaries and Ruff passed, and no push.
- 2026-08-21 - V2-206 Checker PASS; exact Verify passed 4 manifest resource tests, validator/application smoke passed 91 tests, structured path errors and sanitized details passed, and no push.
- 2026-08-21 - V2-207 Checker PASS; exact Verify passed 20 CLI tests, bare-entry/project/typed-failure probes and Ruff passed, and no push.
- 2026-08-21 - V2-208 Checker PASS; exact Verify passed 3 JSON report tests, repeated success/failure outputs were deterministic, report completeness/sanitization and Ruff passed, and no push.
- 2026-08-21 - V2-209 Checker PASS; exact Verify passed 17 DTO/HTTP tests, strict project reader and HTTP smoke/Ruff passed, and no push.
- 2026-08-21 - V2-210 Checker PASS; exact Verify passed 6 Tauri project tests, fmt/protocol regression passed, cross-platform path boundaries and command registration passed, and no push.
- 2026-08-21 - V2-211A Checker PASS; exact Verify passed 33 project transport tests with full suite green (165 tests), typecheck/lint/diff-check passed, 12 independent probes confirmed identity preservation and strict rejection; no push.
- 2026-08-21 - V2-211B Checker PASS; exact Verify passed 61 focused tests with full suite green (179 tests), typecheck/lint/diff-check passed, independent probes confirmed single pick_project invoke, lossless typed validation, cross-transport contract and unchanged openSource; no push.
- 2026-08-21 - V2-212 Checker PASS; exact Verify passed with full suite green (15 files, 189 tests), typecheck/lint/diff-check passed, 6 independent probes confirmed project identity tracking, reset parity with sourceOpened, and project-derived dirty/save/build permissions; no push.
- 2026-08-21 - V2-213 split into ordered children V2-213A and V2-213B after the project-opening label change was found to require ProductBar plus new focused tests, four existing WorkbenchApp vitest assertions, and three e2e specs — beyond the two-file slice; Open refilled with V2-214 per the catalogue; no product code edited in the split cycle.
- 2026-08-21 - V2-213A Checker PASS; exact Verify passed with full suite green (16 files, 197 tests), typecheck/lint/diff-check passed, 4 independent probes confirmed project-selection label, yaml-only accept, project identity plus active source display and handler routing; no push.
- 2026-08-21 - V2-213B Checker PASS; exact Verify exited 0, diff limited to the 3 named e2e files with 6 pure label replacements matching ProductBar aria-label "打开 ThesisForge 项目", git diff --check clean; no push.
- 2026-08-21 - Open refilled with V2-215 and V2-301 per the catalogue dependency order after V2-213B left one Open item; validator.py already loads the project manifest and model.py nodes are additive-safe, so both slices fit the three-file bound; no product code edited.
- 2026-08-21 - V2-214 split into ordered children V2-214A and V2-214B after inspection found the typed envelope project field lives in dto.ts (a fourth file) and the web project-open flow lacks a backend project workspace path; the web upload path stays unchanged until a follow-up backend item is refilled; no product code edited in the split cycle.
- 2026-08-21 - V2-214A Checker PASS; exact Verify green with full suite 16 files/204 tests, typecheck/lint/diff-check clean, diff limited to the 2 named files with single-source ProjectIdentityRef import and optional `project?` payload field, 8 independent probes confirmed byte-identical serialization, Tauri pass-through, JSON round-trip, project-less positive control, and tsc rejection of invalid envelopes; no push.
- 2026-08-22 - V2-214B Checker PASS; exact Verify green with full suite 17 files/214 tests, typecheck/lint/diff-check clean, diff limited to the 3 named files, 4 independent probes confirmed exact {id,root,manifestPath} identity on all five request kinds, A→B switch reset with no stale final-preview resolution, picker cancel/failure paths, and project-key-free web upload payloads; no push.
- 2026-08-22 - Open refilled with V2-302 per the catalogue dependency order after V2-214B left two Open items; the recursive Inline replacement is expected to need re-slicing when its cycle arrives (parser and consumer construction sites exceed the two-file catalogue slice); no product code edited.
- 2026-08-22 - Open refilled with V2-303 per the catalogue dependency order; the basic Block replacement may need re-slicing when its cycle arrives (consumer construction sites exceed the two-file catalogue slice); no product code edited.
- 2026-08-22 - V2-301 split into ordered children V2-301A and V2-301B after the Maker proved the auto-generated `node_id` dataclass field breaks `qa/tools/parser_diff.py` asdict-based parity normalization (30 test_parser_markdown_it parity tests plus 3 test_parser_backend parity tests newly fail; unavoidable while identity is a real per-instance field); V2-301A updates QA parity normalization first, V2-301B carries the model change; failed work restored, no product code kept in the split cycle; full-suite baseline re-measured at 47 failed / 949 passed (`test_parser_backend.py::test_parser_diff_cli_self_check` already fails pre-change).
- 2026-08-22 - V2-215 Checker PASS; exact Verify 7/7 green, baselines (67 core/application/adapter tests) and ruff clean, full-suite failure sets identical HEAD vs candidate (46 pre-existing, zero new), 5 independent probes confirmed structured orphan/type-mismatch errors, figure-width pass, projectless silence, and sorted output; no push.
- 2026-08-22 - V2-301A Checker PASS; diff scoped to qa/tools/parser_diff.py with generic field.compare exclusion, exact Verify 48/48 green, HEAD-vs-worktree byte-parity probe diff empty, compare=False exclusion and semantic-detection probes green, full suite 46 failed / 950 passed matching the fresh baseline; no push.
- 2026-08-22 - V2-301B Checker PASS; exact Verify 11/11 green, baselines 102 passed / 0 failed, 22 independent probes confirmed identity/span/GeneratedOrigin semantics plus `_jsonable` node_id exclusion and parsed-node identity, full-suite failure sets identical HEAD vs candidate (46 → 46, +11 passed); no push.
- 2026-08-22 - V2-302 split into five ordered children V2-302A…E after investigation showed the Strong(children) shape change and CodeSpan→InlineCode rename atomically span model.py + both parser backends + compiler.py + test_parser_contract.py (5 files); V2-302A adds the new recursive types additively, V2-302B unifies markdown-it inline construction onto the shared byte-equivalent `_parse_inline_content` scanner so each flip fits three files, V2-302C/V2-302D flip InlineCode emission and Strong recursion, V2-302E retires CodeSpan and re-pins the Strong contract (the Strong contract assertion goes shape-neutral in V2-302C as disclosed ordered preparation); no product code edited in the split cycle.
- 2026-08-22 - V2-302A Checker PASS; purely additive model.py diff (6 new inline types + CrossReference fallback/display_mode), Verify 12/12, baselines 146/146, probes confirmed identity semantics + HEAD-identical positional binding, full suite 46/973 confined to the 7 known files; no push.
- 2026-08-22 - V2-302B Checker PASS; single-file 622→418 diff with six call sites moved onto `_parse_inline_content` and all dead inline-rule machinery deleted, Verify 48/48, baselines 98/98, HEAD-vs-candidate parity diffs empty on both examples plus adversarial and in-process smoke probes green, full suite 46/973 confined to the 7 known files; no push.
- 2026-08-22 - Protocol note: commit f91b0d8 (chore: ignore local source-delivery archives, .gitignore +3) was created inside the V2-302B subagent window contrary to Maker/Checker commit discipline; content is limited to ignoring the local `thesis-forge-src-*.zip` archive, touches no product code or verification surface, and is retained to avoid revert churn; future Maker/Checker briefs reiterate the single-commit rule.
- 2026-08-22 - V2-302E re-sliced into ordered children V2-302E1 (re-pin Strong contract on recursive children) and V2-302E2 (retire CodeSpan) after the V2-302C Maker found `tests/core/test_source_identity.py` enumerates CodeSpan for identity coverage, which would have made the combined retirement a four-file item; sibling child ordinals updated to /6, historical Done entries left verbatim; no product code edited.
- 2026-08-22 - V2-302C Checker PASS; three-file contract-exact diff (parser single-site InlineCode emission, compiler InlineCode dispatch, contract assertions migrated with Strong isinstance-only), Verify 112/112, baselines 120/120, parse/compile/parity probes green, CodeSpan residuals only in model.py + test_source_identity.py, full suite 46/973 confined to the 7 known files; no push.
- 2026-08-22 - V2-302D split into ordered children V2-302D1 (unpin legacy Strong shape in tests/core/test_inline_model.py) and V2-302D2 (the recursive-container flip) after the Maker's exact Verify went red on the V2-302A-era Emphasis test using `Strong(value="y")` as a child example — a fourth file the parent slice could not absorb; the Maker's parked diff (/tmp/v2-302d.diff, +27/−4 across model.py/parser.py/compiler.py) was set aside uncommitted and will be re-applied verbatim for the V2-302D2 Checker audit after D1 lands; sibling ordinals updated to /7, Done entries left verbatim; no product code committed in the split cycle.
- 2026-08-22 - V2-302D1 Checker PASS; diff exactly +1/−2 confined to tests/core/test_inline_model.py (child swap to InlineCode + Strong import removal, zero Strong matches), Verify 12/12, tests/core/ 34/34, edited file 12/12 against both current model and /tmp flipped Strong(children) copy (import verified), full suite 46/973 confined to the 7 known files; no push.
- 2026-08-22 - V2-302D2 Checker PASS; Maker-parked diff re-applied verbatim audited contract-exact (+27/−4 across model.py/parser.py/compiler.py, no scope creep), Verify 146/146, docx_renderer 86/86, ruff/diff-check clean, independent probes confirmed both-backend nesting with locations/registration/pre-order, compile lowering (CitationRun/bold TextRun/code+bold/FootnoteReferenceRun), and byte-identical HEAD-vs-candidate example parity, full suite 46/973 confined to the 7 known files; no push.
- 2026-08-22 - V2-302E1 Checker PASS; 2-file diff contract-exact (stricter Strong children-content re-pin + 5 non-vacuous Strong inline-model tests), exact Verify 49/49, baselines 205/205, load-bearing/mutation/two-backend probes green, full suite 46 failed / 978 passed confined to the 7 known files; no push.
- 2026-08-22 - V2-302E2 Checker PASS; deletion-only 2-file diff removes the CodeSpan dataclass and its source-identity enumeration, exact Verify 103/103, ImportError/import/behavior/parity probes green, repo-wide CodeSpan grep empty outside LOOP.md, full suite 46 failed / 978 passed confined to the 7 known files; no push.
- 2026-08-22 - Open refilled with V2-304 and V2-305 per the catalogue dependency order after V2-302E2 left one Open item; both model-replacement slices are expected to need re-slicing when their cycles arrive (consumer construction and test-construction sites exceed the two-file catalogue slices); no product code edited.
- 2026-08-22 - V2-303 split into ten ordered children V2-303A…J after investigation showed removing the duplicated block text fields atomically spans model.py + both parsers + compiler + preview/runtime projections + six test files; the ordered path migrates test pins to derived text first (green both ways), enriches compiler fixtures with parser-shaped inlines before the compiler derivation flip, drops text= kwargs before the field removal, and removes the dead _fallback_text_runs in V2-303E; no product code edited in the split cycle.
- 2026-08-22 - V2-303A Checker PASS; scope exactly 2 files (model.py +53/−0 pure addition, new tests/core/test_block_model.py), exact Verify 20/20, baselines 163/163, ruff/diff-check clean, independent probes green (defaults/slots, recursive BulletList→ListItem.children→OrderedList read-back, every inline_plain_text clause incl. TypeError on unknown Inline, non-mutation), full-suite HEAD-vs-candidate failure sets identical at 46 failed / 998 passed confined to the 7 known files; no push.
- 2026-08-22 - V2-303B Checker PASS; diff exactly the 3 named test files (+21/−17, 16/16 HEAD `.text` pins migrated to inline_plain_text, zero residual `.text`), both disclosed re-pins verbatim with comments, exact Verify 82/82, ruff/diff-check clean, baselines 81/81, both-backend probes green incl. no-`text`-kwarg forward simulation, full-suite failure sets identical HEAD vs candidate at 46/998 confined to the 7 known files; no push.

- 2026-08-22 - V2-303C Checker PASS; compiler text authority migrated to inline_plain_text, DOCX/compiler fixtures are parser-shaped, exact Verify 168/168, Ruff/diff-check and full-suite baseline audit passed with 46 known failures / 999 passes; no push.
- 2026-08-22 - V2-303D split into ordered children V2-303D1 and V2-303D2 after CodeGraph/test inspection found preview.py + preview tests and runtime.py + adapter tests are four files; no product code edited in the split cycle, next queue V2-303D1.
- 2026-08-22 - V2-303D1 Checker PASS; preview outline now derives heading text from inline_plain_text, exact Verify 5/5, Ruff/diff-check clean, stale-text regression and parser-shaped fixture coverage passed; no push.
- 2026-08-22 - V2-303D2 Checker PASS; both runtime inspect outline branches now derive heading text from inline_plain_text, exact Verify 33/33, Ruff/diff-check clean, stale-text adapter fixtures passed; no push.
- 2026-08-22 - V2-303E Checker PASS; parsers stopped populating block text and compiler fallback runs were removed, exact Verify 172/172, dual-backend text-authority probe and Ruff/diff-check passed; no push.
- 2026-08-22 - V2-303F Checker PASS; DOCX renderer fixtures now rely solely on inlines, exact Verify 86/86, AST constructor audit and Ruff/diff-check passed; no push.
- 2026-08-22 - V2-303G Checker PASS; compiler fixtures now rely solely on inlines, exact Verify 23/23, AST constructor audit and Ruff/diff-check passed; no push.
- 2026-08-22 - V2-303H Checker PASS; core/adapter fixtures now rely solely on inlines, exact Verify 92/92, AST constructor audit and Ruff/diff-check passed; no push.
- 2026-08-22 - V2-303I Checker PASS; CLI fixtures now rely solely on inlines, exact Verify 4/4, AST constructor audit and Ruff/diff-check passed; no push.
- 2026-08-22 - V2-303J Checker PASS; Heading/Paragraph/ListItem text fields were removed, exact Verify 141/141 plus 123 affected regressions passed, full-suite known failure set remained stable apart from a non-reproducible LibreOffice QA failure; no push.
- 2026-08-22 - V2-304 split into ordered children V2-304A…E after CodeGraph found structured Table migration spans model/parser/compiler/render-plan and DOCX/parser/compiler fixtures beyond the original two-file slice; no product code edited in the split cycle, next queue V2-304A.
- 2026-08-22 - V2-304A Checker PASS; typed TableCell/TableRow primitives and focused model tests added, exact Verify 4/4, Ruff/diff-check clean; no push.
- 2026-08-22 - V2-304B Checker PASS; parser now populates structured table caption/rows/cells while retaining the raw consumer transition, exact Verify 87/87, Ruff/diff-check clean; no push.
- 2026-08-22 - V2-304C Checker PASS; compiler now consumes structured table rows without pipe parsing, exact Verify 109/109, parse-to-compile probe and Ruff/diff-check passed; no push.
- 2026-08-22 - V2-304D Checker PASS; DOCX table fixtures are structured, exact Verify 86/86 and AST audit passed, with no additional product diff because migration landed in C; no push.
- 2026-08-22 - V2-304E split into ordered children V2-304E1 and V2-304E2 after parser contract inspection found a fourth raw Table-field test file; no product code edited in the split cycle, next queue V2-304E1.
- 2026-08-22 - V2-304E1 Checker PASS; parser table contract assertions now use structured caption/rows/cells, exact Verify 32/32, Ruff/diff-check clean; no push.
- 2026-08-22 - V2-304E2 split into ordered children V2-304E2A and V2-304E2B after structured Table fixture audit found raw caption kwargs in compiler and DOCX tests; no product code edited in the split cycle, next queue V2-304E2A.
- 2026-08-22 - V2-304E2A Checker PASS; compiler/DOCX structured Table fixtures now use caption inlines only, exact Verify 109/109, AST/Ruff/diff-check passed; no push.
- 2026-08-22 - V2-304E2B Checker PASS; raw Table caption/markdown fields were removed, exact Verify 157/157, structured end-to-end regression and raw-field scan passed; no push.
- 2026-08-22 - V2-305 split into ordered children V2-305A…E after AST/CodeGraph found typed caption/content and source-identity migration spans model/parser/compiler plus DOCX/preview/validation fixtures; no product code edited in the split cycle, next queue V2-305A.
- 2026-08-22 - V2-305A Checker PASS; typed object caption/display primitives and focused tests added, exact Verify 4/4, Ruff/diff-check clean; no push.

## Sync log
