# Task Report: 006-outline-renderer-neutral-preview

## Status

DONE

## Files Changed

- `src/thesis_forge/application/{contracts,services}.py`
- `src/thesis_forge/adapters/runtime.py`
- `src/thesis_forge/presentation/**`
- `frontend/src/transport/**`
- `frontend/src/state/**`
- `frontend/src/components/**`
- `frontend/src/styles.css`
- `frontend/e2e/workbench.spec.ts`
- `tests/fixtures/preview-workbench-v1.json`
- focused Python and frontend preview tests

## What Changed

- Added `PreviewResult` and `preview_service`. The service reuses the existing
  parse and validation boundaries, compiles only when validation has no fatal
  issue and a template is available, and never invokes the renderer or writes
  an output package.
- Added one framework-neutral presentation mapper for headings, source
  locations, diagnostics markers, compiler order, numbering labels, inline
  references/citations/footnotes, cover, sections, TOC, lists, figures, tables,
  equations, listings, algorithms, bibliography, and explicit unsupported
  nodes.
- Added one versioned `preview` operation to the shared command envelope and
  Python dispatcher. Web and Tauri continue to use the same transport DTO and
  dispatcher contract.
- Added strict nested TypeScript preview validation. Partial preview responses,
  unknown content payloads, invalid source lines, and private `assetPath`
  fields are rejected. Legacy inspect responses containing only `outline`
  remain accepted.
- Added shared outline and paper-preview React components. Outline and preview
  use the same deterministic `selectionId`, optional `semanticId`, and source
  line; activation updates one workspace selection and focuses the editor when
  a line is available.
- Added empty, loading-preserved, ready, validation-blocked, dirty-preserved,
  and unsupported presentation behavior. The paper preview always displays
  `结构预览不代表 Word 最终分页。`
- Replaced the prior refresh-time `inspect` plus `validate` pair with one
  `preview` request that returns diagnostics, outline, and preview from the same
  saved source snapshot.

## TDD Evidence

- Initial Python RED returned `9 failed, 45 passed` because `PreviewResult`,
  `preview_service`, the presentation mapper, adapter operation, and
  architecture boundary did not exist.
- Initial frontend RED returned `10 failed, 1 passed` because deep DTO
  validation, preview state/events, panel components, transport flow, stale
  suppression, and shared selection did not exist.
- Initial GREEN returned `57 passed` for the focused Python set and `14 passed`
  for the new Slice 006 frontend tests.
- Full frontend regression exposed six compatibility failures: legacy inspect
  responses were misclassified as preview responses and four older
  `WorkbenchApp` tests still expected `inspect` plus `validate`.
- Compatibility GREEN preserved legacy inspect while requiring complete
  preview payloads and updated the old tests to the single preview operation;
  the full frontend suite returned `45 passed`.
- The complete bachelor thesis example was then added as a real
  service-to-presentation regression. It verifies compiler order and the
  template-resolved labels `图1-1`, `(2-1)`, and `表2-1`; the focused Python
  set returned `58 passed`.
- Playwright first failed before test execution because Node ESM required a JSON
  import attribute. The E2E fixture loader was changed to `readFileSync` using
  the same golden file; the browser matrix then returned `9 passed`.

## Verification Commands

- `pnpm frontend:test` -> `45 passed`.
- `pnpm frontend:typecheck` -> passed.
- `pnpm frontend:lint` -> passed.
- `pnpm frontend:build` -> Vite production bundle built.
- `pnpm frontend:e2e` -> `9 passed`, `9` intentional runtime/viewport skips.
- focused Python command from the task brief -> `58 passed`.
- `.venv/bin/python -m pytest -q` -> `217 passed in 18.07s`.
- `.venv/bin/ruff check .` -> all checks passed.
- `.venv/bin/python -m pip check` -> no broken requirements.
- `cargo fmt --manifest-path src-tauri/Cargo.toml -- --check` -> passed.
- `cargo test --manifest-path src-tauri/Cargo.toml` -> `4 passed`.
- `cargo check --manifest-path src-tauri/Cargo.toml` -> passed.
- `OPENSPEC_TELEMETRY=0 openspec validate
  build-thesisforge-desktop-ui --strict --json` -> one change passed.
- CodeGraph sync/context -> 126 files, zero pending changes,
  `ev-msa0ibb8` and `ev-msa0ipb3` matched the Slice 006 claim.
- `git diff --check` -> passed before lifecycle closure.

## Concerns

- Exact Word pagination and installed Windows acceptance remain outside this
  slice.
- Unknown future inline-run variants are currently omitted by the mapper rather
  than represented as a new inline unsupported type. The current compiler
  closed union is fully covered; any future inline type must extend the
  versioned DTO and tests.

## Scope Deviations

- None. Parser syntax/IDs, validator rules, template schema and resolver
  precedence, compiler numbering, bibliography semantics, renderer behavior,
  DOCX/OOXML output, database, AI, telemetry, accounts, and packaging were not
  changed.

## Extraction Decision

- Extracted the renderer-neutral Python presentation owner,
  `frontend/src/state/preview.ts`, `PreviewPanels.tsx`, and `PanelHeader.tsx`
  instead of expanding the adapter, reducer, or old panel placeholder owners.
- Kept the versioned preview types and validators in `transport/dto.ts` for
  protocol atomicity. The file is now 644 lines, below the 800-line review
  threshold; extract a dedicated preview DTO owner if Slice 007 adds more
  transport schema.
- Kept the two small preview-response application paths in `WorkbenchApp` for
  this slice. If Slice 007 adds progress/cancellation response variants, extract
  one helper that validates and applies preview responses to avoid drift.

## Follow-up Needed

- Slice 007 remains responsible for background build progress and cancellation.
- Slice 008 remains responsible for complete Web/macOS/Windows distribution
  acceptance.

## Adjudication

Tasks `6.1` through `6.7` are complete with independent spec and quality review,
direct evidence for the preview portion of `A2`, and supporting boundary
evidence for `A7`, `A10`, `A11`, and `A12`. Whole-change verification and
release remain incomplete because Slices 007 and 008 are still open.
