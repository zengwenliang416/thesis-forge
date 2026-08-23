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

- [V2-532] Migrate finalizer tests off the deleted parser
  - Parent: ordered child of the single-parser legacy-file removal gap; prepares the last active test consumer before deleting the hand-written parser module.
  - Files: `tests/test_lo_finalizer.py`, `LOOP.md`
  - Behavior: finalizer tests build a standard V2 project through the canonical parser/application path while retaining field capture, restore, rollback and LibreOffice integration assertions.
  - Verify: `.venv/bin/python -m pytest tests/test_lo_finalizer.py`
  - Acceptance: no `thesis_forge.core.parser` import or `parse_markdown` call remains; the raw and final-auto DOCX fixtures come from a manifest-based V2 project; all existing field, style, OpenXML and TOC assertions remain active; no fallback or compatibility branch is introduced.
  - Verification-surface change: `no`
  - Attempts: 0

- [V2-533] Delete the obsolete hand-written parser module
  - Parent: ordered child of the single-parser legacy-file removal gap; depends on V2-531, V2-532 and V2-533A.
  - Files: `src/thesis_forge/core/parser.py`, `LOOP.md`
  - Behavior: remove the obsolete hand-written Markdown parser after all active tooling and test consumers use the canonical backend.
  - Verify: `test ! -e src/thesis_forge/core/parser.py && ! rg -n --glob '*.py' "from thesis_forge\\.core\\.parser([[:space:]]|$)|import thesis_forge\\.core\\.parser([[:space:]]|$)|parse_markdown(_text)?\\(" src tests qa/tools spikes`
  - Acceptance: the module is absent; no active Python source imports or invokes its APIs; canonical parser tests and application/DOCX regressions remain green; historical reports and catalog prose remain untouched; no compatibility shim is added.
  - Verification-surface change: `yes`; removes the obsolete parser implementation after its active consumers are migrated.
  - Attempts: 1
  - Attempt 1 (2026-08-23): Checker FAIL; the original Verify regex matched canonical `parser_backend`, `parser_markdown_it` and `parser_support` imports because it lacked a module-name boundary, and the independent canonical parser regression found `tests/core/test_markdown_v2_parser_config.py` still reading `src/thesis_forge/core/parser.py` (`96 passed, 1 failed`). Finalizer passed 26/26, application regression 173/173, DOCX/compiler regression 133/133, `git diff --check` and LOOP-LINT passed; the parser deletion was restored, no commit or Done update. V2-533A was split as the ordered prerequisite.


## Done

- [V2-533A] Migrate the remaining parser-configuration test off the obsolete parser module
  - Parent: ordered prerequisite of V2-533; the active parser-configuration test still reads the deleted hand-written parser path.
  - Files: `tests/core/test_markdown_v2_parser_config.py`, `LOOP.md`
  - Behavior: parser-configuration coverage reads the canonical `parser_support.py` public primitives and no longer depends on `src/thesis_forge/core/parser.py`.
  - Verify: `.venv/bin/python -m pytest tests/core/test_markdown_v2_parser_config.py`
  - Acceptance: the test passes; it retains public primitive import/definition assertions and CommonMark/GFM rule assertions; no legacy parser path or compatibility branch remains.
  - Verification-surface change: `no`
  - Attempts: 1
  - Attempt 1 (2026-08-23): Checker PASS; exact Verify passed 2/2, canonical parser regression passed 46/46, target Ruff, `git diff --check`, and LOOP-LINT passed (`open=2 done=163 blocked=0` before this move); independent AST audit confirmed the parser_support target, all four primitive import/definition assertions, private-name guard, CommonMark/GFM rules, and no compatibility/fallback/legacy branch; candidate product diff was exactly `tests/core/test_markdown_v2_parser_config.py`, all pre-existing LOOP/openspec/tests/test_lo_finalizer.py changes were preserved, no push.


- [V2-531] Retire the obsolete legacy-parser comparison spike
  - Parent: ordered child of the single-parser legacy-file removal gap; removes a historical comparison entrypoint whose purpose depends on the deleted hand-written parser.
  - Files: `spikes/phase0/parser/compare.py`, `LOOP.md`
  - Behavior: the obsolete parser comparison script is removed so no active tooling entrypoint depends on `thesis_forge.core.parser`.
  - Verify: `test ! -e spikes/phase0/parser/compare.py && ! rg -n "thesis_forge\\.core\\.parser|existing\\.parse_markdown" spikes/phase0/parser`
  - Acceptance: the script is absent; no remaining file under `spikes/phase0/parser` imports or invokes the hand-written parser; historical reports remain untouched unless separately named by a later item.
  - Verification-surface change: `yes`; removes obsolete spike evidence whose implementation depends on the parser being deleted.
  - Attempts: 1
  - Attempt 1 (2026-08-23): Checker PASS; exact Verify exited 0, `git diff --check` and LOOP-LINT passed (`open=3 done=161 blocked=0` before this move), the candidate deleted only `spikes/phase0/parser/compare.py`, active parser spike entrypoints had no legacy import or invocation, and `REPORT.md`, `results/*.json` and `fixtures/**` were unchanged. Independent AST/runtime and protected-path mutation audits passed; all pre-existing `openspec/**` changes were preserved, one local commit, no push.

- [V2-530] Migrate QA E2E parser consumers to canonical V2 sources
  - Parent: ordered child of the single-parser legacy-file removal gap; removes the QA E2E test's direct dependency on the hand-written parser without preserving legacy fixtures.
  - Files: `tests/test_qa_e2e.py`, `LOOP.md`
  - Behavior: QA E2E tests parse standard V2 source through `create_parser_backend()` and retain full DOCX structure, reference, duplicate-ID and missing-reference assertions.
  - Verify: `.venv/bin/python -m pytest tests/test_qa_e2e.py`
  - Acceptance: the exact Verify passes; the test has no `thesis_forge.core.parser` import or `parse_markdown` call; all source inputs are standard V2 Markdown or typed in-test fixtures; no fallback or compatibility branch is introduced.
  - Verification-surface change: `no`
  - Attempts: 2
  - Attempt 1 (2026-08-23): Checker FAIL; the canonical parser migration passed the exact 4-test command and related regression, but the positive E2E still copied PNGs from `qa/fixtures/e2e/figure-reference/images`, and its new source removed citation, footnote and bibliography coverage from the positive compile/DOCX path. The candidate remained uncommitted for repair; all pre-existing `openspec/**` changes were preserved.
  - Attempt 2 (2026-08-23): Checker PASS; the test now generates PNGs, BibTeX, manifest and standard V2 Markdown entirely under `tmp_path`, restores citation/index, footnote, bibliography-instruction and `word/footnotes.xml` coverage, and retains bookmarks, SEQ/REF/TOC, footer PAGE, `updateFields`, duplicate-ID and missing-reference assertions. Exact Verify passed 4/4; the independent wider regression passed 197/197, target Ruff, `git diff --check`, and LOOP-LINT passed (`open=2 done=160 blocked=0` before this move); AST/runtime and mutation audits found no legacy reads, fallback, compatibility branch, production parser selector or scope creep. Candidate scope before this lifecycle update was exactly `tests/test_qa_e2e.py`; all pre-existing `openspec/**` changes were preserved and unstaged, one local commit, no push.

- [V2-529] Migrate the OMML sample spike to the canonical V2 parser
  - Parent: ordered child of the single-parser legacy-file removal gap; removes one remaining tooling consumer before the hand-written parser can be deleted.
  - Files: `spikes/phase0/omml/build_sample.py`, `spikes/phase0/omml/results/omml_assertions.json`, `LOOP.md`
  - Behavior: the OMML sample builder uses `create_parser_backend()` and generates only manifest-free V2 Markdown semantics, while preserving validation, compilation, DOCX rendering and refreshed OMML evidence.
  - Verify: `.venv/bin/python spikes/phase0/omml/build_sample.py`
  - Acceptance: the script exits 0; the generated sample contains no YAML Front Matter or legacy `:::` container; the tracked JSON evidence reports successful OpenXML validation, per-equation assertions and inline OMML conversion; no `thesis_forge.core.parser` import, fallback or compatibility path remains in the spike.
  - Verification-surface change: `yes`; refreshes the tracked OMML evidence because the canonical parser changes inline-math output.
  - Attempts: 2
  - Attempt 1 (2026-08-23): Checker FAIL; the first canonical migration generated standard V2 source and passed parser/DOCX regressions, but the script exited 0 while its generated evidence reported `inline_math_converted: false`, still used a hard-coded template path alongside manifest metadata, and rewrote the tracked OMML evidence without naming it in Files. The candidate remained uncommitted for repair.
  - Attempt 2 (2026-08-23): Checker PASS; the repaired script selects metadata and `template_id` through generated manifest discovery, fails fast on OpenXML/equation/inline-OMML assertion failures, and refreshes the named evidence JSON. Exact Verify exited 0 with 47 display equations, 2 inline equations, 49 `m:oMath` nodes, `per_equation_all_ok=True`, `inline_math_converted=True`, and `openxml_validate exit=0`; related regression passed 22/22; Ruff, `git diff --check`, and `./lint-loop.sh` passed (`open=3 done=159 blocked=0` before this move). Independent Checker confirmed stable three-file scope, no old parser/fallback/compatibility path, and no pre-existing `openspec/**` changes were touched.

- [V2-528] Migrate architecture tests off the legacy parser module
  - Parent: ordered child of the single-parser legacy-file removal gap; removes the remaining architecture-test import before `src/thesis_forge/core/parser.py` can be deleted.
  - Files: `tests/test_architecture.py`, `LOOP.md`
  - Behavior: architecture tests inspect the canonical parser backend module instead of importing the deleted hand-written parser, while preserving the domain/parser layer-boundary and legacy-import rejection assertions.
  - Verify: `.venv/bin/python -m pytest tests/test_architecture.py`
  - Acceptance: no `import thesis_forge.core.parser` or `parser_module` reference remains; canonical parser backend layer-boundary assertions remain active; renderer, CLI, UI and frontend forbidden-import checks remain unchanged; no fallback or compatibility branch is introduced.
  - Verification-surface change: `no`
  - Attempts: 1
  - Attempt 1 (2026-08-23): Checker PASS; exact Verify `.venv/bin/python -m pytest tests/test_architecture.py` passed 9/9; related regression `.venv/bin/python -m pytest tests/core/test_single_parser_backend.py tests/core/test_legacy_source_rejection.py tests/test_parser_backend.py` passed 15/15; `.venv/bin/ruff check tests/test_architecture.py`, `git diff --check`, and `./lint-loop.sh` passed (`open=1 done=158 blocked=0` before this move). Independent AST/import audit confirmed the canonical target `thesis_forge.core.parser_backend`, no legacy import statement or `parser_module` identifier, three retained `thesis_forge.core.parser` string rejection assertions, all 9 test functions and 17 assertions retained, unchanged renderer/CLI/UI/frontend forbidden-import test bodies, and no fallback, compatibility branch, or product code; candidate scope before this lifecycle update was exactly `tests/test_architecture.py`, all pre-existing `openspec/**` changes were preserved and unstaged, no push.

- [V2-527C] Migrate validator tests from the deleted hand-written parser
  - Parent: ordered child of the single-parser legacy-file removal gap; preserves validator regression coverage while removing the remaining direct parser import.
  - Files: `tests/test_validator.py`, `LOOP.md`
  - Behavior: validator tests use the canonical parser backend or typed domain fixtures, and all existing validation assertions remain active without YAML Front Matter or legacy `:::` source.
  - Verify: `.venv/bin/python -m pytest tests/test_validator.py`
  - Acceptance: no `thesis_forge.core.parser` import or `parse_markdown*` call remains; missing-reference, duplicate-ID, metadata, resource, bibliography, deterministic-order and structured-diagnostic assertions remain green through the V2 path; no fallback or compatibility branch is introduced.
  - Verification-surface change: `no`
  - Attempts: 1
  - Attempt 1 (2026-08-23): Checker PASS; exact Verify `.venv/bin/python -m pytest tests/test_validator.py` passed 17/17; related regression `.venv/bin/python -m pytest tests/core/test_validator_document_index.py tests/core/test_manifest_resource_validation.py tests/core/test_legacy_source_rejection.py tests/test_parser_backend.py` passed 19/19; target Ruff passed through the project `.venv/bin/ruff`, `git diff --check`, and `./lint-loop.sh` passed (`open=1 done=157 blocked=0` before this move). Independent AST, assertion, typed-fixture and runtime audit confirmed the same 17 test functions and 53 assertions remain active, canonical `create_parser_backend().parse_text()`/`parse_file()` usage, typed `Figure`/`BibliographyConfig` fixtures, no `thesis_forge.core.parser` import, no `parse_markdown*` call, no YAML Front Matter, legacy `:::` or old `@prefix:id` source, retained missing-reference/duplicate-ID/metadata/resource/bibliography/deterministic-order/BuildReport structured-diagnostic coverage, and no fallback, compatibility branch or dual data source; candidate scope before lifecycle update was exactly `tests/test_validator.py`, no product code or related regression file changed, all pre-existing `openspec/**` changes were preserved, no push.

- [V2-527B] Retire obsolete V1 hand-written parser contract tests after canonical coverage
  - Parent: ordered child of the single-parser legacy-file removal gap; the deleted parser's Front Matter/V1 container contract must not remain as a production test entry.
  - Files: `tests/test_parser.py`, `tests/test_parser_contract.py`, `LOOP.md`
  - Behavior: remove the tests that exercise the deleted hand-written parser while retaining their supported V2 parser behavior and explicit legacy rejection coverage in the canonical parser test suites.
  - Verify: `.venv/bin/python -m pytest tests/core/test_single_parser_backend.py tests/core/test_markdown_v2_blocks.py tests/core/test_markdown_v2_inlines.py tests/core/test_legacy_source_rejection.py`
  - Acceptance: neither obsolete test file remains as a direct parser entry; the canonical suites pass and cover parser construction, supported V2 blocks/inlines, and structured rejection of Front Matter/legacy syntax; no test-only compatibility shim is added.
  - Verification-surface change: `yes`; removes obsolete V1 parser-contract evidence whose implementation is being deleted while retaining canonical V2 and rejection evidence.
  - Attempts: 1
  - Attempt 1 (2026-08-23): Checker PASS; exact Verify passed 21/21, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; canonical parser regression passed 97/97; independent AST/runtime audit confirmed no production/tooling reference to either deleted test file, canonical factory construction without a selector or legacy registry, typed V2 block/inline coverage, structured `TF-SOURCE-LEGACY-001/002/003` rejection with replacements, code-literal marker exemptions, and no compatibility shim or production diff; candidate scope remained exactly `tests/test_parser.py`, `tests/test_parser_contract.py` and `LOOP.md`, V2-527C remained Open, all pre-existing `openspec/**` changes were preserved, one local commit, no push.

- [V2-527A] Migrate the DOCX renderer test's remaining legacy parser consumer
  - Parent: ordered child of the single-parser legacy-file removal gap; this child removes one remaining direct test dependency before the legacy module can be deleted.
  - Files: `tests/test_docx_renderer.py`, `LOOP.md`
  - Behavior: the complete semantic-fragment DOCX test parses its temporary Markdown through `create_parser_backend()` and preserves all style, field, Review-neutral and DOCX XML assertions.
  - Verify: `.venv/bin/python -m pytest tests/test_docx_renderer.py`
  - Acceptance: the test has no `thesis_forge.core.parser` import or `parse_markdown*` call; the canonical backend parses the existing front-matter-free source; the exact full DOCX regression remains green with no compatibility parser or alternate source.
  - Verification-surface change: `no`
  - Attempts: 1
  - Attempt 1 (2026-08-23): Checker PASS; exact Verify passed 90/90, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent AST/runtime audit confirmed no `thesis_forge.core.parser` import, no `parse_markdown*` call, one canonical `create_parser_backend().parse_file()` call, and the 23-line front-matter-free/no-`:::` source parsed by `MarkdownItParserBackend(name="markdown-it")` into 13 typed blocks; the style, field, Review-neutral and DOCX XML assertions remained unchanged, with no fallback, compatibility parser, alternate source or production diff; candidate scope remained exactly `LOOP.md` and `tests/test_docx_renderer.py`, V2-527B/C remained Open, all pre-existing `openspec/**` changes were preserved, one local commit, no push.

- [V2-526] Project manifest metadata supplies canonical document metadata to validation and cover compilation
  - Files: `src/thesis_forge/core/validator.py`, `tests/core/test_manifest_resource_validation.py`, `LOOP.md`
  - Behavior: a manifest-based v2 project derives the canonical cover and validation metadata from `thesisforge.yaml` without YAML Front Matter or a second metadata source.
  - Verify: `.venv/bin/python -m pytest tests/core/test_manifest_resource_validation.py`
  - Acceptance: `ValidationContext.from_document()` projects manifest title, institution, degree, author, advisor and completion metadata into the canonical dotted fields; required metadata validation passes for a metadata-complete manifest; compiled cover values come from that same projection; projects without the manifest metadata remain diagnostically invalid; no legacy parser, fallback, compatibility alias or silent merge is introduced.
  - Verification-surface change: `no`
  - Attempts: 2
  - Attempt 1 (2026-08-23): Checker FAIL; expected the candidate test to directly assert all 11 canonical CoverInstruction fields and to assert `required-metadata` diagnostics for a manifest with no metadata. Observed exact Verify passed 5/5, target Ruff and `git diff --check` passed, related manifest/validator/compiler regression passed 129/129, and independent runtime probes passed 11/11 cover fields plus 2/2 missing-metadata diagnostics, but the candidate test asserted only 5/11 cover fields and made no assertion for the missing-metadata case; deleting that evidence path would leave the target test green. Static audit found canonical parser use and no legacy parser/fallback/compatibility path. The candidate `src/thesis_forge/core/validator.py` and `tests/core/test_manifest_resource_validation.py` were restored; all pre-existing `openspec/**` changes were preserved; no commit or push.
  - Attempt 2 (2026-08-23): Checker PASS; exact Verify passed 5/5, target Ruff, `git diff --check`, `./lint-loop.sh`, and related manifest/validator/compiler regression passed 130/130. Independent runtime/static audit passed complete and empty manifest projection, 11/11 cover fields, stale-metadata replacement, canonical parser use, and no legacy parser/fallback/compatibility path; mutation audit caught 11/11 cover-field mutations, empty-manifest diagnostic suppression, and stale-metadata merge. Candidate scope remained exactly the three named files, all pre-existing `openspec/**` changes were preserved, one local commit, no push.

- [V2-525] Migrate QA tool DOCX fixture construction to the canonical parser
  - Parent: ordered parser-consumer migration after `V2-524`; removes the next direct test dependency on the deleted hand-written parser while keeping the existing OpenXML quality-gate assertions.
  - Files: `tests/test_qa_tools.py`, `LOOP.md`
  - Behavior: QA tool tests build their sample DOCX from the existing V2 project Markdown through `create_parser_backend().parse_file()` and continue validating all OpenXML checks and tool exit-code behavior.
  - Verify: `.venv/bin/python -m pytest tests/test_qa_tools.py`
  - Acceptance: the exact Verify passes; the test has no `thesis_forge.core.parser` import, does not consume YAML Front Matter or legacy `:::` source, uses the canonical V2 fixture, and retains the full OpenXML/no-repair assertions.
  - Verification-surface change: `no`
  - Attempts: 1
  - Attempt 1 (2026-08-23): Checker PASS; exact Verify passed 14/14, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent AST/runtime audit confirmed no `thesis_forge.core.parser` import, no `parse_markdown*` API, no YAML Front Matter or legacy `:::` source, canonical `create_parser_backend().parse_file()` usage, and the exact existing `tests/fixtures/v2-project/thesis.md`; a real rendered DOCX passed all 13 OpenXML checks with exit-code 0 and identical stdout/file JSON reports; all pre-existing OpenXML, exit-code, JSON, and no-repair assertions remained AST-identical; no fallback, compatibility layer, dual data source, or silent degradation; candidate scope remained exactly `LOOP.md` and `tests/test_qa_tools.py`, all pre-existing `openspec/**` changes were preserved, no push.

- [V2-524] Migrate the compiler citation-order parser test to the canonical backend
  - Parent: ordered parser-consumer migration after `V2-523`; removes the next direct test dependency on the deleted hand-written parser while preserving citation extraction from semantic object captions.
  - Files: `tests/test_compiler.py`, `LOOP.md`
  - Behavior: the compiler citation-order test parses a standard V2 figure caption through `create_parser_backend().parse_text()` and continues proving that the parsed citation reaches the global `RenderPlan` citation order.
  - Verify: `.venv/bin/python -m pytest tests/test_compiler.py`
  - Acceptance: the exact Verify passes; the test has no `thesis_forge.core.parser` import or legacy `:::` source, uses the canonical parser factory, and retains the `container2026` citation-order assertion.
  - Verification-surface change: `no`
  - Attempts: 1
  - Attempt 1 (2026-08-23): Checker PASS; exact Verify passed 24/24, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent AST/runtime audit confirmed canonical `create_parser_backend().parse_text()` usage, no legacy parser import, `parse_markdown*` API, YAML Front Matter or `:::` source, typed Figure/caption Citation output, and `RenderPlan.citation_order == ("container2026",)`; no fallback, compatibility layer, dual data source, or silent degradation; non-target compiler tests/assertions remained unchanged; candidate scope remained exactly `LOOP.md` and `tests/test_compiler.py`, all pre-existing `openspec/**` changes were preserved and unstaged, no push.

- [V2-523] Migrate object override validation tests to the canonical parser
  - Parent: ordered parser-consumer migration after `V2-522`; removes the next direct test dependency on the deleted hand-written parser while retaining project manifest layout discovery.
  - Files: `tests/core/test_object_overrides.py`, `LOOP.md`
  - Behavior: object override tests parse standard V2 figure, display-equation and GFM table syntax through `create_parser_backend().parse_file()` and continue validating manifest-driven layout overrides.
  - Verify: `.venv/bin/python -m pytest tests/core/test_object_overrides.py`
  - Acceptance: the exact Verify passes; the test has no `thesis_forge.core.parser` import or legacy `:::` source, uses the canonical parser factory, and retains valid, orphan and type-mismatch override assertions.
  - Verification-surface change: `no`
  - Attempts: 1
  - Attempt 1 (2026-08-23): Checker PASS; exact Verify passed 7/7, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent AST/runtime audit confirmed canonical `parser_backend.create_parser_backend().parse_file()` usage, no legacy parser import, `parse_markdown*` API, YAML Front Matter or `:::` source, typed Figure/Equation/Table output with stable IDs, and valid/orphan/type-mismatch manifest override assertions; no fallback, compatibility layer, dual data source, or silent degradation; candidate scope remained exactly `LOOP.md` and `tests/core/test_object_overrides.py`, all pre-existing `openspec/**` changes were preserved and unstaged, one local commit, no push.

- [V2-522] Remove the parser markdown-it test import from the legacy parser module
  - Parent: ordered parser-consumer migration after `V2-521`; moves the parser markdown-it error assertions to the canonical parser support module.
  - Files: `tests/test_parser_markdown_it.py`, `LOOP.md`
  - Behavior: parser markdown-it tests import `ParseError` from `parser_support` while retaining the canonical backend, parser-diff, legacy rejection and structured error coverage.
  - Verify: `.venv/bin/python -m pytest tests/test_parser_markdown_it.py`
  - Acceptance: the exact Verify passes; the test has no `thesis_forge.core.parser` import, and canonical backend, parser-diff, legacy rejection and structured error assertions remain unchanged.
  - Verification-surface change: `no`
  - Attempts: 1
  - Attempt 1 (2026-08-23): Checker PASS; exact Verify passed 35/35, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent AST/runtime audit confirmed the canonical parser backend import, `ParseError` from `parser_support` only, retained parser-diff/legacy rejection/structured-error assertions, and no legacy parser import, parse_markdown APIs, fallback, compatibility layer, or dual source of truth; candidate scope remained exactly `LOOP.md` and `tests/test_parser_markdown_it.py`, all pre-existing `openspec/**` paths were preserved and unstaged, one local commit, no push.

- [V2-521] Remove the V2 table test import from the legacy parser module
  - Parent: ordered parser-consumer migration after `V2-520`; moves the remaining V2 table error assertions to the canonical parser support module.
  - Files: `tests/core/test_markdown_v2_tables.py`, `LOOP.md`
  - Behavior: V2 table tests import `ParseError` from `parser_support` while continuing to exercise `MarkdownItParserBackend`.
  - Verify: `.venv/bin/python -m pytest tests/core/test_markdown_v2_tables.py`
  - Acceptance: the exact Verify passes; the test has no `thesis_forge.core.parser` import, and standard GFM table/caption, alignment, typed inline and structured error assertions remain unchanged.
  - Verification-surface change: `no`
  - Attempts: 1
  - Attempt 1 (2026-08-23): Checker PASS; exact Verify passed 6/6, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent AST/runtime audit confirmed the canonical `MarkdownItParserBackend` path, `ParseError` from `parser_support` only, unchanged table/caption/alignment/typed-inline/structured-error assertions, no legacy parser import, YAML Front Matter, legacy `:::`, fallback, compatibility layer, or dual source of truth; candidate scope remained exactly `LOOP.md` and `tests/core/test_markdown_v2_tables.py`, all pre-existing `openspec/**` paths were preserved and unstaged, one local commit, no push.

- [V2-520] Remove V2 fence and equation test imports from the legacy parser module
  - Parent: ordered parser-consumer migration after `V2-519`; moves error assertions to the canonical parser support module without changing parser behavior.
  - Files: `tests/core/test_markdown_v2_fences.py`, `tests/core/test_markdown_v2_equations.py`, `LOOP.md`
  - Behavior: V2 fence and display-equation tests import `ParseError` from `parser_support` while continuing to exercise `MarkdownItParserBackend`.
  - Verify: `.venv/bin/python -m pytest tests/core/test_markdown_v2_fences.py tests/core/test_markdown_v2_equations.py`
  - Acceptance: the exact Verify passes; neither test imports `thesis_forge.core.parser`, and standard fence/equation semantics and structured error assertions remain unchanged.
  - Verification-surface change: `no`
  - Attempts: 1
  - Attempt 1 (2026-08-23): Checker PASS; exact Verify passed 18/18, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent AST/runtime audit confirmed both tests import `MarkdownItParserBackend` and `ParseError` from canonical modules, retain standard fence/equation typed assertions and structured diagnostics, and contain no legacy parser import, fallback, compatibility layer, or dual source of truth; candidate scope remained exactly the two named tests plus this lifecycle update, all pre-existing `openspec/**` paths were preserved and unstaged, one local commit, no push.

