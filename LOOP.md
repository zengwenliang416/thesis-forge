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

- [V2-103A2] Preserve live-preview BuildReport diagnostics and cancellation state
  - Parent: ordered child 2/2 of `V2-103A`; the parent requirement remains unchanged: live-preview failures expose typed diagnostics and do not remain stuck in building state.
  - Files: `frontend/src/components/WorkbenchApp.tsx`, `frontend/src/state/workspace.ts`, `frontend/src/components/WorkbenchBuildFlow.test.tsx`
  - Behavior: live-preview `completed.report` diagnostics retain source line, target and details in workspace state; canceled reports end the active preview operation without stealing or leaving the preview in `building`.
  - Verify: `pnpm --dir frontend test -- WorkbenchBuildFlow.test.tsx && pnpm --dir frontend typecheck`
  - Acceptance: publish/live-preview completed-report regression tests cover failed, canceled and diagnostic-bearing reports; stale/previous preview state is not overwritten by a failed or canceled attempt.
  - Verification-surface change: authorized; adds focused Workbench completed-report regression cases.
  - Attempts: 0

- [V2-105] Emit correct typed stage lifecycle transitions
  - Files: `src/thesis_forge/application/services.py`, `tests/application/test_build_stage_lifecycle.py`
  - Behavior: emit stage started before work, succeeded only after completion, failed on error and skipped for downstream stages.
  - Verify: `.venv/bin/python -m pytest tests/application/test_build_stage_lifecycle.py`
  - Acceptance: entering validate does not mark validate successful; a validate failure marks compile/render/finalize/postflight skipped.
  - Verification-surface change: authorized; creates one focused lifecycle test.
  - Attempts: 0

## Done

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

## Sync log
