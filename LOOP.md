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

- [V2-102] Emit typed failed BuildReports from the backend build stream
  - Files: `src/thesis_forge/adapters/runtime.py`, `tests/adapters/test_build_report_events.py`
  - Behavior: validation, compile, render, finalize, permission, cancellation, and transport failures emit a terminal typed report instead of one error string
  - Verify: `.venv/bin/python -m pytest tests/adapters/test_build_report_events.py`
  - Acceptance: every terminal failure includes outcome, failedStage, complete diagnostics, primaryDiagnosticId, stage states, and sanitized logs; validation issues retain code, severity, source line, target, details, and order
  - Verification-surface change: authorized; creates one focused event-stream test
  - Attempts: 0

- [V2-103] Parse BuildReport v2 in the frontend transport
  - Files: `frontend/src/transport/buildEvents.ts`, `frontend/src/transport/buildEvents.test.ts`
  - Behavior: the frontend accepts the protocol examples for success and failure, rejects message-only terminal errors, and exposes typed stage and diagnostic data
  - Verify: `pnpm --dir frontend test -- buildEvents.test.ts`
  - Acceptance: runtime guards validate outcome, intent, stage lifecycle, diagnostics, primary error, logs, source ranges, and output/stale-preview fields without using `any`
  - Verification-surface change: authorized; creates one focused transport test
  - Attempts: 0

## Done

- [V2-101] Introduce the typed application BuildReport contract
  - Files: `src/thesis_forge/application/contracts.py`, `tests/application/test_build_report_contract.py`
  - Behavior: application-layer success, validation failure, stage failure, cancellation, and permission failure can all be represented by one typed BuildReport with stage lifecycle, complete diagnostics, a primary diagnostic, bounded logs, intent, outcome, and output policy
  - Verify: `.venv/bin/python -m pytest tests/application/test_build_report_contract.py`
  - Acceptance: BuildValidationError preserves every original issue; message-only terminal failures are not part of the application contract; stage states distinguish pending/running/succeeded/failed/skipped
  - Verification-surface change: authorized; creates one focused contract test
  - Attempts: 0

## Blocked

## Cycle log

- 2026-08-20 - V2-101 Checker PASS; exact Verify `.venv/bin/python -m pytest tests/application/test_build_report_contract.py` passed 6 tests; scope limited to the two named implementation/test files, no push.

## Sync log