- [V2-519] Migrate the typed table model test to the canonical parser
  - Parent: ordered parser-consumer migration after `V2-518`; reduces the remaining test dependency on the removable hand-written parser.
  - Files: `tests/core/test_table_model.py`, `LOOP.md`
  - Behavior: the table model test parses standard GFM table syntax through `create_parser_backend()` and asserts typed rows, cells and caption in the canonical path.
  - Verify: `.venv/bin/python -m pytest tests/core/test_table_model.py`
  - Acceptance: the exact Verify passes; the test has no `core.parser` import, YAML Front Matter or legacy `:::` source, and retains typed table/cell/caption assertions.
  - Verification-surface change: `no`
  - Attempts: 2
  - Attempt 1 (2026-08-23): Checker FAIL; exact Verify passed 6/6, target Ruff and `git diff --check` passed, and the canonical GFM/typed table runtime passed, but the test only compared `inline_plain_text(...)` containing raw `[@...]` text and had no direct `Citation` or `DocumentIndex` assertion. Candidate files were restored; no commit or push. Existing `openspec/**` changes were preserved.
  - Attempt 2 (2026-08-23): Checker PASS; exact Verify passed 6/6, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent AST/runtime audit confirmed the canonical parser backend import, no YAML Front Matter or legacy `:::` input, typed GFM `Table`/`TableRow`/`TableCell`/caption output, direct `Citation` nodes and `DocumentIndex` citation order, and no fallback, compatibility layer, or dual source of truth; candidate scope remained exactly the named test file plus this lifecycle update; all pre-existing `openspec/**` paths were preserved and unstaged; one local commit, no push.

- [V2-518] Migrate core model tests to the canonical parser entry
  - Parent: ordered preparation child after `V2-320`; removes two remaining core-test dependencies on the deleted hand-written parser before the legacy module can be removed.
  - Files: `tests/core/test_no_manual_caches.py`, `tests/core/test_thesis_object_model.py`, `LOOP.md`
  - Behavior: core model and cache tests parse standard V2 Markdown through `create_parser_backend()` instead of importing `core.parser`.
  - Verify: `.venv/bin/python -m pytest tests/core/test_no_manual_caches.py tests/core/test_thesis_object_model.py`
  - Acceptance: the exact Verify passes; both tests contain no `core.parser` import, use no YAML Front Matter or legacy `:::` containers, and retain typed object/citation assertions.
  - Verification-surface change: `no`
  - Attempts: 1
  - Attempt 1 (2026-08-23): Checker PASS; exact Verify passed 9/9, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent AST/runtime audit confirmed the canonical parser backend import, no YAML Front Matter or legacy `:::` inputs, typed Figure/Listing/Algorithm/Equation objects, citation order and manual-cache absence; candidate scope remained exactly the three named files, all pre-existing `openspec/**` paths were preserved and unstaged, one local commit, no push.

- [V2-517] Add field, bookmark, style and numbering DOCX postflight validation
  - Files: `src/thesis_forge/renderers/docx/package.py`, `tests/renderers/docx/test_package_semantics_v2.py`, `LOOP.md`
  - Behavior: validate bookmark pairs/names, field structure, style IDs, numIds, footnotes, sections and media in generated DOCX packages.
  - Verify: `.venv/bin/python -m pytest tests/renderers/docx/test_package_semantics_v2.py`
  - Acceptance: structural Word repair risks are reported as stable `TF-DOCX-*` errors.
  - Verification-surface change: `yes`; adds the executable `docx.postflight` capability evidence named by `spec/format-capabilities.yaml`.
  - Attempts: 2
  - Attempt 1 (2026-08-23): Checker FAIL; exact Verify passed 8/8, related DOCX/application regressions, target Ruff and `git diff --check` passed, but deleting a positive footnote definition's `w:footnoteRef` expected `TF-DOCX-FOOTNOTE-005` and observed `PASS`; candidate remained uncommitted for Maker repair.
  - Attempt 2 (2026-08-23): Checker PASS; exact Verify passed 9/9, related DOCX regression passed 9/9, full DOCX renderer regression passed 90/90, related application regression passed 16/16, target Ruff and `git diff --check` passed; independent audit confirmed valid packages with retained `-1/0` separator footnotes, `TF-DOCX-FOOTNOTE-005` for a missing positive `w:footnoteRef`, and the bookmark/field/style/numbering/section/media diagnostics; all pre-existing `openspec/**` paths were preserved and unstaged, one local commit, no push.

- [V2-406] Add executable evidence for the Review marker-leak contract
  - Parent: evidence-closure child of catalogue item `V2-406`; the existing canonical fixture and Review projector provide the source and production seams.
  - Files: `tests/contracts/test_review_marker_leaks.py`
  - Behavior: scan normal Review content for Front Matter, `:::`, `{#`, raw citation keys, legacy references and absolute paths while excluding literal code.
  - Verify: `.venv/bin/python -m pytest tests/contracts/test_review_marker_leaks.py`
  - Acceptance: all technical markers are absent from visible normal content; the evidence must exercise the canonical fixture through typed compilation and Review, preserve source navigation metadata separately, and retain marker-like literal code.
  - Verification-surface change: `yes`; creates the capability evidence required by `spec/format-capabilities.yaml`; `tests/fixtures/v2-project/thesis.md` is an existing read-only input for this evidence.
  - Attempts: 2
  - Attempt 1 (2026-08-23): Checker FAIL; exact Verify passed 2/2, target Ruff, `git diff --check`, and the requested Review regression passed 8/8. Mutation audit killed stable-ID and raw-citation marker branches, canonical compiler bypass, CitationRun raw-text leakage, ReferenceRun target leakage, source-navigation removal, and listing-code sanitization. Evidence gaps remained: deleting the `---`/`:::` scan items still passed because the canonical fixture contains neither input, and removing ReferenceRun display-text sanitization still passed because the test supplied already-clean `图1-1`; the new evidence also had no explicit unknown/boundary input. Candidate test restored; no production or fixture change, no commit or push.
  - Attempt 2 (2026-08-23): Checker PASS; exact Verify passed 6/6, target Ruff, `git diff --check`, Review regression passed 8/8, and `./lint-loop.sh` passed. Independent audit killed 8/8 runtime mutants and 5/5 static deletion mutants across canonical parser/compiler bypass, ReferenceRun display-text sanitization, CitationRun raw-text fallback, source-navigation removal, literal-code exemption, unknown instruction/inline boundaries, and Front Matter/legacy coverage. Candidate scope remained exactly the named test file plus this lifecycle update; no production or fixture change, all pre-existing `openspec/**` paths were preserved and unstaged, one local commit, no push.

- [V2-508] Add executable capability evidence for the Word field builder contract
  - Parent: evidence-closure child of catalogue item `V2-508`; the existing DOCX field helpers already emit the required field families and cached values.
  - Files: `src/thesis_forge/renderers/docx/fields.py`, `tests/renderers/docx/test_fields_v2.py`
  - Behavior: build typed TOC, SEQ, REF, PAGEREF, PAGE and NUMPAGES field structures with cached results.
  - Verify: `.venv/bin/python -m pytest tests/renderers/docx/test_fields_v2.py`
  - Acceptance: begin/separate/end structure is valid and Word-specific code stays in DOCX layer; the evidence covers typed TOC/SEQ/REF/PAGEREF/PAGE/NUMPAGES production, cached reader-visible results, update-on-open/dirty semantics, and field pairing.
  - Verification-surface change: `yes`; creates the capability evidence required by `spec/format-capabilities.yaml`.
  - Attempts: 1
  - Attempt 1 (2026-08-23): Checker PASS; exact Verify passed 1/1, related `tests/test_docx_renderer.py` regression passed 90/90, architecture/RenderPlan regression passed 15/15, target Ruff, and `git diff --check` passed. Independent mutation audit passed 10/10 across field instructions, cached results, begin dirty, separate/end pairing, nested TOC PAGEREF, TOC end placement, update-on-open settings, and the core DOCX/OXML boundary. The persisted DOCX XML proved all six field families, reader-visible caches, dirty/updateFields semantics, hyperlinks, and paired structures; `core/render_plan.py` remained DOCX/OXML-free. Candidate scope was the named test file plus this lifecycle update; `fields.py`, `toc.py`, `captions.py`, and `core/render_plan.py` were audited unchanged, all pre-existing `openspec/**` paths were preserved and unstaged, one local commit, no push.

- [V2-514] Add executable capability evidence for the semantic bibliography region
  - Parent: evidence-closure child of catalogue item `V2-514`; existing compiler, Review, and DOCX bibliography seams are already present.
  - Files: `tests/core/test_bibliography_region.py`
  - Behavior: exercise one manifest-selected bibliography region from canonical source parsing through validation, typed compilation, Review projection, and DOCX rendering.
  - Verify: `.venv/bin/python -m pytest tests/core/test_bibliography_region.py`
  - Acceptance: the evidence proves the manifest bibliography resource and citation closure, exactly one semantic bibliography title and one ordered entry list, no orphan bibliography instruction without its title region, readable Review entries, and styled DOCX title/entries without raw citation markers.
  - Verification-surface change: `yes`; creates the capability evidence required by `spec/format-capabilities.yaml`.
  - Attempts: 2
  - Attempt 1 (2026-08-23): Checker FAIL; exact Verify passed 1/1 and related compiler/Review/DOCX/resource regression passed 147/147, but independent mutation audit found four evidence gaps: the manifest bibliography path was not independently attributable, one entry did not prove ordering or omission behavior, the explicit formatter bypassed manifest citation-style selection, and DOCX assertions only checked that styles were non-empty rather than checking semantic style IDs and definitions. Candidate remained Open for repair; no production code changed, no commit or push.
  - Attempt 2 (2026-08-23): Checker PASS; exact Verify passed 1/1, related manifest/resource/compiler/Review/DOCX regression passed 140/140, target Ruff, `git diff --check`, and `./lint-loop.sh` passed. Independent mutation audit passed 10/10: unique semantic title and bibliography instruction, non-orphan ordering, manifest path/database source attribution, manifest citation-style/provider attribution, two-entry ordering, marker-free Review, concrete `TFBibliographyTitle`/`TFBibliographyEntry` DOCX styles and definitions. Candidate scope remained exactly the named test file plus this lifecycle update; all pre-existing `openspec/**` paths were preserved and unstaged; no production code changed, no push.

- [V2-503E] Add executable capability evidence for semantic TOC and section resolution
  - Parent: evidence-closure child of catalogue item `V2-503`; depends on completed symbol/numbering and template section work.
  - Files: `tests/core/test_region_resolver.py`
  - Behavior: exercise the compiler’s manifest-selected TOC and section planning path as one resolved semantic region flow.
  - Verify: `.venv/bin/python -m pytest tests/core/test_region_resolver.py`
  - Acceptance: the evidence proves legal region order and required-region handling, one resolved TOC instruction with cached heading entries, section-break roles and page-number policy reaching DOCX, and duplicate/invalid placement rejection where the current validation contract defines it; it is non-empty executable evidence and the shared manifest path covers `region.toc` and `region.sections`.
  - Verification-surface change: `yes`; creates the capability evidence required by `spec/format-capabilities.yaml`.
  - Attempts: 1
  - Attempt 1 (2026-08-23): Checker PASS; exact Verify `.venv/bin/python -m pytest tests/core/test_region_resolver.py` passed 2/2; related canonical-parser, Review-region and DOCX regression passed 100/100; target Ruff, `git diff --check`, and `./lint-loop.sh` passed. Independent runtime audit confirmed manifest-selected template resolution, canonical markdown-it parser to compiler single TOC with cached heading entries, front_matter/main section roles, typed Review projection, DOCX sectPr/page-number policy, real TOC field/cache, and RegionsSpec duplicate/missing-main validation. Candidate diff contained only the named test file; existing `openspec/**` changes were preserved and ignored; no commit had been created before this lifecycle update and no push.

- [V2-507E1] Establish template and symbol numbering inputs for listings and algorithms
  - Parent: ordered preparation child 1/4 of evidence-closure item `V2-507E`; the original `V2-507E` Behavior and Acceptance remain unchanged across E1 through E4.
  - Files: `src/thesis_forge/templates/model.py`, `src/thesis_forge/core/symbols.py`, `tests/core/test_listing_algorithm_numbering.py`
  - Behavior: expose configured listing/algorithm numbering and caption-prefix policy through the template contract and resolve chapter, continuous or disabled sequence inputs from the authoritative symbol table.
  - Verify: `.venv/bin/python -m pytest tests/core/test_listing_algorithm_numbering.py`
  - Acceptance: listing and algorithm have distinct validated numbering policies with deterministic sequence values, labels and bookmark inputs; numbering remains template-driven and no renderer-side counter or compatibility alias is introduced.
  - Verification-surface change: `no`
  - Attempts: 1
  - Attempt 1 (2026-08-23): Checker PASS; exact Verify passed 4/4; related symbol/template regression passed 83/83, compiler/DOCX regression passed 114/114, target Ruff, `git diff --check`, and `./lint-loop.sh` passed. Independent audit confirmed distinct `ListingSpec`/`AlgorithmSpec` template entries, authoritative `SymbolTable` chapter/continuous/none inputs, deterministic chapter reset and continuous increments, configured prefixes, stable bookmarks, invalid-mode diagnostics, unchanged figure/table/equation behavior, no renderer-side counter, no compatibility alias or second source, and no unrelated candidate files. The split-cycle `LOOP.md` changes and pre-existing `openspec/**` paths were preserved; one local commit, no push.

- [V2-507E2] Carry typed listing and algorithm numbering through the RenderPlan compiler
  - Parent: ordered preparation child 2/4 of evidence-closure item `V2-507E`; depends on `V2-507E1`; the original `V2-507E` Behavior and Acceptance remain unchanged across E1 through E4.
  - Files: `src/thesis_forge/core/render_plan.py`, `src/thesis_forge/core/compiler.py`, `tests/core/test_listing_algorithm_render_plan.py`
  - Behavior: compile Listing and Algorithm nodes into typed instructions carrying their resolved caption/body data, stable bookmark and sequence information without flattening semantic source content.
  - Verify: `.venv/bin/python -m pytest tests/core/test_listing_algorithm_render_plan.py`
  - Acceptance: compiler output is driven by `SymbolTable` numbering inputs, `ListingInstruction` and `AlgorithmInstruction` expose one authoritative typed contract, literal code/body remains exact, and payloads contain no duplicate raw/resolved source or renderer-specific implementation detail.
  - Verification-surface change: `no`
  - Attempts: 2
  - Pre-check repair (2026-08-23): the exact Verify initially failed 2/2 because the new test used the legacy `parse_markdown_text` entry and therefore did not produce typed Listing/Algorithm nodes; the test was changed to the canonical `MarkdownItParserBackend` entry, and the exact Verify then passed 2/2.
  - Attempt 1 (2026-08-23): Checker FAIL; exact Verify passed 2/2, related core/compiler/DOCX regression passed 129/129, target Ruff, `git diff --check`, and `./lint-loop.sh` passed. Independent audit found that listing and algorithm payloads reused `SequenceInstruction.payload` and exposed DOCX-specific `field_code`; the candidate remained uncommitted and was retained for repair.
  - Attempt 2 (2026-08-23): Checker PASS; exact Verify passed 2/2, related core/compiler/DOCX regression passed 129/129, target Ruff, `git diff --check`, and `./lint-loop.sh` passed. Independent audit confirmed SymbolTable-only numbering/bookmark inputs, chapter/continuous/none behavior, exact literal code/body, renderer-neutral payloads without `field_code`/`raw`/`markdown`, preserved typed `SequenceInstruction.field_code` for DOCX renderers, no compatibility alias or second source, and no `docx`/`lxml` imports. Candidate scope remained the three named files plus this lifecycle update; all pre-existing `openspec/**` paths were preserved and unstaged; one local commit, no push.

- [V2-507E3] Project typed listing and algorithm instructions into readable Review content
  - Parent: ordered preparation child 3/4 of evidence-closure item `V2-507E`; depends on `V2-507E2`; the original `V2-507E` Behavior and Acceptance remain unchanged across E1 through E4.
  - Files: `src/thesis_forge/presentation/review.py`, `tests/presentation/test_listing_algorithm_review.py`
  - Behavior: map compiled listing and algorithm instructions to reader-facing Review content while keeping source navigation and technical identity outside visible prose.
  - Verify: `.venv/bin/python -m pytest tests/presentation/test_listing_algorithm_review.py`
  - Acceptance: captions remain readable, literal code/body is preserved, stable IDs/bookmark names and citation/reference syntax do not leak into normal visible prose, and literal code marker text remains exempt only inside the code block.
  - Verification-surface change: `no`
  - Attempts: 1
  - Attempt 1 (2026-08-23): Checker PASS; exact Verify passed 2/2, related Review-region regression passed 6/6, Preview regression passed 5/6 with the known clean-baseline YAML Front Matter rejection at `tests/test_preview_presentation.py::test_complete_example_preview_preserves_compiler_order_and_numbering`, compiler/RenderPlan regression passed 30/30, target Ruff, `git diff --check`, and `./lint-loop.sh` passed. Independent audit confirmed the existing Review projector preserves listing code verbatim, sanitizes algorithm/caption technical markers, keeps source navigation in `ReviewBlock.source`, rejects unknown instructions explicitly, and adds no compatibility/fallback path. Candidate scope was the single named test file plus this lifecycle update; all pre-existing `openspec/**` paths were preserved and unstaged; one local commit, no push.

- [V2-507E4] Add executable listing and algorithm DOCX capability evidence
  - Parent: ordered evidence child 4/4 of `V2-507E`; depends on `V2-507E1`, `V2-507E2` and `V2-507E3`; the original `V2-507E` Behavior and Acceptance remain unchanged.
  - Files: `src/thesis_forge/renderers/docx/renderer.py`, `tests/renderers/docx/test_listing_algorithm.py`
  - Behavior: render listing and algorithm captions/content through configured paragraph styles with real sequence fields and paired stable bookmarks, and prove the complete source/IR/compiler/Review/DOCX path.
  - Verify: `.venv/bin/python -m pytest tests/renderers/docx/test_listing_algorithm.py`
  - Acceptance: the non-empty evidence proves both capabilities are not flattened to generic prose, captions and literal bodies survive Review and DOCX, configured style tokens are applied, real SEQ/bookmark structures are paired, unsupported object policy is explicit, and visible output contains no technical ID markers; the shared manifest evidence paths are executable.
  - Verification-surface change: `yes`; creates the capability evidence required by `spec/format-capabilities.yaml`.
  - Attempts: 3
  - Attempt 1 (2026-08-23): Checker FAIL; exact Verify passed 2/2, related parser/numbering/RenderPlan/Review/DOCX regression passed 107 tests plus figure/table/math caption regression passed 5 tests, target Ruff, `git diff --check`, and `./lint-loop.sh` passed. Independent mutation audit found weak evidence for real SEQ field structure, readable label placement inside the bookmark range, and complete literal listing/algorithm content; the candidate was retained for repair with no commit or push.
  - Attempt 2 (2026-08-23): Checker FAIL; exact Verify passed 2/2, target Ruff and `git diff --check` passed, but independent probes found unknown `RenderNode` still emitted the forbidden `[kind] {payload}` debug fallback and Listing/Algorithm ignored `CaptionSpec.position="bottom"`; the candidate was retained for repair with no commit or push.
  - Attempt 3 (2026-08-23): Checker PASS; exact Verify passed 4/4, related DOCX/compiler/Review regression passed 103/103, target Ruff, `git diff --check`, and `./lint-loop.sh` passed. Independent audit confirmed real SEQ `begin/separate/end` with dirty flag, readable labels inside paired stable bookmarks, complete parser/IR/compiler/Review/DOCX literal preservation including XML line breaks, configured caption styles and top/bottom positions, explicit rejection of unknown typed and `RenderNode` instructions, and no compatibility alias, debug fallback, duplicate source field, or scope creep. Candidate scope was exactly the two named product/test files plus this lifecycle update; all pre-existing `openspec/**` paths were preserved and unstaged; one local commit, no push.

- [V2-511E] Add executable capability evidence for the required DOCX math corpus
  - Parent: evidence-closure child of catalogue item `V2-511`; depends on completed `V2-510A`; the first unmet contract reported by `scripts/verify_thesisforge_v2_goal.py`.
  - Files: `tests/renderers/docx/test_math_corpus_v2.py`
  - Behavior: exercise the canonical Equation source/IR/compiler/Review/DOCX path for the required offline math corpus and prove editable OMML plus resolved sequence/bookmark semantics.
  - Verify: `.venv/bin/python -m pytest tests/renderers/docx/test_math_corpus_v2.py`
  - Acceptance: the evidence covers supported inline/display formula shapes through `EquationInstruction`, readable Review projection, native `m:oMath` output, real SEQ/bookmark structure when numbered, and explicit failure for unsupported or malformed math; it is non-empty executable evidence and the manifest path becomes valid without changing the capability registry.
  - Verification-surface change: `yes`; creates the capability evidence required by `spec/format-capabilities.yaml`.
  - Attempts: 2
  - Attempt 1 (2026-08-23): Checker FAIL; exact Verify `.venv/bin/python -m pytest tests/renderers/docx/test_math_corpus_v2.py` passed 3/3, but `.venv/bin/ruff check tests/renderers/docx/test_math_corpus_v2.py` failed `I001` because the `pytest` and `lxml` imports are out of order; `git diff --check` passed. Independent AST/runtime/XML audit passed the canonical parser -> Equation IR -> EquationInstruction -> math preflight -> ReviewEquationContent -> DOCX path, native fraction/sum/matrix OMML (`m:f`/`m:nary`/`m:m`), real SEQ and paired bookmarks, marker-free Review/DOCX text, structured unsupported/malformed diagnostics, and matching `object.equation` manifest evidence path. V2-511E remains Open; the Checker did not modify the candidate test, no commit or push, and all pre-existing `openspec/**` paths were preserved.
  - Attempt 2 (2026-08-23): Checker PASS; exact Verify `.venv/bin/python -m pytest tests/renderers/docx/test_math_corpus_v2.py` passed 3/3, `.venv/bin/ruff check tests/renderers/docx/test_math_corpus_v2.py` passed, and `git diff --check` passed. Independent AST/runtime/XML audit confirmed the canonical markdown-it parser -> Equation IR -> EquationInstruction -> validation/math preflight -> ReviewEquationContent -> DOCX path, real fraction/sum/matrix AST and `m:f`/`m:nary`/`m:m` OMML, exact SEQ fields with one-to-one same-paragraph formula bookmark pairs, marker-free Review/DOCX visible text, structured unsupported/malformed diagnostics, raw backslash corpus, no hidden skip or Pandoc/API/network dependency, and matching executable `object.equation` manifest evidence path. `./lint-loop.sh` passed; original Behavior/Acceptance and Attempt 1 remain intact, Open order is preserved, and all pre-existing `openspec/**` paths remain preserved and unstaged.

- [V2-506D] Render canonical typed table cells in DOCX and add capability evidence
  - Parent: ordered preparation child 5/5 of the re-sliced `V2-506`; depends on `V2-506M2`; the original V2-506 Behavior and Acceptance remain unchanged.
  - Files: `src/thesis_forge/renderers/docx/tables.py`, `tests/renderers/docx/test_structured_table.py`
  - Behavior: render structured headers, alignments and canonical typed cell runs in native DOCX tables without pipe parsing or semantic flattening.
  - Verify: `.venv/bin/python -m pytest tests/renderers/docx/test_structured_table.py`
  - Acceptance: the evidence test proves native table/caption/SEQ/bookmark and configured borders/alignment; cell strong/link/math/break/reference/citation/footnote semantics reach DOCX through the shared seam; visible cell text contains no raw citation or stable-ID markers; `spec/format-capabilities.yaml` object.table evidence path exists and is executable.
  - Verification-surface change: `yes`; creates the capability evidence required by `spec/format-capabilities.yaml`.
  - Attempts: 1
  - Attempt 1 (2026-08-23): Checker PASS; exact Verify passed 1/1; related regression passed 123/123 with no candidate-only failure; target Ruff, `git diff --check`, and `./lint-loop.sh` passed. CodeGraph/source audit confirmed the renderer uses canonical `TableCellInstruction.inlines` through `render_inline_runs`/`InlineHandlers`, preserves existing caption/SEQ/bookmark, alignment and border logic, and adds no pipe parsing, `cell.text` source, compatibility/fallback branch, raw marker or `[kind]` payload. Independent DOCX OPC/XML audit passed native table rows and alignments, borders, real SEQ begin/separate/end, paired bookmark start/end, bold/code/link/math/soft-break/hard-break/REF/citation/footnote cell semantics, hyperlink relationship and footnotes part, marker-free visible `w:t`, and matching executable `object.table` evidence path. Candidate scope was exactly the two named files; completed T/P1/M1/M2 and all pre-existing `openspec/**` paths were preserved; one local commit, no push.

- [V2-506M2] Establish canonical typed table-cell RenderPlan runs
  - Parent: ordered preparation child 4/5 of the re-sliced `V2-506`; depends on `V2-506M1`; the original V2-506 Behavior and Acceptance remain unchanged.
  - Files: `src/thesis_forge/core/render_plan.py`, `src/thesis_forge/core/compiler.py`, `tests/core/test_typed_table_render_plan.py`
  - Behavior: make structured table cells carry one validated tuple of canonical `InlineRun` values, remove raw `TableInstruction.markdown` and stored cell text, and compile cell Inline semantics through the authoritative compiler seam.
  - Verify: `.venv/bin/python -m pytest tests/core/test_typed_table_render_plan.py`
  - Acceptance: typed cells preserve text, strong/emphasis/code, link, math, soft/hard break, reference, citation and footnote runs; readable `text` is only a derived projection; unknown Inline values fail explicitly; `TableInstruction.payload` has no raw markdown or second cell source; existing downstream consumers remain green through a derived projection only.
  - Verification-surface change: `no`
  - Attempts: 1
  - Attempt 1 (2026-08-23): Checker PASS; exact Verify passed 7/7; related regression passed 131/132 with the sole clean-baseline failure at `tests/test_preview_presentation.py::test_complete_example_preview_preserves_compiler_order_and_numbering` (`TF-SOURCE-LEGACY-001` YAML Front Matter rejection), reproduced identically on an isolated clean `HEAD`. Target Ruff, `git diff --check`, and `./lint-loop.sh` passed. CodeGraph/source and runtime audits confirmed exactly three candidate files, one validated tuple of canonical InlineRun values, `TableCellInstruction.text` as a property only, no `TableCellRuns` or `TableInstruction.markdown`, compiler use of `context.inlines(... retain_citation_raw=False)`, derived-only downstream `cell.text` consumers, eight canonical run shapes, cleared citation raw, correct reference/footnote runs, explicit unknown-run failure, and no raw citation/target leakage in cell projections or table rows payload. V2-506D was not started; all pre-existing `openspec/**` paths remained uncommitted; one local commit, no push.
  - Parent re-slice history (2026-08-23): Checker FAIL; expected: the exact Verify and related regression would pass after the strict typed table-cell change. Observed: the exact Verify passed 7/7, but the related regression failed 130 passed, 2 failed because `tests/test_compiler.py` still accesses removed `table.markdown`; the second failure was the known clean-baseline `TF-SOURCE-LEGACY-001` YAML Front Matter rejection. The work was re-sliced into `V2-506M1` and `V2-506M2`, and all three candidate files were restored to `HEAD=e0ac590`; no commit or push.

