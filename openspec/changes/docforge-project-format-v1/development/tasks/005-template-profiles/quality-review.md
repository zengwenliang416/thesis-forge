# Quality Review: 005-template-profiles

## Verdict

approved

## Review Scope

- Independent quality re-review of the current working tree on August 27,
  2026.
- This review changed only this file. No implementation, ledger, report, or
  spec-review file was modified.
- The six findings from the previous review were independently reproduced
  against the current code and closed below.

## QR Closure

- **QR-001: RenderPlan empty optional bindings — closed (HIGH).**
  `_compile_cover()` now rejects unresolved required bindings and constructs
  `CoverInstruction.bindings` only from non-empty resolved values
  (`src/docforge/core/compiler.py:417-436`). An independent minimal generic
  compile produced exactly
  `(('metadata.title.zh', 'Only title'),)` with no empty values. The
  regression in `tests/compiler/test_template_profiles.py:69-103` asserts the
  same RenderPlan boundary, not only DOCX visibility.

- **QR-002: legacy Validator required default — closed (HIGH).**
  The thesis-shaped default was removed; `ValidationContext` defaults to an
  empty tuple and `from_document()` maps an omitted argument to `()`
  (`src/docforge/core/validator.py:60-104`). A bare document validated with
  both `ValidationContext()` and `ValidationContext.from_document(...)`
  produced no `required-metadata` issue. Template-owned requirements remain
  active through the same validator path and include `template_id`
  (`src/docforge/core/validator.py:239-270`).

- **QR-003: English-only locale handling — closed (MEDIUM).**
  `ManifestBindingData` carries project language, primary language subtags
  are normalized, and grouped localized bindings choose the preferred value
  with deterministic fallback (`src/docforge/templates/bindings.py:17-24`,
  `49-62`, `106-180`). Independent checks covered `zh-Hant`, `zh-TW`
  bilingual preference, `en-GB` English-only, `en-US` Chinese fallback, and
  missing-title diagnostics. The English-only generic project validated
  without a required-metadata issue and compiled one binding:
  `('metadata.title.en', 'English-only title')`. The generic template declares
  the one-title group in `templates/base/docforge-standard.yaml:14-35`;
  no duplicate fallback title was emitted.

- **QR-004: generic clean-install coverage — closed (HIGH).**
  The distribution verifier now requires the generic template in wheel and
  sdist checks and runs installed `inspect`, `validate`, `review`, and `build`
  for both `docforge-general` and `docforge-academic`, including visible DOCX
  text assertions (`scripts/verify_distribution.py:30-89`,
  `457-588`). A fresh wheel/sdist build followed by the verifier returned
  `ok=True`, `isolated_install=True`; both fixture flows completed all four
  stages. The generic DOCX contained the expected common values and none of
  the forbidden academic labels.

- **QR-005: `compile_document()` required-field fail-open — closed (MEDIUM).**
  `MissingRequiredBindingError` is a `CompilerError` carrying deterministic
  missing paths (`src/docforge/core/compiler.py:149-157`, `417-436`).
  Direct compilation of an academic template without its profile raised the
  error before returning a plan, with all eight expected missing paths.
  Application validation still reports structured template-scoped issues
  before its compile handoff.

- **QR-006: binding registry parity — closed (MEDIUM).**
  The descriptor registry now owns labels, formatting kinds, localized
  groups, and default-cover selection (`src/docforge/templates/model.py:191-285`,
  `433-439`). Resolver formatting and presentation labels consume that
  registry (`src/docforge/templates/bindings.py:65-103`,
  `src/docforge/presentation/metadata.py:1-4`). Independent parity checks
  matched all 18 `MetadataBindingPath` values and presentation labels;
  tests also cover custom multi-author joining with `join_with=" & "`
  (`tests/templates/test_metadata_bindings.py:54-65`, `137-158`).

## Separation Of Concerns

- Manifest data remains grouped as `metadata`, optional `academic`, and
  `render`; locale context is attached without flattening the domain model.
- Required-field enforcement and optional omission happen before RenderPlan
  construction. `CoverInstruction` contains renderer-neutral binding pairs,
  and the DOCX cover renderer only consumes template items and resolved values
  (`src/docforge/core/render_plan.py:531-553`,
  `src/docforge/renderers/docx/cover.py:11-32`).
- A static scan found no renderer branch on document type, profile, or
  template ID.

## Component Cohesion / Coupling

- Binding descriptors, locale selection, required-field enforcement, and
  presentation labels remain in their owning template/compiler/presentation
  modules.
- The compiler hands renderer-neutral binding pairs to RenderPlan; the DOCX
  renderer does not inspect project profiles or template identities.
- No new cross-layer dependency or compatibility path was introduced.

## Test Quality

- `PYTHONPATH=src .venv/bin/python -m pytest tests/templates tests/compiler tests/project -q`
  -> `128 passed`.
- `PYTHONPATH=src .venv/bin/python -m pytest tests/templates/test_metadata_bindings.py tests/compiler/test_template_profiles.py tests/test_distribution.py -q`
  -> `27 passed`.
- Extended compiler, template, RenderPlan, manifest-resource, and review
  regressions -> `119 passed`.
- Scoped `ruff check` -> passed; `git diff --check` -> passed.
- The targeted C901 check still reports four inherited large functions:
  `_compile_inlines`, `_initial_citation_numbers`, `_compile_block`, and
  `_validate_bibliography`. The new binding module and cover helper do not
  introduce a new complexity finding; this remains a non-blocking inherited
  risk.

## Error Handling

- Required template bindings fail before RenderPlan construction through
  `MissingRequiredBindingError`, while application validation returns
  structured template-scoped diagnostics.
- The current full Python suite passes (`1379 passed`), including the
  repository-owned projects and fixtures that had previously exercised
  obsolete manifest and source contracts. Those earlier failures remain in
  the append-only validation ledger with later passing adjudication.

## Scope Notes

- `src/docforge/presentation/metadata.py` and
  `scripts/verify_distribution.py` are direct consumers needed to close
  QR-006 and QR-004, although the original brief's allowed-file list did not
  explicitly name them. This is an ownership/bookkeeping note for the lead,
  not an unresolved functional defect in the Task 005 slice.

## Reuse / Duplication

- The descriptor registry is reused by binding resolution, default-cover
  selection, and presentation labels.
- General and academic clean-install flows use the same package, CLI,
  validator, compiler, and renderer path.
- No duplicate binding registry, template loader, or profile-specific compile
  pipeline was added.

## Complexity Delta

- Complexity added by locale-aware bindings and required-field enforcement is
  localized to existing template/compiler modules and directly covers the task
  contract.
- Four inherited C901 findings remain non-blocking; the new binding module and
  cover helper do not add another complexity finding.

## Residual Risk

- Manually constructed `CoverInstruction` values are not runtime-validated
  against the closed path registry, but compiler-produced plans are typed and
  all template fields are validated before resolution.
- Full repository release, desktop E2E, and other task-owned checks remain
  outside this review. No blocking Task 005 quality finding remains.

## Required Fixes

- None for the Task 005 quality slice.

## Acceptance Assertions Verified

- `A2`: the generic template validates and builds without academic-only
  metadata or labels.
- `A3`: typed academic metadata remains optional and template-scoped.
- `A7`: binding resolution, validation, RenderPlan, and installed package
  flows pass for generic and academic projects.
