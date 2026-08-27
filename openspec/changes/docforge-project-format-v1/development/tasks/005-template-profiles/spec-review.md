# Spec Review: 005-template-profiles

## Verdict

approved

This independent review covers Task 005 items 5.1 through 5.5 against the
current checkout on August 27, 2026. The Task 005 slice satisfies the
generic-template, typed-profile, template-resolution, RenderPlan, and
renderer-neutral binding requirements. This verdict does not close the
broader change-level acceptance ledger.

## Missing Requirements

- None for Task 005 items 5.1 through 5.5.
- `5.1`: `tests/templates/test_metadata_bindings.py` covers common and
  academic binding values, template-scoped required metadata, registry/path
  parity, locale selection, and custom multi-author joining. The compiler
  tests cover optional metadata omission and direct failure for unresolved
  academic requirements.
- `5.2`: manifest data remains grouped as typed `metadata`, optional
  `academic`, and `render` values. `resolve_template_bindings()` resolves
  template-declared values before `CoverInstruction` construction, while
  required values are enforced and empty optional values are omitted at the
  RenderPlan boundary.
- `5.3`: `docforge-standard` is present in the checkout and wheel force-include
  list. It declares only common metadata fields and has one required group,
  `metadata.title`, containing locale alternatives that resolve to one
  effective title. It declares no academic fields or academic placeholders.
- `5.4`: repository-owned academic templates use typed `academic.*` and
  `metadata.*` paths. Academic requirements remain owned by template
  declarations; the parser and DOCX renderer contain no general/academic
  document-type or template-ID branch.
- `5.5`: general and academic fixtures resolve through the selected templates,
  produce binding-based RenderPlans, complete the CLI flow, and pass visible
  DOCX checks. The packaged wheel is also exercised without checkout template
  files.

## Extra Behavior

- None in product behavior. The registry-backed presentation lookup, compiler
  enforcement, and isolated distribution checks are direct consumers and
  verification support for the Task 005 binding boundary; no compatibility
  alias, fabricated metadata, parser branch, or renderer profile branch was
  added.

## Misunderstood Requirements

- None. Academic metadata remains an optional typed profile and becomes
  required only when the selected academic template declares it.
- The generic template's title alternatives intentionally share one required
  group, so a `zh-*` or `en-*` project may satisfy the requirement with its
  preferred locale or the available fallback. A missing subtitle remains
  valid, and the generic template renders only fields it declares.
- The active project-template resolver is the strongly typed YAML model under
  `src/docforge/templates/model.py`; the separate `templates/v2` pipeline is
  not an active project-template resolution path for this task.

## Cannot Verify From Diff

- Full change-level CLI/desktop E2E, protocol parity, installed-workbench
  sensory behavior, repository facticity, release closure, and the final
  acceptance receipt remain owned by other tasks.
- `A2`, `A3`, and `A7` are verified here only for the Task 005
  general/academic template, compiler, RenderPlan, and renderer-neutral slice.
  This review does not claim complete cancellation, atomic-output, or
  cross-runtime lifecycle verification.
- `acceptance.json` still records the change-level assertions as `failing`;
  this task-local approval does not change those statuses.
- The task report records implementation files outside the original brief
  allowlist, including `src/docforge/core`, presentation metadata, packaging,
  and distribution verification. Those files are direct consumers required by
  the current implementation boundary; ownership reconciliation remains a
  controller/ledger concern, not an unresolved Task 005 functional defect.

## Acceptance Assertions Verified

- `A2` (Task 005 slice): the general fixture uses `document.md` and
  `docforge-standard`; `inspect`, `validate`, `review`, and `build` complete,
  and the generated Review/DOCX contain common metadata without academic
  labels or values.
- `A3` (Task 005 slice): the academic fixture supplies the typed optional
  academic profile and builds with an academic template, while the general
  fixture validates without university, degree, advisor, student, or
  completion requirements.
- `A7` (Task 005 slice): general and academic documents produce resolved
  binding-based RenderPlans consumed by the same DOCX cover renderer. Static
  inspection found no renderer branch on document type, profile, or template
  ID.

## Required Fixes

- None for Task 005. No blocking spec or implementation gap remains in items
  5.1 through 5.5.

## Verification Evidence

- `PYTHONPATH=src .venv/bin/python -m pytest tests/templates tests/compiler tests/project tests/core/test_manifest_resource_validation.py tests/test_distribution.py -q`
  -> `147 passed in 20.06s`.
- `PYTHONPATH=src .venv/bin/python -m pytest tests/templates/test_metadata_bindings.py tests/compiler/test_template_profiles.py -q`
  -> `13 passed in 1.29s`; this directly covers the Task 005 binding,
  locale, required-group, RenderPlan, and visible generic DOCX assertions.
- `.venv/bin/ruff check src/docforge/templates src/docforge/core/compiler.py src/docforge/core/validator.py src/docforge/core/render_plan.py src/docforge/project tests/templates tests/compiler tests/project tests/core/test_manifest_resource_validation.py tests/test_distribution.py scripts/verify_distribution.py`
  -> `All checks passed!`.
- `dist=$(mktemp -d /tmp/docforge-spec-review-20260827-r3.XXXXXX)` followed by
  `.venv/bin/python -m build --no-isolation --wheel --sdist --outdir /tmp/docforge-spec-review-20260827-r3.fsObYe`
  -> `DIST_DIR=/tmp/docforge-spec-review-20260827-r3.fsObYe`; built
  `docforge-0.1.0-py3-none-any.whl` and `docforge-0.1.0.tar.gz`.
- `PYTHONPATH=src .venv/bin/python scripts/verify_distribution.py --dist-dir /tmp/docforge-spec-review-20260827-r3.fsObYe`
  -> `ok: true`; the wheel contained 93 files, isolated installation and
  `pip check` passed, and both `docforge-general` and `docforge-academic`
  completed `inspect`, `validate`, `review`, and `build` with Review artifacts
  and visible DOCX checks.
- Inline A2/A3/A7 fixture probe using
  `PYTHONPATH=src .venv/bin/python` resolved `docforge-general` through
  `docforge-standard` with 6 common bindings and no academic text, resolved
  `docforge-academic` through `example-university-2026` with 10 expected
  academic bindings, and rendered both plans through the same `DocxRenderer`
  without validation errors.
- Inline locale/required-binding probe using
  `PYTHONPATH=src .venv/bin/python` selected `metadata.title.zh` for `zh-TW`
  and `metadata.title.en` for `en-GB`, accepted an English-only title,
  produced one `metadata.title` required-group issue when absent, and direct
  compilation of an academic template without its required profile raised
  `MissingRequiredBindingError` before returning a plan.
- `rg -n -i 'document\.type|template_id|docforge-standard|academic' src/docforge/renderers`
  and the same scan over the three parser modules -> no matches
  (`renderer_scan_exit=1`, `parser_scan_exit=1`).
- `git diff --check` -> passed.