- [V2-506M1] Migrate existing compiler table fixture assertion away from obsolete `table.markdown`
  - Parent: ordered preparation child 3/5 of the re-sliced `V2-506`; depends on `V2-506P1`; the original V2-506 Behavior and Acceptance remain unchanged.
  - Files: `tests/test_compiler.py`
  - Behavior: replace only the obsolete markdown-empty assertion with the canonical derived-cell/table payload contract needed before strict removal.
  - Verify: `.venv/bin/python -m pytest tests/test_compiler.py`
  - Acceptance: existing row/header/alignment/text/numbering assertions remain green, no production compatibility field/alias, no compiler behavior change.
  - Verification-surface change: `no`
  - Attempts: 1
  - Attempt 1 (2026-08-23): Checker PASS; exact Verify passed 24/24, `.venv/bin/ruff check tests/test_compiler.py`, `git diff --check`, and `./lint-loop.sh` passed (`LOOP-LINT: PASS — open=3 done=133 blocked=0` before this lifecycle update). The candidate diff was exactly one assertion replacement in `tests/test_compiler.py`; all existing row/header/alignment/text/numbering assertions remained green, `rg -n "table\.markdown" tests src frontend` found no consumer, and no production compatibility field/alias, fallback, second data source, or compiler behavior change was introduced. `openspec/**` and pre-existing `LOOP.md` changes were preserved and unstaged; one local Checker commit, no push.

- [V2-506P1] Migrate direct RenderPlan table fixtures to canonical typed cells
  - Parent: ordered preparation child 2/5 of the re-sliced `V2-506`; depends on `V2-506T`; the original V2-506 Behavior and Acceptance remain unchanged.
  - Files: `tests/test_render_plan.py`, `tests/test_preview_presentation.py`, `tests/presentation/test_review_regions.py`
  - Behavior: migrate every direct `TableInstruction` fixture to the upcoming canonical typed-cell constructor and remove raw `markdown` fixture data before strict RenderPlan enforcement.
  - Verify: `.venv/bin/python -m pytest tests/test_render_plan.py tests/test_preview_presentation.py tests/presentation/test_review_regions.py`
  - Acceptance: the named fixtures contain no `TableCellInstruction(text=...)` or `TableInstruction(markdown=...)` construction; all existing table payload, Preview and Review assertions remain green; no production compatibility path or alternate cell source is added.
  - Verification-surface change: `no`
  - Attempts: 1
  - Attempt 1 (2026-08-23): Checker PASS; exact Verify collected 18 tests with 17 passed and one known clean-baseline failure at `tests/test_preview_presentation.py::test_complete_example_preview_preserves_compiler_order_and_numbering` (`TF-SOURCE-LEGACY-001` YAML Front Matter rejection); isolated clean `HEAD=08eb4d8` produced the identical 17/1 result. AST/static audit found all three direct `TableInstruction` fixtures use `TableInstruction.from_typed_rows`, all four cells use `TableCellInstruction.from_inlines`, no `TableCellInstruction(text=...)`, `TableInstruction(markdown=...)`, or raw markdown fixture field, and the header/alignment/numbering/payload/Preview/Review assertions remain present and passing where reached. Typed-table/compiler regression passed 30/30, DOCX renderer regression passed 90/90; target Ruff, `git diff --check`, and `./lint-loop.sh` passed (`LOOP-LINT: PASS — open=3 done=132 blocked=0`). Candidate product scope was exactly the three named test files with no production compatibility layer or alternate source; unrelated `openspec/**` paths were preserved and unstaged; one local Checker commit, no push.

- [V2-506T] Define canonical typed table-cell constructors
  - Parent: ordered preparation child 1/5 of the re-sliced `V2-506`; the original V2-506 Behavior and Acceptance remain unchanged across T, P1, M1, M2 and D.
  - Files: `src/thesis_forge/core/render_plan.py`, `tests/core/test_typed_table_render_plan.py`
  - Behavior: define the renderer-neutral typed table-cell value and canonical constructors that accept validated `InlineRun` tuples before the strict RenderPlan consumer migration.
  - Verify: `.venv/bin/python -m pytest tests/core/test_typed_table_render_plan.py`
  - Acceptance: the typed cell value accepts exactly a tuple of declared `InlineRun` values, exposes only a derived readable projection, and provides canonical table constructors without raw `text=` or `markdown=` fixture arguments; existing compiler, Preview, Review and DOCX consumers remain green and no renderer/compiler path changes.
  - Verification-surface change: `no`
  - Attempts: 1
  - Attempt 1 (2026-08-23): Checker PASS; exact Verify passed 6/6; related compiler/DOCX/core inline regression passed 124/124; Preview/Review combination passed 11/12 with the sole clean-baseline `TF-SOURCE-LEGACY-001` YAML Front Matter failure at `tests/test_preview_presentation.py::test_complete_example_preview_preserves_compiler_order_and_numbering`, reproduced identically on isolated clean `HEAD=b77449f`; target Ruff, `git diff --check`, and `./lint-loop.sh` passed. Independent typed-boundary audit confirmed all eight InlineRun types are retained, readable projection is derived through the shared helper, list/iterator/tuple-subclass/unknown inputs are rejected, canonical constructor signatures expose neither `text` nor `markdown`, RenderPlan imports remain renderer-neutral, compiler/Preview/Review/DOCX consumer files are unchanged, and no silent fallback, legacy compatibility branch, second source of truth, or `[kind]` payload was added. Candidate product scope was exactly `src/thesis_forge/core/render_plan.py` and `tests/core/test_typed_table_render_plan.py`; `LOOP.md` is lifecycle-only, all `openspec/**` paths were preserved and unstaged, and no push.

- [V2-505B] Render rich figure captions in DOCX
  - Parent: ordered preparation child after the re-sliced `V2-505A`; depends on `V2-505A2C` and all seven `V2-505A1*` preparation children; the parent Behavior and Acceptance remain unchanged.
  - Files: `src/thesis_forge/renderers/docx/captions.py`, `src/thesis_forge/renderers/docx/figures.py`, `tests/renderers/docx/test_figure_rich_caption.py`
  - Behavior: render typed figure caption runs, fields, citations, references and configured styles in DOCX.
  - Verify: `.venv/bin/python -m pytest tests/renderers/docx/test_figure_rich_caption.py`
  - Acceptance: figure caption XML contains resolved readable content and valid field/bookmark structure, with no raw citation or cross-reference marker.
  - Verification-surface change: authorized; creates the capability evidence required by `spec/format-capabilities.yaml`.
  - Attempts: 1
  - Attempt 1 (2026-08-23): Checker PASS; exact Verify passed 1/1; related DOCX regression passed 91/91; target Ruff, `git diff --check`, and `./lint-loop.sh` passed. Independent CodeGraph/source and DOCX OPC/XML audits confirmed that `render_figure` forwards `FigureInstruction.caption` unchanged into the shared `add_caption` seam; all requested Text/Strong/Code/Hyperlink/Math/SoftBreak/HardBreak/Reference/Citation/FootnoteReference semantics are preserved; SEQ/REF fields have begin/separate/end structure and readable cached results; bookmarks cover only label/sequence; hyperlink, OMML, breaks, footnote references, template font/size/alignment, ordinary table captions, and marker-free visible `w:t` are valid. Candidate scope was exactly the three named files with `figures.py` unchanged; all pre-existing dirty paths were preserved; one local Checker commit, no push.

- [V2-505A2M] Store canonical typed figure-caption runs in the RenderPlan
  - Parent: ordered preparation child 3/4 of the re-sliced `V2-505A2`; depends on `V2-505A2P2` and `V2-505A1M`; the original V2-505A2 Behavior and Acceptance remain unchanged across `V2-505A2M` and `V2-505A2C`.
  - Files: `src/thesis_forge/core/render_plan.py`, `src/thesis_forge/core/compiler.py`, `tests/core/test_figure_caption_runs.py`
  - Behavior: establish one authoritative typed figure-caption representation in `FigureInstruction` and compile every caption Inline into that representation with document-order citation numbering.
  - Verify: `.venv/bin/python -m pytest tests/core/test_figure_caption_runs.py`
  - Acceptance: figure instructions carry canonical caption runs without a second raw caption source or compatibility alias; compiler output preserves label, sequence and bookmark data, resolves emphasis/link/math/break/reference/citation semantics, suppresses raw markers, and gives figure-before-body citations earlier ordinals.
  - Verification-surface change: no
  - Attempts: 3
  - Attempt 1 (2026-08-23): Checker FAIL; exact Verify passed 3/3; related core/Preview/Review/DOCX regression passed 141/142 with the known clean-baseline `tests/test_preview_presentation.py::test_complete_example_preview_preserves_compiler_order_and_numbering` YAML Front Matter failure; target Ruff, `git diff --check`, and `./lint-loop.sh` passed. Independent audit found `FigureInstruction` retains a public `caption` constructor/property/payload alongside `_caption_inlines` and `caption_inlines`, which is the forbidden raw/typed dual representation and compatibility path. A runtime probe also found the derived caption/payload leaks `[@cap]` when a `ReferenceRun.display_text` comes from a target figure caption containing a citation; unknown Inline failure, all ten Inline subclass branches, figure-before-body citation order, and renderer-neutral RenderPlan imports otherwise passed. Candidate files were restored; V2-505A2M remains Open; no commit or push.
  - Attempt 2 (2026-08-23): Checker FAIL; exact Verify passed 3/3; related core/compiler/DOCX/Review regression passed 293/294 with the existing parser-primitive baseline failure at `tests/core/test_markdown_v2_parser_config.py::test_markdown_v2_uses_public_parser_primitives`; Preview passed 5/6 with the known clean-baseline `tests/test_preview_presentation.py::test_complete_example_preview_preserves_compiler_order_and_numbering` YAML Front Matter failure (`TF-SOURCE-LEGACY-001`); target Ruff, `git diff --check`, and `./lint-loop.sh` passed. Expected: `FigureInstruction` must reject a raw caption input, and no target heading/figure citation or stable ID may leak into `ReferenceRun.display_text`, derived caption text, or payload. Actual: `FigureInstruction(caption="raw caption")` was accepted through `__post_init__`; a no-template runtime probe produced `FigureInstruction.payload["label"] == "sec:target fig:target[@source]"`, target figure payload label `"目标图题 fig:other[@targetfig]"`, `RenderPlan.references["fig:target"].display_text == "目标图题 fig:other[@targetfig]"`, and `ReferenceRun.display_text == "目标图题 fig:other"`. Inline coverage, explicit unknown-Inline failure, caption citation `raw=""`, figure-before-body ordinals, label/sequence/bookmark preservation, and renderer-neutral RenderPlan checks otherwise passed. Candidate files were restored; V2-505A2M remains Open; no commit or push.
  - Attempt 3 (2026-08-23): Checker PASS; exact Verify passed 5/5; related core/compiler/DOCX/Review regression passed 300/301 with only the clean-baseline parser primitive failure at `tests/core/test_markdown_v2_parser_config.py::test_markdown_v2_uses_public_parser_primitives`; Preview passed 5/6 with only the clean-baseline YAML Front Matter rejection `TF-SOURCE-LEGACY-001` at `tests/test_preview_presentation.py::test_complete_example_preview_preserves_compiler_order_and_numbering`; isolated clean `HEAD=b5d1940` reproduced both baseline failures. Target Ruff, `git diff --check`, and `./lint-loop.sh` passed. Independent structure/runtime audit confirmed one strict `caption: CaptionRuns` field with raw-string `TypeError`, no `caption_inlines` alias or second payload source, all eleven requested Inline branches, explicit unknown-Inline failure, empty caption citation raw with unchanged body citation raw, figure-before-body citation ordinals, preserved label/sequence/bookmark, marker/ID-free no-template label/caption/reference projections, and renderer-neutral RenderPlan imports. Candidate scope was exactly the three named files; A2C and B were not started; unrelated dirty paths were preserved; one local Checker commit, no push.

- [V2-505A2C] Compile rich figure captions and complete the DOCX inline consumer seam
  - Parent: ordered preparation child 4/4 of the re-sliced `V2-505A2`; depends on `V2-505A2M`, `V2-505A1P3`, `V2-505A1R`, `V2-505A1D1` and `V2-505A1D2`; the original V2-505A2 Behavior and Acceptance remain unchanged.
  - Files: `src/thesis_forge/renderers/docx/inlines.py`, `tests/core/test_figure_caption_runs.py`
  - Behavior: complete and evidence the shared DOCX inline consumer seam for ordinary body and future figure-caption runs without rejection or silent loss.
  - Verify: `.venv/bin/python -m pytest tests/core/test_figure_caption_runs.py`
  - Acceptance: DOCX dispatch accepts every declared `InlineRun`, including link/math/soft-break/hard-break runs, through the shared seam; unknown runs fail explicitly; the test proves no ordinary body or figure-caption run is silently dropped, while raw citation/reference markers remain absent.
  - Verification-surface change: no
  - Attempts: 1
  - Inherited Attempt 1 (2026-08-22): Checker FAIL; exact Verify `.venv/bin/python -m pytest tests/core/test_figure_caption_runs.py` passed 1/1; related compiler/RenderPlan/SymbolTable regression passed 35/35; target Ruff and `git diff --check` passed. Expected: typed caption runs preserve Inline semantics, the plan has one authoritative resolved caption representation without raw citation/reference markers, and figure-caption citations retain document order. Observed: `_compile_inlines` silently dropped `Emphasis`, `Link`, `InlineMath`, and `SoftBreak`; `FigureInstruction.caption` and its payload retained `[@smith2025]` and `fig:appendix` while the payload omitted `caption_inlines`; a figure-before-body citation received ordinal 2 while the later paragraph citation received ordinal 1. Cross-reference resolution and label/sequence/bookmark probes passed. Candidate files were restored; no commit or push.
  - Inherited Attempt 2 (2026-08-22): Checker FAIL; exact Verify passed 1/1; related regression passed 43/44 with the known clean-baseline `tests/test_preview_presentation.py::test_complete_example_preview_preserves_compiler_order_and_numbering` YAML Front Matter failure; DOCX regression passed 86/86; target Ruff, `git diff --check`, and `./lint-loop.sh` passed. Independent probes confirmed lossless figure InlineRun coverage, resolved caption and payload without raw citation/reference text, figure-before-body citation order, and old positional `FigureInstruction` construction. However, shared `_compile_inlines` emits `LinkRun`/`MathRun`/`BreakRun` for ordinary body inlines while Preview silently drops them and Review/DOCX reject them (`TypeError`/`DocxRenderError`), creating a real global regression and partial public seam. Candidate files were restored; no commit or push.
  - Attempt 1 (2026-08-23): Checker PASS; exact Verify passed 7/7; full `tests/test_docx_renderer.py` passed 90/90; target Ruff, `git diff --check`, and `./lint-loop.sh` passed. Independent CodeGraph and runtime audit confirmed the shared DOCX dispatch consumes all eight declared `InlineRun` variants for ordinary body and compiled figure-caption runs, explicitly rejects unknown runs, preserves handler events without silent loss, and keeps caption citation/reference technical markers out of the dispatched values. Candidate product change was exactly `tests/core/test_figure_caption_runs.py`; `src/thesis_forge/renderers/docx/inlines.py` was audited unchanged; pre-existing dirty paths were preserved; one local Checker commit, no push.

- [V2-505A2P2] Migrate direct FigureInstruction fixtures to typed captions
  - Parent: ordered prerequisite 2/4 of the re-sliced `V2-505A2`; depends on `V2-505A2P1`; the original V2-505A2 Behavior and Acceptance remain unchanged across P1, P2, A2M and A2C.
  - Files: `tests/test_render_plan.py`, `tests/test_preview_presentation.py`, `tests/presentation/test_review_regions.py`
  - Behavior: update every direct FigureInstruction fixture to pass `CaptionRuns` rather than a raw caption string before strict constructor enforcement.
  - Verify: `.venv/bin/python -m pytest tests/test_render_plan.py tests/test_preview_presentation.py tests/presentation/test_review_regions.py`
  - Acceptance: the named tests contain no raw-string FigureInstruction caption construction, remain green, and add no production compatibility path or alternate caption field.
  - Verification-surface change: no
  - Attempts: 1
  - Attempt 1 (2026-08-23): Checker PASS; exact Verify produced 17 passed/1 known clean-HEAD failure at `tests/test_preview_presentation.py::test_complete_example_preview_preserves_compiler_order_and_numbering` with YAML Front Matter `TF-SOURCE-LEGACY-001`; clean HEAD produced the identical 17/1 result; target Ruff, `git diff --check`, and `./lint-loop.sh` passed. AST audit confirmed all four direct FigureInstruction fixtures use `CaptionRuns`, including the positional fixture; candidate scope was exactly the three named test files with no production diff, raw caption, compatibility helper, or second caption field. Post-update LOOP-LINT passed with V2-505A2M, V2-505A2C and V2-505B still Open; one local commit, no push.

- [V2-505A2P1] Define the renderer-neutral typed caption value
  - Parent: ordered prerequisite 1/4 of the re-sliced `V2-505A2`; the original V2-505A2 Behavior and Acceptance remain unchanged across P1, P2, A2M and A2C.
  - Files: `src/thesis_forge/core/render_plan.py`, `tests/core/test_caption_runs_model.py`
  - Behavior: define the `CaptionRuns` typed value that will become the single FigureInstruction caption representation in the next preparation child.
  - Verify: `.venv/bin/python -m pytest tests/core/test_caption_runs_model.py`
  - Acceptance: `CaptionRuns` validates the declared `InlineRun` tuple and exposes one readable string projection without renderer/OOXML imports, raw caption aliases, or changes to existing FigureInstruction construction in this preparation child.
  - Verification-surface change: no
  - Attempts: 3
  - Attempt 1 (2026-08-23): Checker FAIL; exact Verify passed 2/2; target Ruff, `git diff --check`, and `./lint-loop.sh` passed. Expected: `CaptionRuns` accepts and stores only a declared `tuple[InlineRun, ...]`, with the readable projection and explicit unknown-run failure at that boundary. Actual: `CaptionRuns([TextRun("list")])` and `CaptionRuns(iter((TextRun("iterator"),)))` were both accepted and normalized into stored tuples, so the constructor accepts undeclared container types. Renderer-neutral import checks passed, and `FigureInstruction` plus `compiler.py` construction remained unchanged. Candidate files were restored; V2-505A2P1 remains Open; no commit or push.
  - Attempt 2 (2026-08-23): Checker FAIL; exact Verify passed 4/4; target Ruff, `git diff --check`, and `./lint-loop.sh` passed. Expected: the outer constructor accepts only the exact built-in `tuple` container, validates every element through `ensure_inline_run`, projects all eight canonical `InlineRun` variants readably, and rejects unknown values without renderer/OOXML dependencies. Actual: list, iterator, and unknown-object inputs were rejected, all-eight projection and renderer-neutral import checks passed, and `FigureInstruction` plus `compiler.py` remained unchanged, but `CaptionRuns(TupleSubclass((TextRun("subclass"),)))` was accepted because the boundary uses `isinstance(runs, tuple)` rather than an exact-type check. Candidate files were restored; V2-505A2P1 remains Open; V2-505A2P2/V2-505A2M/V2-505A2C/V2-505B remain Open, no commit or push.
  - Attempt 3 (2026-08-23): Checker PASS; exact Verify passed 5/5; target Ruff, `git diff --check`, and `./lint-loop.sh` passed (`LOOP-LINT: PASS — open=5 done=126 blocked=0` before this lifecycle update). Independent audit confirmed exact built-in tuple acceptance with list, iterator and tuple-subclass rejection; all eight canonical InlineRun projections; per-element `ensure_inline_run` validation; explicit unknown-element and invalid-container failures; renderer-neutral imports; unchanged FigureInstruction fields and payload seam; no `compiler.py` diff; and no raw caption alias or dual payload source. Candidate scope was exactly the two named files before this lifecycle update, all unrelated dirty paths were preserved, one local commit, no push.

- [V2-505A1D2] Consume canonical inline runs in DOCX footnote rendering
  - Parent: ordered preparation child 6/7 of the re-sliced `V2-505A1`; depends on `V2-505A1D1`.
  - Files: `src/thesis_forge/renderers/docx/footnotes.py`, `tests/test_docx_renderer.py`
  - Behavior: footnote definitions and references use the same canonical inline consumer seam as body content.
  - Verify: `.venv/bin/python -m pytest tests/test_docx_renderer.py -k test_docx_footnote_consumes_all_inline_run_variants`
  - Acceptance: footnote inline content preserves hyperlink, math and break semantics, shares no duplicate dispatch logic, and rejects unknown runs explicitly.
  - Verification-surface change: no
  - Attempts: 1
  - Attempt 1 (2026-08-23): Checker PASS; exact focused Verify passed 1/1, full `tests/test_docx_renderer.py` passed 90/90, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent DOCX/XML audit confirmed the shared `render_inline_runs` seam, footnote-part hyperlink relationship, native inline OMML, space-only soft breaks, real `w:br` hard breaks, preserved reference/citation/footnote-reference behavior, and explicit nested/unknown-run failures; candidate scope was exactly the two named files before this lifecycle update, all unrelated dirty paths were preserved, `V2-505A2` was not started, one local commit, no push.

- [V2-505A1D1] Consume canonical inline runs in DOCX body rendering
  - Parent: ordered preparation child 5/7 of the re-sliced `V2-505A1`; depends on `V2-505A1R`.
  - Files: `src/thesis_forge/renderers/docx/inlines.py`, `src/thesis_forge/renderers/docx/renderer.py`, `tests/test_docx_renderer.py`
  - Behavior: the shared DOCX inline dispatch and typed renderer consume hyperlink, math, soft-break and hard-break runs without rejection or silent loss.
  - Verify: `.venv/bin/python -m pytest tests/test_docx_renderer.py -k test_docx_renderer_consumes_all_inline_run_variants`
  - Acceptance: body/heading/list inline rendering covers every canonical run; soft breaks do not create `w:br`, hard breaks do; hyperlink and math paths produce their configured native structures; unknown runs fail with `DocxRenderError`.
  - Verification-surface change: no
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; exact Verify passed 1/1, full `tests/test_docx_renderer.py` passed 88/88, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent DOCX/XML audit confirmed all eight canonical runs through the shared body/heading/list seam, external hyperlink relationship plus `w:hyperlink`, inline `m:oMath`, space-only soft breaks, real `w:br` hard breaks, preserved reference/citation/footnote-reference behavior, and explicit `DocxRenderError` for unknown or unconfigured runs; candidate scope was exactly the three named files before this lifecycle update, all unrelated dirty paths were preserved, `V2-505A1D2` was not started, one local commit, no push.

- [V2-505A1P1] Project canonical inline runs in the Python Preview mapper
  - Parent: ordered preparation child 1/3 of the re-sliced `V2-505A1P`; the original A1P Behavior and Acceptance remain unchanged across A1P1, A1P2 and A1P3; depends on `V2-505A1M`.
  - Files: `src/thesis_forge/presentation/preview.py`, `tests/test_preview_presentation.py`
  - Behavior: the Python Preview mapper projects all eight canonical InlineRun variants, preserves hyperlink text/destination and math fallback text, distinguishes soft/hard breaks, rejects unknown values, and never emits raw citation/reference markers.
  - Verify: `.venv/bin/python -m pytest tests/test_preview_presentation.py -k test_preview_serializes_all_inline_run_variants`
  - Acceptance: the focused projection test covers text, semantic reference, hyperlink, math, soft break, hard break, citation and footnote runs; empty citation text never falls back to raw citation syntax; unknown runs fail explicitly; the mapper output is the source for the ordered transport child.
  - Verification-surface change: no
  - Attempts: 1
  - Inherited Attempt 1 (2026-08-22): the superseded A1P candidate projected all eight runs and passed the focused test, but leaked `CitationRun.raw` when text was empty; the independent Checker also found the new run shapes require the ordered frontend transport and panel children; candidate files were restored with no commit or push.
  - Attempt 1 (2026-08-22): Checker PASS; exact Verify passed 1/1; target Ruff, `git diff --check`, and `./lint-loop.sh` passed; complete preview tests were 5 passed/1 known clean-HEAD baseline failure at `test_complete_example_preview_preserves_compiler_order_and_numbering` with `TF-SOURCE-LEGACY-001`, while clean HEAD was 4 passed/1 with the identical failure and no candidate-only failure; independent AST/runtime probes confirmed all eight ordered projections, hyperlink destination, math readable fallback, distinct soft/hard break text, raw citation suppression, formatted citation preservation, and explicit unknown-run `TypeError`; candidate scope was exactly the two named product/test files plus this lifecycle update, frontend P2/P3 and A1R were not audited or modified, all unrelated dirty paths were preserved, one local commit and no push.

- [V2-505A1P2] Accept canonical inline runs in the Preview transport contract
  - Parent: ordered preparation child 2/3 of the re-sliced `V2-505A1P`; depends on `V2-505A1P1`.
  - Files: `frontend/src/transport/dto.ts`, `frontend/src/transport/previewDto.test.ts`
  - Behavior: the strict Preview transport DTO accepts the four new serialized inline run variants without accepting unknown types, extra keys, or compatibility payloads.
  - Verify: `pnpm --dir frontend exec vitest run src/transport/previewDto.test.ts`
  - Acceptance: the TypeScript union and runtime validator accept hyperlink text/destination, math latex/text, soft-break text and hard-break text alongside the existing four variants; malformed shapes and unknown run types remain rejected.
  - Verification-surface change: no
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; exact Verify passed 9/9, combined Preview transport regression passed 31/31, `pnpm --dir frontend typecheck`, `pnpm --dir frontend lint`, `git diff --check`, and `./lint-loop.sh` passed; independent DTO audit confirmed the exact eight-member TypeScript union, strict runtime field whitelists for all new runs, nested text/list/footnote validation, and rejection of unknown run types, extra keys, and malformed shapes; candidate scope was exactly the two named files before this lifecycle update, all unrelated dirty paths were preserved, one local commit and no push.

- [V2-505A1P3] Render canonical inline runs in the Preview panels
  - Parent: ordered preparation child 3/3 of the re-sliced `V2-505A1P`; depends on `V2-505A1P2`.
  - Files: `frontend/src/components/PreviewPanels.tsx`, `frontend/src/components/PreviewPanels.test.tsx`
  - Behavior: Preview panels render hyperlink destinations, readable math fallback text, and visibly distinct soft/hard breaks without exposing technical markers.
  - Verify: `pnpm --dir frontend exec vitest run src/components/PreviewPanels.test.tsx`
  - Acceptance: the focused panel test covers all four new run variants; hyperlinks retain destination semantics, math remains readable, soft breaks normalize spacing, hard breaks remain visible, and existing reference/citation/footnote rendering is unchanged.
  - Verification-surface change: no
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; exact Verify passed 6/6; `pnpm --dir frontend typecheck`, `pnpm --dir frontend lint`, `git diff --check`, and `./lint-loop.sh` passed; independent audit confirmed all eight canonical inline runs, real hyperlink destination semantics without visible technical markers, readable math fallback, soft-break space normalization, hard-break `<br>` semantics, and unchanged reference/citation/footnote rendering; candidate scope was exactly the two named frontend files before this lifecycle update, all unrelated dirty paths were preserved, and no push.

- [V2-505A1R] Project every canonical inline run in Review
  - Parent: ordered preparation child 4/7 of the re-sliced `V2-505A1`; depends on `V2-505A1P3`.
  - Files: `src/thesis_forge/presentation/review.py`, `tests/presentation/test_review_regions.py`
  - Behavior: Review projects every canonical InlineRun into readable marker-free content while retaining math and visible break semantics.
  - Verify: `.venv/bin/python -m pytest tests/presentation/test_review_regions.py -k test_review_projects_all_inline_run_variants`
  - Acceptance: link destinations and citation keys remain out of visible normal Review text; math has readable fallback content; soft/hard breaks remain distinguishable; unknown runs fail explicitly.
  - Verification-surface change: no
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; focused Verify passed 1/1; full `tests/presentation/test_review_regions.py` passed 6/6; target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent code audit confirmed all eight canonical inline projections, readable hyperlink/math fields with technical markers excluded from visible text, distinct soft/hard break Review runs, preserved text/reference/citation/footnote behavior, and explicit unknown-run `TypeError`; candidate scope was exactly the two named files before this lifecycle update, all unrelated dirty paths were preserved, no `V2-505A1D1` was started, no push.

- [V2-505A1M] Establish canonical typed inline RenderPlan runs
  - Parent: ordered preparation child 1/7 of the re-sliced `V2-505A1`; the original V2-505A1 Behavior and Acceptance remain unchanged across A1M, A1P1, A1P2, A1P3, A1R, A1D1 and A1D2.
  - Files: `src/thesis_forge/core/render_plan.py`, `tests/core/test_typed_inline_render_plan.py`
  - Behavior: define the capability-registered `SoftBreakRun`, `HardBreakRun`, `HyperlinkRun` and `MathRun` types in one `InlineRun` union with explicit unknown-run failure.
  - Verify: `.venv/bin/python -m pytest tests/core/test_typed_inline_render_plan.py`
  - Acceptance: the RenderPlan names exactly match `spec/format-capabilities.yaml`; all new runs carry their semantic fields without aliases or compatibility names; typed caption storage is not added as a second raw `caption` source in this preparation child.
  - Verification-surface change: no
  - Attempts: 1
  - Inherited Attempt 1 (2026-08-22): Checker FAIL; the superseded three-file A1 candidate passed 14 tests with the same one YAML Front Matter baseline failure as clean HEAD, and related regression passed 136/137 with the same baseline node. Target Ruff and `git diff --check` passed. Independent probes found the candidate used non-contract names `BreakRun`/`LinkRun`, retained `FigureInstruction.caption` beside `caption_inlines`, allowed raw markers through the figure caption projection, and left figure caption runs unconsumed by Preview/Review. Candidate files were restored; registry preserved; no commit or push.
  - Attempt 1 (2026-08-22): Checker PASS; exact Verify passed 5/5; targeted Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent AST/runtime audit confirmed the four canonical new dataclasses, the exact eight-member `InlineRun` union, renderer-neutral imports, explicit `TypeError` at the typed seam, and no aliases, generic payload, fallback, `caption_inlines`, or forbidden consumer modifications; candidate scope was exactly the two named product/test files, pre-existing `LOOP.md`, registry, OpenSpec codegraph and template-v2 dirty changes were preserved, and no push.

- [V2-512] Validate footnote graph integrity
  - Files: `src/thesis_forge/core/validator.py`, `tests/core/test_footnote_integrity_v2.py`
  - Behavior: validate footnote definitions and references as one graph, rejecting duplicate definitions, missing definitions and nested footnote references while allowing repeated references to one definition.
  - Verify: `.venv/bin/python -m pytest tests/core/test_footnote_integrity_v2.py`
  - Acceptance: duplicate definitions retain both source locations in structured issues; missing and nested references fail before compile/render; repeated references resolve without duplicate or overwritten footnote IDs.
  - Verification-surface change: authorized; creates the capability evidence required by `spec/format-capabilities.yaml`.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; exact Verify passed 4/4; related DocumentIndex/compiler/DOCX regression passed 123/123; targeted Ruff, `git diff --check`, and independent build-stop/compile-ID probes passed; missing and nested footnotes stopped at validation before compiler invocation, repeated references shared one definition ID, and duplicate issues retained both source locations; candidate scope was exactly the three named files, the pre-existing `openspec/.specnav/change-registry.json` was preserved and uncommitted, no push.

- [V2-501] Centralize semantic symbols and resolved cross-reference targets
  - Files: `src/thesis_forge/core/symbols.py`, `src/thesis_forge/core/compiler.py`, `tests/core/test_symbol_table.py`
  - Behavior: the compiler builds one symbol table containing public IDs, target types, display labels, numbering inputs and deterministic bookmark names before producing any render instruction.
  - Verify: `.venv/bin/python -m pytest tests/core/test_symbol_table.py`
  - Acceptance: duplicate public IDs and sanitized or truncated bookmark collisions fail before rendering; compiled references and existing figure/table/equation labels continue to resolve from the centralized entries.
  - Verification-surface change: authorized; creates the capability evidence required by `spec/format-capabilities.yaml`.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; exact Verify passed 5/5; related compiler/DOCX regression passed 110/110; targeted Ruff, `git diff --check`, and LOOP-LINT passed; independent SymbolTable and compile probes confirmed centralized public IDs, target types, display labels, numbering inputs, deterministic bookmarks, duplicate-ID and sanitized/truncated-bookmark collision rejection before RenderPlan generation, and preserved figure/table/equation labels, ReferenceRun, and RenderPlan.references; candidate scope was exactly the three named files plus this lifecycle update, the pre-existing `openspec/.specnav/change-registry.json` was preserved and uncommitted, no push.

- [V2-510A] Preflight inline and display math during validation
  - Parent: first executable child of catalogue item `V2-510`; re-sliced because the validation contract requires both the pure math seam and validator integration.
  - Files: `src/thesis_forge/core/math.py`, `src/thesis_forge/core/validator.py`, `tests/core/test_math_preflight.py`
  - Behavior: validate every parsed inline/display formula with the deterministic math converter before compile/render and return structured source-linked diagnostics for unsupported or malformed syntax.
  - Verify: `.venv/bin/python -m pytest tests/core/test_math_preflight.py`
  - Acceptance: supported inline and display formulas produce no math-preflight error; unsupported/malformed formulas produce stable structured issues with target, line and error details; no external provider or DOCX render is needed.
  - Verification-surface change: no
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; exact Verify passed 3/3; related regression was 199 passed/1 baseline failure at `tests/core/test_markdown_v2_parser_config.py::test_markdown_v2_uses_public_parser_primitives`, matching clean HEAD at 196 passed/1 same failure and recorded out-of-scope; targeted Ruff, `git diff --check`, and LOOP-LINT passed; static/runtime audit confirmed pure local math conversion, structured unsupported/malformed error issues with source navigation and no absolute path leakage, supported formulas clear, and no compatibility, fallback, silent-degradation, or dual-field path; candidate scope was exactly the three named files, the pre-existing `openspec/.specnav/change-registry.json` was preserved and uncommitted, one local commit, no push.

- [V2-320C] Migrate the first canonical V2 test cluster off core.parser
  - Parent: ordered preparation child 3/3 of the re-sliced `V2-320`; depends on `V2-320A`; the original V2-320 Behavior and Acceptance remain unchanged across the children.
  - Files: `tests/core/test_legacy_source_rejection.py`, `tests/core/test_markdown_v2_inlines.py`, `tests/core/test_markdown_v2_figures.py`
  - Behavior: canonical V2 tests import ParseError and shared parser primitives from the parser-support seam rather than the legacy parser module, while preserving their rejection, inline, and figure assertions.
  - Verify: `.venv/bin/python -m pytest tests/core/test_legacy_source_rejection.py tests/core/test_markdown_v2_inlines.py tests/core/test_markdown_v2_figures.py`
  - Acceptance: the selected tests contain no `core.parser` import and remain green against the canonical markdown-it backend; no compatibility import is added.
  - Verification-surface change: no.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; exact Verify passed 18/18; targeted Ruff, `git diff --check`, and `./lint-loop.sh` passed; candidate scope was exactly the three named test files with no production code, compatibility layer, or selector changes, the pre-existing `openspec/.specnav/change-registry.json` was preserved and uncommitted, one local commit, no push.

- [V2-320B] Remove the legacy parser from the public core surface
  - Parent: ordered preparation child 2/3 of the re-sliced `V2-320`; depends on `V2-320A`; the original V2-320 Behavior and Acceptance remain unchanged across the children.
  - Files: `src/thesis_forge/core/__init__.py`, `src/thesis_forge/core/parser_backend.py`, `tests/architecture/test_no_legacy_parser.py`
  - Behavior: stop importing or exporting `parse_markdown` and `parse_markdown_text` from `thesis_forge.core`, and add an architecture contract proving production modules no longer depend on `core.parser` outside the legacy implementation itself.
  - Verify: `.venv/bin/python -m pytest tests/architecture/test_no_legacy_parser.py`
  - Acceptance: the public core surface exposes the canonical parser factory/type and support ParseError only; the architecture test fails on any production import of `core.parser` outside `parser.py`.
  - Verification-surface change: no.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; exact Verify passed 2/2; related parser/backend regression passed 77/77; targeted Ruff, `git diff --check`, and `./lint-loop.sh` passed; the independent AST boundary probe found no production `core.parser` import outside legacy `parser.py`, and the runtime probe confirmed that `thesis_forge.core` has no `parse_markdown` or `parse_markdown_text`, `ParseError` is from `parser_support`, and `create_parser_backend()` returns the exact `MarkdownItParserBackend` type with no selector or compatibility re-export; candidate scope was exactly the three named files, `V2-320C` remained Open, the pre-existing `openspec/.specnav/change-registry.json` was preserved and uncommitted, the total-goal verifier retained 11 unrelated gaps, one local commit, no push.

- [V2-320A] Extract parser-neutral primitives from the legacy parser seam
  - Parent: ordered preparation child 1/3 of the re-sliced `V2-320`; the original V2-320 Behavior and Acceptance remain unchanged across the children.
  - Files: `src/thesis_forge/core/parser.py`, `src/thesis_forge/core/parser_markdown_it.py`, `src/thesis_forge/core/parser_support.py`
  - Behavior: move the shared ParseError, Front Matter, container, inline, and bibliography primitives used by the canonical markdown-it backend into one parser-support module; route both current parser implementations through that module without duplicating or re-exporting a backend selector.
  - Verify: `.venv/bin/python -m pytest tests/test_parser_backend.py tests/test_parser_markdown_it.py tests/test_parser_contract.py`
  - Acceptance: `parser_markdown_it.py` has no dependency on `core.parser`; every shared symbol has one authoritative definition; canonical parser and existing parser-contract coverage remain green.
  - Verification-surface change: no.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; exact Verify passed 73/73; targeted Ruff, `git diff --check`, and the final LOOP-LINT passed; the independent AST seam probe found no `core.parser` import in `parser_markdown_it.py`, exactly one definition each for ParseError, Front Matter, inline, container, and bibliography helpers in `parser_support.py`, and shared-symbol identity through the support module; normalized output for a rich legacy fixture was identical between the clean HEAD parser and the extracted parser with 0 diffs; both current parser paths parsed a stable heading, while the legacy and v2 fixtures produced their expected stable IDs; candidate scope was exactly the three named product files, the pre-existing `openspec/.specnav/change-registry.json` was preserved and uncommitted, no push.

- [V2-319D] Delete the parser registry and legacy backend API
  - Parent: ordered child 4/4 of the re-sliced `V2-319`; depends on `V2-319C`; parent Behavior and Acceptance remain unchanged.
  - Files: `src/thesis_forge/core/parser_backend.py`, `tests/core/test_single_parser_backend.py`
  - Behavior: remove `PARSER_BACKENDS`, parser-name lookup, `parser_backend_names()`, and `LegacyParserBackend`; leave exactly one production parser factory/type.
  - Verify: `.venv/bin/python -m pytest tests/core/test_single_parser_backend.py tests/test_parser_backend.py tests/test_parser_markdown_it.py`
  - Acceptance: no CLI/env/parser-name switching remains and static/runtime checks show one production parser path.
  - Verification-surface change: no.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; exact Verify passed 45/45; `.venv/bin/ruff check src/thesis_forge/core/parser_backend.py tests/core/test_single_parser_backend.py`, `git diff --check`, and `./lint-loop.sh` passed (`LOOP-LINT: PASS — open=1 done=112 blocked=0` before this lifecycle update). Production static search found no `PARSER_BACKENDS`, `LegacyParserBackend`, `get_parser_backend`, or `parser_backend_names` definitions/calls, and no parser CLI/env/name selector or parser compatibility branch; runtime probes confirmed `create_parser_backend()` has no parameters, returns exact `MarkdownItParserBackend`, and the four old module APIs are absent. Candidate scope was exactly the two named files before this LOOP update; `openspec/.specnav/change-registry.json` was preserved and uncommitted; the total-goal verifier retained 11 unrelated historical/future contract gaps; one local commit and no push.

- [V2-319C2B] Rebase template-v2 editor L5 fixtures on canonical source
  - Parent: ordered child 2/2 of the re-sliced `V2-319C2`; depends on `V2-319C2A`; the original `V2-319C2` Behavior and Acceptance remain unchanged.
  - Files: `tests/test_template_v2_editor.py`
  - Behavior: the template-v2 editor L5 validator-error fixture uses canonical v2 Markdown and still proves duplicate IDs are reported after the parser seam changes.
  - Verify: `.venv/bin/python -m pytest tests/test_template_v2_editor.py -k 'lint_l5'`
  - Acceptance: all template-v2 L5 fixture coverage uses canonical source syntax without YAML Front Matter or a compatibility branch.
  - Verification-surface change: no.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; exact Verify passed 4/4; `.venv/bin/ruff check tests/test_template_v2_editor.py`, `git diff --check`, and `./lint-loop.sh` passed (`LOOP-LINT: PASS — open=2 done=111 blocked=0` before this lifecycle update); the candidate diff was limited to removal of the YAML Front Matter from the canonical duplicate-ID fixture, with no production code, compatibility branch, or old YAML fixture residue; the duplicate-ID validator assertion remained green; `openspec/.specnav/change-registry.json` was preserved and uncommitted; no push.

- [V2-319C2A] Migrate template-v2 L5 lint and canonical fixtures
  - Parent: ordered child 1/2 of the re-sliced `V2-319C2`; depends on `V2-319C1`; the original `V2-319C2` Behavior and Acceptance remain unchanged across C2A and C2B.
  - Files: `src/thesis_forge/templates/v2/lint.py`, `tests/test_template_v2.py`, `spikes/phase0/docx-template/package-sample/fixtures/minimal/thesis.md`
  - Behavior: template-v2 L5 fixture lint uses the canonical parser factory/type, the generated and shipped fixtures use canonical v2 source without YAML Front Matter, and metadata-free fixture validation explicitly uses `required_metadata=()` rather than a legacy fallback.
  - Verify: `.venv/bin/python -m pytest tests/test_template_v2.py tests/test_parser_backend.py tests/test_parser_markdown_it.py`
  - Acceptance: template tooling and its fixture coverage use the same single-parser API as the application path, with no legacy import, automatic migration, compatibility branch, or silent skip.
  - Verification-surface change: no.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; the effective LOOP Verify ran 102 tests with 97 passed and 5 pre-existing package-sample `reference.docx`/`shell.docx` missing-asset failures; isolated clean HEAD ran 96 passed and 6 failed, with the candidate failure set a strict subset and only the clean-only YAML Front Matter failure at `test_lint_l1_external_relationship_allowlist`; targeted Ruff, `git diff --check`, and `./lint-loop.sh` passed; canonical parser, metadata-free L5, and duplicate-ID probes passed; candidate scope was exactly the three named files, C2B was untouched, the pre-existing registry was preserved, and no push.

- [V2-319C1] Migrate public core exports to the canonical parser API
  - Parent: ordered child 1/2 of the re-sliced `V2-319C`; depends on `V2-319B`; the original `V2-319C` Behavior and Acceptance remain unchanged across C1 and C2.
  - Files: `src/thesis_forge/core/__init__.py`
  - Behavior: the public core surface exposes the canonical parser factory/type without importing or exporting `LegacyParserBackend`, parser registry lookup, or parser-name switching.
  - Verify: `.venv/bin/python -m pytest tests/core/test_single_parser_backend.py tests/test_parser_backend.py tests/test_parser_markdown_it.py`
  - Acceptance: public core imports use the same single-parser API as the application path; template-v2 migration remains the dependent C2 child.
  - Verification-surface change: no.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; exact Verify passed 44/44; targeted Ruff, `git diff --check`, and `./lint-loop.sh` passed; the public-surface probe confirmed `core.create_parser_backend` is the canonical factory returning `MarkdownItParserBackend`, the three legacy/registry names are absent from the core public surface, and `parse_markdown`/`parse_markdown_text` remain available; candidate scope was exactly `src/thesis_forge/core/__init__.py`, registry preserved and uncommitted, no push.

- [V2-319B] Remove parser-name switching from the QA diff tool
  - Parent: ordered child 2/4 of the re-sliced `V2-319`; depends on `V2-319A2B`; parent Behavior and Acceptance remain unchanged.
  - Files: `qa/tools/parser_diff.py`, `tests/test_parser_backend.py`, `tests/test_parser_markdown_it.py`
  - Behavior: replace the dual-backend CLI and registry/name assertions with canonical single-parser calls while retaining deterministic document normalization coverage.
  - Verify: `.venv/bin/python -m pytest tests/test_parser_backend.py tests/test_parser_markdown_it.py`
  - Acceptance: the QA tool has no backend-name CLI/env selector and its tests no longer depend on parser registry switching.
  - Verification-surface change: no.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; exact Verify `.venv/bin/python -m pytest tests/test_parser_backend.py tests/test_parser_markdown_it.py` passed 41/41; related regression `.venv/bin/python -m pytest tests/test_parser_contract.py tests/test_adapters.py` passed 65/65; target Ruff, `git diff --check`, and CLI probe passed. The CLI probe confirmed canonical self-check exit 0, exact dump names `canonical-a.normalized.json` and `canonical-b.normalized.json`, illegal `--allow` exit 2, and rejection of the removed `--backend-a` selector. Candidate and clean-HEAD archive runs both passed the exact and related commands with empty failure node sets. Static scope review found no registry/name lookup, legacy fallback, parser-name selector, environment switch, or compatibility branch in the three candidate files; the candidate scope was exactly those three files before this LOOP update, and the pre-existing `openspec/.specnav/change-registry.json` remained uncommitted and unchanged by the Checker.

- [V2-319A2B] Route application dependencies through the canonical parser
  - Parent: ordered child 2/2 of the re-sliced `V2-319A2`; depends on `V2-319A2A`; original `V2-319A2` Behavior and Acceptance remain unchanged.
  - Files: `src/thesis_forge/application/services.py`, `tests/test_application_services.py`
  - Behavior: make `ApplicationDependencies` use the canonical parser factory by default and align application-service coverage with the v2 source contract.
  - Verify: `.venv/bin/python -m pytest tests/test_application_services.py`
  - Acceptance: the default application path uses the canonical v2 parser seam and the full application-service regression remains green.
  - Verification-surface change: no.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; exact Verify passed 77/77; related regression `.venv/bin/python -m pytest tests/application/test_project_services.py tests/test_application_services.py tests/test_adapters.py` passed 115/115; `.venv/bin/ruff check src/thesis_forge/application/services.py tests/test_application_services.py`, `git diff --check`, and `./lint-loop.sh` passed (`LOOP-LINT: PASS — open=4 done=107 blocked=0`). Runtime probe confirmed `ApplicationDependencies().parser_backend` is `MarkdownItParserBackend` from `thesis_forge.core.parser_markdown_it`, and its dataclass default factory is `create_parser_backend`; static scope review found no `LegacyParserBackend` import, fallback, selector, or compatibility branch in the candidate files. Candidate and clean-HEAD `tests/test_acceptance.py` runs both produced 2 passed/6 failed with the identical six failure nodes: `test_complete_example_inventory_and_offline_inspect_are_read_only`, `test_complete_example_validates_and_builds_offline_without_mutating_inputs`, `test_complete_example_docx_contains_required_visible_content_and_word_objects`, `test_complete_example_repeated_builds_have_identical_plan_and_word_ooxml`, `test_complete_example_two_templates_change_style_not_semantics`, and `test_same_list_markdown_uses_hut_and_default_template_policies_offline`; these are old YAML/project-entry fixtures outside this item. Candidate `tests/test_lo_finalizer.py` was 8 passed/5 errors versus clean HEAD 13 passed; all five candidate-only errors are the same old `examples/complete-thesis/thesis.md` YAML Front Matter fixture and remain out of scope. Candidate scope was exactly the two named files before the LOOP update; `openspec/.specnav/change-registry.json` was preserved and uncommitted; no push.

- [V2-319A2A] Rebase adapter and acceptance fixtures on the canonical parser seam
  - Parent: ordered preparation child 1/2 of the re-sliced `V2-319A2`; preserves the original `V2-319A2` Behavior and Acceptance for the dependent child.
  - Files: `tests/test_adapters.py`, `tests/test_acceptance.py`
  - Behavior: application-adapter and template-error regression fixtures that exercise application services use canonical v2 source/dependency seams instead of YAML Front Matter assumptions.
  - Verify: `.venv/bin/python -m pytest tests/test_adapters.py tests/test_acceptance.py -k 'dispatcher or template_failures'`
  - Acceptance: the selected adapter/template-error coverage is green before the production default flips and introduces no new failure when the canonical default is enabled.
  - Verification-surface change: no.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; exact Verify 12/12, full adapter regression 33/33, application regression 115/115, target Ruff, `git diff --check`, and LOOP-LINT passed; candidate and clean-HEAD acceptance runs were both 2 passed/6 failed with the identical six baseline failure nodes, while the selected canonical-default simulation remained green at 12/12 and adapters 33/33; runtime probes confirmed `MarkdownItParserBackend` through the real dependency/context seams. Candidate scope was exactly the two named test files, the registry was preserved and unstaged, one local commit and no push.

- [V2-319A1] Establish the canonical parser factory/type
  - Parent: ordered child 1/2 of the re-sliced `V2-319A`; parent Behavior and Acceptance remain unchanged.
  - Files: `src/thesis_forge/core/parser_backend.py`, `tests/core/test_single_parser_backend.py`
  - Behavior: expose the canonical single-parser factory/type without adding a parser selector.
  - Verify: `.venv/bin/python -m pytest tests/core/test_single_parser_backend.py`
  - Acceptance: the focused contract identifies the canonical v2 parser factory/type; application default migration remains the dependent child.
  - Verification-surface change: no.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; exact Verify `.venv/bin/python -m pytest tests/core/test_single_parser_backend.py` passed 3/3; related parser/backend/contract regression `.venv/bin/python -m pytest tests/test_parser_backend.py tests/test_parser_markdown_it.py tests/test_parser_contract.py` passed 76/76; target Ruff, `git diff --check`, and `./lint-loop.sh` passed. Static review confirmed the canonical factory is parameterless and always returns `MarkdownItParserBackend`, with no selector/fallback/compatibility branch; tests assert non-empty v2 parse output and a stable heading ID. Candidate scope was exactly the two named files; the registry was preserved and unstaged; one local commit and no push.

- [V2-317] Listing and algorithm fences
  - Files: `src/thesis_forge/core/parser_markdown_it.py`, `tests/core/test_markdown_v2_fences.py`
  - Behavior: parse fenced listing/algorithm attributes into typed nodes.
  - Verify: `.venv/bin/python -m pytest tests/core/test_markdown_v2_fences.py`
  - Acceptance: literal code markers remain literal; required IDs/titles follow the spec.
  - Verification-surface change: authorized; creates focused listing/algorithm evidence.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; exact Verify passed 9/9; related parser/backend/contract regression passed 105/105; target Ruff, `git diff --check`, and `./lint-loop.sh` passed. Independent probes confirmed ordinary backtick/tilde fences remain literal CodeBlock, listing/algorithm become typed nodes with typed titles, algorithm body/body_lines preserve blank-line locations, malformed ID/title/prefix/attribute cases fail explicitly, and arbitrary fenced code is not misclassified. Candidate scope was the two named product files plus LOOP, `change-registry.json` was preserved and unstaged, one local commit and no push.

- [V2-316] Display math and equation ID
  - Files: `src/thesis_forge/core/parser_markdown_it.py`, `tests/core/test_markdown_v2_equations.py`
  - Behavior: parse display math plus following `{#eq:id}` as Equation and support unnumbered display math explicitly.
  - Verify: `.venv/bin/python -m pytest tests/core/test_markdown_v2_equations.py`
  - Acceptance: duplicate or detached equation ID is diagnosed.
  - Verification-surface change: authorized; creates focused display-equation evidence.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; exact Verify passed 9/9; related parser/backend/contract regression passed 96/96; target Ruff, `git diff --check`, `./lint-loop.sh`, and an independent runtime probe covering multi-line/single-line display math, unnumbered equations, adjacent IDs, duplicate/detached/invalid IDs, unclosed delimiters, and empty formulas passed. The known V2-314 inline baseline failure remained unchanged and outside the candidate diff; scope was the two named product files plus LOOP, `change-registry.json` was preserved and unstaged, one local commit and no push.

- [V2-315] GFM table and caption
  - Files: `src/thesis_forge/core/parser_markdown_it.py`, `tests/core/test_markdown_v2_tables.py`
  - Behavior: parse structured rows/cells/alignment and the following `: caption {#tbl:id}` line.
  - Verify: `.venv/bin/python -m pytest tests/core/test_markdown_v2_tables.py`
  - Acceptance: escaped pipes and inline semantics in cells work; malformed column counts fail.
  - Verification-surface change: authorized; creates focused standard-table evidence.
  - Attempts: 2
  - Attempt 1 (2026-08-22): Checker FAIL; exact Verify passed 6/6, related parser/backend/contract regression passed 76/76, target Ruff, `git diff --check`, and `./lint-loop.sh` passed, but an independent probe found valid GFM `A | B` / `--- | ---` rows were rejected because the candidate required outer pipes; candidate files were restored, registry was preserved and unstaged, no commit or push.
  - Attempt 2 (2026-08-22): Checker PASS; exact Verify `.venv/bin/python -m pytest tests/core/test_markdown_v2_tables.py` passed 6/6; related regression `.venv/bin/python -m pytest tests/core/test_markdown_v2_tables.py tests/core/test_markdown_v2_figures.py tests/test_parser_markdown_it.py tests/test_parser_backend.py tests/test_parser_contract.py` passed 87/87; target Ruff `./.venv/bin/ruff check src/thesis_forge/core/parser_markdown_it.py tests/core/test_markdown_v2_tables.py`, `git diff --check`, and `./lint-loop.sh` passed. Independent Python/runtime probe printed markdown-it tight-caption token maps (`table_open.map=[0,4]`, caption `tr_open.map=[3,4]`), verified optional outer pipes, escaped pipe as one typed `Text` cell, left/center/right alignment, typed caption/id, no-blank and blank-line caption consumption before heading, malformed caption/column `ParseError`, and no-caption behavior. The repair removes the outer-pipe requirement and consumes caption content from the actual table/tr/paragraph token maps; registry remained preserved and unstaged.

- [V2-314] Standard image to Figure
  - Files: `src/thesis_forge/core/parser_markdown_it.py`, `tests/core/test_markdown_v2_figures.py`
  - Behavior: parse `![caption](path){#fig:id}` as Figure and reject figure without valid ID.
  - Verify: `.venv/bin/python -m pytest tests/core/test_markdown_v2_figures.py`
  - Acceptance: caption is typed inline content; width is not read from Markdown.
  - Verification-surface change: authorized; creates focused standard-figure evidence.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; exact Verify passed 5/5, related parser/backend/contract regression passed 85/85, target Ruff, `git diff --check`, and `./lint-loop.sh` passed. Independent Python probe confirmed Figure id/src/location, typed Strong and semantic caption inlines, explicit ParseError for missing/wrong/empty IDs, `Figure.width is None` with Markdown width not read, footnote-definition consumption to the following heading, citation/semantic-link indexing, and explicit rejection of images embedded in ordinary paragraphs. Scope was the two named product files plus LOOP update; registry remained unchanged and unstaged; no V2-315 changes and no push.

- [V2-313] Basic block conversion
  - Files: `src/thesis_forge/core/parser_markdown_it.py`, `tests/core/test_markdown_v2_blocks.py`
  - Behavior: parse headings, paragraphs, nested lists, blockquotes and code blocks.
  - Verify: `.venv/bin/python -m pytest tests/core/test_markdown_v2_blocks.py`
  - Acceptance: source spans and heading IDs are accurate.
  - Verification-surface change: authorized; creates focused basic-block evidence.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; exact Verify passed 4/4, related parser/backend/contract regression passed 80/80, target Ruff, `git diff --check`, and `./lint-loop.sh` passed. Independent Python probe confirmed heading level/ID/title inline SourceLocation, paragraph block line/SoftBreak/text SourceLocation, ordered and nested unordered list start/ordinal/level/item line and text column, BlockQuote line with typed Paragraph child, and fenced CodeBlock language/literal/line. Candidate scope was the named test plus LOOP update with no parser diff; `change-registry.json` was unchanged and unstaged; no undeclared production change or blockquote-nested-list extension was added; no push.

- [V2-312] Academic inline conversion
  - Files: `src/thesis_forge/core/parser_markdown_it.py`, `tests/core/test_markdown_v2_semantic_inlines.py`
  - Behavior: parse citation clusters, semantic internal links and footnote references.
  - Verify: `.venv/bin/python -m pytest tests/core/test_markdown_v2_semantic_inlines.py`
  - Acceptance: normal links remain links; `#fig:*` targets become CrossReference with fallback label.
  - Verification-surface change: authorized; creates focused academic-inline evidence.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; exact Verify passed 4/4, related parser/backend/contract regression passed 80/80, target Ruff, `git diff --check`, and `./lint-loop.sh` passed. Independent Python probe confirmed all seven semantic targets (`fig`, `tbl`, `eq`, `sec`, `chap`, `lst`, `alg`) become `CrossReference` with target/fallback, ordinary URL and `#fragment` remain `Link`, citation cluster is `Citation`, footnote reference/definition are typed, and SourceLocation line/column mapping is correct under the block location contract. V2-312 diff was limited to the two named product files before this LOOP update; the pre-existing registry remained preserved; no push.

- [V2-318] Explicit legacy syntax rejection
  - Files: `src/thesis_forge/core/parser_markdown_it.py`, `tests/core/test_legacy_source_rejection.py`, `tests/test_parser_markdown_it.py`
  - Scope note: the existing markdown-it backend test contains legacy parity fixtures; its legacy-input assertions are re-expressed as explicit rejection checks while standard-token coverage remains.
  - Behavior: reject YAML Front Matter, legacy thesis containers and legacy `@fig:*` references before generic parsing.
  - Verify: `.venv/bin/python -m pytest tests/core/test_legacy_source_rejection.py`
  - Acceptance: diagnostics include replacement examples and do not flatten old syntax to text.
  - Verification-surface change: authorized; creates focused legacy-source rejection evidence.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; exact Verify 5/5, related parser/backend/contract regression 76/76, core/parser/compiler regression 183/183, target Ruff, `git diff --check`, and `./lint-loop.sh` passed. Independent probes confirmed valid/unclosed/invalid Front Matter, all six legacy containers, all seven legacy reference prefixes, line/code/replacement diagnostics, citation-like/inline/fenced literal safety, preflight ordering before `self._md.parse` and document node construction, and fenced CodeBlock preservation.

- [V2-311] Standard inline conversion
  - Files: `src/thesis_forge/core/parser_markdown_it.py`, `tests/core/test_markdown_v2_inlines.py`, `tests/test_parser_markdown_it.py`
  - Behavior: convert text, breaks, strong, emphasis, code, links and inline math to typed Inline nodes with SourceSpan.
  - Verify: `.venv/bin/python -m pytest tests/core/test_markdown_v2_inlines.py`
  - Acceptance: ordinary newline becomes SoftBreak; explicit hard break is distinct.
  - Verification-surface change: authorized; creates the v2 inline conversion tests.
  - Attempts: 2
  - Attempt 1 (2026-08-22): Checker FAIL; exact Verify passed 5/5, related parser/backend/contract regression passed 81/81, core/parser/compiler regression passed 139/139, target Ruff, `git diff --check`, and `./lint-loop.sh` passed. Independent probes confirmed nested Strong/Emphasis spans, SoftBreak versus HardBreak, code `$...$` isolation, defined `footnote_ref` retention, and explicit unknown-token `ParseError`; however, valid CommonMark `[link](https://example.com/a_(b))` raised `ParseError` because `_consume_link()` stopped at the first `)`, and valid escaped text `cost \$5 and $x$` failed source mapping. Expected standard link/text token conversion without loss; observed rejection of valid inline forms. The three candidate files were restored to `HEAD`, `openspec/.specnav/change-registry.json` was preserved, no commit or push.
  - Attempt 2 (2026-08-22): Checker PASS; exact Verify passed 8/8, related parser/backend/contract regression passed 81/81, core/parser/compiler regression passed 183/183, target Ruff, `git diff --check`, and `./lint-loop.sh` passed. Independent probes confirmed nested Strong/Emphasis spans, SoftBreak versus HardBreak, code `$...$` isolation, balanced-parenthesis ordinary links, reference-link cursor preservation, escaped-dollar source mapping, HTTPS/email autolinks, and explicit unknown-image `ParseError`; candidate scope was exactly the three named product files, `change-registry.json` was preserved, and no push.

- [V2-310B1] Route enabled standard block tokens through a typed consumer
  - Parent: ordered child 1/2 of the re-sliced `V2-310B`; the parent Behavior and Acceptance remain unchanged.
  - Files: `src/thesis_forge/core/parser_markdown_it.py`, `tests/test_parser_markdown_it.py`
  - Behavior: standard Markdown block tokens have a typed/lossless consumer or an explicit diagnostic path before the production preset enables them; no token is silently ignored or flattened into Paragraph.
  - Verify: `.venv/bin/python -m pytest tests/test_parser_markdown_it.py tests/test_parser_backend.py tests/test_parser_contract.py`
  - Acceptance: parser/backend regressions remain green; independent default-token probes show blockquote, fence and table tokens reach typed nodes, while unsupported standard tokens fail explicitly instead of being silently discarded.
  - Verification-surface change: authorized; extends parser block-consumer regression coverage.
  - Attempts: 3
  - Attempt 1 (2026-08-22): Checker FAIL; exact Verify passed 82/82, related parser/core/compiler regression passed 173/173, target Ruff, `git diff --check`, LOOP-LINT, and top-level default-token probes passed; however, a mixed default document failed because `_emit_fence()` returned a fixed `1` while the caller assigned it to the absolute token index, leaving `blockquote_close` unconsumed, and a list containing an indented fence hung in `_scan_list`; expected every enabled block token to be consumed or explicitly diagnosed, observed token-index loss and a non-terminating compatibility path. Candidate and HEAD full pytest failure sets matched the known 45 failures (`1079 passed, 45 failed` vs `1078 passed, 45 failed`), the two candidate files were restored, `change-registry.json` was preserved, no commit or push.
  - Attempt 2 (2026-08-22): Checker FAIL; exact Verify passed 84/84, target Ruff, `git diff --check`, and LOOP-LINT passed. The mixed default probe consumed `BlockQuote -> CodeBlock -> Table -> Heading` in order; list fence/blockquote/table/code_block/hr probes terminated within the timeout with stable `ParseError`, and the injected unknown token produced an explicit diagnostic. However, a list containing an indented setext heading (`heading_open`) returned `ListBlock` plus a flattened `Paragraph` instead of a stable `ParseError`, violating the immutable no-token-loss/no-Paragraph-flattening behavior for other standard blocks. Candidate full pytest was `1081 passed, 45 failed`; clean HEAD was `1078 passed, 45 failed`, with the same 45 failure nodes. The two candidate files were restored, `change-registry.json` and prior LOOP history were preserved, no commit or push.
  - Attempt 3 (2026-08-22): Checker PASS; exact Verify passed 85/85, related parser/core/compiler regression passed 123/123, target Ruff, `git diff --check`, and LOOP-LINT passed. The independent mixed default probe consumed `BlockQuote -> CodeBlock -> Table -> Heading` in order; list fence/blockquote/table/indented-code/hr/setext plus html_block/reference token paths terminated within the timeout with stable explicit `ParseError`; top-level code_block/hr/html_block/reference/unknown paths produced explicit diagnostics. Candidate full pytest was `1082 passed, 45 failed`; clean HEAD was `1078 passed, 45 failed`, with an identical known 45-node failure set. The candidate diff was limited to the two named files, `change-registry.json` remained preserved, and no push.

- [V2-310B2] Enable the markdown-it CommonMark/GFM configuration
  - Parent: ordered child 2/2 of the re-sliced `V2-310B`; depends on `V2-310B1`.
  - Files: `src/thesis_forge/core/parser_markdown_it.py`, `tests/core/test_markdown_v2_parser_config.py`, `tests/test_parser_markdown_it.py`
  - Scope note: enabling the default preset changes the intended type of the standard top-level tables and blockquote in `bachelor-full-template`; the existing legacy-parity fixture pin must be re-expressed as a typed-block assertion in the named parser test.
  - Behavior: enable required CommonMark/GFM rules and remove legacy semantic-equivalence configuration.
  - Verify: `.venv/bin/python -m pytest tests/core/test_markdown_v2_parser_config.py`
  - Acceptance: emphasis, links, images, backticks, blockquote and fence are enabled; the backend does not disable those rules; the parser/backend baseline stays green after the production preset changes.
  - Verification-surface change: authorized; extends the v2 parser configuration tests.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; exact Verify 2/2, related parser/backend/contract regression 85/85, core/parser/compiler regression 134/134, target Ruff, `git diff --check`, LOOP-LINT, production active-rule/mixed-block probe, and full-repo failure-set comparison passed; candidate had 45 failures versus clean HEAD 46, with no candidate-only failure and only the removed `bachelor-full-template` parity pin clean-only; scope was the three named files, registry preserved, no push.

- [V2-310A] Remove private parser-helper imports through a shared public seam
  - Parent: ordered child 1/2 of the re-sliced `V2-310`; the parent Behavior and Acceptance remain unchanged.
  - Files: `src/thesis_forge/core/parser.py`, `src/thesis_forge/core/parser_markdown_it.py`, `tests/core/test_markdown_v2_parser_config.py`
  - Behavior: the markdown-it backend consumes the existing parser primitives through public names without copying legacy parsing logic or importing private helpers.
  - Verify: `.venv/bin/python -m pytest tests/core/test_markdown_v2_parser_config.py tests/test_parser_markdown_it.py tests/test_parser_backend.py`
  - Acceptance: the focused AST pin finds no private parser-helper import; parser/backend parity and existing parser behavior remain green; no CommonMark block is flattened as part of this seam change.
  - Verification-surface change: authorized; creates the focused v2 parser configuration test.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; exact Verify 50/50, parser/core regression 141/141, target Ruff, `git diff --check`, LOOP-LINT, unchanged full-repo failure set of 45, and 8 cross-worktree parser/backend digests passed; public seam only, no V2-310B/V2-311 scope, and the pre-existing `change-registry.json` was preserved.

- [V2-309C] Emit canonical duplicate diagnostics from validation
  - Files: `src/thesis_forge/core/validator.py`, `src/thesis_forge/application/contracts.py`, `tests/test_validator.py`
  - Behavior: validate_document bridges duplicate-ID findings from the derived index into the canonical application diagnostic contract, preserving order, locations and structured details.
  - Verify: `.venv/bin/python -m pytest tests/test_validator.py`
  - Acceptance: duplicate IDs are no longer production-only unlocated ValidationIssue values; the BuildReport boundary receives stable code/category/stage/source/related fields without a parallel diagnostic model.
  - Verification-surface change: authorized; extends validator diagnostic coverage.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; exact Verify 17/17, target Ruff, `git diff --check`, core/application/adapter regression 54/54, application/CLI/E2E regression 84/84, and independent coordinate/order/legacy probes passed; DocumentIndex nested conflicts bridge to duplicate-id issues with source/related details, canonical `TF-SEMANTIC-DUPLICATE-ID`/semantic/validate fields, unique validation IDs, and source-file-only ranges; diff limited to the three named files, while the pre-existing `change-registry.json` timestamp change was preserved; no push.

- [V2-309B] Make diagnostic presentation headless-safe
  - Files: `src/thesis_forge/presentation/diagnostics.py`, `src/thesis_forge/ui/__init__.py`, `tests/core/test_diagnostics.py`
  - Behavior: presentation localizes ValidationIssue and the canonical BuildDiagnostic through a formatter registry; derived-index duplicate diagnostics carry both locations and unique IDs without eager core imports.
  - Verify: `.venv/bin/python -m pytest tests/core/test_diagnostics.py tests/test_architecture.py`
  - Acceptance: legacy ValidationIssue messages remain unchanged; typed diagnostics localize; nested and locationless duplicate definitions report both locations with unique IDs; importing headless UI does not load application/compiler/rendering modules.
  - Verification-surface change: authorized; creates focused diagnostics tests.
  - Attempts: 2
  - Attempt 1 (2026-08-22): Checker FAIL; the legacy `duplicate-id` formatter read the new canonical `details.object_id` fallback, changing `ValidationIssue(target=None, details={"object_id": ...})` from the historical `重复 ID：` to `重复 ID：<id>`; exact Verify 15/15, Ruff, diff-check, headless import and duplicate-location probes otherwise passed. 修正为 legacy/canonical 分离 formatter 并补充回归 pin。
  - Attempt 2 (2026-08-22): Checker PASS; exact Verify 16/16, related regression 169/169, target Ruff, diff-check, headless architecture probe, and nested/locationless duplicate probe passed; legacy `duplicate-id` target=None behavior remains pinned, and canonical `TF-SEMANTIC-DUPLICATE-ID` uses a separate formatter.

- [V2-309A] Harden the canonical BuildDiagnostic contract
  - Parent: ordered child 1/3 of the re-sliced `V2-309`.
  - Files: `src/thesis_forge/application/contracts.py`, `tests/application/test_build_report_contract.py`, `tests/adapters/test_build_report_dto.py`
  - Behavior: the existing BuildDiagnostic/BuildSourceRange contract is the sole typed diagnostic model; details and source ranges reject malformed runtime values while preserving related locations.
  - Verify: `.venv/bin/python -m pytest tests/application/test_build_report_contract.py tests/adapters/test_build_report_dto.py`
  - Acceptance: no second core diagnostic model is introduced; BuildReport and DTOs preserve stable code/category/stage/source/related/suggestion/details fields and reject invalid typed values.
  - Verification-surface change: authorized; extends diagnostic contract coverage.
  - Attempts: 3
  - Attempt 1 (2026-08-22): Checker FAIL; exact Verify 16/16, target Ruff, `git diff --check`, and application/adapter regression 57/57 passed, but tests did not cover every malformed runtime boundary.
  - Attempt 2 (2026-08-22): Checker FAIL; exact Verify 43/43, target Ruff, `git diff --check`, and application/adapter regression 84/84 passed, but same-line reverse columns, individual id/code/message type failures, and non-Mapping/detail-key failures lacked direct tests.
  - Attempt 3 (2026-08-22): Checker PASS; exact Verify 47/47, application/adapter regression 88/88, target Ruff and `git diff --check` passed; implementation uses the existing BuildDiagnostic contract, all malformed boundaries have direct tests, DTO round-trip/path sanitization remain green, no push.

- [V2-307G2] Remove the cache fields and register_inlines from ThesisDocument
  - Parent: ordered child 14/14 of `V2-307`; depends on `V2-307G1`.
  - Files: `src/thesis_forge/core/model.py`, `tests/core/test_no_manual_caches.py`
  - Behavior: `inline_content`, `cross_references`, `citations`, `footnote_references` and `register_inlines` are removed from ThesisDocument.
  - Verify: `.venv/bin/python -m pytest tests/core/ tests/test_parser.py tests/test_parser_markdown_it.py tests/test_compiler.py`
  - Acceptance: no cache field or registration method remains in the model; baselines stay green.
  - Verification-surface change: authorized; finalizes the no-manual-caches test.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; model.py diff is deletion-only (four cache fields plus the register_inlines method; index_by_id retained with its live preview caller), the no-manual-caches test rewritten to absence pins (hasattr on parsed documents, exact derived citation order, model and compiler source scans), exact Verify 166/166, Ruff and `git diff --check` clean, repo-wide greps found no functional cache references, attribute probes confirmed slots AttributeError and TypeError on cache kwargs, broader regression 200/200 and parity OK, DocumentIndex and validator-index suites 16/16; no push.

- [V2-307G1] Fixtures drop redundant cache constructor kwargs
  - Parent: ordered child 13a/14 of `V2-307` (G re-sliced); depends on `V2-307F`.
  - Files: `tests/test_compiler.py`, `tests/test_docx_renderer.py`, `tests/core/test_manifest_resource_validation.py`
  - Behavior: the eleven redundant `citations=[...]` mirror kwargs are removed from ThesisDocument constructions; the citations already live in real inline content.
  - Verify: `.venv/bin/python -m pytest tests/test_compiler.py tests/test_docx_renderer.py tests/core/test_manifest_resource_validation.py`
  - Acceptance: no cache-field constructor kwarg remains in the three files; suites stay green before and after the model drops the fields.
  - Verification-surface change: authorized; removes redundant fixture kwargs.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; diff is deletion-only (eleven citations= mirror kwargs, 5/3/3), exact Verify 114/114, Ruff and `git diff --check` clean, repo-wide tests grep finds zero cache constructor kwargs, apply-and-restore simulation of the field-less model kept all three suites 114/114 green (only the G2-owned cache-clear test failed as pre-authorized), broader baseline 100/100, model.py restored byte-exact; no push.

- [V2-307F] Markdown-it parser stops registering inlines
  - Parent: ordered child 12/13 of `V2-307`; depends on `V2-307E`.
  - Files: `src/thesis_forge/core/parser_markdown_it.py`
  - Behavior: the markdown-it backend no longer calls `register_inlines`.
  - Verify: `.venv/bin/python -m pytest tests/test_parser_markdown_it.py tests/test_parser_backend.py tests/test_parser_contract.py`
  - Acceptance: no `register_inlines` call remains in parser_markdown_it.py; parity stays OK.
  - Verification-surface change: none.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; diff is 0 additions / 8 deletions (seven register_inlines call sites plus the now-unused _parse_container_inlines import; the helper itself retained in parser.py), exact Verify 81/81, Ruff and `git diff --check` clean, repo-wide grep found register_inlines only at its model.py definition (self-recursion internal), empty-cache probe confirmed mdit parses leave caches empty with full index derivation, parity OK on all three shipped examples, broader baselines 134/134; no push.

- [V2-307E] Legacy parser stops registering inlines
  - Parent: ordered child 11/13 of `V2-307`; depends on `V2-308` (all readers migrated first).
  - Files: `src/thesis_forge/core/parser.py`
  - Behavior: the legacy parser no longer calls `register_inlines`; its output documents carry blocks/inlines only.
  - Verify: `.venv/bin/python -m pytest tests/test_parser.py tests/test_parser_contract.py tests/test_parser_backend.py`
  - Acceptance: no `register_inlines` call remains in parser.py; suites stay green with empty cache lists.
  - Verification-surface change: none.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; diff is exactly the five deleted register_inlines call lines with `_parse_container_inlines` retained for the markdown-it backend, exact Verify 50/50, Ruff and `git diff --check` clean, empty-cache probe confirmed legacy parses leave all four caches empty while block inlines and the derived index keep full semantics, broader baselines 232/232 and parity OK, source-wide grep found no remaining cache readers in production; no push.

- [V2-308B] Validator consumes DocumentIndex
  - Parent: second child of the re-sliced `V2-308`; depends on `V2-308A`.
  - Files: `src/thesis_forge/core/validator.py`, `tests/core/test_validator_document_index.py`
  - Behavior: ID, reference, citation and footnote validation reads one derived DocumentIndex instead of parser-maintained caches.
  - Verify: `.venv/bin/python -m pytest tests/core/test_validator_document_index.py`
  - Acceptance: nested caption/cell semantics are validated through the derived index.
  - Verification-surface change: authorized; creates focused validator index tests.
  - Attempts: 2
  - Attempt 1 (2026-08-22): Checker FAIL; the four-site flip matched the item's planned swap list, but a residual `document.index_by_id()` read remained in `_validate_layout_overrides` — layout-override ID validation is inside the item's immutable Behavior scope, so the candidate was completed with a fifth swap in the same two files rather than restored.
  - Attempt 2 (2026-08-22): Checker PASS; validator.py diff is one import plus five swaps (cross-references by_id+sequence, bibliography citations local, template citation line, layout overrides by_id), exact Verify 3/3 with caption/cell/body-line pins, broad baselines 181/181 and object-overrides 7/7, grep found zero cache-field or index_by_id reads, layout-override probe confirmed orphan/type-mismatch/duplicate semantics under first-wins by_id, cache-clear parity probe byte-identical on a non-empty issue list, negative control confirmed cache-only citations are invisible; no push.

- [V2-308A] Manifest-resource validation fixtures carry real content citations
  - Parent: first child of the re-sliced `V2-308`; depends on `V2-307D2`.
  - Files: `tests/core/test_manifest_resource_validation.py`
  - Behavior: the three ThesisDocument fixtures place their Citation inside Paragraph inlines instead of injecting it only into the `citations` cache field.
  - Verify: `.venv/bin/python -m pytest tests/core/test_manifest_resource_validation.py`
  - Acceptance: the fixtures are green before and after the validator stops reading the cache; no fixture constructs a citation that exists only in a cache field.
  - Verification-surface change: authorized; migrates validation fixtures.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; diff is exactly the three fixtures carrying their citation in Paragraph inlines (blocks list added where absent) with the same object mirrored in the cache kwarg, exact Verify 4/4, Ruff and `git diff --check` clean, standalone probes proved index-derived citations are object-identical for all three shapes while a cache-only citation yields an empty index, broader tests/core baseline 87/87, one stray blank line squashed before commit; no push.

- [V2-307D2] E2E and object-model test cache pins migrate to index reads
  - Parent: ordered child 10/13 of `V2-307`; depends on `V2-307D1`.
  - Files: `tests/test_qa_e2e.py`, `tests/core/test_thesis_object_model.py`
  - Behavior: assertions on cache fields re-express against DocumentIndex-derived sequences.
  - Verify: `.venv/bin/python -m pytest tests/test_qa_e2e.py tests/core/test_thesis_object_model.py`
  - Acceptance: no cache-field assertion remains in the two files; suites stay green.
  - Verification-surface change: authorized; migrates e2e and object-model assertions.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; both files show only assertion-source swaps plus one sorted DocumentIndex import, exact Verify 9/9, Ruff and `git diff --check` clean, zero cache-field assertions remain, broader baselines 123/123 and CLI 23/23, expected values unchanged; no push.

- [V2-307D1e] Parser test cache pins migrate to index reads
  - Parent: ordered child 9/13 of `V2-307`; depends on `V2-307D1d`.
  - Files: `tests/test_parser.py`, `tests/test_parser_contract.py`, `tests/test_parser_markdown_it.py`
  - Behavior: assertions on `doc.inline_content`/`doc.citations`/`doc.cross_references`/`doc.footnote_references` re-express against DocumentIndex-derived sequences.
  - Verify: `.venv/bin/python -m pytest tests/test_parser.py tests/test_parser_contract.py tests/test_parser_markdown_it.py`
  - Acceptance: no cache-field assertion remains in the three files; suites stay green.
  - Verification-surface change: authorized; migrates parser test assertions.
  - Attempts: 2
  - Attempt 2 (2026-08-22): Checker PASS after the D1a-D1d re-slice prerequisites landed; unstaged diff is purely assertion-source swaps plus one sorted import per file, exact Verify 83/83, Ruff and `git diff --check` clean, grep sweep finds zero cache-field assertions in the three files, value-equivalence probe showed index-derived and cache-derived citations/cross-references/footnote labels are object-identical on the complete-thesis corpus, broader baselines 99/99 and parity OK (45 blocks / 92 inlines), expected-value sides unchanged; no push.
  - Attempt 1 (2026-08-22): Checker FAIL; migrating all 20 cache-pin sites left 4 tests red — expected index-derived values, observed typed-model defects the cache had masked: caption inline locations carry the container start line (figure line 1 vs caption line 3; both backends), table-cell inline locations are misaligned (line 4 vs data-row line 6), and algorithm-body citations are unrepresentable (Algorithm.body is verbatim-only, cache-only semantics). Files restored; re-sliced into D1a–D1e fixing the typed model first.

- [V2-307D1d] DocumentIndex traverses Algorithm body lines
  - Parent: ordered child 8/13 of `V2-307`; depends on `V2-307D1c`.
  - Files: `src/thesis_forge/core/index.py`, `tests/core/test_document_index.py`
  - Behavior: the index traversal walks Algorithm body_lines so body citations/references join the derived collections.
  - Verify: `.venv/bin/python -m pytest tests/core/test_document_index.py tests/core/test_no_manual_caches.py`
  - Acceptance: algorithm-body citations appear in index.citations with accurate locations.
  - Verification-surface change: authorized; extends index traversal tests.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; index.py diff is exactly the Algorithm body_lines walk inside the captioned-blocks branch, one new index test pins the (5, 9) body citation, exact Verify 16/16, broader baselines 153/153, end-to-end probe confirmed index.citations equals the cache-registered citation with document order preserved and the unknown-subclass TypeError contract intact; no push.

- [V2-307D1c] Markdown-it populates typed Algorithm body lines
  - Parent: ordered child 7/13 of `V2-307`; depends on `V2-307D1b`.
  - Files: `src/thesis_forge/core/parser_markdown_it.py`, `tests/test_parser_markdown_it.py`
  - Behavior: the markdown-it backend populates the same typed `body_lines`.
  - Verify: `.venv/bin/python -m pytest tests/test_parser_markdown_it.py tests/test_parser_backend.py`
  - Acceptance: both backends yield identical body_lines and parity stays OK.
  - Verification-surface change: authorized; adds backend body-line pins.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; parser_markdown_it.py needed zero production changes because container emission reuses the shared `_parse_container` (import verified at lines 63/311), the cycle adds one explicit markdown-it pin test (body citation at (5, 9) plus cross-backend body_lines/body equality), exact Verify 49/49, broader parser baseline 42/42, parity OK on both shipped examples, mutation-reasoning confirmed the pin is non-vacuous; no push.

- [V2-307D1b] Legacy parser populates typed Algorithm body lines
  - Parent: ordered child 6/13 of `V2-307`; depends on `V2-307D1a`.
  - Files: `src/thesis_forge/core/model.py`, `src/thesis_forge/core/parser.py`, `tests/test_parser_contract.py`
  - Behavior: Algorithm owns `body_lines` typed inline sequences populated by the legacy parser while `body` stays verbatim.
  - Verify: `.venv/bin/python -m pytest tests/test_parser_contract.py tests/core/`
  - Acceptance: algorithm-body citations are representable on the typed node with accurate locations; model and core baselines stay green.
  - Verification-surface change: authorized; adds typed body-line pins.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; model.py adds only the defaulted Algorithm.body_lines field, parser.py diff confined to the algorithm branch (body_lines from located non-empty content lines with absolute line numbers; caption_inlines on the shared accurate construction), one pin block added, exact Verify 118/118, broader baselines 148/148, probes confirmed flattened body_lines equals the algorithm container's cache-registered inline sequence (kind/line/column identical), verbatim body unchanged, markdown-it identical via the shared container path, parity OK; no push.

- [V2-307D1a] Caption and table-cell inline source locations are accurate
  - Parent: ordered child 5/13 of `V2-307` (D1 re-sliced); depends on `V2-307C`.
  - Files: `src/thesis_forge/core/parser.py`, `src/thesis_forge/core/parser_markdown_it.py`, `tests/test_parser_contract.py`
  - Behavior: figure/table caption inlines carry the caption line/column and table-cell inlines carry their own row line, matching the locations the parser registers today, in both backends.
  - Verify: `.venv/bin/python -m pytest tests/test_parser_contract.py tests/test_parser_backend.py tests/test_parser.py`
  - Acceptance: typed caption/cell citation locations equal the cache-registered locations for the same source (e.g. figure caption line 3, table data-row line 6); both backends agree and parity stays OK.
  - Verification-surface change: authorized; adds typed-object location pins.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; parser.py diff confined to _parse_container (caption line/column via body offsets, located content lines, shared caption_inlines) and _parse_table_rows (located (line_no, raw) pairs, per-row source lines), parser_markdown_it.py needed zero changes because it reuses _parse_container, two typed-location pins added next to the cache pins, exact Verify 50/50, broader baselines 245/245 and CLI 23/23, parity OK on both shipped examples, probes confirmed typed caption (line,column) == cache and typed cell line == cache on both backends; no push.

- [V2-307C] QA parity tool derives normalized sequences from the index
  - Parent: ordered child 4/9 of `V2-307`; depends on `V2-307B`.
  - Files: `qa/tools/parser_diff.py`, `tests/test_parser_backend.py`
  - Behavior: parser_diff's normalized inline/citation/reference sequences come from DocumentIndex; parity semantics and normalized keys are unchanged.
  - Verify: `.venv/bin/python -m pytest tests/test_parser_backend.py tests/test_parser_markdown_it.py`
  - Acceptance: legacy-vs-markdown-it parity stays OK on shipped examples; no parser_diff read of the cache fields remains.
  - Verification-surface change: authorized; migrates the parity-tool regression.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; parser_diff.py diff is the DocumentIndex import, one index build in normalize_document, docstring note, and OK-message count source swap (tests/test_parser_backend.py needed zero changes), exact Verify 48/48, Ruff and `git diff --check` clean, parity probes green on all three shipped examples (45/87, 43/82, 185/305 blocks/inlines; 0 exemptions) plus legacy/legacy self-check, index-vs-cache completeness probe showed equal index-derived counts (87=87) on both backends with six caption/cell inlines newly covered, normalized JSON keys unchanged, grep found no cache-field read; no push.

- [V2-307B] CLI inspect JSON derives semantic collections from the index
  - Parent: ordered child 3/9 of `V2-307`; depends on `V2-307A2` (the split parent reference `V2-307A` was corrected when the parent split into A1/A2).
  - Files: `src/thesis_forge/cli.py`, `tests/test_cli.py`
  - Behavior: inspect's `inline_content`/`cross_references`/`citations`/`footnote_references` JSON entries are computed from DocumentIndex traversal.
  - Verify: `.venv/bin/python -m pytest tests/test_cli.py tests/cli/`
  - Acceptance: inspect JSON payloads stay shape- and value-identical on parser-shaped projects; no CLI read of the cache fields remains.
  - Verification-surface change: authorized; migrates the inspect JSON pin.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; cli.py diff is one sorted import plus index-derived reads of the four JSON entries, test_cli.py adds the full 10-kind inline_content sequence pin, exact Verify 23/23, broader cli/adapters baseline 48/48, Ruff and `git diff --check` clean, value-identity probe confirmed index-derived and cache-derived payloads are asdict-equal on the fixture, grep found no CLI cache-field read under any variable name; no push.

- [V2-307A2] DocumentIndex gains the full inline sequence; compiler derives semantics from it
  - Parent: ordered child 2/9 of `V2-307`; depends on `V2-307A1`.
  - Files: `src/thesis_forge/core/index.py`, `src/thesis_forge/core/compiler.py`, `tests/core/test_no_manual_caches.py`
  - Behavior: DocumentIndex exposes the traversal-ordered full inline sequence; the compiler's footnote-label and citation collection read the derived index instead of `ThesisDocument` cache fields.
  - Verify: `.venv/bin/python -m pytest tests/core/test_no_manual_caches.py tests/core/test_document_index.py tests/test_compiler.py`
  - Acceptance: compiling a parser-shaped document after clearing the four cache lists produces an identical RenderPlan; parsed figure-caption citations join the citation order; no compiler read of `document.citations`/`document.footnote_references` remains.
  - Verification-surface change: authorized; creates the no-manual-caches focused test.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; index.py diff is the pure additive pre-order `inlines` sequence, compiler.py diff is one import plus three lines in `_initial_citation_numbers` (index built once; referenced_labels and the tail numbering loop read the index), exact Verify 39/39, Ruff and `git diff --check` clean, broader baselines 177/177, independent probes confirmed identical RenderPlan with cleared caches, figure-caption citations joining the order, zero compiler cache-field reads by grep, and a non-vacuous tamper simulation on the source-scan pin; no push.

- [V2-307A1] Compiler container-citation pin migrates to parsed content
  - Parent: ordered child 1/9 of `V2-307` (was 1/8 before this split); depends on `V2-306`.
  - Files: `tests/test_compiler.py`
  - Behavior: `test_compile_document_includes_registered_container_citations_in_global_order` constructs its container citation through parsed figure-caption content instead of injecting it only into the `ThesisDocument.citations` cache.
  - Verify: `.venv/bin/python -m pytest tests/test_compiler.py`
  - Acceptance: the pin is green before and after the compiler stops reading the cache; no test constructs a citation that exists only in a cache field.
  - Verification-surface change: authorized; migrates the compiler container-citation pin.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; diff limited to the named file (renamed test parses a figure container whose caption carries the citation; parse_markdown_text import added), exact Verify 24/24 green on the cache-based compiler and 27/27 green with the parked V2-307A2 flip applied then restored, Ruff and `git diff --check` clean, survey of all five remaining `citations=[...]` constructions in the file confirmed every citation also lives in real inline content; no push.

- [V2-306] DocumentIndex derives semantic indexes by traversal
  - Files: `src/thesis_forge/core/index.py`, `tests/core/test_document_index.py`
  - Behavior: one DocumentIndex builder derives the ID, citation, cross-reference and footnote indexes by traversing the immutable document; duplicate public IDs surface every conflicting location instead of overwriting.
  - Verify: `.venv/bin/python -m pytest tests/core/test_document_index.py`
  - Acceptance: nested caption inlines, table cells, list-item children, footnote definitions and nested Strong/Emphasis children are indexed; duplicate IDs report both locations and never overwrite by dictionary construction.
  - Verification-surface change: authorized; creates focused DocumentIndex tests.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; diff limited to the 2 new files (pure addition, no production consumer yet), traversal covers all 14 Block subclasses with nested caption/cell/list-item/footnote/Strong>Emphasis indexing, by_id keeps the first claimant while id_conflicts records every later claimant with both nodes, unknown Block/Inline subclasses raise TypeError naming the class, traversal is non-mutating, exact Verify 12/12, Ruff and `git diff --check` clean, baselines (tests/core/ + test_compiler) 107/107, independent probes confirmed nested semantic collection, triple-duplicate conflict shape, and both TypeError paths; no push.

- [V2-305E2B] Remove raw thesis-object caption/text fields
  - Parent: ordered child 8/8 of `V2-305`; depends on `V2-305E2A`.
  - Files: `src/thesis_forge/core/model.py`, `src/thesis_forge/core/parser.py`, `tests/core/test_thesis_object_model.py`
  - Behavior: Figure/Listing/Algorithm no longer store raw caption strings and FootnoteDefinition no longer stores duplicate text; typed inlines/content are authoritative.
  - Verify: `.venv/bin/python -m pytest tests/core/test_thesis_object_model.py tests/test_parser.py tests/test_parser_contract.py tests/test_compiler.py tests/test_docx_renderer.py tests/test_preview_presentation.py`
  - Acceptance: no raw caption/text plus typed-inline duplication remains for the targeted objects; all structured object paths stay green.
  - Verification-surface change: authorized; finalizes the rich thesis-object model contract.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; Figure/Listing/Algorithm raw caption fields and FootnoteDefinition text field were removed, parser constructors use typed fields, raw IR scan is clean outside template configuration, exact Verify 162/162, Ruff and `git diff --check` clean; no push.

- [V2-305E2A] Migrate parser object caption assertions
  - Parent: ordered child 7/8 of `V2-305`; depends on `V2-305E1B`.
  - Files: `tests/test_parser_contract.py`
  - Behavior: parser Figure/Algorithm caption assertions read caption inlines instead of raw caption fields.
  - Verify: `.venv/bin/python -m pytest tests/test_parser_contract.py`
  - Acceptance: parser object contract remains green without raw caption assertions.
  - Verification-surface change: authorized; migrates parser object contract assertions.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; Figure/Algorithm parser assertions now use caption_inlines, exact Verify 32/32, Ruff and `git diff --check` clean; no push.

- [V2-305E1B] Migrate manifest validation object captions
  - Parent: ordered child 6/7 of `V2-305`; depends on `V2-305E1A`.
  - Files: `tests/core/test_manifest_resource_validation.py`
  - Behavior: Figure fixtures rely on caption inlines rather than raw caption strings.
  - Verify: `.venv/bin/python -m pytest tests/core/test_manifest_resource_validation.py`
  - Acceptance: manifest/resource validation regression remains green with typed figure caption fixtures.
  - Verification-surface change: authorized; migrates validation object fixtures.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; Figure fixture uses caption_inlines only, exact Verify 4/4, AST/Ruff/diff-check clean; no push.

- [V2-305E1A] Migrate compiler/DOCX/preview object captions
  - Parent: ordered child 5/7 of `V2-305`; depends on `V2-305D`.
  - Files: `tests/test_compiler.py`, `tests/test_docx_renderer.py`, `tests/test_preview_presentation.py`
  - Behavior: Figure/Listing/Algorithm fixtures rely on caption inlines rather than raw caption strings.
  - Verify: `.venv/bin/python -m pytest tests/test_compiler.py tests/test_docx_renderer.py tests/test_preview_presentation.py`
  - Acceptance: object compiler, DOCX and preview regressions remain green with typed caption fixtures.
  - Verification-surface change: authorized; migrates object caption fixtures.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; AST found zero raw caption kwargs for Figure/Listing/Algorithm, exact Verify 115/115, Ruff and `git diff --check` clean; no push.

- [V2-305D] Migrate DOCX/preview object fixtures
  - Parent: ordered child 4/5 of `V2-305`; depends on `V2-305C`.
  - Files: `tests/test_docx_renderer.py`, `tests/test_preview_presentation.py`, `tests/core/test_manifest_resource_validation.py`
  - Behavior: object fixtures construct typed captions/content and preserve DOCX/preview/validation assertions.
  - Verify: `.venv/bin/python -m pytest tests/test_docx_renderer.py tests/test_preview_presentation.py tests/core/test_manifest_resource_validation.py`
  - Acceptance: object XML/preview/resource checks remain green without raw caption fixture fields.
  - Verification-surface change: authorized; migrates object fixtures.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; Figure/Listing/Algorithm fixtures carry caption_inlines and Equation fixtures carry display state, exact Verify 95/95, AST/Ruff/diff-check clean; no push.

- [V2-305C] Compile typed object captions/content and equation display
  - Parent: ordered child 3/5 of `V2-305`; depends on `V2-305B`.
  - Files: `src/thesis_forge/core/compiler.py`, `src/thesis_forge/core/render_plan.py`, `tests/test_compiler.py`
  - Behavior: compiler consumes typed captions/content and equation display state, deriving renderer-neutral instruction text/runs without reading raw caption duplicates.
  - Verify: `.venv/bin/python -m pytest tests/test_compiler.py`
  - Acceptance: caption citations/cross-references/strong text and equation display semantics remain represented in the RenderPlan.
  - Verification-surface change: authorized; migrates compiler object fixtures.
  - Attempts: 2
  - Attempt 1 (2026-08-22): exact Verify exposed a misplaced `display=block.display` keyword on TableInstruction and the EquationInstruction display regression; candidate corrected without scope expansion.
  - Attempt 2 (2026-08-22): Checker PASS; typed Figure/Listing/Algorithm captions and Equation display flow into RenderPlan, exact Verify 24/24, render-plan/preview regression 11/11, Ruff and `git diff --check` clean; no push.

- [V2-305B] Populate typed object fields during parsing
  - Parent: ordered child 2/5 of `V2-305`; depends on `V2-305A`.
  - Files: `src/thesis_forge/core/model.py`, `src/thesis_forge/core/parser.py`, `tests/core/test_thesis_object_model.py`
  - Behavior: figure/listing/algorithm captions and equation display state are populated from parser-normalized source data while current consumers remain green.
  - Verify: `.venv/bin/python -m pytest tests/core/test_thesis_object_model.py tests/test_parser.py tests/test_parser_contract.py`
  - Acceptance: parser-produced typed captions preserve citations/cross-references and object source locations; existing code/body semantics remain unchanged.
  - Verification-surface change: authorized; extends parser/object contract tests.
  - Attempts: 1
  - Attempt 1 (2026-08-22): Checker PASS; parser populates typed captions for figure/listing/algorithm and explicit Equation display=True, caption citations remain indexed, exact Verify 87/87 including markdown-it regression, Ruff and `git diff --check` clean; no push.

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

- [V2-404] Review listing, algorithm, cover, TOC and bibliography
  - Files: `src/thesis_forge/presentation/review.py`, `tests/presentation/test_review_regions.py`
  - Behavior: cover all remaining typed instructions and semantic regions.
  - Verify: `.venv/bin/python -m pytest tests/presentation/test_review_regions.py`
  - Acceptance: no registered instruction lacks a Review projection.
  - Verification-surface change: authorized; creates focused Review-region evidence.
  - Attempts: 2
  - Attempt 1 (2026-08-22): Checker FAIL; exact Verify passed 4/4, `git diff --check`, registry/unknown-instruction coverage, and static direct-import probe passed, but target Ruff failed with I001/UP035/RUF022/F401. Independent visible-content probes found ordinary non-code TextRun values leaking `fig:leak`, `[@secret-key]`, `{#fig:leak}`, and `/tmp/...`; expected Review content to hide stable IDs, citation keys, technical markers, and local paths. The two selected files were restored, `openspec/.specnav/change-registry.json` was preserved, no commit or push.
  - Attempt 2 (2026-08-22): Checker PASS; exact Verify passed 4/4, target Ruff and `git diff --check` passed; registry coverage/unknown-instruction, visible-content marker, code/listing literal-exemption, and headless import-isolation probes passed. Ordinary non-code TextRun values hide fig/tbl/eq/sec/chap/lst/alg IDs, citation keys, `{#id}`, and `/tmp`/`/Users` paths; importing review does not initialize application or renderer/docx modules. Candidate scope was exactly the two named files, the pre-existing `change-registry.json` was preserved, one local commit and no push.

## Blocked

## Blocked archive

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
  - Closed (2026-08-22): superseded by Done `V2-115A` (fresh replacement, explicit-undefined-ID coverage included); closure evidence today: `pnpm --dir frontend exec vitest run src/transport/buildEvents.test.ts src/transport/transports.test.ts` green 68/68 and `pnpm --dir frontend typecheck` clean; no push.

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
  - Closed (2026-08-22): superseded by Done `V2-113A` (fresh replacement, attributable boundary fixtures); closure evidence today: `src/transport/buildEvents.test.ts` green within the 68/68 run above; no push.

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
  - Closed (2026-08-22): superseded by Done `V2-113A` through the `V2-112A` replacement chain; closure evidence today: `src/transport/buildEvents.test.ts` green within the 68/68 run above; no push.

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
  - Closed (2026-08-22): superseded by Done `V2-106A` (strict DTO/transport primitive guards) plus Done `V2-113A` (decoder date-time/code strictness) and Done `V2-111D`/`V2-114B` (legacy `event.error` typing removed from consumers); closure evidence today: `transports.test.ts` 22/22, `buildEvents.test.ts` 46/46, typecheck clean, and a production scan of `frontend/src` finds zero `event.error` reads; no push.

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
  - Closed (2026-08-22): superseded by Done `V2-107A` (terminal stage lifecycle) and Done `REG-001` (unstarted-upstream regression fix); closure evidence today: `.venv/bin/python -m pytest tests/application/test_build_stage_lifecycle.py tests/test_sidecar.py tests/adapters/test_build_report_events.py tests/test_adapters.py::test_build_event_stream_emits_ordered_progress_and_one_success` green 27/27; no push.

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
  - Closed (2026-08-22): superseded by Done `V2-107B` (runtime terminalization carries the actual lifecycle snapshot, no `default_stages` fallback); closure evidence today: the same backend run green 27/27 with `tests/test_sidecar.py` and the adapters stream test included; no push.


## Cycle log

- 2026-08-23 - V2-525 Checker PASS Attempt 1; exact Verify passed 14/14, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent AST/runtime/OpenXML audit confirmed canonical parser migration, the existing V2 fixture, real DOCX 13/13 OpenXML checks, unchanged exit-code/JSON/no-repair assertions, and no fallback/compatibility/dual-source/silent-degradation path; V2-525 moved from Open to Done, candidate scope remained exactly `LOOP.md` and `tests/test_qa_tools.py`, all pre-existing `openspec/**` changes were preserved and unstaged, no push.
- 2026-08-23 - V2-524 Checker PASS Attempt 1; exact Verify passed 24/24, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent AST/runtime audit confirmed canonical parser migration, typed Figure/caption Citation output, `RenderPlan.citation_order == ("container2026",)`, unchanged non-target compiler tests/assertions, and no fallback/compatibility/dual-source/silent-degradation path; V2-524 moved from Open to Done, candidate scope remained exactly `LOOP.md` and `tests/test_compiler.py`, all pre-existing `openspec/**` changes were preserved and unstaged, no push.
- 2026-08-23 - V2-523 Checker PASS Attempt 1; exact Verify passed 7/7, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent AST/runtime audit confirmed standard V2 figure/display-equation/GFM table parsing and manifest override issue coverage; V2-523 moved from Open to Done, candidate scope remained exactly `LOOP.md` and `tests/core/test_object_overrides.py`, all pre-existing `openspec/**` changes were preserved and unstaged, one local commit, no push.
- 2026-08-23 - V2-522 Checker PASS Attempt 1; exact Verify passed 35/35, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent AST/runtime audit confirmed the canonical parser backend import, `ParseError` from `parser_support` only, retained parser-diff/legacy rejection/structured-error assertions, and no legacy parser import, parse_markdown APIs, fallback, compatibility layer, or dual source of truth; V2-522 moved from Open to Done, candidate scope remained exactly `LOOP.md` and `tests/test_parser_markdown_it.py`, all pre-existing `openspec/**` paths were preserved and unstaged, one local commit, no push.
- 2026-08-23 - V2-519 Checker FAIL Attempt 1; exact Verify passed 6/6, target Ruff and `git diff --check` passed, but independent evidence audit found no direct typed Citation/DocumentIndex assertion; candidate files were restored, no commit or push, and existing `openspec/**` changes were preserved.
- 2026-08-23 - V2-519 Checker PASS Attempt 2; exact Verify passed 6/6, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent AST/runtime audit confirmed the canonical parser backend import, no YAML Front Matter or legacy `:::` input, typed GFM `Table`/`TableRow`/`TableCell`/caption output, direct `Citation` nodes and `DocumentIndex` citation order, and no fallback, compatibility layer, or dual source of truth; V2-519 moved from Open to Done, candidate scope remained exactly the named test file plus this lifecycle update, all pre-existing `openspec/**` paths were preserved and unstaged, one local commit, no push.
- 2026-08-23 - V2-517 Checker PASS Attempt 2; exact Verify passed 9/9, related DOCX/application regressions passed, target Ruff and `git diff --check` passed, and independent DOCX footnote/semantic mutation audit passed; V2-517 moved from Open to Done, candidate scope remained exactly the three named files, all pre-existing `openspec/**` paths were preserved and unstaged, one local commit, no push.
- 2026-08-23 - V2-508 Checker PASS Attempt 1; exact Verify passed 1/1, related DOCX regression passed 90/90, architecture/RenderPlan regression passed 15/15, target Ruff, `git diff --check`, and independent 10/10 mutation audit passed; V2-508 moved to Done, the existing field production chain was audited unchanged, all pre-existing `openspec/**` paths were preserved and unstaged, one local commit, no push.
- 2026-08-23 - V2-514 Checker PASS Attempt 2; exact Verify passed 1/1, related manifest/resource/compiler/Review/DOCX regression passed 140/140, target Ruff, `git diff --check`, and LOOP-LINT passed; independent 10/10 mutation audit passed for manifest resource/provider attribution, unique semantic title/list, Review marker hygiene, and concrete DOCX bibliography styles; V2-514 moved to Done, all pre-existing `openspec/**` paths were preserved and unstaged, no push.
- 2026-08-23 - V2-503E Checker PASS Attempt 1; exact Verify passed 2/2, related canonical-parser/Review/DOCX regression passed 100/100, target Ruff, `git diff --check`, and LOOP-LINT passed; independent manifest-to-compiler/Review/DOCX runtime audit passed; V2-503E moved to Done, candidate scope was exactly `tests/core/test_region_resolver.py` plus this lifecycle update, all pre-existing `openspec/**` paths were preserved and unstaged, one local commit pending, no push.
- 2026-08-23 - V2-507E4 Checker PASS Attempt 3; exact Verify passed 4/4, related DOCX/compiler/Review regression passed 103/103, target Ruff, `git diff --check`, LOOP-LINT, and independent DOCX XML/mutation audit passed; Attempt 1 evidence-strength and Attempt 2 unknown-RenderNode fallback/CaptionSpec.position findings were repaired within the three-file boundary; V2-507E4 moved to Done, V2-503E remains next, all pre-existing `openspec/**` paths were preserved and unstaged, one local commit, no push.
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
- 2026-08-22 - V2-305B Checker PASS; parser populates typed object captions and explicit equation display state, exact Verify 87/87, Ruff/diff-check clean; no push.
- 2026-08-22 - V2-305C Checker PASS; compiler typed caption/display flow is represented in RenderPlan, exact Verify 24/24 plus 11 render-plan/preview regressions, Ruff/diff-check clean; no push.
- 2026-08-22 - V2-305D Checker PASS; DOCX/preview/validation fixtures use typed captions and equation display, exact Verify 95/95, AST/Ruff/diff-check clean; no push.
- 2026-08-22 - V2-305E split into ordered children V2-305E1A, V2-305E1B and V2-305E2 after AST found raw object captions across five fixture/parser surfaces; no product code edited in the split cycle, next queue V2-305E1A.
- 2026-08-22 - V2-305E1A Checker PASS; compiler/DOCX/preview object fixtures now use caption inlines only, exact Verify 115/115, AST/Ruff/diff-check passed; no push.
- 2026-08-22 - V2-305E1B Checker PASS; manifest Figure fixture now uses caption inlines only, exact Verify 4/4, AST/Ruff/diff-check passed; no push.
- 2026-08-22 - V2-305E2 split into ordered children V2-305E2A and V2-305E2B after parser contract inspection found raw Figure/Algorithm caption assertions; no product code edited in the split cycle, next queue V2-305E2A.
- 2026-08-22 - V2-305E2A Checker PASS; parser Figure/Algorithm caption assertions now use caption_inlines, exact Verify 32/32, Ruff/diff-check clean; no push.
- 2026-08-22 - V2-305E2B Checker PASS; rich object raw caption/text fields were removed, exact Verify 162/162, raw IR scan and Ruff/diff-check passed; no push.
- 2026-08-22 - Open refilled with V2-306, V2-307 and V2-308 per the catalogue dependency order after V2-305E2B left Open empty; V2-307 is expected to need re-slicing when its cycle arrives (cache consumers span validator/preview/runtime beyond the three-file slice); no product code edited.
- 2026-08-22 - Historical Blocked ledger closed: the six three-failure items (V2-114A, V2-112A, V2-111A, V2-103A1, V2-105B1, V2-105B2) moved verbatim into ## Blocked archive with per-item supersession notes; every superseding Done behavior re-verified green today (backend lifecycle/sidecar/report 27/27; frontend buildEvents 46 + transports 22; typecheck clean; zero production event.error reads); ## Blocked is now empty; no product code edited.
- 2026-08-22 - V2-306 Checker PASS; DocumentIndex derives ID/citation/reference/footnote indexes by traversal with first-wins by_id plus per-conflict both-node records and TypeError on unknown nodes, exact Verify 12/12, Ruff/diff-check and baselines 107/107 clean, pure addition confirmed; no push.
- 2026-08-22 - V2-307A split into ordered children V2-307A1 and V2-307A2 after the exact Verify exposed tests/test_compiler.py's synthetic container-citation pin injecting a citation that exists only in the ThesisDocument.citations cache (a fourth file); A1 re-pins that test onto parsed figure-caption content (green before and after the flip), A2 carries the parked compiler/index flip (/tmp/v2-307a2.diff); no product code remains edited in the split cycle.
- 2026-08-22 - V2-307A1 Checker PASS; container-citation pin re-based on parsed figure-caption content, exact Verify 24/24 (27/27 with the parked A2 flip), cache-only-citation survey clean; no push.
- 2026-08-22 - V2-307A2 Checker PASS; compiler footnote/citation collection now derives from the DocumentIndex full inline sequence, exact Verify 39/39 and baselines 177/177, cache-clear compile equality and caption-citation probes green; no push.
- 2026-08-22 - V2-307B Checker PASS; CLI inspect JSON now derives all four semantic collections from DocumentIndex with value-identical payloads, exact Verify 23/23 and cli/adapters baseline 48/48; no push.
- 2026-08-22 - V2-307C Checker PASS; parser_diff normalization now derives inline/citation/reference sequences from DocumentIndex with parity green on all three shipped examples and zero cache-field reads, exact Verify 48/48; no push.
- 2026-08-22 - V2-307D1a Checker PASS; caption inlines now carry the caption line/column and table-cell inlines their own row line in both backends (markdown-it inherits the shared _parse_container fix), exact Verify 50/50 with typed-vs-cache location pins, baselines and parity green; no push.
- 2026-08-22 - V2-307D1b Checker PASS; Algorithm owns typed body_lines populated from located content lines with cache-equal locations, exact Verify 118/118 and baselines 148/148; no push.
- 2026-08-22 - V2-307D1c Checker PASS; markdown-it typed body_lines pinned identical to legacy through the shared container path with zero production changes, exact Verify 49/49; no push.
- 2026-08-22 - V2-307D1d Checker PASS; DocumentIndex now traverses Algorithm body_lines so body citations join the derived collections with accurate locations and document order, exact Verify 16/16 and baselines 153/153; no push.
- 2026-08-22 - V2-307D1e Checker PASS on Attempt 2 after the re-slice prerequisites; all parser-test cache pins now read DocumentIndex-derived sequences with zero cache-field assertions remaining, exact Verify 83/83 and value-equivalence probes green; no push.
- 2026-08-22 - V2-307D2 Checker PASS; e2e and object-model cache pins now read DocumentIndex-derived sequences, exact Verify 9/9 with baselines green; no push.
- 2026-08-22 - V2-308A Checker PASS; the three manifest-resource fixtures now carry their citations in Paragraph inlines with object-identical index derivation proven, exact Verify 4/4 and tests/core 87/87; no push.
- 2026-08-22 - V2-308B Checker FAIL Attempt 1 (residual index_by_id read in _validate_layout_overrides), completed with the fifth in-scope swap; V2-308B Checker PASS Attempt 2 — all five validator rules now read the derived DocumentIndex with cache-independence, layout-override and negative-control probes green, exact Verify 3/3 and baselines 181/181; no push.
- 2026-08-22 - V2-307E Checker PASS; legacy parser no longer registers inlines (five call sites removed), caches empty on parse with semantics preserved in blocks and the derived index, exact Verify 50/50 and baselines 232/232; no push.
- 2026-08-22 - V2-307F Checker PASS; markdown-it backend no longer registers inlines (seven sites plus unused import removed), caches empty on both backends with parity green on all three examples, exact Verify 81/81; no push.
- 2026-08-22 - V2-307G1 Checker PASS; eleven redundant citations= mirror kwargs deleted from compiler/DOCX/manifest fixtures, both-ways proof green under a simulated field-less model, exact Verify 114/114; no push.
- 2026-08-22 - V2-307G2 Checker PASS; ThesisDocument lost the four cache fields and register_inlines (deletion-only, index_by_id retained for its preview caller), absence pins and source scans green, exact Verify 166/166, broader regression 200/200, parity OK — V2-307 (all fourteen children) and V2-308 are complete; no push.
- 2026-08-22 - Open refilled with V2-309, V2-310 and V2-311 per the catalogue dependency order after V2-307/V2-308 completed; V2-309 and V2-311 are expected to need re-slicing when their cycles arrive (ValidationIssue shape changes ripple through adapters/CLI/protocol, and inline conversion spans the shared scanner); no product code edited.
- 2026-08-22 - V2-309 Checker FAIL Attempt 1; focused tests 3/3, target Ruff, diff-check, core regression 94/94 and LOOP-LINT passed, but the candidate eagerly imported the core stack into headless presentation, introduced a second unused Diagnostic beside BuildDiagnostic, accepted malformed runtime parameter/coordinate types, and generated colliding IDs for locationless duplicates; selected files restored and re-sliced into ordered V2-309A/V2-309B/V2-309C, no commit or push.
- 2026-08-22 - V2-309A Checker FAIL Attempts 1/2 then PASS Attempt 3; the existing BuildDiagnostic contract was hardened with complete runtime boundary tests while preserving BuildReport/DTO round-trip and path sanitization, exact Verify 47/47 and application/adapter regression 88/88; no push.
- 2026-08-22 - V2-309B Checker PASS Attempt 2; exact Verify 16/16, related regression 169/169, target Ruff/diff-check, headless architecture probe, and nested/locationless duplicate probe passed; legacy formatter behavior remained unchanged, no push.
- 2026-08-22 - V2-310 Checker FAIL Attempt 1; exact Verify 2/2, parser/core regressions 181/181, target Ruff, diff-check and LOOP-LINT passed, but standard block tokens were flattened to Paragraph by `_emit_raw_token_range` and the candidate added a legacy compatibility layer beyond V2-310; both candidate files were restored, candidate/baseline full pytest failure sets matched at 45, `change-registry.json` was preserved, no commit or push.
- 2026-08-22 - V2-310 split into ordered children V2-310A and V2-310B after Checker evidence showed the candidate crossed the block/inline conversion boundary and flattened enabled standard Markdown tokens; A isolates the private-helper seam, B carries the configuration flip, and no product code was edited in the split cycle.
- 2026-08-22 - V2-310A Checker PASS; exact Verify 50/50, parser/core regression 141/141, target Ruff, diff-check, LOOP-LINT, unchanged full-repo failure set of 45, and 8 cross-worktree parser/backend digests passed; public seam only, no V2-310B/V2-311 scope, no push.
- 2026-08-22 - V2-307G split into ordered children V2-307G1 and V2-307G2 after a repo-wide survey found eleven redundant citations= mirror kwargs across test_compiler/test_docx_renderer/test_manifest_resource_validation fixtures (a fourth file beyond G's two); G1 drops the mirrors (green both ways), G2 removes the fields and rewrites the no-manual-caches pin; no product code edited in the split cycle.
- 2026-08-22 - V2-308 split into ordered children V2-308A and V2-308B before any product edit after inspection found tests/core/test_manifest_resource_validation.py constructs three cache-only citations that would break the validator flip (a third file beyond the item's named two); A migrates the fixtures to real Paragraph inline citations (green both ways), B carries the validator flip; no product code edited in the split cycle.
- 2026-08-22 - V2-307D1 Checker FAIL Attempt 1 then re-sliced into ordered children V2-307D1a…D1e after independent Checker grep found 20 cache-pin sites (18 in test_parser_contract.py) and completing them exposed typed-model defects the cache masked: caption inline locations carry the container start line in both backends, table-cell inline locations are misaligned by the metadata/blank rows, and algorithm-body citations exist only in the cache (Algorithm.body is verbatim-only); children fix caption/cell locations, add typed Algorithm body_lines to the model and both parsers, extend index traversal, then finish the pin migration; three test files restored, no product code edited in the split cycle.
- 2026-08-22 - V2-307 split into eight ordered children V2-307A…G after grep mapping showed removing the four cache fields atomically spans model.py + both parsers (12 registration call sites) + compiler.py + validator.py + cli.py + qa/tools/parser_diff.py plus seven test files; children migrate readers first (compiler/CLI/parity-tool/test pins, with V2-308 landing between D2 and E), then stop registration per parser, then remove the fields; no product code edited in the split cycle.
- 2026-08-22 - V2-309C Checker PASS; exact Verify 17/17, target Ruff, `git diff --check`, core/application/adapter regression 54/54, application/CLI/E2E regression 84/84, and independent coordinate/order/legacy probes passed; LOOP.md pre-check found V2-309C, V2-310 and V2-311 Open, so only V2-309C moved to Done; the pre-existing `change-registry.json` change was preserved; no push.
- 2026-08-22 - V2-310B Checker FAIL Attempt 1; exact Verify 2/2 but the related regression passed only 75/81 because enabling the default preset emitted fence/blockquote/table/setext/hr tokens that `_walk` silently discarded, causing token loss and parity regressions; the candidate was restored with no commit or push, and V2-310B was re-sliced into ordered children V2-310B1/B2.
- 2026-08-22 - V2-310B1 Checker FAIL Attempt 1; exact Verify 82/82, related parser/core/compiler regression 173/173, target Ruff, diff-check, LOOP-LINT, and top-level default-token probes passed, but mixed default tokens exposed `_emit_fence()` resetting the absolute token index to `1` and leaving `blockquote_close` unconsumed, while a list with an indented fence hung in `_scan_list`; candidate and HEAD retained the same known full-repo failure set of 45, the two candidate files were restored, `change-registry.json` was preserved, no commit or push.
- 2026-08-22 - V2-310B1 Checker FAIL Attempt 2; exact Verify 84/84, target Ruff, `git diff --check`, and LOOP-LINT passed; mixed default block order and list fence/blockquote/table/code_block/hr timeout/diagnostic probes passed, but an indented setext heading inside a list still flattened to `ListBlock + Paragraph` instead of explicit `ParseError`; candidate and HEAD full pytest failure sets remained identical at 45 nodes (`1081 passed, 45 failed` vs `1078 passed, 45 failed`), the two candidate files were restored, `change-registry.json` was preserved, no commit or push.

- 2026-08-22 - V2-310B1 Checker PASS Attempt 3; exact Verify 85/85, related parser/core/compiler regression 123/123, target Ruff, `git diff --check`, and LOOP-LINT passed; mixed default blockquote/fence/table/setext probe produced typed `BlockQuote -> CodeBlock -> Table -> Heading` in order, list fence/blockquote/table/indented-code/hr/setext/html_block/reference probes produced stable explicit `ParseError` within timeout, and top-level unsupported/unknown probes produced explicit diagnostics; candidate scope was exactly the two named files before the LOOP update, full-repo candidate/clean-HEAD results were `1082 passed, 45 failed` vs `1078 passed, 45 failed` with an identical known 45-node failure set, `change-registry.json` was preserved, one local commit and no push.
- 2026-08-22 - V2-310B2 Checker PASS; exact Verify `.venv/bin/python -m pytest tests/core/test_markdown_v2_parser_config.py` passed 2/2; related regression `.venv/bin/python -m pytest tests/test_parser_markdown_it.py tests/test_parser_backend.py tests/test_parser_contract.py` passed 85/85 and core/parser/compiler regression `.venv/bin/python -m pytest tests/core/ tests/test_parser.py tests/test_compiler.py` passed 134/134; `.venv/bin/ruff check src/thesis_forge/core/parser_markdown_it.py tests/core/test_markdown_v2_parser_config.py tests/test_parser_markdown_it.py`, `git diff --check`, and `./lint-loop.sh` passed; production probe confirmed active block/inline rules, no disabled rules or disable call, `MarkdownIt("default")`, mixed `BlockQuote -> CodeBlock -> Table -> Heading`, and explicit unsupported diagnostics; full-repo candidate/clean-HEAD failure sets were 45/46 with candidate a subset and only `tests/test_parser_markdown_it.py::test_parity_with_legacy_on_fixtures[bachelor-full-template]` clean-only; scope was the three named files plus `LOOP.md`, pre-existing `openspec/.specnav/change-registry.json` was preserved, no push.
- 2026-08-22 - V2-311 Checker FAIL Attempt 1; exact Verify passed 5/5, related parser/backend/contract regression passed 81/81, core/parser/compiler regression passed 139/139, target Ruff, diff-check, and LOOP-LINT passed, but independent probes rejected a valid balanced-parenthesis link destination and escaped text during source mapping; the three candidate files were restored, the pre-existing `change-registry.json` was preserved, and no commit or push.
- 2026-08-22 - V2-311 Checker PASS Attempt 2; exact Verify passed 8/8, related parser/backend/contract regression passed 81/81, core/parser/compiler regression passed 183/183, target Ruff, diff-check, and LOOP-LINT passed, and independent probes covered nested inlines, distinct soft/hard breaks, code-math isolation, balanced ordinary/reference links, escaped-dollar mapping, autolinks, and explicit image-token errors; candidate scope was the three named product files, `change-registry.json` was preserved, one local commit and no push.

- 2026-08-22 - V2-318 Checker PASS
- 2026-08-22 - V2-404 Checker FAIL Attempt 1; exact Verify passed 4/4, `git diff --check` and registry/unknown/static-import probes passed, but target Ruff failed and normal Review TextRun content leaked stable IDs, raw citation keys, technical attributes, and local paths; selected files restored, `change-registry.json` preserved, no commit or push.
- 2026-08-22 - V2-404 Checker PASS Attempt 2; exact Verify passed 4/4, target Ruff and `git diff --check` passed, registry/unknown-instruction coverage, visible-content marker, code/listing literal-exemption, and headless import-isolation probes passed; candidate scope was exactly the two named files, `change-registry.json` was preserved, one local commit and no push.

- 2026-08-22 - V2-312 Checker PASS; exact Verify passed 4/4, related parser/backend/contract regression passed 80/80, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent semantic-inline probe covered seven CrossReference targets/fallbacks, ordinary URL and fragment Link preservation, Citation, FootnoteReference, FootnoteDefinition, and SourceLocation mapping; V2-312 product scope was exactly the two named files, registry preserved, no push.
- 2026-08-22 - V2-313 Checker PASS; exact Verify passed 4/4, related parser/backend/contract regression passed 80/80, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent block probe covered heading/paragraph/list/blockquote/fence fields and SourceLocation values, scope guard found no parser or undeclared production diff, and the pre-existing registry remained unchanged and unstaged; no blockquote-nested-list extension, no push.
- 2026-08-22 - V2-314 Checker PASS; exact Verify passed 5/5, related parser/backend/contract regression passed 85/85, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent probe covered Figure id/src/location, typed Strong/semantic captions, explicit invalid-ID errors, width not read, footnote `_walk` advancement with citation/semantic-link indexing, and ordinary-paragraph image rejection; scope was the two named product files plus LOOP, registry preserved and unstaged, no V2-315, no push.
- 2026-08-22 - V2-315 Checker FAIL Attempt 1; exact Verify passed 6/6, related parser/backend/contract regression passed 76/76, target Ruff, `git diff --check`, and `./lint-loop.sh` passed, but an independent GFM probe found valid tables without outer pipes were rejected; candidate files were restored, registry preserved and unstaged, no commit or push.
- 2026-08-22 - V2-315 Checker PASS Attempt 2; exact Verify 6/6, related regression 87/87, target Ruff, diff-check, LOOP-LINT, and independent GFM table/caption runtime probes passed; V2-315 moved to Done, scope limited to parser/test plus LOOP, registry preserved and unstaged, one local commit and no push.
- 2026-08-22 - V2-316 Checker PASS; exact Verify passed 9/9, related regression 96/96, target Ruff, `git diff --check`, LOOP-LINT, and independent display-equation runtime probes passed; the known V2-314 inline baseline failure was unchanged and outside the candidate diff, V2-316 moved to Done, registry preserved and unstaged, one local commit and no push.
- 2026-08-22 - V2-317 Checker PASS; exact Verify passed 9/9, related regression 105/105, target Ruff, `git diff --check`, LOOP-LINT, and independent listing/algorithm fence probes passed; V2-317 moved to Done, registry preserved and unstaged, one local commit and no push.
- 2026-08-22 - V2-319 split into ordered children V2-319A through V2-319D after CodeGraph found the single-parser change spans the core factory, application default, QA dual-backend CLI/tests, public core exports, and template lint consumer; no product code edited in the split cycle, next queue is V2-319A.
- 2026-08-22 - V2-319A split into ordered children V2-319A1 and V2-319A2 after a runtime probe showed switching `ApplicationDependencies` from legacy to markdown-it rejects the existing YAML Front Matter example and breaks the 77-test application-service baseline; no product code edited in the split cycle, next queue is V2-319A1.
- 2026-08-22 - V2-319A1 Checker PASS Attempt 1; exact Verify 3/3, related parser/backend/contract regression 76/76, target Ruff, `git diff --check`, and LOOP-LINT passed; parameterless canonical factory/type and non-empty v2 parse coverage were confirmed, registry preserved and unstaged, one local commit and no push.
- 2026-08-22 - V2-319A2 split into ordered children V2-319A2A and V2-319A2B after the candidate passed its 78-test application-service Verify but introduced 7 new adapter failures and 1 new acceptance failure when compared with clean HEAD; candidate product/test changes were restored, and the prep child will rebase those fixtures before the canonical application default flips.
- 2026-08-22 - V2-319A2A Checker PASS Attempt 1; exact Verify 12/12, full adapter/application regressions 33/33 and 115/115, target Ruff, diff-check, LOOP-LINT, canonical seam probes, and selected canonical-default simulation passed; candidate/clean-HEAD acceptance failure sets matched at the same six baseline nodes, registry preserved, one local commit and no push.
- 2026-08-22 - V2-319A2B Checker PASS Attempt 1; exact Verify 77/77, related application/project/adapter regression 115/115, target Ruff, `git diff --check`, and LOOP-LINT passed; runtime confirmed the default `ApplicationDependencies` parser is `MarkdownItParserBackend` through `create_parser_backend`, candidate/clean-HEAD acceptance failure sets were identical at the same six old-fixture nodes, and the five candidate-only `lo_finalizer` errors were isolated to the known YAML Front Matter fixture; scope was the two named candidate files plus this LOOP lifecycle update, registry preserved and uncommitted, one local commit and no push.
- 2026-08-22 - V2-319B Checker PASS Attempt 1; exact Verify 41/41, related parser/adapter regression 65/65, target Ruff, `git diff --check`, post-update LOOP-LINT, and canonical CLI self-check/dump/illegal-allow probes passed; candidate and clean-HEAD exact/related failure node sets were both empty, the three candidate files had no backend-name selector, registry lookup, legacy fallback, environment switch, or compatibility branch, and `openspec/.specnav/change-registry.json` remained preserved and uncommitted; one local commit, no push.
- 2026-08-22 - V2-319C Checker FAIL Attempt 1; expected candidate and clean-HEAD exact Verify failure node sets to match, observed candidate 96/6 versus isolated clean HEAD 97/5 with the additional `tests/test_template_v2.py::test_lint_l1_external_relationship_allowlist` failure caused by canonical rejection of YAML Front Matter as `TF-SOURCE-LEGACY-001`; target Ruff, `git diff --check`, and LOOP-LINT passed, candidate files were restored, the pre-existing registry was preserved, and no Done move, commit, or push.
- 2026-08-22 - V2-319C split into ordered children V2-319C1 and V2-319C2 after CodeGraph and fixture inspection showed the canonical L5 migration crosses the public core export, template lint, test-generated YAML fixture, and package-sample fixture surfaces; no product code edited in the split cycle, next queue is V2-319C1.
- 2026-08-22 - V2-319C1 Checker PASS Attempt 1; exact Verify 44/44, targeted Ruff, `git diff --check`, LOOP-LINT, and the canonical public-surface probe passed; only `src/thesis_forge/core/__init__.py` plus this lifecycle update changed, `change-registry.json` was preserved and uncommitted, and no push.
- 2026-08-22 - V2-319C2 split into ordered children V2-319C2A and V2-319C2B after fixture audit found `tests/test_template_v2_editor.py::test_lint_l5_fixture_validator_error_fails` writes YAML Front Matter that would fail the canonical parser; no product code edited in the split cycle, next queue is V2-319C2A.
- 2026-08-22 - V2-319C2A Checker PASS; candidate failure set was a strict subset of isolated clean HEAD (`97 passed/5 pre-existing package-sample missing-DOCX failures` vs `96 passed/6 failed`), targeted Ruff, `git diff --check`, LOOP-LINT, canonical parser/L5/duplicate-ID probes passed, and only C2A plus `LOOP.md` changed; C2B and the pre-existing registry were preserved, no push.
- 2026-08-22 - V2-319C2B Checker PASS; exact Verify passed 4/4, targeted Ruff, `git diff --check`, LOOP-LINT, and the canonical duplicate-ID fixture audit passed; candidate scope was only `tests/test_template_v2_editor.py`, with no production or compatibility diff, the pre-existing registry preserved and unstaged, and no push.
- 2026-08-22 - V2-319D Checker PASS Attempt 1; exact Verify passed 45/45, targeted Ruff, `git diff --check`, LOOP-LINT, and the single-parser static/runtime audit passed; candidate scope was exactly the two named files, the pre-existing registry was preserved and uncommitted, the total-goal verifier retained 11 unrelated contract gaps, one local commit, no push.
- 2026-08-22 - V2-320 split into ordered children V2-320A through V2-320C after CodeGraph found that `parser_markdown_it.py` still imports eight shared primitives from `core.parser` and more than twenty tests/auxiliary tools import the legacy module; no product code edited in the refill cycle, next queue is V2-320A.
- 2026-08-22 - V2-320A Checker PASS Attempt 1; exact Verify passed 73/73, targeted Ruff, `git diff --check`, final LOOP-LINT, and independent seam/parity/runtime probes passed; V2-320B and V2-320C remain Open, the pre-existing `change-registry.json` was preserved and uncommitted, and no push.
- 2026-08-22 - V2-320B Checker PASS Attempt 1; exact Verify passed 2/2, related parser/backend regression 77/77, targeted Ruff, `git diff --check`, LOOP-LINT, independent AST/runtime boundary probes, and the 11-gap total-goal audit passed; V2-320C remains Open, the pre-existing `change-registry.json` was preserved and uncommitted, one local commit, no push.
- 2026-08-22 - V2-320C Checker PASS Attempt 1; exact Verify passed 18/18, targeted Ruff, `git diff --check`, and LOOP-LINT passed; candidate scope was exactly the three named test files with no production code, compatibility layer, or selector changes, the pre-existing `change-registry.json` was preserved and uncommitted, one local commit, no push.
- 2026-08-22 - V2-510A Checker PASS Attempt 1; exact Verify passed 3/3; related regression was 199 passed/1 baseline failure at `tests/core/test_markdown_v2_parser_config.py::test_markdown_v2_uses_public_parser_primitives`, matching clean HEAD at 196 passed/1 same failure and recorded out-of-scope; targeted Ruff, `git diff --check`, and LOOP-LINT: PASS — open=0 done=117 blocked=0; static/runtime audit confirmed pure local math conversion, structured unsupported/malformed error issues with source navigation and no absolute path leakage, supported formulas clear, and no compatibility, fallback, silent-degradation, or dual-field path; candidate scope was exactly the three named files, the pre-existing `openspec/.specnav/change-registry.json` was preserved and uncommitted, one local commit, no push.
- 2026-08-22 - V2-501 Checker PASS Attempt 1; exact Verify 5/5, compiler/DOCX regression 110/110, targeted Ruff, `git diff --check`, LOOP-LINT, and independent symbol/compile probes passed; V2-501 moved from Open to Done, the candidate scope was exactly the three named implementation/test files plus this lifecycle update, the pre-existing `openspec/.specnav/change-registry.json` was preserved and uncommitted, and no push.
- 2026-08-22 - V2-512 Checker PASS Attempt 1; exact Verify 4/4, related DocumentIndex/compiler/DOCX regression 123/123, targeted Ruff, `git diff --check`, and independent build-stop/compile-ID probes passed; V2-512 moved from Open to Done, missing and nested references stopped before compiler invocation, duplicate issues retained both source locations, repeated references shared one definition ID, the candidate scope was exactly the three named files, the pre-existing `openspec/.specnav/change-registry.json` was preserved and uncommitted, and no push.
- 2026-08-22 - V2-505 split into ordered children V2-505A and V2-505B after CodeGraph showed rich figure captions cross the typed RenderPlan/compiler seam and the DOCX caption/figure seam, exceeding the three-file implementation bound; no product code edited in the split cycle, next queue is V2-505A.
- 2026-08-22 - V2-505A Checker FAIL Attempt 1; exact Verify passed 1/1 and related compiler/RenderPlan/SymbolTable regression passed 35/35, but independent typed-caption probes found silent Inline loss, raw marker dual representation/payload omission, and figure-before-paragraph citation ordinal inversion; candidate files were restored, V2-505A and V2-505B remain Open, the registry was preserved, and no commit or push.

- 2026-08-22 - V2-505A Checker FAIL Attempt 2; typed-caption seam probes passed, but shared compiler InlineRun expansion caused Preview loss and Review/DOCX rejection for ordinary rich body inlines; candidate files and test were restored, V2-505A and V2-505B remain Open, registry preserved, no commit or push.
- 2026-08-22 - V2-505A split into ordered children V2-505A1 and V2-505A2 after CodeGraph confirmed the missing `LinkRun`/`MathRun`/`BreakRun` definitions belong to the shared RenderPlan seam and cannot be consumed independently within the three-file bound; no product code edited in the split cycle, next queue is V2-505A1, and V2-505B remains dependent on the completed re-sliced A.
- 2026-08-22 - V2-505A1 Checker FAIL Attempt 1; exact Verify and 137-test related regression matched clean HEAD at the same YAML Front Matter baseline failure, but capability names disagreed with `spec/format-capabilities.yaml`, `FigureInstruction` kept a raw `caption` alongside typed `caption_inlines`, figure caption runs were not consumed by Preview/Review, and Preview lost hyperlink destination semantics; the three candidate files were restored, the A1 three-file boundary was rejected for re-slicing, the registry was preserved, and no commit or push.
- 2026-08-22 - V2-505A1 split into ordered children V2-505A1M, V2-505A1P, V2-505A1R, V2-505A1D1 and V2-505A1D2 after the Checker found canonical run-name, figure-caption source-of-truth, Preview/Review projection and DOCX footnote fan-out beyond the three-file bound; no product code edited in the split cycle, next queue is V2-505A1M.
- 2026-08-22 - V2-505A1M Checker PASS Attempt 1; exact Verify `.venv/bin/python -m pytest tests/core/test_typed_inline_render_plan.py` passed 5/5; targeted Ruff `.venv/bin/ruff check src/thesis_forge/core/render_plan.py tests/core/test_typed_inline_render_plan.py`, `git diff --check`, and `./lint-loop.sh` passed; independent audit confirmed exact canonical run names/fields, the eight-member union, distinct soft/hard nominal types, explicit unknown-run `TypeError`, renderer-neutral dependency boundary, and no forbidden consumer or caption-source changes; scope was exactly `src/thesis_forge/core/render_plan.py` and `tests/core/test_typed_inline_render_plan.py`, all unrelated dirty paths including `LOOP.md` history, registry, `template-v2-build-pipeline-p1/**`, and `v2-rich-inline-renderplan-p1/codegraph/**` were preserved, and no push.
- 2026-08-22 - V2-505A1P Checker FAIL Attempt 1; exact Verify passed 1/1, target Ruff, `git diff --check`, and LOOP-LINT passed; complete preview presentation tests were 5 passed/1 known clean-HEAD YAML Front Matter baseline failure, but raw citation fallback leaked `[@ref-1]` and the new four Python run types were not accepted by the actual frontend transport DTO/validator or rendered by the Preview component; the two candidate files were restored, A1P remains Open pending split/third-file protocol work, all unrelated dirty paths were preserved, and no commit or push.
- 2026-08-22 - V2-505A1P split into ordered children V2-505A1P1, V2-505A1P2 and V2-505A1P3 after the independent Checker found that raw citation cleanup belongs in the Python mapper while the new Preview run shapes also require the frontend transport DTO, validator tests, panel renderer and panel tests; no product code edited in the split cycle, all unrelated dirty paths were preserved, and the next queue is V2-505A1P1.
- 2026-08-22 - V2-505A1P1 Checker PASS Attempt 1; exact Verify passed 1/1, target Ruff, `git diff --check`, and LOOP-LINT passed; complete preview tests were 5 passed/1 known clean-HEAD baseline failure at `test_complete_example_preview_preserves_compiler_order_and_numbering` with `TF-SOURCE-LEGACY-001`, clean HEAD was 4 passed/1 with the identical failure, and independent AST/runtime probes passed for all eight ordered variants, raw citation suppression, formatted citation preservation, and explicit unknown-run rejection; V2-505A1P1 moved to Done, candidate scope was exactly the two named files plus this lifecycle update, unrelated dirty paths were preserved, one local commit, no push.
- 2026-08-22 - V2-505A1P2 Checker PASS Attempt 1; exact Verify passed 9/9, combined Preview transport regression passed 31/31, frontend typecheck/lint, `git diff --check`, and LOOP-LINT passed; independent DTO audit confirmed all eight canonical runs, strict new-run field shapes, and rejection of unknown types, extra keys, and malformed shapes; V2-505A1P2 moved from Open to Done, candidate scope was exactly the two named frontend files plus this lifecycle update, all unrelated dirty paths were preserved, one local commit, no push.
- 2026-08-22 - V2-505A1P3 Checker PASS Attempt 1; exact Verify passed 6/6, `pnpm --dir frontend typecheck`, `pnpm --dir frontend lint`, `git diff --check`, and `./lint-loop.sh` passed; independent audit confirmed all eight canonical inline runs, real hyperlink destination semantics without visible technical markers, readable math fallback, soft-break space normalization, hard-break `<br>` semantics, and unchanged reference/citation/footnote rendering; candidate scope was exactly the two named frontend files before this lifecycle update, all unrelated dirty paths were preserved, one local commit, no push.

- 2026-08-22 - V2-505A1R Checker PASS Attempt 1; exact focused Verify passed 1/1, full Review regression passed 6/6, target Ruff, `git diff --check`, and LOOP-LINT passed; Review code audit confirmed all eight canonical inline projections, marker-free visible text, preserved hyperlink/math semantics, distinct soft/hard breaks, unchanged text/reference/citation/footnote behavior, and explicit unknown-run rejection; V2-505A1R moved from Open to Done, no `V2-505A1D1` started, unrelated dirty paths preserved, no push.
- 2026-08-22 - V2-505A1D1 Checker PASS; exact focused Verify 1/1, full DOCX renderer regression 88/88, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent DOCX/XML audit confirmed the eight canonical inline runs, shared body/heading/list dispatch, native hyperlink/math and soft/hard break semantics, preserved reference/citation/footnote-reference behavior, and explicit unknown/unconfigured-run errors; V2-505A1D1 moved from Open to Done, candidate scope was exactly the three named files before this lifecycle update, unrelated dirty paths were preserved, V2-505A1D2 was not started, no push.
- 2026-08-23 - V2-505A1D2 Checker PASS Attempt 1; exact focused Verify passed 1/1, full DOCX renderer regression 90/90, target Ruff, `git diff --check`, and LOOP-LINT passed; independent DOCX/XML audit confirmed the shared `render_inline_runs` seam, footnote-part hyperlink relationship, native inline OMML, space-only soft breaks, real `w:br` hard breaks, preserved reference/citation/footnote-reference behavior, and explicit nested/unknown-run failures; V2-505A1D2 moved from Open to Done, V2-505A2 was not started, unrelated dirty paths preserved, one local commit, no push.
- 2026-08-23 - V2-505A2 split into ordered children V2-505A2M and V2-505A2C after CodeGraph confirmed that the typed `FigureInstruction` caption representation lives in `render_plan.py`, a fourth file outside the original A2 boundary; no product code edited in the split cycle, next queue is V2-505A2M, and V2-505B now depends on V2-505A2C.
- 2026-08-23 - V2-505A2M boundary refined before implementation because changing `FigureInstruction` without its compiler constructor would leave a broken intermediate baseline; A2M now owns `render_plan.py` plus `compiler.py` and its focused caption test, while A2C owns the DOCX seam and the same focused test; no product code edited.
- 2026-08-23 - V2-505A2M Checker FAIL Attempt 1; exact Verify passed 3/3, related core/Preview/Review/DOCX regression passed 141/142 with the known clean-baseline YAML Front Matter failure, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent audit found the forbidden `FigureInstruction` caption compatibility alias/dual representation and raw citation leakage through resolved reference display text; candidate files restored, V2-505A2M remains Open, no commit or push.
- 2026-08-23 - V2-505A2M Checker FAIL Attempt 2; exact Verify passed 3/3, related core/compiler/DOCX/Review regression passed 293/294 with the existing parser-primitive baseline failure, Preview passed 5/6 with the known YAML Front Matter baseline failure, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent runtime probe found raw `FigureInstruction` constructor compatibility and no-template label/reference payload leakage of `[@...]` and stable IDs; candidate files restored, V2-505A2M remains Open, no commit or push.
- 2026-08-23 - V2-505A2M split into ordered prerequisites V2-505A2P1 and V2-505A2P2 after Attempt 2 showed that strict canonical-only construction requires migrating three existing direct FigureInstruction fixtures; no product code changed in the split cycle, next queue is V2-505A2P1.
- 2026-08-23 - V2-505A2P1 Checker FAIL Attempt 1; exact Verify passed 2/2, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent runtime probe showed `CaptionRuns` accepts list and iterator inputs despite the tuple-only typed-boundary contract, while renderer-neutral imports and the unchanged FigureInstruction/compiler seam passed; candidate files restored, V2-505A2P1 remains Open, V2-505A2P2/V2-505A2M/V2-505A2C/V2-505B remain Open, no commit or push.
- 2026-08-23 - V2-505A2P1 Checker FAIL Attempt 2; exact Verify passed 4/4, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; the independent strict-boundary probe rejected list, iterator, and unknown-object inputs and passed all-eight projection, renderer-neutral import, and unchanged FigureInstruction/compiler checks, but accepted a tuple subclass through `isinstance(runs, tuple)` despite the exact built-in tuple contract; candidate files restored, V2-505A2P1 remains Open, V2-505A2P2/V2-505A2M/V2-505A2C/V2-505B remain Open, no commit or push.
- 2026-08-23 - V2-505A2P1 Checker PASS Attempt 3; exact Verify passed 5/5, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent audit confirmed exact built-in tuple acceptance with list, iterator and tuple-subclass rejection, all-eight canonical projections, `ensure_inline_run` validation, explicit unknown-element/container failures, renderer-neutral imports, unchanged FigureInstruction/compiler seams, and no raw caption alias or dual payload source; V2-505A2P1 moved to Done, V2-505A2P2/V2-505A2M/V2-505A2C/V2-505B remain Open, one local commit, no push.
- 2026-08-23 - V2-505A2P2 Checker PASS Attempt 1; exact Verify was 17 passed/1 known clean-HEAD YAML Front Matter baseline failure (`TF-SOURCE-LEGACY-001`), clean HEAD matched exactly; target Ruff, `git diff --check`, and `./lint-loop.sh` passed; all four direct FigureInstruction fixtures use CaptionRuns including the positional fixture, candidate scope is the three named test files with no production or compatibility diff, V2-505A2M/V2-505A2C/V2-505B remain Open, one local commit, no push.

- 2026-08-23 - V2-505A2M Checker PASS Attempt 3; exact Verify 5/5, related regression 300/301 plus Preview 5/6 with only the two clean-HEAD baseline failures, target Ruff, `git diff --check`, `./lint-loop.sh`, and independent typed-caption/marker/import probes passed; V2-505A2M moved to Done, V2-505A2C and V2-505B remain Open, one local commit, no push.
- 2026-08-23 - V2-505A2C Checker PASS Attempt 1; exact Verify 7/7, full DOCX regression 90/90, target Ruff, `git diff --check`, post-update `./lint-loop.sh`, and independent shared-seam probes passed; V2-505A2C moved from Open to Done, the candidate test was the only product diff, all pre-existing dirty paths were preserved, one local commit, no push.
- 2026-08-23 - V2-505B Checker PASS Attempt 1; exact Verify 1/1, related DOCX regression 91/91, target Ruff, `git diff --check`, LOOP-LINT, and independent DOCX OPC/XML audit passed; V2-505B moved from Open to Done, `figures.py` was audited unchanged and ordinary table caption regression passed, the three named candidate files remained the scope, all pre-existing dirty paths including `openspec/**` were preserved, one local commit, no push.
- 2026-08-23 - V2-506P1 re-sliced before implementation: direct table fixtures require the canonical typed-cell constructor, but the current production RenderPlan exposes only `text`/`markdown`; moved V2-506M ahead of V2-506P1 so the next cycle can establish the constructor without a failing fixture-only intermediate state; no product code edited, no commit or push.
- 2026-08-23 - V2-506M re-sliced before implementation: strict typed-cell removal spans `render_plan.py`, `compiler.py` and the three direct fixture files, so a green three-file cycle needs an ordered typed-constructor preparation first; added V2-506T, then V2-506P1, V2-506M and V2-506D, with no product code edited, no commit or push.
- 2026-08-23 - V2-506T Checker PASS Attempt 1; exact Verify 6/6, related compiler/DOCX/core inline regression 124/124, Preview/Review 11/12 with the identical clean-HEAD YAML Front Matter baseline failure, target Ruff, `git diff --check`, LOOP-LINT, and independent typed-boundary/renderer-neutral/scope audits passed; V2-506T moved from Open to Done, `openspec/**` was preserved and unstaged, one local commit, no push.
- 2026-08-23 - V2-506P1 Checker PASS Attempt 1; exact Verify 17/18 with the sole clean-baseline `TF-SOURCE-LEGACY-001` failure reproduced at the same Preview test on isolated `HEAD=08eb4d8`, AST fixture audit and table payload/Preview/Review assertions passed, typed-table/compiler regression 30/30 and DOCX regression 90/90 passed, target Ruff/diff-check/LOOP-LINT passed, three-file product scope and unstaged `openspec/**` were preserved, one local commit, no push.

- 2026-08-23 - V2-506M Checker FAIL Attempt 1; exact Verify passed 7/7, related regression failed with 130 passed and 2 failed because `tests/test_compiler.py` still accesses removed `table.markdown`, plus the known clean-baseline `TF-SOURCE-LEGACY-001` YAML Front Matter failure; target Ruff, `git diff --check`, and `./lint-loop.sh` passed; candidate files were restored to `HEAD=e0ac590`, V2-506M was re-sliced into V2-506M1 and V2-506M2, V2-506D became ordered child 5/5, no product candidate remains, no commit or push.

- 2026-08-23 - V2-506M1 Checker PASS Attempt 1; exact Verify 24/24, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; the candidate diff was exactly one `tests/test_compiler.py` assertion replacement, `table.markdown` has no remaining consumer under `tests`, `src`, or `frontend`, no production compatibility path or compiler behavior change was introduced, and `V2-506M1` moved from Open to Done; `openspec/**` and pre-existing `LOOP.md` changes were preserved and unstaged, one local commit, no push.
- 2026-08-23 - V2-506M2 Checker PASS Attempt 1; exact Verify passed 7/7, related regression passed 131/132 with the sole clean-baseline `TF-SOURCE-LEGACY-001` Preview failure reproduced on clean HEAD, target Ruff, `git diff --check`, LOOP-LINT, and independent typed-table CodeGraph/runtime/scope audits passed; V2-506D was not started, pre-existing `openspec/**` paths were preserved and unstaged, one local commit, no push.
- 2026-08-23 - V2-506D Checker PASS Attempt 1; exact Verify 1/1, related regression 123/123, target Ruff, `git diff --check`, LOOP-LINT, and independent DOCX OPC/XML audit passed; object.table evidence path matched and was executable, all pre-existing `openspec/**` paths remained unstaged, one local commit, no push.
- 2026-08-23 - V2-511E Checker FAIL Attempt 1; pytest passed 3/3 and `git diff --check` passed, but the exact target Ruff failed `I001` import ordering in `tests/renderers/docx/test_math_corpus_v2.py`; independent canonical-pipeline, native OMML/XML, SEQ/bookmark, Review marker, structured-diagnostic, wrong-backslash, and manifest-path audits passed; V2-511E remains Open, no candidate repair, no commit or push, and pre-existing `openspec/**` paths were preserved.
- 2026-08-23 - V2-511E Checker PASS Attempt 2; exact Verify passed 3/3, target Ruff, `git diff --check`, LOOP-LINT, and independent AST/runtime/XML audit all passed; canonical parser -> Equation IR -> EquationInstruction -> validation/math preflight -> ReviewEquationContent -> DOCX was executable offline, fraction/sum/matrix produced real `m:f`/`m:nary`/`m:m`, SEQ and formula bookmark pairs were exact, visible Review/DOCX text was marker-free, unsupported/malformed diagnostics were structured, raw backslash corpus and no-hidden-skip checks passed, and the manifest evidence path was executable; V2-511E moved to Done with original Behavior/Acceptance and Attempt 1 retained, Open order preserved, candidate scope limited to `tests/renderers/docx/test_math_corpus_v2.py` plus `LOOP.md`, all pre-existing `openspec/**` paths preserved and unstaged, one local commit, no push.
- 2026-08-23 - V2-507E split into ordered children V2-507E1 through V2-507E4 after current CodeGraph and source audits found listing/algorithm numbering policy, symbol resolution, typed RenderPlan/compiler data, Review projection and DOCX evidence span more than three repository files; no product code edited, the original Behavior/Acceptance remain immutable, V2-503E stays after the four children, and the preserved `openspec/**` worktree remains untouched.
- 2026-08-23 - V2-507E1 Checker PASS Attempt 1; exact Verify passed 4/4, related symbol/template regression passed 83/83, compiler/DOCX regression passed 114/114, target Ruff, `git diff --check`, LOOP-LINT, and independent template/symbol runtime probes passed; V2-507E1 moved to Done, V2-507E2 remains next, the candidate scope was exactly the three named files plus this lifecycle update, all pre-existing `openspec/**` paths were preserved and unstaged, one local commit, no push.
- 2026-08-23 - V2-507E2 Checker PASS Attempt 2; exact Verify passed 2/2, related core/compiler/DOCX regression passed 129/129, target Ruff, `git diff --check`, LOOP-LINT, and independent typed numbering/payload/renderer-neutral probes passed; Attempt 1's DOCX `field_code` payload leakage was removed while `SequenceInstruction.field_code` remained available to DOCX renderers; V2-507E2 moved to Done, V2-507E3 remains next, the candidate scope was exactly the three named files plus this lifecycle update, all pre-existing `openspec/**` paths were preserved and unstaged, one local commit, no push.
- 2026-08-23 - V2-507E3 Checker PASS Attempt 1; exact Verify passed 2/2, related Review regions passed 6/6, Preview passed 5/6 with only the known clean-baseline YAML Front Matter rejection, compiler/RenderPlan passed 30/30, target Ruff, `git diff --check`, LOOP-LINT, and independent Review marker/source-navigation probes passed; V2-507E3 moved to Done, V2-507E4 remains next, the candidate scope was exactly the named test file plus this lifecycle update, all pre-existing `openspec/**` paths were preserved and unstaged, one local commit, no push.
- 2026-08-23 - V2-406 Checker PASS Attempt 2; exact Verify passed 6/6, Review regression passed 8/8, target Ruff, `git diff --check`, LOOP-LINT, and independent 8/8 runtime plus 5/5 static mutation audits passed; V2-406 moved to Done with original Behavior/Acceptance and Attempt 1 retained, the canonical parser/compiler/Review path and source-navigation/code-literal boundaries were verified, candidate scope was exactly the named test file plus this lifecycle update, all pre-existing `openspec/**` paths were preserved and unstaged, one local commit, no push.
- 2026-08-23 - V2-518 Checker PASS Attempt 1; exact Verify passed 9/9, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent AST/runtime audit confirmed the canonical parser backend import, no YAML Front Matter or legacy `:::` inputs, typed Figure/Listing/Algorithm/Equation objects, citation order and manual-cache absence; V2-518 moved from Open to Done, candidate scope remained exactly the three named files, all pre-existing `openspec/**` paths were preserved and unstaged, one local commit, no push.
- 2026-08-23 - V2-520 Checker PASS Attempt 1; exact Verify passed 18/18, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent AST/runtime audit confirmed both tests import `MarkdownItParserBackend` and `ParseError` from canonical modules, retain standard fence/equation typed assertions and structured diagnostics, and contain no legacy parser import, fallback, compatibility layer, or dual source of truth; V2-520 moved to Done, candidate scope remained exactly the two named tests plus `LOOP.md`, all pre-existing `openspec/**` paths were preserved and unstaged, one local commit, no push.
- 2026-08-23 - V2-521 Checker PASS; exact Verify passed 6/6, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent AST/runtime audit confirmed the canonical `MarkdownItParserBackend` path, `ParseError` from `parser_support` only, unchanged table/caption/alignment/typed-inline/structured-error assertions, no legacy parser import, YAML Front Matter, legacy `:::`, fallback, compatibility layer, or dual source of truth; candidate scope remained exactly `LOOP.md` and `tests/core/test_markdown_v2_tables.py`, all pre-existing `openspec/**` paths were preserved and unstaged, one local commit, no push.
- 2026-08-23 - V2-526 Checker FAIL Attempt 1; exact Verify passed 5/5, target Ruff and `git diff --check` passed, related regression passed 129/129, and independent runtime/static probes passed canonical projection, 11/11 cover fields, 2/2 missing-metadata diagnostics, stale-metadata replacement, and no legacy parser/fallback/compatibility path; expected direct target-test evidence for all fields and missing diagnostics was absent, so the candidate product/test files were restored, all pre-existing `openspec/**` changes were preserved, and no commit or push.

- 2026-08-23 - V2-526 Checker PASS Attempt 2; exact Verify passed 5/5, target Ruff, `git diff --check`, `./lint-loop.sh`, and related manifest/validator/compiler regression passed 130/130; independent runtime/static audit passed complete and empty manifest projection, 11/11 cover fields, stale-metadata replacement, canonical parser use, and no legacy parser/fallback/compatibility path; mutation audit caught 11/11 cover-field mutations, empty-manifest diagnostic suppression, and stale-metadata merge; V2-526 moved from Open to Done, candidate scope remained exactly `LOOP.md`, `src/thesis_forge/core/validator.py`, and `tests/core/test_manifest_resource_validation.py`, all pre-existing `openspec/**` changes were preserved, one local commit, no push.
- 2026-08-23 - V2-527A Checker PASS Attempt 1; exact Verify passed 90/90, target Ruff, `git diff --check`, and `./lint-loop.sh` passed; independent AST/runtime audit confirmed the canonical parser migration, front-matter-free source, retained style/field/Review-neutral/DOCX XML assertions, no legacy parser/fallback/compatibility/alternate-source path, and no production diff; V2-527A moved from Open to Done, V2-527B/C remained Open, candidate scope was exactly `LOOP.md` and `tests/test_docx_renderer.py`, all pre-existing `openspec/**` changes were preserved, one local commit, no push.

- 2026-08-23 - V2-527B Checker PASS Attempt 1; exact Verify passed 21/21, target Ruff, `git diff --check`, `./lint-loop.sh`, and canonical parser regression passed 97/97; independent AST/runtime audit confirmed the obsolete V1 parser tests are absent, no production/tooling reference or test-only compatibility shim exists, canonical V2 parser construction/blocks/inlines and structured Front Matter/legacy rejection evidence remain executable, V2-527B moved from Open to Done, V2-527C remained Open, all pre-existing `openspec/**` changes were preserved, one local commit, no push.
- 2026-08-23 - V2-527C Checker PASS Attempt 1; exact Verify passed 17/17, related regression passed 19/19, target Ruff via the project `.venv/bin/ruff`, `git diff --check`, and `./lint-loop.sh` passed; independent AST/assertion/runtime audit confirmed canonical parser and typed-domain fixture coverage, all 17 tests and 53 assertions retained, no legacy parser import/call, YAML Front Matter, `:::`, old reference source, fallback, compatibility branch or dual data source, and only `tests/test_validator.py` was the candidate diff while all pre-existing `openspec/**` changes were preserved; V2-527C moved from Open to Done, no push.
- 2026-08-23 - V2-528 Checker PASS Attempt 1; exact Verify `.venv/bin/python -m pytest tests/test_architecture.py` passed 9/9; related regression `.venv/bin/python -m pytest tests/core/test_single_parser_backend.py tests/core/test_legacy_source_rejection.py tests/test_parser_backend.py` passed 15/15; `.venv/bin/ruff check tests/test_architecture.py`, `git diff --check`, and `./lint-loop.sh` passed (`open=0 done=159 blocked=0` after this move); independent AST/import audit confirmed the canonical target `thesis_forge.core.parser_backend`, no legacy import statement or `parser_module` identifier, three retained `thesis_forge.core.parser` string rejection assertions, all 9 test functions and 17 assertions retained, unchanged renderer/CLI/UI/frontend forbidden-import test bodies, and no fallback, compatibility branch, or product code; candidate scope before this lifecycle update was exactly `tests/test_architecture.py`, all pre-existing `openspec/**` changes were preserved and unstaged, one local commit, no push.
- 2026-08-23 - V2-529 Checker PASS Attempt 2; exact Verify passed with 47 display equations, 2 inline equations, 49 `m:oMath` nodes, `per_equation_all_ok=True`, `inline_math_converted=True`, and `openxml_validate exit=0`; related parser/OMML regression passed 22/22, target Ruff, `git diff --check`, and LOOP-LINT passed (`open=2 done=160 blocked=0`); independent scope and runtime audit confirmed the three named files, manifest-derived metadata/template selection, fail-fast structural assertions, no legacy parser/fallback/compatibility path, and preservation of all pre-existing `openspec/**` changes; one local commit, no push.
- 2026-08-23 - V2-530 Checker PASS Attempt 2; exact Verify passed 4/4, the independent wider regression passed 197/197, target Ruff, `git diff --check`, and LOOP-LINT passed (`open=2 done=160 blocked=0` before this move); runtime and mutation audits confirmed zero legacy fixture reads, complete tmp-path V2 project inputs, restored citation/footnote/bibliography DOCX coverage, retained structural field/bookmark/footer/diagnostic assertions, and unchanged pre-existing `openspec/**` worktree state; one local commit, no push.
- 2026-08-23 - V2-531 Checker PASS Attempt 1; exact Verify exited 0, `git diff --check` and LOOP-LINT passed (`open=3 done=161 blocked=0` before this move); independent AST/runtime and protected-path audits confirmed `compare.py` removal, no active legacy parser calls in `spikes/phase0/parser`, unchanged historical reports/results/fixtures, and preserved pre-existing `openspec/**` changes; one local commit, no push.

- 2026-08-23 - V2-533A Checker PASS Attempt 1; exact Verify passed 2/2, canonical parser regression passed 46/46, target Ruff, `git diff --check`, and LOOP-LINT passed (`open=2 done=163 blocked=0` before this move); independent AST audit confirmed the parser_support target, all four primitive import/definition assertions, private-name guard, CommonMark/GFM rules, and no compatibility/fallback/legacy branch; candidate product diff was exactly `tests/core/test_markdown_v2_parser_config.py`, all pre-existing LOOP/openspec/tests/test_lo_finalizer.py changes were preserved, no push.
## Sync log
